"""Actual local HTTP jobs, report exports and failure behavior."""
import io
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request,urlopen
from http.server import ThreadingHTTPServer
import zipfile
import start

class HTTPIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=start.REPORT_ROOT;cls.temp=tempfile.TemporaryDirectory();start.REPORT_ROOT=Path(cls.temp.name)
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),start.Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join();start.REPORT_ROOT=cls.old;cls.temp.cleanup()
    def post(self,payload,path='/api/run',origin=None):
        headers={'Content-Type':'application/json'}
        if origin:headers['Origin']=origin
        with urlopen(Request(self.base+path,data=json.dumps(payload).encode(),headers=headers),timeout=30) as response:return json.load(response)
    def complete(self,job):
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            with urlopen(self.base+'/api/jobs/'+job) as response:r=json.load(response)
            if r['status']!='RUNNING':return r
            time.sleep(.02)
        self.fail('Job did not complete')
    def test_full_run_and_complete_report_bundle(self):
        job=self.post({'serial':'UNIT-<script>','operator':'Verification'})['job_id'];status=self.complete(job)
        self.assertEqual(status['status'],'COMPLETE');r=status['result'];self.assertEqual(r['virtual_suite_verdict'],'PASS')
        with urlopen(self.base+'/api/report/'+r['run_id']+'.zip') as response:raw=response.read()
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            self.assertIn('lower_protection.csv',z.namelist());self.assertIn('upper_switching_shutdown.csv',z.namelist())
            html=z.read('report.html').decode();self.assertIn('UNIT-&lt;script&gt;',html);self.assertNotIn('UNIT-<script>',html)
            meta=json.loads(z.read('report.json'));self.assertFalse(meta['hardware_release']);self.assertNotIn('trace',meta['waveforms'][0])
            lines=z.read('lower_switching.csv').decode().splitlines();self.assertEqual(len(lines),len(r['waveforms'][0]['trace'])+1)
    def test_invalid_request_is_rejected(self):
        for body in ({'parameters':{'bus_v':-1}},{'station':{'door_closed':'yes'}},{'mode':'preset_good'}):
            with self.assertRaises(HTTPError) as caught:self.post(body)
            self.assertEqual(caught.exception.code,400)
    def test_foreign_origin_is_rejected(self):
        with self.assertRaises(HTTPError) as caught:self.post({},origin='https://example.com')
        self.assertEqual(caught.exception.code,403)
    def test_run_concurrency_and_stop(self):
        job=self.post({})['job_id']
        with self.assertRaises(HTTPError) as caught:self.post({})
        self.assertEqual(caught.exception.code,409)
        self.post({},'/api/stop/'+job);r=self.complete(job)
        self.assertEqual(r['status'],'COMPLETE');self.assertEqual(r['result']['virtual_suite_verdict'],'ABORTED')
        self.assertFalse(r['result']['hardware_release'])
    def test_station_block_and_unknown_routes(self):
        job=self.post({'station':{'door_closed':False}})['job_id'];r=self.complete(job)['result']
        self.assertEqual(r['waveforms'],[]);self.assertEqual(r['virtual_suite_verdict'],'ABORTED')
        with self.assertRaises(HTTPError) as caught:self.post({},'/api/hardware')
        self.assertEqual(caught.exception.code,404)
    def test_configuration_and_assets(self):
        for path in ('/','/app.js','/style.css','/model.html','/api/config'):
            with urlopen(self.base+path) as response:self.assertEqual(response.status,200);self.assertGreater(len(response.read()),100)
    def test_report_path_traversal_is_rejected(self):
        with self.assertRaises(HTTPError) as caught:urlopen(self.base+'/api/report/..%2fphysics.py')
        self.assertEqual(caught.exception.code,404)

if __name__=='__main__':unittest.main()
