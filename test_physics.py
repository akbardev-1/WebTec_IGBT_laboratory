"""Numerical verification and physical sensitivity, not measured-device validation."""
import math
import unittest
import physics
import suite

class CircuitVerification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.normal=physics.run({})
        cls.fault=physics.run({},experiment='protection')
    def test_energy_conservation_normal_and_fault(self):
        for r in (self.normal,self.fault):
            s=r['solver'];self.assertLess(abs(s['energy_balance_residual_j']),1e-7)
            self.assertLess(s['max_kcl_residual_a'],1e-7)
            self.assertGreater(s['numerical_dissipation_j'],0)
    def test_half_timestep_convergence(self):
        fine=physics.run({},dt_ns=.25,include_trace=False)
        for key in ('peak_vce_v','peak_ic_a','device_energy_mj','turn_on_window_mj','turn_off_window_mj'):
            self.assertLess(abs(self.normal['metrics'][key]/fine['metrics'][key]-1),.025,key)
    def test_initial_static_calibration_point(self):
        current=physics.transistor(15,2.05,0,1e3,1,1e8)[0]
        self.assertAlmostEqual(current,80,places=5)
    def test_inductive_ramp_and_dc_link_droop(self):
        m=self.normal['metrics'];self.assertLess(m['tracking_error_pct'],1)
        lower_cap=physics.run({'dc_cap_uf':100},include_trace=False)['metrics']
        self.assertGreater(lower_cap['bus_droop_pct'],m['bus_droop_pct']*4)
        self.assertLess(lower_cap['first_pulse_current_a'],m['first_pulse_current_a'])
        high_l=physics.run({'load_uh':1000},include_trace=False)['metrics']
        self.assertLess(high_l['first_pulse_current_a'],m['first_pulse_current_a']*.52)
    def test_fault_current_is_solved_and_latches_off(self):
        m=self.fault['metrics'];self.assertGreater(m['peak_ic_a'],200)
        self.assertGreater(m['trip_detect_us'],m['fault_insert_us'])
        self.assertLess(m['fault_to_off_us'],5)
        self.assertTrue(all(row[7]<0 for row in self.fault['trace'] if row[0]>m['trip_off_us']+.001))
    def test_slow_protection_fails_actual_timing(self):
        r=physics.run({'trip_us':12},experiment='protection')
        self.assertGreater(r['metrics']['fault_to_off_us'],10)
        checks=suite.dynamic_checks(r,r['parameters'])
        self.assertEqual(next(c['status'] for c in checks if c['key']=='detection_response'),'FAIL')
    def test_companion_diode_changes_other_switch_waveform(self):
        r=physics.run({},freewheel_values={'diode_r_factor':10})
        self.assertNotAlmostEqual(r['metrics']['peak_vce_v'],self.normal['metrics']['peak_vce_v'],places=1)
        self.assertGreater(r['solver']['diode_loss_j'],self.normal['solver']['diode_loss_j'])
    def test_temperature_and_power_are_coupled(self):
        r=self.normal;m=r['metrics']
        self.assertGreater(m['peak_temperature_c'],25)
        self.assertLessEqual(m['peak_temperature_c']-25,m['device_energy_mj']/1000/.1*1.001)
        hot=physics.run({'temperature_c':100},include_trace=False)
        self.assertGreater(hot['metrics']['peak_temperature_c'],100)
        self.assertNotAlmostEqual(hot['metrics']['peak_ic_a'],m['peak_ic_a'],places=2)
    def test_cancellation_inhibits_gate(self):
        calls=0
        def stop():
            nonlocal calls
            calls+=1
            return calls>=10
        r=physics.run({},stop_requested=stop)
        self.assertTrue(r['aborted']);event=next(x for x in r['events'] if x['label'].startswith('Operator stop'))
        self.assertTrue(all(x[7]<0 for x in r['trace'] if x[0]>event['time_us']+.001))
    def test_trace_is_complete_and_finite(self):
        r=self.normal;self.assertEqual(len(r['trace']),r['solver']['steps']+1)
        self.assertTrue(all(len(row)==len(r['trace_columns']) and all(math.isfinite(x) for x in row) for row in r['trace']))
        self.assertTrue(all(b[0]>a[0] for a,b in zip(r['trace'],r['trace'][1:])))
    def test_invalid_numbers_cannot_become_pass(self):
        for values in ({'bus_v':float('nan')},{'gate_on':True},{'bus_v':-1},{'scenario':'healthy'}):
            with self.assertRaises(ValueError):physics.run(values)

