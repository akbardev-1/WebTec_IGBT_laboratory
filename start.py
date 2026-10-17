"""Local-only application, cancellable virtual jobs, and durable run reports."""
import argparse
import csv
import html
import json
from pathlib import Path
import threading
import time
from uuid import UUID, uuid4
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
import suite

ROOT=Path(__file__).resolve().parent
REPORT_ROOT=ROOT/'reports'
FILES={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),
       '/style.css':('style.css','text/css; charset=utf-8'),'/model.html':('model.html','text/html; charset=utf-8')}
JOBS={};JOB_LOCK=threading.Lock();RUN_LOCK=threading.Lock()

def without_traces(value):
    if isinstance(value,dict):return {k:without_traces(v) for k,v in value.items() if k!='trace'}
    if isinstance(value,list):return [without_traces(v) for v in value]
    return value

def printable_report(r):
    esc=lambda x:html.escape(str(x))
    sections=[]
    for test in r['tests']+r['shutdowns']:
        rows=''.join('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in [c['label'],c['value'],c['limit'],c['unit'],c['status'],c['basis']])+'</tr>' for c in test['checks'])
        sections.append('<h2>'+esc(test['label'])+' — '+esc(test['status'])+'</h2><table><thead><tr><th>Check</th><th>Calculated</th><th>Limit</th><th>Unit</th><th>Outcome</th><th>Basis</th></tr></thead><tbody>'+rows+'</tbody></table>')
    coverage=''.join('<li>'+esc(x['key']+': '+x['status'])+'</li>' for x in r['coverage'])
    blocks=''.join('<li>'+esc(x)+'</li>' for x in r['qualification_blockers'])
    return '<!doctype html><html lang="en"><meta charset="utf-8"><title>IGBT virtual test report</title><style>body{font:14px system-ui;max-width:1200px;margin:35px auto;padding:0 20px;color:#20374a}h1{font-size:27px}h2{font-size:18px;margin-top:30px}table{border-collapse:collapse;width:100%;font-size:11px}th,td{padding:8px;border:1px solid #ccc;text-align:left}th{background:#edf3f6}pre{white-space:pre-wrap;font-size:10px}li{margin:7px 0}@media print{button{display:none}h2{break-after:avoid}tr{break-inside:avoid}}</style><h1>IGBT 3D Virtual Lab — run report</h1><button onclick="print()">Print / save PDF</button><p><b>Virtual suite: '+esc(r['virtual_suite_verdict'])+' · Hardware qualification: INCOMPLETE</b></p><p>Assembly: '+esc(r['serial'])+' · Operator: '+esc(r['operator'])+'<br>Run: '+esc(r['run_id'])+' · '+esc(r['created_utc'])+'<br>Version: '+esc(r['model_version'])+' · Profile: '+esc(r['profile']['id'])+'</p><p>'+esc(r['completion_statement'])+'</p><p>Estimated automated cycle: '+esc(round(r['timing']['estimated_automated_cycle_s'],3))+' s. Estimated total including assumed handling: '+esc(round(r['timing']['estimated_total_s'],2))+' s. These are model estimates, not measured throughput.</p><h2>Mandatory coverage</h2><ul>'+coverage+'</ul>'+''.join(sections)+'<h2>Hardware qualification blockers</h2><ul>'+blocks+'</ul><h2>Inputs and traceability</h2><pre>'+esc(json.dumps({k:r[k] for k in ('parameters','device_parameters','station','profile_sha256','sources','timeline')},indent=2))+'</pre><p>Raw waveform CSVs and numerical diagnostics accompany this report. No physical instrument was controlled and no real IGBT was tested.</p></html>'

def save_report(result):
    folder=REPORT_ROOT/result['run_id'];folder.mkdir(parents=True,exist_ok=False)
    result['saved_report']='reports/'+result['run_id']
    (folder/'report.json').write_text(json.dumps(without_traces(result),indent=2,allow_nan=False),encoding='utf-8')
    (folder/'report.html').write_text(printable_report(result),encoding='utf-8')
    for item in result['tests']+result['waveforms']+result['shutdowns']:
        if 'trace' not in item:continue
        key=item.get('test_key',item.get('key'))
        with (folder/(key+'.csv')).open('w',newline='',encoding='utf-8') as f:
            writer=csv.writer(f);writer.writerow(item['trace_columns']);writer.writerows(item['trace'])
    with zipfile.ZipFile(folder/'report.zip','w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(folder.iterdir()):
            if path.name!='report.zip':z.write(path,path.name)
    return folder

def launch(payload):
    suite.validate_request(payload)
    if not RUN_LOCK.acquire(blocking=False):return None
    job_id=str(uuid4());stop=threading.Event()
    job={'id':job_id,'status':'RUNNING','phase':'Checking station interlocks','completed':0,'required':len(suite.REQUIRED),'stop':stop}
    with JOB_LOCK:
        # Retain recent results in memory; all completed reports persist on disk.
        for key in list(JOBS)[:-2]:
            if JOBS[key]['status']!='RUNNING':del JOBS[key]
        JOBS[job_id]=job
    def progress(phase,completed,total):
        with JOB_LOCK:job.update(phase=phase,completed=completed,required=total)
    def work():
        started=time.perf_counter()
        try:
            r=suite.execute(payload,progress,stop.is_set)
            r['computation_seconds']=time.perf_counter()-started
            save_report(r)
            with JOB_LOCK:job.update(status='COMPLETE',phase='Report saved',result=r)
        except Exception as exc:
            with JOB_LOCK:job.update(status='ERROR',phase='No valid result',error=str(exc),verdict='INVALID')
        finally:RUN_LOCK.release()
    thread=threading.Thread(target=work,daemon=True);thread.start()
    return job_id

class Handler(BaseHTTPRequestHandler):
    server_version='IGBTVirtualLab/2.0'
    def send(self,status,body,mime,download=None):
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        if download:self.send_header('Content-Disposition','attachment; filename="'+download+'"')
        self.end_headers()
        try:self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError):pass
    def json(self,status,data):self.send(status,json.dumps(data,allow_nan=False).encode(),'application/json; charset=utf-8')
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/api/config':return self.json(200,suite.configuration())
        if path.startswith('/api/jobs/'):
            key=path.rsplit('/',1)[-1]
            with JOB_LOCK:
                job=JOBS.get(key)
                if job is None:return self.json(404,{'error':'Job not found. Saved reports remain in reports/.'})
                data={k:v for k,v in job.items() if k!='stop'}
            return self.json(200,data)
        if path.startswith('/api/report/'):
            name=path.rsplit('/',1)[-1]
            try:
                key,extension=name.rsplit('.',1)
                if str(UUID(key))!=key or extension not in ('zip','html'):raise ValueError()
                body=(REPORT_ROOT/key/('report.'+extension)).read_bytes()
            except (ValueError,OSError):return self.json(404,{'error':'Report not found.'})
            return self.send(200,body,'application/zip' if extension=='zip' else 'text/html; charset=utf-8','igbt_'+name if extension=='zip' else None)
        if path=='/model-notes':return self.send(200,(ROOT/'MODEL.md').read_bytes(),'text/plain; charset=utf-8')
        if path=='/instructions':return self.send(200,(ROOT/'docs/OPERATING_PROCEDURE.md').read_bytes(),'text/plain; charset=utf-8')
        if path in FILES:
            filename,mime=FILES[path]
            return self.send(200,(ROOT/'static'/filename).read_bytes(),mime)
        self.json(404,{'error':'Unknown route.'})
    def do_POST(self):
        path=urlsplit(self.path).path
        origins=(f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}')
        origin=self.headers.get('Origin')
        if origin and origin not in origins:return self.json(403,{'error':'Open the app at its localhost address.'})
        if path.startswith('/api/stop/'):
            key=path.rsplit('/',1)[-1]
            with JOB_LOCK:
                job=JOBS.get(key)
                if job is None:return self.json(404,{'error':'Job not found.'})
                if job['status']=='RUNNING':job['stop'].set()
            return self.json(200,{'stop_requested':True,'note':'Any active virtual pulse is inhibited; calculated shutdown still runs. This controls no hardware.'})
        if path!='/api/run':return self.json(404,{'error':'Unknown route.'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=24000:raise ValueError('Invalid request size.')
            payload=json.loads(self.rfile.read(size))
            job=launch(payload)
        except (ValueError,TypeError,UnicodeDecodeError) as exc:return self.json(400,{'error':str(exc)})
        if job is None:return self.json(409,{'error':'A virtual run is already active.'})
        self.json(202,{'job_id':job})
    def log_message(self,fmt,*args):
        if not self.path.startswith('/api/jobs/'):print('[virtual lab] '+fmt%args,flush=True)

def main():
    parser=argparse.ArgumentParser(description='IGBT 3D virtual laboratory. No hardware interface.')
    parser.add_argument('--port',type=int,default=8787);parser.add_argument('--no-browser',action='store_true')
    parser.add_argument('--verify',action='store_true',help='Run numerical, decision and HTTP checks, then exit.')
    args=parser.parse_args()
    if args.verify:
        import unittest
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT),'test_*.py')).wasSuccessful() else 1
    try:server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    except OSError as exc:print('Cannot start:',exc,'\nTry: python start.py --port 8788');return 1
    url=f'http://127.0.0.1:{server.server_port}/'
    print('\nIGBT 3D VIRTUAL LAB 2.0\n'+url+'\nCtrl+C stops the local server.\n',flush=True)
    if not args.no_browser:
        timer=threading.Timer(.5,webbrowser.open,args=(url,));timer.daemon=True;timer.start()
    try:server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:pass
    finally:
        with JOB_LOCK:
            for job in JOBS.values():job['stop'].set()
        server.server_close()
    return 0

if __name__=='__main__':raise SystemExit(main())
