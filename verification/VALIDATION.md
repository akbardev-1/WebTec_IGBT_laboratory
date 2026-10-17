# Verification evidence and limits

Version 2.0.0, executed 2026-10-17 in the supplied Linux workspace with Python 3.12. This document distinguishes **software/numerical verification** from **validation against physical measurements**. The latter has not been performed because no real module data or measured traces were supplied.

## Executed checks

`python start.py --verify` completed **29 tests, all passing**. The exact output is in `numerical_and_api_checks.txt`.

| Evidence group | What was actually checked |
|---|---|
| Conservation | Normal and companion-fault KCL residuals and complete modeled energy accounting |
| Numerical accuracy | 0.5 ns versus 0.25 ns edge steps; all selected peak/energy differences below 2.5% |
| Analytical relationships | 80 A / 2.05 V static calibration point; inductive current ramp; insulation RC source division |
| Physical sensitivity | Load inductance, DC-link capacitance, opposite-device diode resistance, temperature and conduction factor change calculated quantities |
| Protection | An explicit RL fault produces current and detection; late shutdown fails timing; expected prompt shutdown may pass the protection group |
| Decisions | Ten mandatory groups required for a full pass; partial coverage is incomplete; high conduction loss is detected before pulsing |
| Inhibits | Every station input can prevent energization; driver/insulation failures inhibit pulse escalation |
| Stored energy | Completed discharge meets all three bounds; very high dump resistance and failed isolation feedback block access |
| Interruption | Gate inhibit after stop; computed shutdown retained; aborted acquisition never earns overall pass |
| HTTP / reports | Real local server, asynchronous jobs, concurrent-run rejection, cancellation, JSON/HTML/CSV ZIP, full row counts, escaped identifiers, invalid inputs/origins/paths |

These negative-input tests verify detection and control logic. They do not feed preset outcomes to the simulator. Runtime traces always come from the equations and selected physical inputs.

## Reference full suite

`reference/default_run/` contains a full reference report, all raw CSVs and a bundled ZIP. `reference/summary.json` contains stable summary fields and the exact profile traceability. `Reference_Waveforms.png` plots computed data; it contains no measured hardware traces.

| Reference quantity | Calculated value, rounded |
|---|---:|
| Mandatory groups passed | 10 of 10 |
| Overall virtual suite | PASS |
| Hardware qualification | INCOMPLETE |
| Default normal peak IC | 65.318 A |
| Default normal peak VCE | 547.862 V |
| Companion-fault peak IC | 277.143 A |
| Fault insertion to current below 10% | 2.365 µs |
| Executed powered acquisitions / discharge checks | 4 / 4 |
| Estimated automated cycle | 11.831 s |
| Total with assumed 90 s handling + 2 s report allowance | 103.831 s |

The full-suite default effective gate rails include modeled supply droop. Direct `physics.run({})` uses the input ±15 V rails directly, so its nominal values differ slightly. Upper and lower default results match because their input properties are identical and their terminal references are mirrored; they are not independent measured samples.

| Direct-circuit metric | Relative difference after halving timestep |
|---|---:|
| Peak VCE | 1.2714% |
| Peak IC | 0.3746% |
| Total device energy | 0.2309% |
| 2 µs turn-on window energy | 0.9667% |
| 2 µs turn-off window energy | 0.3071% |

This comparison supports numerical resolution at the reference point. It is not a general error bound for all permitted parameter extremes and does not establish semiconductor model accuracy. The largest reference full-suite energy residual is below 2×10⁻¹⁰ J; explicit numerical damping is separately reported.

## Interface and 3D evidence

`python verification/run_ui_checks.py` passed the optional Node.js checks:

- Actual API configuration and full calculation rendered through the application code.
- All ten coverage groups, independent hardware state, waveform graphs and trace selection.
- Waveform cursor updates to 3D, edge zoom, replay and correct µs/second units.
- Calculated insulation failure, incomplete partial suite, door interlock, stop and network-error handling.
- 608-component WebGL command stream, finite matrices, camera presets, orbit/zoom, ray selection, cutaway, door animation, current/status colors and final station-door bindings.

Exact logs: `check_ui.txt` and `check_model.txt`. These are DOM/network and WebGL-command harnesses, not a full graphical browser session. No installed browser binary was available for end-to-end graphical testing; Windows/macOS-specific launch and browser rendering were not directly executed in this environment.

`render_3d.py` also compiled the viewer's actual shaders and rendered its embedded geometry through Mesa OpenGL ES. `render_3d.txt` records success and `IGBT_Test_Cell_Preview.png` is the resulting offscreen render. It verifies geometry/shader rendering, not browser layout or physical construction validity. Instrument-face graphics in the concept CAD are static illustrations; the application's separate numerical waveform graphs contain the calculated traces.

## Reproduction

```text
python start.py --verify
python verification/run_ui_checks.py
python verification/make_reference.py
```

Only the first command and normal app need Python's standard library. The second requires Node.js 18+. The third always writes reports; optional plots additionally require NumPy/Matplotlib. `render_3d.py` requires a Linux EGL/GLES environment, NumPy and Pillow and is a development check, not a runtime requirement. CAD regeneration has its own optional dependencies in `cad/README.md`.

## Unverified physical claims

No real IGBT was connected, pulsed, diagnosed, damaged or accepted. No OEM calibration, full SOA assessment, reverse-recovery validation, nonlinear-capacitance fit, accurate optical protocol, uncertainty budget, mechanical proof test, insulation certification or independent protection qualification was performed. Those dependencies are itemized in `docs/OEM_DATA_AND_VALIDATION.md`.
