"""Required-test orchestration and explicit virtual/OEM decision separation."""
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import physics

ROOT = Path(__file__).resolve().parent
PROFILE_BYTES = (ROOT/'profiles/prototype.json').read_bytes()
PROFILE = json.loads(PROFILE_BYTES)
LIMITS = PROFILE['limits']
EXTRA = [
    ('supply_vrms','Driver supply input',100,0,130,1,'Vrms','supply'),
    ('supply_khz','Driver supply frequency',25,1,50,.1,'kHz','supply'),
    ('supply_r','Driver source resistance',10,0,1000,1,'Ω','supply'),
    ('driver_idle_w','Driver idle consumption',4,0,40,.1,'W','supply'),
    ('driver_pwm_khz','Gate activity for power check',10,.1,50,.1,'kHz','supply'),
    ('fiber_delay_us','Command propagation delay',.2,0,20,.1,'µs','supply'),
    ('status_delay_us','Status propagation delay',.2,0,20,.1,'µs','supply'),
    ('ins_cap_nf','Insulation capacitance',10,.1,10000,1,'nF','insulation'),
    ('ins_source_kohm','Insulation source resistance',100,1,1000,1,'kΩ','insulation'),
    ('ins_dwell_s','Insulation dwell',1,.01,30,.1,'s','insulation'),
    ('dump_r_ohm','DC-link discharge resistance',1000,100,10000000,100,'Ω','shutdown'),
    ('precharge_r_ohm','Precharge resistance',100,10,1000,10,'Ω','shutdown'),
    ('charge_limit_a','DC source current limit',.5,.01,2,.1,'A','shutdown'),
    ('fault_r_ohm','Companion short resistance',.05,.01,10,.01,'Ω','protection'),
    ('fault_l_uh','Companion short inductance',2,.1,100,.1,'µH','protection'),
]
EXTRA_DEFAULTS={x[0]:x[2] for x in EXTRA}
STATION={
    'door_closed':'Door closed', 'fixture_clamped':'Module clamped',
    'connector_engaged':'Test connector engaged', 'earth_connected':'Protective earth connected',
    'estop_released':'Emergency stop released', 'fiber_connected':'Command/status fiber connected',
    'coolant_ready':'Cooling available', 'source_isolation_feedback':'Source isolation contact open feedback',
}
DEVICE_KEYS={'ron_factor','ce_mohm','gate_mohm','temperature_c','thermal_c_j_k','thermal_r_k_w',
             'diode_vf_v','diode_r_factor','diode_reverse_mohm'}
REQUIRED=['station','driver','fiber','insulation']+[f'{pos}_{test}' for pos in ('lower','upper') for test in ('static','switching','protection')]
MODES={'full':'Complete required suite','static':'Static checks only','switching':'Switching only','protection':'Protection only'}

def configuration():
    c=physics.configuration()
    c['parameters'] += [dict(zip(['key','label','default','min','max','step','unit','category'],p)) for p in EXTRA]
    c.update(station=STATION,device_override_keys=sorted(DEVICE_KEYS),profile=PROFILE,
             profile_sha256=hashlib.sha256(PROFILE_BYTES).hexdigest(),modes=MODES,
             model='Reduced-order finite-DC-link prototype with explicit assumptions')
    return c

