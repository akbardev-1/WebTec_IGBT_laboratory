"""Recompute a full reference report and optional plots. No reference data feeds the solver."""
from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import physics,suite,start
folder=ROOT/'verification'/'reference';folder.mkdir(exist_ok=True)
r=suite.execute({'serial':'REFERENCE-SURROGATE','operator':'Numerical verification'})
r['computation_seconds']=None
start.REPORT_ROOT=folder
start.save_report(r)
# Keep a stable, portable reference folder name without changing the report's actual run ID.
old=folder/r['run_id'];target=folder/'default_run'
if target.exists():
    import shutil
    shutil.rmtree(target)
old.rename(target)
fine=physics.run({},dt_ns=.25,include_trace=False);coarse=physics.run({},dt_ns=.5,include_trace=False)
convergence={key:abs(coarse['metrics'][key]/fine['metrics'][key]-1)*100 for key in ('peak_vce_v','peak_ic_a','device_energy_mj','turn_on_window_mj','turn_off_window_mj')}
summary={'version':physics.VERSION,'default_full_suite':r['virtual_suite_verdict'],'coverage':r['counts'],'hardware_qualification':r['hardware_qualification'],'virtual_access_permitted':r['virtual_access_permitted'],'timing':r['timing'],'half_step_relative_difference_pct':convergence,'metrics':{w['test_key']:w['metrics'] for w in r['waveforms']},'shutdowns':{d['key']:{'duration_s':d['duration_s'],'final_state':d['trace'][-1],'metrics':d['metrics']} for d in r['shutdowns']},'energy_residuals_j':{w['test_key']:w['solver']['energy_balance_residual_j'] for w in r['waveforms']}}
(folder/'summary.json').write_text(json.dumps(summary,indent=2))
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print('Reports generated; optional Matplotlib/NumPy plots skipped.');raise SystemExit(0)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.2})
fig,axs=plt.subplots(3,2,figsize=(13,10),layout='constrained');fig.suptitle('IGBT virtual prototype 2.0 — calculated reference evidence',fontsize=16,fontweight='bold')
a=np.array(r['waveforms'][0]['trace']);b=np.array(r['waveforms'][1]['trace']);d=np.array(r['shutdowns'][0]['trace']);ins=np.array(next(t for t in r['tests'] if t['key']=='insulation')['trace'])
axs[0,0].plot(a[:,0],a[:,3],color='#c65727');axs[0,0].set(title='Lower switch: double-pulse collector current',xlabel='Time [µs]',ylabel='IC [A]')
axs[0,1].plot(a[:,0],a[:,2],color='#197a9b');axs[0,1].set(title='Collector voltage with finite DC-link droop',xlabel='Time [µs]',ylabel='VCE [V]')
axs[1,0].plot(b[:,0],b[:,3],color='#c65727');axs[1,0].set(xlim=(3.5,8),title='Companion RL short: current interruption',xlabel='Time [µs]',ylabel='IC [A]')
m=r['waveforms'][1]['metrics'];axs[1,0].axvline(m['fault_insert_us'],color='#555',ls='--',label='Fault applied');axs[1,0].axvline(m['trip_off_us'],color='#a52323',ls=':',label='OFF command');axs[1,0].legend(fontsize=8)
axs[1,1].plot(d[:,0],d[:,1],color='#197a9b');axs[1,1].axhline(30,color='#a52323',ls='--',label='30 V prototype bound');axs[1,1].set(title='Post-pulse DC-link discharge',xlabel='Time after acquisition [s]',ylabel='DC-link [V]');axs[1,1].legend(fontsize=8)
axs[2,0].plot(d[:,0],d[:,3],color='#8462ad');axs[2,0].set(title='Stored energy after acquisition',xlabel='Time after acquisition [s]',ylabel='Energy [J]',yscale='log');axs[2,0].axhline(.25,color='#a52323',ls='--')
axs[2,1].plot(ins[:,0],ins[:,1],color='#197a9b');axs[2,1].set(title='Insulation dwell and separate discharge',xlabel='Time [s]',ylabel='Insulation node [V]')
fig.text(.5,-.015,'Calculated surrogate results. No measured hardware data. Physical qualification: INCOMPLETE.',ha='center',fontsize=10,color='#6a4d16')
fig.savefig(ROOT/'verification'/'Reference_Waveforms.png',dpi=160,bbox_inches='tight');plt.close(fig)
print(json.dumps({'virtual_suite':r['virtual_suite_verdict'],'required_groups_passed':r['counts']['PASS'],'default_peak_ic_a':r['waveforms'][0]['metrics']['peak_ic_a'],'default_peak_vce_v':r['waveforms'][0]['metrics']['peak_vce_v'],'protection_fault_to_off_us':m['fault_to_off_us'],'estimated_cycle_s':r['timing']['estimated_total_s'],'convergence_pct':convergence},indent=2))
