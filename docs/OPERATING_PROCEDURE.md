# Operating procedure

## Virtual laboratory

1. Extract the complete ZIP. Open the folder containing `start.py` in VS Code. Run `python start.py` on Windows or `python3 start.py` on macOS/Linux. Python 3.10+ and WebGL 2 are required; no pip install is needed.
2. Open the printed localhost URL. Do not open `static/index.html` directly. The Python server performs calculations and saves reports.
3. Enter an assembly identifier and operator name. These identify a virtual input snapshot; they are not evidence of a physical unit being connected.
4. Keep **Complete required suite** selected for an overall prototype decision. Review the station states and all assumed physical inputs. Defaults are a public surrogate profile, not the OEM locomotive module.
5. If needed, expand **Independent upper / lower properties**. Blank entries inherit shared values; a numeric override changes that position's actual model parameter. There is no healthy/faulty preset selector.
6. Click **Run virtual test suite**. Inputs lock during computation. Static, insulation or driver failures prevent escalation to powered acquisitions. The calculation applies a declared companion RL short only in the protection experiment.
7. To interrupt an active calculation, click **Stop active virtual run**. The server inhibits the gate, calculates shutdown, saves an ABORTED report and skips remaining work. The run may finish before a click arrives. This button is not a physical emergency stop.
8. Read the overall verdict and every mandatory-coverage chip. **PASS** requires all required groups and all shutdowns. A partial test selection produces **INCOMPLETE** unless an evaluated check fails. **ABORTED** means the workflow was interrupted or preconditions were unmet. A numerical/network/saving error produces **NO VALID RESULT**.
9. Select a recorded stage above the time slider. Inspect either device's switching/protection trace, its shutdown, the driver AC waveform, or the insulation charge/discharge. Switching traces use µs; shutdown and auxiliary traces use seconds. Edge zoom applies only to circuit traces.
10. Use Replay, the slider or a graph click to move the cursor. Playback stretches the selected window to six seconds. The 3D current intensity is calculated from the cursor trace; it is not measured current or temperature. The shutdown display shows a current upper bound, not a continued transistor waveform.
11. Inspect the check table: calculated value, limit, outcome and source. A failed check can indicate unsuitable settings or an altered model parameter; it does not uniquely diagnose a real failure mechanism.
12. Check virtual fixture access after discharge. Failed residual-energy checks retain the access block. Door position is an interlock input and moves the model door; changing it to open before a run blocks energization.
13. Use **Open printable report** to print or save PDF in the browser. **Download report + all CSVs** obtains the complete run ZIP. **Selected trace CSV** exports the displayed trace. Every completed run is also saved in `reports/<run-id>/` with HTML, JSON and all raw CSVs.
14. Changing any input marks the old result **INPUTS CHANGED**. Existing downloads retain the old report/input snapshot. Run again to evaluate new settings. **Reset values** changes inputs only; it is not a new electrical test or proof that a failed physical condition recovered.
15. Press Ctrl+C in the terminal to stop the local server after the run and report save. Closing the browser does not cancel a server-side calculation. Restarting the server preserves saved reports but loses its in-memory recent-job list; open saved `report.html` directly to review those runs.

## What the decisions do not mean

Hardware qualification always remains INCOMPLETE. No instrument is connected or controlled. No module is approved for installation. The physical project requires exact OEM data, measured model correlation and an independently reviewed station. There are no burning/damage animations because irreversible device damage is not modeled.

## Verification

Run `python start.py --verify` from the project folder. The included tests check conservation, convergence, physical sensitivity, protection timing, coverage, discharge, cancellation and the real local HTTP/report path. Node-based UI/WebGL harnesses are in `verification/` for development; Node is optional and unnecessary to run the lab.

## Troubleshooting

| Symptom | Action |
|---|---|
| `python` is not recognized | Install Python 3.10+ with the PATH option; on Windows try `py -3 start.py` if the launcher is installed |
| Browser did not open | Enter the URL printed by the server manually |
| Port 8787 is occupied | Run `python start.py --port 8788` and open the matching URL |
| Solver unavailable | Keep the Python terminal running; use localhost rather than an HTML file path |
| Blank 3D area | Enable WebGL 2 / browser hardware acceleration; try a current supported browser. Numerical results can still be inspected in reports |
| Permission error saving reports | Move the extracted project to a writable user folder; a save failure never produces a successful report |
| INCOMPLETE result | Check test selection, missing coverage, comparison envelope and energy-window duration |
| ABORTED before pulses | Review each virtual station input |
| Discharge FAIL | Review dump resistance and residual limits; changing a value creates a new virtual experiment, not a repair of real equipment |
| Calculation interrupted / browser connection lost | Check the terminal and `reports/`. Do not infer success from a previous green result |

## Physical commissioning framework — requires an approved station

This is a sequence for the responsible engineering team to turn the proposal into an approved test process, not instructions to energize the concept CAD.

1. Obtain exact assembly/device/driver part numbers, drawings, pinout, fiber protocol, supply requirements, cooling conditions, allowable stimuli and acceptance criteria. Resolve the 10 µs fault wording and real device short-circuit withstand.
2. Review the electrical design, independent gate inhibit, current/voltage limits, stored-energy containment, isolation contactors, protective earth, discharge redundancy, access locking and fixture handling. Approve components, ratings and installation conditions.
3. Validate controls and interlock behavior with isolated low-energy dummy loads. Demonstrate that a laptop/network/software failure cannot maintain an unsafe gate command, defeat isolation or grant access.
4. Calibrate instruments, verify polarity/range and protection settings, establish voltage/current probe deskew, and document measurement uncertainty. Verify absence-of-voltage and discharge using independent means defined by the approved procedure.
5. Correlate the model to approved reference hardware starting at authorized low-energy conditions. Increase energy only through the agreed commissioning stages. Short-circuit testing requires a separately engineered, limited-energy setup; never assume the virtual 400 V fault experiment is a safe physical starting point.
6. Establish an approved reference module and permitted verification artifacts for known electrical limits. Run repeatability/reproducibility and environmental tests; validate fail/abort/inconclusive paths without intentionally damaging production modules.
7. Release a versioned acceptance profile and test instruction with engineering/quality sign-off, operator training, maintenance/calibration intervals and record retention. Then measure cycle time on the actual fixture.
8. During operation, identify and inspect each module, use the approved lifting/fixture method, verify connections/cooling/interlocks, run the released procedure, review complete evidence, verify energy isolation before access and quarantine failed or incomplete units. A reset must never silently turn a failed record into a pass.