def validate_request(request):
    if not isinstance(request,dict):raise ValueError('Request must be an object.')
    allowed={'parameters','device_overrides','station','mode','serial','operator'}
    if set(request)-allowed:raise ValueError('Unknown request field.')
    raw=request.get('parameters',{})
    if not isinstance(raw,dict):raise ValueError('Parameters must be an object.')
    if set(raw)-set(physics.DEFAULTS)-set(EXTRA_DEFAULTS):raise ValueError('Unknown physical parameter.')
    p=physics.validate({k:v for k,v in raw.items() if k in physics.DEFAULTS})
    extra={}
    for key,_,default,lo,hi,*_ in EXTRA:
        v=raw.get(key,default)
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not lo<=v<=hi:
            raise ValueError(f'{key} must be a finite number between {lo} and {hi}.')
        extra[key]=float(v)
    station={k:True for k in STATION};submitted=request.get('station',{})
    if not isinstance(submitted,dict) or set(submitted)-set(STATION):raise ValueError('Unknown station input.')
    if any(type(v) is not bool for v in submitted.values()):raise ValueError('Station states must be Boolean.')
    station.update(submitted)
    overrides=request.get('device_overrides',{})
    if not isinstance(overrides,dict) or set(overrides)-{'upper','lower'}:raise ValueError('Unknown device position.')
    devices={}
    for pos in ('lower','upper'):
        d=overrides.get(pos,{})
        if not isinstance(d,dict) or set(d)-DEVICE_KEYS:raise ValueError('Invalid device override.')
        devices[pos]=physics.validate(p|d)
    mode=request.get('mode','full')
    if mode not in MODES:raise ValueError('Unknown test selection.')
    labels={}
    for k,default in [('serial','VIRTUAL-ASSEMBLY'),('operator','Local operator')]:
        value=request.get(k,default)
        if not isinstance(value,str) or not 1<=len(value.strip())<=80 or any(ord(c)<32 for c in value):raise ValueError(f'{k} must be 1–80 printable characters.')
        labels[k]=value.strip()
    return p,extra,station,devices,mode,labels

def check(key,label,value,limit,unit,passed,basis):
    return dict(key=key,label=label,value=value,limit=limit,unit=unit,
                status='INCOMPLETE' if passed is None else 'PASS' if passed else 'FAIL',basis=basis)

def test_result(key,label,checks,duration_s=0,**more):
    status='FAIL' if any(c['status']=='FAIL' for c in checks) else 'INCOMPLETE' if any(c['status']!='PASS' for c in checks) else 'PASS'
    return dict(key=key,label=label,status=status,checks=checks,duration_s=duration_s,**more)

def static_tests(pos,p):
    l=LIMITS;temp=p['temperature_c'];current=l['static_test_a'];lo=0.;hi=50.
    for _ in range(70):
        vc=(lo+hi)/2
        if physics.transistor(15,vc,0,1e3,p['ron_factor'],p['ce_mohm']*1e6,temp,p['diode_vf_v'],physics.DIODE_R*p['diode_r_factor'])[0]<current:lo=vc
        else:hi=vc
    vce=(lo+hi)/2;limit=l['static_vce_max_25c_v']+.0004*(temp-25)
    gate_na=l['gate_leak_test_v']/(p['gate_mohm']*1e6)*1e9
    block_ua=l['blocking_test_v']/(p['ce_mohm']*1e6)*1e6
    vf=p['diode_vf_v']+physics.DIODE_R*p['diode_r_factor']*l['diode_test_a']
    rev_ua=l['diode_reverse_test_v']/p['diode_reverse_mohm']
    c=[check('gate_leak','Gate leakage at +20 V',gate_na,l['gate_leak_max_na'],'nA',gate_na<=l['gate_leak_max_na'],'Surrogate maximum at 20 V; resistive leakage approximation'),
       check('blocking','Blocking leakage at 1200 V, gate 0 V',block_ua,l['blocking_max_ua'],'µA',block_ua<=l['blocking_max_ua'],'Surrogate maximum; separate current-limited static stimulus, not DC-link charging'),
       check('vcesat','Static VCE at 80 A, gate +15 V',vce,limit,'V',vce<=limit,'2.85 V surrogate maximum at 25 °C; temperature offset above 25 °C is assumed'),
       check('diode_forward','Diode forward voltage at 1 mA',vf,f"{l['diode_forward_min_v']}–{l['diode_forward_max_v']}",'V',l['diode_forward_min_v']<=vf<=l['diode_forward_max_v'],'Project voltage range; 1 mA stimulus is assumed, not power-current VF'),
       check('diode_reverse','Diode reverse leakage at 100 V',rev_ua,l['diode_reverse_max_ua'],'µA',rev_ua<=l['diode_reverse_max_ua'],'Quantifies project “open”; voltage and 10 µA threshold are provisional')]
    return test_result(pos+'_static',pos.title()+' static checks',c,1.25,
        stimulus={'gate_leak_v':20,'blocking_v':1200,'vcesat_current_a':80,'vcesat_gate_v':15,'diode_forward_a':.001,'diode_reverse_v':100,'per_check_settle_and_acquisition_s':.25},
        note='Independent low-energy static instruments; 80 A VCE measurement is a brief controlled-current pulse. No damage or breakdown model.')

