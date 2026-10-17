"""Reduced-order IGBT laboratory. SI units internally; no external dependencies.

Backward-Euler modified nodal equations, with a safeguarded scalar Newton solve.
The verdict is calculated from the solved waveforms and explicit limits.
See MODEL.md for equations, provenance, scope and omitted physics.
"""
import math
from datetime import datetime, timezone
from uuid import uuid4

VERSION = '2.0.0'
PARAMETERS = [
    # key, label, default, minimum, maximum, step, unit, category
    ('bus_v', 'DC bus', 400, 20, 1400, 10, 'V', 'circuit'),
    ('load_uh', 'Load inductance', 500, 20, 2000, 10, 'µH', 'circuit'),
    ('load_r', 'Load resistance', .1, .01, 20, .01, 'Ω', 'circuit'),
    ('pulse_us', 'First pulse duration', 75, 1, 150, 1, 'µs', 'circuit'),
    ('gap_us', 'Off interval', 8, 2, 30, 1, 'µs', 'circuit'),
    ('second_us', 'Second pulse duration', 3, .5, 10, .5, 'µs', 'circuit'),
    ('gate_on', 'Gate drive ON', 15, 0, 22, .5, 'V', 'gate'),
    ('gate_off', 'Gate drive OFF', -15, -22, 0, .5, 'V', 'gate'),
    ('gate_r', 'Total gate resistance', 4.7, 1, 100, .1, 'Ω', 'gate'),
    ('stray_nh', 'Freewheel loop inductance', 50, 5, 1000, 5, 'nH', 'gate'),
    ('ron_factor', 'On-state slope factor', 1, .5, 20, .1, '×', 'device'),
    ('ce_mohm', 'Collector–emitter shunt', 100, .00001, 1000, .00001, 'MΩ', 'device'),
    ('ins_mohm', 'Busbar insulation resistance', 100, .01, 1000, .01, 'MΩ', 'device'),
    ('ins_v', 'Insulation test voltage', 500, 50, 1000, 50, 'V', 'device'),
    ('desat_v', 'Desaturation threshold', 9, 4, 30, .5, 'V', 'protection'),
    ('blank_us', 'Turn-on blanking', 2, .5, 5, .5, 'µs', 'protection'),
    ('trip_us', 'Detection-to-OFF command', 1, 0, 20, .5, 'µs', 'protection'),
    ('dc_cap_uf', 'DC-link capacitance', 470, 100, 2000, 10, 'µF', 'circuit'),
    ('gate_mohm', 'Gate insulation resistance', 100, .01, 1000, 1, 'MΩ', 'device'),
    ('temperature_c', 'Initial junction / sink temperature', 25, 25, 125, 1, '°C', 'device'),
    ('thermal_c_j_k', 'Effective thermal capacitance', .1, .01, 10, .01, 'J/K', 'device'),
    ('thermal_r_k_w', 'Junction-to-sink resistance', .6, .1, 5, .1, 'K/W', 'device'),
    ('diode_vf_v', 'Diode forward intercept', .7, .1, 1.5, .01, 'V', 'device'),
    ('diode_r_factor', 'Diode series resistance factor', 1, .1, 100, .1, '×', 'device'),
    ('diode_reverse_mohm', 'Diode reverse shunt', 1000, .01, 10000, 1, 'MΩ', 'device'),
]
DEFAULTS = {p[0]: p[2] for p in PARAMETERS}
SOURCES = [
    {'title': 'NU IEEE 2026 IGBT test cell_AK_Final, slides 5–6, 8–11',
     'kind': 'User project brief', 'url': None},
    {'title': 'onsemi NXH80T120L2Q0S2G, Rev. 6; half-bridge IGBT, tables 1 and 3',
     'kind': 'Public surrogate device; not the locomotive module',
     'url': 'https://www.onsemi.com/download/data-sheet/pdf/nxh80t120l2q0s2g-d.pdf'},
    {'title': 'Tektronix: Double Pulse Testing for Power Semiconductor Devices',
     'kind': 'Test topology and measured quantities',
     'url': 'https://www.tek.com/en/documents/application-note/double-pulse-test-tektronix-afg31000-arbitrary-function-generator'},
]

