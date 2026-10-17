"""Optional developer checks. Requires Node.js 18+, not required to run the lab."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import start
node=shutil.which('node')
if not node:raise SystemExit('Node.js 18+ is required for these optional developer checks.')
with tempfile.TemporaryDirectory() as tmp:
    start.REPORT_ROOT=Path(tmp)
    server=ThreadingHTTPServer(('127.0.0.1',0),start.Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        for script in ('check_ui.cjs','check_model.cjs'):
            completed=subprocess.run([node,str(ROOT/'verification'/script),f'http://127.0.0.1:{server.server_port}'],capture_output=True,text=True,timeout=90)
            output=completed.stdout+completed.stderr
            print(output)
            (ROOT/'verification'/(script.replace('.cjs','')+'.txt')).write_text(output,encoding='utf-8')
            if completed.returncode:raise SystemExit(completed.returncode)
    finally:server.shutdown();server.server_close();thread.join()