def driver_test(p,e):
    l=LIMITS
    power=e['driver_idle_w']+800e-9*(p['gate_on']-p['gate_off'])*e['driver_pwm_khz']*1000
    discriminant=e['supply_vrms']**2-4*e['supply_r']*power
    loaded=(e['supply_vrms']+math.sqrt(discriminant))/2 if discriminant>=0 else 0
    scale=loaded/l['supply_vrms'];on=p['gate_on']*scale;off=p['gate_off']*scale
    checks=[check('supply_voltage','Loaded driver supply',loaded,'95–105','Vrms',95<=loaded<=105,'100 Vrms project target; ±5% prototype tolerance; constant-power load'),
            check('supply_frequency','Driver supply frequency',e['supply_khz'],'23.75–26.25','kHz',23.75<=e['supply_khz']<=26.25,'25 kHz project target; ±5% assumed'),
            check('driver_power','Driver power per channel',power,l['driver_max_w'],'W',power<=l['driver_max_w'],'Project 20 W maximum; idle input plus Qg × gate swing × activity frequency'),
            check('rail_on','Effective ON rail',on,'14–16','V',14<=on<=16,'Project +15 V; ±1 V assumed. Idealized isolated rail conversion'),
            check('rail_off','Effective OFF rail',off,'−16 to −14','V',-16<=off<=-14,'Project −15 V; ±1 V assumed. Supply frequency is not gate PWM frequency')]
    trace=[[i/(e['supply_khz']*1000)*5/200,math.sqrt(2)*loaded*math.sin(2*math.pi*5*i/200)] for i in range(201)]
    return test_result('driver','Driver supply and rail checks',checks,.25,
        metrics={'power_per_channel_w':power,'loaded_supply_vrms':loaded,'effective_gate_on_v':on,'effective_gate_off_v':off},
        trace_columns=['time_s','supply_v'],trace=trace),on,off

def insulation_test(p,e):
    l=LIMITS;r=p['ins_mohm']*1e6;rs=e['ins_source_kohm']*1e3;c=e['ins_cap_nf']*1e-9
    tau=c*r*rs/(r+rs);vinf=p['ins_v']*r/(r+rs);dwell=e['ins_dwell_s']
    vf=vinf*(-math.expm1(-dwell/tau));leak=vf/r*1000;error=abs(vf-p['ins_v'])/p['ins_v']*100
    # Dedicated insulation discharge resistor equals the declared source resistance.
    td=tau*max(0,math.log(max(vf,1e-12)/LIMITS['access_voltage_max_v']))
    trace=[]
    for i in range(161):
        t=dwell*i/160;v=vinf*(-math.expm1(-t/tau));trace.append([t,v,v/r*1000])
    for i in range(1,81):
        t=(td+5*tau)*i/80;v=vf*math.exp(-t/tau);trace.append([dwell+t,v,v/r*1000])
    checks=[check('ins_voltage','Insulation voltage attained',error,l['insulation_voltage_tolerance_pct'],'% error',error<=l['insulation_voltage_tolerance_pct'],'Checks source droop and RC settling at the selected provisional voltage'),
            check('ins_leak','Insulation leakage after dwell',leak,l['insulation_max_ma'],'mA',leak<=l['insulation_max_ma'],'Project ≤2 mA; voltage and dwell await OEM approval'),
            check('ins_discharge','Insulation node discharged',trace[-1][1],l['access_voltage_max_v'],'V',trace[-1][1]<=l['access_voltage_max_v'],'Separate current-limited insulation circuit; provisional access threshold')]
    return test_result('insulation','Busbar insulation and discharge',checks,trace[-1][0],
        metrics={'dwell_s':dwell,'time_constant_s':tau,'steady_voltage_v':vinf,'measured_voltage_v':vf,'leakage_ma':leak},
        trace_columns=['time_s','insulation_voltage_v','leakage_ma'],trace=trace)