class SuiteVerification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.full=suite.execute({})
    def test_full_required_coverage_and_hardware_separation(self):
        r=self.full;self.assertEqual(r['virtual_suite_verdict'],'PASS');self.assertEqual(r['counts']['PASS'],10)
        self.assertEqual(len(r['shutdowns']),4);self.assertFalse(r['hardware_release']);self.assertEqual(r['hardware_qualification'],'INCOMPLETE')
    def test_expected_fault_trip_can_pass_protection_test(self):
        for t in self.full['tests']:
            if t['key'].endswith('_protection'):self.assertEqual(t['status'],'PASS')
    def test_no_access_with_residual_energy(self):
        for d in self.full['shutdowns']:
            self.assertTrue(d['access_permitted']);last=d['trace'][-1]
            self.assertLessEqual(last[1],30);self.assertLessEqual(last[2],.1);self.assertLessEqual(last[3],.25)
        p,e,station,devices,mode,labels=suite.validate_request({})
        slow=suite.shutdown(p,e|{'dump_r_ohm':1e7},self.full['waveforms'][0])
        self.assertFalse(slow['access_permitted']);self.assertEqual(slow['status'],'FAIL');self.assertEqual(slow['duration_s'],10)
        welded=suite.shutdown(p,e,self.full['waveforms'][0],False)
        self.assertFalse(welded['access_permitted'])
    def test_interlocks_inhibit_all_powered_tests(self):
        for key in suite.STATION:
            r=suite.execute({'station':{key:False}})
            self.assertEqual(r['virtual_suite_verdict'],'ABORTED',key);self.assertEqual(r['waveforms'],[])
    def test_high_conduction_loss_is_detected_before_pulsing(self):
        r=suite.execute({'device_overrides':{'upper':{'ron_factor':4}}})
        self.assertEqual(r['virtual_suite_verdict'],'FAIL');self.assertEqual(r['waveforms'],[])
        tests={t['key']:t for t in r['tests']}
        self.assertEqual(tests['lower_static']['status'],'PASS');self.assertEqual(tests['upper_static']['status'],'FAIL')
    def test_insulation_source_compliance_and_leakage(self):
        p,e,*_=suite.validate_request({})
        r=suite.insulation_test(p|{'ins_mohm':.1},e)
        self.assertEqual(r['status'],'FAIL');self.assertAlmostEqual(r['metrics']['measured_voltage_v'],250)
        self.assertAlmostEqual(r['metrics']['leakage_ma'],2.5)
        full=suite.execute({'parameters':{'ins_mohm':.1}})
        self.assertEqual(full['waveforms'],[])
    def test_driver_collapse_inhibits_switching(self):
        r=suite.execute({'parameters':{'driver_idle_w':30}})
        self.assertEqual(r['virtual_suite_verdict'],'FAIL');self.assertEqual(r['waveforms'],[])
    def test_partial_suite_never_claims_full_pass(self):
        r=suite.execute({'mode':'static'})
        self.assertEqual(r['virtual_suite_verdict'],'INCOMPLETE');self.assertEqual(r['counts']['NOT RUN'],4)
    def test_invalid_energy_window_is_incomplete(self):
        r=physics.run({'second_us':.5})
        checks=suite.dynamic_checks(r,r['parameters'])
        self.assertEqual(next(c['status'] for c in checks if c['key']=='turn_on_window_mj'),'INCOMPLETE')
    def test_operator_stop_preserves_shutdown(self):
        count=0
        def stop():
            nonlocal count
            count+=1
            return count>20
        r=suite.execute({},stop_requested=stop)
        self.assertEqual(r['virtual_suite_verdict'],'ABORTED');self.assertTrue(r['shutdowns'])
        self.assertTrue(r['shutdowns'][-1]['access_permitted'])
    def test_report_has_inputs_limits_sources_and_timing(self):
        r=self.full;self.assertEqual(len(r['profile_sha256']),64)
        self.assertGreater(r['timing']['estimated_automated_cycle_s'],5)
        for test in r['tests']+r['shutdowns']:
            for c in test['checks']:self.assertTrue(c['basis']);self.assertIn('limit',c)

if __name__=='__main__':unittest.main()
