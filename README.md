# IGBT 3D Virtual Lab

An offline virtual prototype for testing an IGBT phase assembly before installation: interactive 3D station, electrical solver, switching traces, protection tests, and traceable reports.

## Run

Requires **Python 3.10+** and a browser with **WebGL 2**. No pip packages or internet connection are needed.

1. Extract the ZIP completely.
2. Open `IGBT_Virtual_Lab_Final` in VS Code.
3. Open a terminal and run:

```powershell
python .\start.py
```

Open **http://127.0.0.1:8787** and click **Run virtual test suite**. Windows users can also double-click `START_LAB.bat`. On macOS/Linux, use `python3 start.py`. Stop the server with Ctrl+C. If the port is occupied, use `python start.py --port 8788`.

## Included

- Upper/lower static, double-pulse and protection tests.
- Driver supply, logical fiber timing and insulation checks.
- Interlocks, stop requests, thermal estimates and discharge verification.
- Interactive 3D inspection, waveform replay and independent device parameters.
- Printable reports, JSON metadata and full CSV traces in `reports/`.
- Test procedure, parameter/duration justification, equipment budget and editable STEP CAD.

Results are calculated from physical inputs; there is no preset pass/fail scenario selector.

## Verify

```powershell
python .\start.py --verify
```

**VIRTUAL SUITE PASS** means all required prototype checks and shutdowns passed. **Hardware qualification remains INCOMPLETE**: this model uses a public surrogate and explicit assumptions. It does not test, certify or control a real IGBT.

Start with [REQUIREMENTS.md](REQUIREMENTS.md), [MODEL.md](MODEL.md), [operating procedure](docs/OPERATING_PROCEDURE.md), [equipment and cost](docs/EQUIPMENT_AND_COST.md), and [verification evidence](verification/VALIDATION.md).