def shutdown(p,e,result,isolated=True):
    """Conservative post-pulse current envelope; DC-link analytic RC discharge."""
    l=LIMITS;m=result['metrics'];cap=p['dc_cap_uf']*1e-6;load_l=p['load_uh']*1e-6
    fault=result['experiment']=='protection';loop_l=load_l+(e['fault_l_uh']*1e-6 if fault else p['stray_nh']*1e-9)
    magnetic=.5*load_l*m['final_load_a']**2+.5*p['stray_nh']*1e-9*m['final_diode_a']**2+.5*e['fault_l_uh']*1e-6*m['final_fault_a']**2
    ibound=math.sqrt(2*magnetic/loop_l)
    diode_r=physics.DIODE_R*result['freewheel_parameters']['diode_r_factor']
    resistance=p['load_r']+min(diode_r,e['fault_r_ohm']) if fault else p['load_r']+diode_r
    tau_i=loop_l/resistance;tau_v=e['dump_r_ohm']*cap
    gate_abs=max(abs(p['gate_on']),abs(p['gate_off']),abs(m['peak_gate_v']),abs(m['min_gate_v']))
    voltage_bound=max(abs(m['peak_vce_v']),abs(m['final_bus_v']))
    auxiliary_energy=.5*physics.CGE*gate_abs**2+.5*physics.CGC*(voltage_bound+gate_abs)**2+.5*physics.CCE*voltage_bound**2
    def sample(t):
        v=m['final_bus_v']*math.exp(-t/tau_v) if isolated else m['final_bus_v']
        i=ibound*math.exp(-t/tau_i)
        energy=.5*cap*v*v+.5*loop_l*i*i+auxiliary_energy
        return [t,v,i,energy]
    def safe(row):return abs(row[1])<=l['access_voltage_max_v'] and row[2]<=l['access_current_max_a'] and row[3]<=l['access_stored_energy_max_j']
    timeout=l['discharge_timeout_s'];lo=0.;hi=timeout
    if safe(sample(hi)):
        for _ in range(64):
            mid=(lo+hi)/2
            if safe(sample(mid)):hi=mid
            else:lo=mid
        duration=min(timeout,hi+.005)
    else:duration=timeout
    # Dense logarithmic early samples preserve the fast magnetic-energy decay.
    times=sorted({0.,duration}|{duration*i/160 for i in range(161)}|{min(duration,10**(-7+i*7/100)) for i in range(101)})
    trace=[sample(t) for t in times];last=trace[-1]
    checks=[check('isolation','Source isolation confirmed',isolated,True,'',isolated,'Physical contact feedback is represented as an explicit station input'),
            check('bus_safe','Residual DC-link voltage',last[1],l['access_voltage_max_v'],'V',abs(last[1])<=l['access_voltage_max_v'],'Prototype access threshold; not a universal safe-touch declaration'),
            check('current_safe','Residual current upper bound',last[2],l['access_current_max_a'],'A',last[2]<=l['access_current_max_a'],'Passive RL envelope includes signed companion-path energy'),
            check('energy_safe','Residual stored energy',last[3],l['access_stored_energy_max_j'],'J',last[3]<=l['access_stored_energy_max_j'],'DC capacitor plus magnetic energy and conservative gate-capacitance allowance')]
    return test_result(result['test_key']+'_shutdown',result['position'].title()+' '+result['experiment']+' shutdown',checks,duration,
        access_permitted=all(c['status']=='PASS' for c in checks),trace_columns=['time_s','dc_bus_v','current_bound_a','stored_energy_j'],trace=trace,
        metrics={'initial_stored_energy_j':sample(0)[3],'final_stored_energy_j':last[3],'peak_dump_power_w':m['final_bus_v']**2/e['dump_r_ohm'],'dump_energy_j':.5*cap*(m['final_bus_v']**2-last[1]**2)},
        note='Post-pulse passive-network envelope; no continuation of the nanosecond transistor solver. A failed shutdown blocks virtual fixture access.')