def configuration():
    return {'version': VERSION, 'parameters': [dict(zip(
        ['key','label','default','min','max','step','unit','category'], p)) for p in PARAMETERS],
        'sources': SOURCES, 'model': 'Reduced-order circuit / public surrogate, 25 °C',
        'hardware_qualified': False}

def validate(values):
    if not isinstance(values, dict):
        raise ValueError('Parameters must be an object.')
    if set(values) - set(DEFAULTS):
        raise ValueError('Unknown parameter: ' + ', '.join(sorted(set(values)-set(DEFAULTS))))
    p = dict(DEFAULTS)
    for key, _, default, low, high, *_ in PARAMETERS:
        value = values.get(key, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(key + ' must be a finite number.')
        if not low <= value <= high:
            raise ValueError(f'{key} must be between {low} and {high}.')
        p[key] = float(value)
    return p

# Cies, Coes, Cres at 20 V, held constant as a stated approximation.
CGE, CGC, CCE = 19.06e-9, .34e-9, .06e-9
VTH, GM, V0 = 5.45, 25.0, .7
# Matches one typical static point: Ic=80 A, Vge=15 V => Vce=2.05 V.
KNEE = -(2.05 - V0) / math.log(1 - 80 / (GM * (15 - VTH)))
TAU_ON, TAU_OFF = 20e-9, 100e-9  # illustrative carrier response, not fitted OEM values
DIODE_V, DIODE_R = .7, .03525  # 2.11 V at 40 A, surrogate half-bridge diode typical

def transistor(vg, vc, capacity_old, dt, factor, rshunt, temperature=25, diode_v=.7, diode_r=.03525):
    """Passive terminal law and analytic partial derivative dIc/dVc along gate KCL."""
    delta=temperature-25
    threshold=VTH-.005*delta
    gm=GM/(1+.002*delta)
    offset=V0-.0015*delta
    # Illustrative interpolation through 2.05 V / 25 C and 2.10 V / 150 C at 80 A.
    knee_t=-(2.05+.0004*delta-offset)/math.log(1-80/(gm*(15-threshold)))
    target = gm * max(vg - threshold, 0)
    tau = TAU_ON if target > capacity_old else TAU_OFF
    w = dt / (tau + dt)
    capacity = (1-w) * capacity_old + w * target
    knee = knee_t * factor
    if vc > offset:
        exp = math.exp(-min((vc-offset)/knee, 700))
        shape, slope = 1-exp, exp/knee
    else:
        shape, slope = 0., 0.
    reverse = min(0., (vc + diode_v)/diode_r)
    current = capacity * shape + vc/rshunt + reverse
    dc = capacity*slope + 1/rshunt + (1/diode_r if vc < -diode_v else 0)
    dg = w * gm * shape if vg > threshold else 0.
    return current, dc, dg, capacity

def run(values=None, dt_ns=.5, include_trace=True, experiment='switching', fault_r=.05, fault_l_uh=2., command_delay_us=0., stop_requested=None, freewheel_values=None):
    p = validate({} if values is None else values)
    if experiment not in ('switching','protection'):raise ValueError('Unknown circuit experiment.')
    if not .01<=fault_r<=10 or not .1<=fault_l_uh<=100 or not 0<=command_delay_us<=20:raise ValueError('Invalid fault-path or command-delay setting.')
    if not isinstance(dt_ns, (int,float)) or not math.isfinite(dt_ns) or not .1 <= dt_ns <= 20:
        raise ValueError('Internal timestep must be 0.1–20 ns.')
    hmax = dt_ns * 1e-9
    bus, L, R = p['bus_v'], p['load_uh']*1e-6, p['load_r']
    LS, RG, rshunt = p['stray_nh']*1e-9, p['gate_r'], p['ce_mohm']*1e6
    t1, t2 = (2+command_delay_us)*1e-6, (2+command_delay_us+p['pulse_us'])*1e-6
    t3, t4 = t2+p['gap_us']*1e-6, t2+(p['gap_us']+p['second_us'])*1e-6
    end = t4 + max(12, p['trip_us']+6,6*p['gate_r']*(CGE+CGC)*1e6)*1e-6
    edges = [t1, t2, t3, t4, end]
    fault_time=t1+2e-6 if experiment=='protection' else None
    if fault_time is not None:edges=sorted(edges+[fault_time])
    CB=p['dc_cap_uf']*1e-6;RGE=p['gate_mohm']*1e6
    freewheel=validate(freewheel_values) if freewheel_values is not None else p
    dv=freewheel['diode_vf_v'];dr=DIODE_R*freewheel['diode_r_factor'];dsh=freewheel['diode_reverse_mohm']*1e6
    LF=fault_l_uh*1e-6
    vb=bus; fault_i=0.;temperature=p['temperature_c'];max_temperature=temperature
    # State: gate voltage, collector voltage, load current, diode current, carrier capacity.
    vg, vc, il, diode, capacity = p['gate_off'], bus, 0., 0., 0.
    initial_energy = .5*CGE*vg*vg+.5*CGC*(vg-vc)**2+.5*CCE*vc*vc+.5*CB*vb*vb
    source_energy = device_energy = load_energy = diode_energy = gate_energy = numerical_energy = 0.
    gate_insulation_energy=fault_energy=diode_shunt_energy=0.
    forced_off=None
    max_residual = 0.
    trip_detect = trip_command = off_complete = None
    fault_ic = None
    t = 0.
    max_iterations = 0
    rows = [[0., vg, vc, 0., il, diode, 0., p['gate_off'], 0.,vb,fault_i,temperature]]
    phase_times = [dict(time_us=x*1e6, label=label) for x,label in zip(
        [0,t1,t2,t3,t4,end], ['Initial OFF','Pulse 1 ON','Freewheel interval','Pulse 2 ON','Final OFF','End'])]
    while t < end - 1e-15:
        if forced_off is None and stop_requested and len(rows)%128==0 and stop_requested():
            forced_off=t
        upcoming = next(x for x in edges if x > t+1e-15)
        edge_window = max(2e-6, 6*RG*(CGE+CGC))
        active_edges=edges[:-1]+([trip_command] if trip_command is not None else [])+([forced_off] if forced_off is not None else [])
        near_edge=any(-1e-15 <= t-edge < edge_window for edge in active_edges)
        dt = min(hmax if near_edge else 40*hmax, upcoming-t)
        if trip_command is not None and trip_command > t+1e-15:
            dt = min(dt, trip_command-t)
        mid = t+dt*.5
        pulse_start = t1 if t1 <= mid < t2 else t3 if t3 <= mid < t4 else None
        command_on = forced_off is None and pulse_start is not None and (trip_command is None or mid < trip_command)
        drive = p['gate_on'] if command_on else p['gate_off']
        # Eliminate gate node, load inductor and unilateral diode to leave one scalar KCL.
        gate_a = ((CGE+CGC)*vg-CGC*vc+dt*drive/RG) / (CGE+CGC+dt/RG+dt/RGE)
        gate_b = CGC / (CGE+CGC+dt/RG+dt/RGE)
        load_a = L*il/(L+dt*R)
        load_b = dt/(L+dt*R)
        diode_a = (LS*diode-dt*dv)/(LS+dt*dr)
        diode_b = dt/(LS+dt*dr)
        fault_active=fault_time is not None and mid>=fault_time
        fa=LF*fault_i/(LF+dt*fault_r) if fault_active else 0.
        fb=dt/(LF+dt*fault_r) if fault_active else 0.
        cap_a = -(CCE+CGC)*vc/dt + CGC*vg/dt-CGC*gate_a/dt
        cap_b = (CCE+CGC-CGC*gate_b)/dt
        def residual(x):
            g = gate_a+gate_b*x
            current, dc, dg, q = transistor(g,x,capacity,dt,p['ron_factor'],rshunt,temperature,p['diode_vf_v'],DIODE_R*p['diode_r_factor'])
            # DC-link source is disconnected during the pulse. Solve capacitor KCL,
            # including the optional physical companion-short RL branch.
            denom=CB/dt+load_b+fb+1/dsh
            va=(CB/dt*vb-load_a-fa)/denom;vs=(load_b+fb+1/dsh)/denom
            vn=va+vs*x
            conducting=diode_a+diode_b*(x-vn)>0
            if conducting:
                denom+=diode_b
                va=(CB/dt*vb-load_a-fa+diode_a)/denom
                vs=(load_b+fb+diode_b+1/dsh)/denom;vn=va+vs*x
            d=max(0.,diode_a+diode_b*(x-vn))
            ln=load_a+load_b*(vn-x);fn=fa+fb*(vn-x)
            f=cap_a+cap_b*x+current+d-ln-fn+(x-vn)/dsh
            df=cap_b+dc+dg*gate_b+(load_b+fb+1/dsh+(diode_b if conducting else 0.))*(1-vs)
            return f,df,current,d,q,g,vn,ln,fn
        lo, hi = -10000., max(10000., bus+abs(il)*dt/(CCE+CGC)*4)
        if residual(lo)[0] > 0 or residual(hi)[0] < 0:
            raise ArithmeticError('Circuit root is outside the supported numerical range.')
        x = min(hi, max(lo, vc))
        for iteration in range(60):
            f, df, ic, dn, qn, gn, vbn, ln, fn = residual(x)
            if abs(f) < 1e-8:
                break
            if f > 0: hi=x
            else: lo=x
            step = x-f/df
            x = step if lo < step < hi else (lo+hi)*.5
        else:
            raise ArithmeticError('Circuit solver did not converge. No device verdict is valid.')
        max_iterations=max(max_iterations,iteration+1)
        max_residual=max(max_residual,abs(f))
        vn=x
        ig=(drive-gn)/RG
        power=ic*vn
        source_energy += dt*drive*ig
        device_energy += dt*power
        gate_energy += dt*RG*ig*ig
        load_energy += dt*R*ln*ln
        diode_energy += dt*(dv*dn+dr*dn*dn)
        diode_shunt_energy+=dt*(vbn-vn)**2/dsh
        gate_insulation_energy+=dt*gn*gn/RGE
        fault_energy+=dt*fault_r*fn*fn
        numerical_energy += .5*(CGE*(gn-vg)**2+CGC*((gn-vn)-(vg-vc))**2
                              +CCE*(vn-vc)**2+L*(ln-il)**2+LS*(dn-diode)**2+CB*(vbn-vb)**2+LF*(fn-fault_i)**2)
        vg,vc,il,diode,capacity=gn,vn,ln,dn,qn
        vb,fault_i=vbn,fn
        ct=p['thermal_c_j_k'];rt=p['thermal_r_k_w']
        temperature=(temperature+dt*(power+p['temperature_c']/rt)/ct)/(1+dt/(rt*ct))
        max_temperature=max(max_temperature,temperature)
        t += dt
        if command_on and t-pulse_start >= p['blank_us']*1e-6 and vc>p['desat_v'] and trip_detect is None:
            trip_detect=t
            trip_command=t+p['trip_us']*1e-6
            fault_ic=abs(ic)
        if trip_command is not None and fault_ic>=1. and t>=trip_command and off_complete is None and abs(ic)<.1*fault_ic:
            off_complete=t
        rows.append([t*1e6,vg,vc,ic,il,diode,power,drive,1. if trip_detect is not None else 0.,vb,fault_i,temperature])

    final_energy=.5*CGE*vg*vg+.5*CGC*(vg-vc)**2+.5*CCE*vc*vc+.5*L*il*il+.5*LS*diode*diode+.5*CB*vb*vb+.5*LF*fault_i*fault_i
    losses=device_energy+gate_energy+load_energy+diode_energy+gate_insulation_energy+fault_energy+diode_shunt_energy
    balance=source_energy-(final_energy-initial_energy)-losses-numerical_energy
    peak_v=max(r[2] for r in rows)
    peak_i=max(abs(r[3]) for r in rows)
    peak_diode=max(r[5] for r in rows)
    # A defined 10 ns measurement aperture avoids an undefined numerical derivative bandwidth.
    slew=0.; j=0
    for b in rows:
        old_time=b[0]-.01
        if old_time<0: continue
        while j+1<len(rows) and rows[j+1][0]<old_time: j+=1
        a,c=rows[j],rows[j+1]
        old_i=a[3]+(c[3]-a[3])*(old_time-a[0])/(c[0]-a[0])
        slew=max(slew,abs(b[3]-old_i)/.01)
    # Baseline check is after settling and before the first command edge.
    off_rows=[r for r in rows if .8 <= r[0] <= 1.8]
    off_current=max(abs(r[3]) for r in off_rows)
    first_rows=[r for r in rows if (t2-1e-6)*1e6 <= r[0] < t2*1e6-1e-8]
    first=first_rows[-1]
    expected=(bus-2.05)/R*(-math.expm1(-R*p['pulse_us']*1e-6/L))
    tracking=abs(first[4]-expected)/max(expected,1e-9)*100
    insulation=p['ins_v']/(p['ins_mohm']*1e6)*1000
    latency=(off_complete-trip_detect)*1e6 if off_complete is not None else None
    def energy_window(start, stop):
        return sum(b[6]*(b[0]-a[0])*1e-6 for a,b in zip(rows,rows[1:]) if start<=b[0]*1e-6<stop)*1000
    metrics={
        'peak_vce_v':peak_v,'peak_ic_a':peak_i,'peak_diode_a':peak_diode,
        'peak_gate_v':max(r[1] for r in rows),'min_gate_v':min(r[1] for r in rows),
        'max_didt_a_us':slew,'off_current_ma':off_current*1000,
        'first_pulse_current_a':first[4],'expected_rl_current_a':expected,
        'tracking_error_pct':tracking,'on_vce_v':first[2],
        'insulation_leakage_ma':insulation,'device_energy_mj':device_energy*1000,
        'turn_on_window_mj':energy_window(t3,t3+2e-6),
        'turn_off_window_mj':energy_window(t2,t2+2e-6),
        'trip_detect_us':trip_detect*1e6 if trip_detect is not None else None,
        'trip_off_us':trip_command*1e6 if trip_command is not None else None,
        'protection_response_us':latency,
        'fault_to_off_us':(off_complete-fault_time)*1e6 if off_complete is not None and fault_time is not None else None,
        'fault_insert_us':fault_time*1e6 if fault_time is not None else None,
        'final_bus_v':vb,'final_load_a':il,'final_fault_a':fault_i,'final_diode_a':diode,
        'initial_temperature_c':p['temperature_c'],'peak_temperature_c':max_temperature,'final_temperature_c':temperature,
        'bus_droop_pct':(bus-vb)/bus*100,
    }
    checks=[]
    def check(key,label,value,limit,unit,passed,basis):
        checks.append(dict(key=key,label=label,value=value,limit=limit,unit=unit,
                           status='N/A' if passed is None else 'PASS' if passed else 'FAIL',basis=basis))
    check('vce','Collector voltage ceiling',peak_v,1200,'V',peak_v<=1200,'Public surrogate absolute rating; not a complete SOA assessment')
    check('ic','Collector current ceiling',peak_i,201,'A',peak_i<=201,'Public surrogate pulsed-current ceiling; pulse and thermal SOA not qualified')
    check('diode','Freewheel current ceiling',peak_diode,84,'A',peak_diode<=84,'Public surrogate diode repetitive peak ceiling; thermal conditions not qualified')
    check('gate_abs','Absolute gate voltage',max(abs(r[1]) for r in rows),20,'V',all(abs(r[1])<=20 for r in rows),'Public surrogate absolute rating')
    interrupted=trip_command is not None and trip_command<t2
    check('gate_on','Settled ON gate voltage',None if interrupted else first[1],'14–16','V',None if interrupted else 14<=first[1]<=16,
          'Not evaluated: protection interrupted the first pulse' if interrupted else 'Project target +15 V; ±1 V tolerance is an engineering assumption')
    check('gate_off','Settled OFF gate voltage',off_rows[-1][1],'-16 to -14','V',-16<=off_rows[-1][1]<=-14,'Project target −15 V; ±1 V tolerance is an engineering assumption')
    check('blocking','OFF-state collector current',off_current*1000,.3,'mA',off_current<=.0003,'Screening assumption based on surrogate 300 µA maximum at 1200 V, Vge=0; actual conditions differ')
    check('current_build','First-pulse current tracking',tracking,10,'%',tracking<=10,'Engineering check against series-RL current, assumed constant 2.05 V device drop')
    check('slew','Current slew over 10 ns',slew,5000,'A/µs',slew<=5000,'Project brief maximum; 10 ns measurement aperture is assumed, not specified in the brief')
    check('insulation','Steady insulation leakage',insulation,2,'mA',insulation<=2,'Project brief limit; selected voltage is provisional because brief omits voltage and duration')
    check('desat','Uncommanded protection trip',1 if trip_detect is not None else 0,0,'trips',trip_detect is None,'A normal double pulse must complete without desaturation shutdown')
    if trip_detect is not None:
        check('response','Detection to 10% fault current',latency,10,'µs',None if fault_ic<1 else latency is not None and latency<=10,
              'N/A when detected current is below the assumed 1 A measurement floor; otherwise brief 10 µs target with a defined 10% endpoint. Not survival proof.')
        phase_times.extend([dict(time_us=trip_detect*1e6,label='Desaturation detected'),dict(time_us=trip_command*1e6,label='Protection OFF command')])
    verdict='MODEL FAIL' if any(c['status']=='FAIL' for c in checks) else 'MODEL PASS'
    if fault_time is not None:phase_times.append(dict(time_us=fault_time*1e6,label='Companion RL short applied'))
    if forced_off is not None:phase_times.append(dict(time_us=forced_off*1e6,label='Operator stop: gate inhibited'))
    if abs(balance)>max(1e-7,initial_energy*1e-6):
        raise ArithmeticError('Numerical energy balance failed; no valid model verdict.')
    result={
        'run_id':str(uuid4()),'created_utc':datetime.now(timezone.utc).isoformat(),
        'model_version':VERSION,'mode':'PHYSICS_MODEL','hardware_qualified':False,
        'verdict':verdict,'parameters':p,'metrics':metrics,'checks':checks,
        'scope':'Reduced-order circuit with finite DC link and illustrative thermal model; uncalibrated surrogate',
        'experiment':experiment,'aborted':forced_off is not None,
        'freewheel_parameters':{k:freewheel[k] for k in ('diode_vf_v','diode_r_factor','diode_reverse_mohm')},
        'sources':SOURCES,'events':sorted(phase_times,key=lambda x:x['time_us']),
        'solver':{'method':'Backward Euler, scalar Newton KCL','edge_step_ns':dt_ns,'quiet_step_ns':40*dt_ns,'steps':len(rows)-1,
                  'max_newton_iterations':max_iterations,'max_kcl_residual_a':max_residual,
                  'energy_balance_residual_j':balance,'numerical_dissipation_j':numerical_energy,
                  'source_energy_j':source_energy,'stored_energy_change_j':final_energy-initial_energy,
                  'device_loss_j':device_energy,'gate_resistor_loss_j':gate_energy,
                  'load_resistor_loss_j':load_energy,'diode_loss_j':diode_energy,'diode_shunt_loss_j':diode_shunt_energy,'gate_insulation_loss_j':gate_insulation_energy,'fault_path_loss_j':fault_energy},
        'trace_columns':['time_us','vge_v','vce_v','ic_a','il_a','diode_a','device_power_w','drive_v','fault_latched','dc_bus_v','companion_path_a','junction_estimate_c'],
        'limitations':['Not calibrated to the locomotive module.',
                       'Constant capacitances and approximate carrier response; diode reverse recovery omitted.',
                       'Illustrative lumped thermal network; no thermal runaway, avalanche, physical damage or EMI model.',
                       'Upper and lower tests use mirrored terminal references; no simultaneous PWM leg or OEM optical protocol.',
                       'Full SOA and exact assembly interfaces remain unverified.',
                       'MODEL PASS covers only the listed checks, not hardware release.'],
    }
    if include_trace: result['trace']=rows
    return result

if __name__=='__main__':
    import json, time
    start=time.perf_counter()
    r=run(include_trace=False)
    print(json.dumps(r,indent=2))
    print('Elapsed seconds:',round(time.perf_counter()-start,3))