def dynamic_checks(result,p):
    l=LIMITS;m=result['metrics'];fault=result['experiment']=='protection'
    common=[c for c in result['checks'] if c['key'] in ('vce','gate_abs','slew')]
    common.append(check('temperature','Estimated peak junction temperature',m['peak_temperature_c'],l['junction_max_c'],'°C',m['peak_temperature_c']<=l['junction_max_c'],'Surrogate maximum; illustrative lumped thermal model, not validated SOA'))
    if fault:
        common.extend([
            check('fault_stimulus','Fault detected after short insertion',m['trip_detect_us'],m['fault_insert_us'],'µs',m['trip_detect_us'] is not None and m['trip_detect_us']>=m['fault_insert_us'],'A trip before the applied fault does not demonstrate the required protection response'),
            check('detection_response','Detection to current below 10%',m['protection_response_us'],l['desat_to_current_off_max_us'],'µs',m['protection_response_us'] is not None and m['protection_response_us']<=l['desat_to_current_off_max_us'],'Project ~10 µs requirement; 10% of detection current endpoint is explicitly assumed'),
            check('fault_response','Fault insertion to current below 10%',m['fault_to_off_us'],l['prototype_fault_to_off_max_us'],'µs',m['fault_to_off_us'] is not None and 0<=m['fault_to_off_us']<=l['prototype_fault_to_off_max_us'],'Additional 5 µs prototype deadline; conditional surrogate rating does not prove survival'),
            check('fault_voltage_scope','Fault bus within prototype envelope',p['bus_v'],600,'V',p['bus_v']<=600,'Surrogate short-circuit rating is conditional at 600 V/+15 V and ≤150 °C; this is only a boundary screen')])
    else:
        common += [c for c in result['checks'] if c['key'] in ('ic','diode','gate_on','current_build','desat')]
        finalgate=result['trace'][-1][1]
        common.append(check('final_off_gate','OFF gate after final pulse',finalgate,'−16 to −14','V',-16<=finalgate<=-14,'Calculated final transition, not the initialized OFF state'))
        scale=(p['bus_v']/l['energy_reference_v'])*(m['expected_rl_current_a']/l['energy_reference_a'])*(1+.004*(p['temperature_c']-25))
        windows_valid=p['second_us']>=l['energy_window_us'] and p['gap_us']>=l['energy_window_us']
        for key,label,budget in [('turn_on_window_mj','Second turn-on energy in 2 µs','on_window_budget_at_400v60a_mj'),('turn_off_window_mj','First turn-off energy in 2 µs','off_window_budget_at_400v60a_mj')]:
            limit=l[budget]*scale
            common.append(check(key,label,m[key],limit,'mJ',m[key]<=limit if windows_valid else None,'Prototype energy budget scaled by requested V × ideal-RL current and assumed temperature factor; not datasheet Eon/Eoff'))
        in_range=l['valid_bus_min_v']<=p['bus_v']<=l['valid_bus_max_v'] and l['valid_requested_current_min_a']<=m['expected_rl_current_a']<=l['valid_requested_current_max_a']
        common.append(check('profile_envelope','Requested current / bus in comparison envelope',f"{m['expected_rl_current_a']:.3f} A / {p['bus_v']:.3f} V",'20–80 A / 100–600 V','',True if in_range else None,'Outside this provisional comparison envelope, no complete model acceptance is issued'))
    return common

def execute(request,progress=None,stop_requested=None):
    p,e,station,devices,mode,labels=validate_request(request)
    stop_requested=stop_requested or (lambda:False)
    report=dict(run_id=str(uuid4()),created_utc=datetime.now(timezone.utc).isoformat(),model_version=physics.VERSION,
        mode='VIRTUAL_SUITE',selected_tests=mode,**labels,parameters=p|e,device_parameters=devices,station=station,
        profile=PROFILE,profile_sha256=hashlib.sha256(PROFILE_BYTES).hexdigest(),sources=physics.SOURCES,
        tests=[],shutdowns=[],waveforms=[],timeline=[],virtual_suite_verdict='INCOMPLETE',hardware_qualification='INCOMPLETE',hardware_qualified=False,hardware_release=False,
        qualification_blockers=PROFILE['qualification_blockers'],virtual_access_permitted=True,aborted=False)
    def add(item):
        report['tests'].append(item)
        report['timeline'].append({'label':item['label'],'duration_s':item['duration_s']})
        if progress:progress(item['label'],len(report['tests']),len(REQUIRED))
    pre=[check(k,label,station[k],True,'',station[k],'Virtual safety-chain input; not measured hardware') for k,label in STATION.items()]
    add(test_result('station','Station interlocks',pre,.25))
    if any(not v for v in station.values()):
        report['aborted']=True;report['abort_reason']='A station precondition is not satisfied; no power stimulus was applied.'
        report['virtual_access_permitted']=False
        return finalize(report)
    driver,on,off=driver_test(p,e);add(driver)
    fiber=[check('command_delay','Command propagation delay',e['fiber_delay_us'],LIMITS['fiber_latency_max_us'],'µs',e['fiber_delay_us']<=LIMITS['fiber_latency_max_us'],'Logical transport delay; 1 µs assumed, no OEM optical protocol'),
           check('status_delay','Fault-status propagation delay',e['status_delay_us'],LIMITS['fiber_latency_max_us'],'µs',e['status_delay_us']<=LIMITS['fiber_latency_max_us'],'Logical returned-status delay; local trip does not wait for laptop status')]
    add(test_result('fiber','Fiber command and returned-status timing',fiber,.1))
    if mode in ('full','static'):add(insulation_test(p,e))
    insulation_ok=next((t['status']=='PASS' for t in report['tests'] if t['key']=='insulation'),True)
    enabled=driver['status']=='PASS' and all(c['status']=='PASS' for c in fiber) and insulation_ok
    if mode in ('full','static'):
        for pos in ('lower','upper'):add(static_tests(pos,devices[pos]))
        enabled=enabled and all(t['status']=='PASS' for t in report['tests'] if t['key'].endswith('_static'))
    for pos in ('lower','upper'):
        if stop_requested():report['aborted']=True;report['abort_reason']='Operator requested stop.';break
        device=devices[pos]
        # A failed low-energy screen prevents escalating the virtual stimulus.
        static_ok=next((t['status']=='PASS' for t in report['tests'] if t['key']==pos+'_static'),True)
        if not enabled or not static_ok:continue
        for experiment in ('switching','protection'):
            if mode not in ('full',experiment):continue
            if stop_requested():report['aborted']=True;report['abort_reason']='Operator requested stop.';break
            if progress:progress(pos.title()+' '+experiment+': solving circuit',len(report['tests']),len(REQUIRED))
            effective=device|{'gate_on':on,'gate_off':off}
            # The gate law supports ±22 V input; driver prechecks prevent out-of-range rails.
            cap=device['dc_cap_uf']*1e-6
            charge_time=cap*device['bus_v']/e['charge_limit_a']+5*e['precharge_r_ohm']*cap
            report['timeline'].append(dict(label=pos.title()+' '+experiment+' precharge and settle',duration_s=charge_time))
            result=physics.run(effective,experiment=experiment,fault_r=e['fault_r_ohm'],fault_l_uh=e['fault_l_uh'],command_delay_us=e['fiber_delay_us'],stop_requested=stop_requested,freewheel_values=devices['upper' if pos=='lower' else 'lower'])
            result.update(position=pos,test_key=pos+'_'+experiment)
            checks=dynamic_checks(result,effective)
            if result['aborted']:
                checks.append(check('interrupted','Required acquisition completed',False,True,'',False,'Operator stop inhibited the gate during calculation'))
                report['aborted']=True;report['abort_reason']='Operator stop inhibited gates; shutdown completed before returning the report.'
            if experiment=='protection':
                result['metrics']['returned_fault_status_us']=(result['metrics']['trip_detect_us']+e['status_delay_us']) if result['metrics']['trip_detect_us'] is not None else None
            result['checks']=checks
            result['verdict']='MODEL FAIL' if any(c['status']=='FAIL' for c in checks) else 'MODEL INCOMPLETE' if any(c['status']!='PASS' for c in checks) else 'MODEL PASS'
            add(test_result(result['test_key'],pos.title()+' '+experiment,checks,result['trace'][-1][0]*1e-6,metrics=result['metrics'],solver=result['solver']))
            report['waveforms'].append(result)
            down=shutdown(effective,e,result,station['source_isolation_feedback'])
            report['shutdowns'].append(down);report['timeline'].append({'label':down['label'],'duration_s':down['duration_s']})
            report['virtual_access_permitted']=down['access_permitted']
            # Tests start at the configured thermal baseline after a calculated cooling interval.
            rise=max(0,result['metrics']['final_temperature_c']-device['temperature_c'])
            cooling=device['thermal_c_j_k']*device['thermal_r_k_w']*max(0,math.log(max(rise,1e-12)/LIMITS['cooling_reset_rise_c']))
            report['timeline'].append(dict(label=pos.title()+' thermal reset dwell (estimated)',duration_s=cooling))
            if not down['access_permitted'] or report['aborted']:break
        if not report['virtual_access_permitted'] or report['aborted']:break
    return finalize(report)

def finalize(r):
    executed={t['key']:t for t in r['tests']}
    r['coverage']=[{'key':key,'status':executed[key]['status'] if key in executed else 'NOT RUN'} for key in REQUIRED]
    allchecks=[c for t in r['tests']+r['shutdowns'] for c in t['checks']]
    failed=any(c['status']=='FAIL' for c in allchecks)
    incomplete=any(x['status']!='PASS' for x in r['coverage']) or any(c['status']=='INCOMPLETE' for c in allchecks)
    r['virtual_suite_verdict']='ABORTED' if r['aborted'] else 'FAIL' if failed else 'INCOMPLETE' if incomplete else 'PASS'
    r['counts']={s:sum(x['status']==s for x in r['coverage']) for s in ('PASS','FAIL','INCOMPLETE','NOT RUN')}
    r['counts']['total_required']=len(REQUIRED)
    r['timing']={'estimated_automated_cycle_s':sum(t['duration_s'] for t in r['timeline']),
                 'assumed_operator_handling_s':90,'assumed_report_overhead_s':2,
                 'note':'Analytical stimulus, charging, discharge and thermal dwell estimates; not measured station throughput or computation time. Verify by commissioning time study.'}
    r['timing']['estimated_total_s']=r['timing']['estimated_automated_cycle_s']+92
    r['completion_statement']='Virtual PASS means every required prototype check and discharge passed. Physical module qualification remains INCOMPLETE.'
    return r
