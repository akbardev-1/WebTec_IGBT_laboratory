# Requirements and final-version coverage

Source: user-supplied **NU IEEE 2026 IGBT test cell_AK_Final**, slides 5–6, 8–11. Version 2.0.0 is the final **virtual prototype and engineering proposal** package. It is not a validated digital twin or an approved production test station.

## Problem and intended outcome

The presentation describes defective modules being discovered after installation in a locomotive. Removing and replacing them consumes labor and delays operation. The proposed solution is a dedicated pre-installation bench test cell that screens the phase assembly, records the evidence on a laptop, and distinguishes a measured failure from an incomplete test.

The source describes 36 modules per locomotive and a roughly 55 lb / 25 kg phase assembly. A complete screening plan therefore needs repeatable handling and identification as well as electrical measurements. Passing a convenient simulation is not the objective: the objective is a credible test process with justified acceptance limits and known coverage.

## Seven assigned tasks

| Original task | Delivered here | Status and boundary |
|---|---|---|
| 1. Propose a prototype bench tester before installation | Fixed test architecture, 3D station, STEP assembly, component specifications and commissioning gates | Complete as a virtual prototype proposal; detailed construction drawings require actual assembly dimensions/interfaces |
| 2. Check multiple parameters / working condition | Ten required groups: station, driver, fiber, insulation, lower/upper static, switching and protection; shutdown after each powered acquisition | Implemented for the declared surrogate profile; real-module working condition is not established |
| 3. Laptop test report | Local app; run ID, assembly/operator ID, UTC time, input snapshot, profile hash, limits, provenance, coverage, numerical evidence; HTML, JSON and CSV ZIP | Implemented and integration-tested |
| 4. Select and justify the best test parameters | `docs/TEST_PLAN.md`, profile and MODEL document: gate, static leakage/conduction, diode, insulation, dynamic switching, fault timing and residual energy | Complete proposal; omitted OEM stimuli/tolerances explicitly remain assumptions |
| 5. Justify test duration | Per-stage computed timing, precharge/discharge/thermal reset equations, operator allowance and throughput estimate | Complete analytical estimate; physical time study remains necessary |
| 6. Provide instructions | `docs/OPERATING_PROCEDURE.md`, launchers, verification command, troubleshooting and staged hardware commissioning | Complete virtual procedure and physical commissioning framework; not an energized-work permit |
| 7. Estimate equipment cost | Itemized USD budget, dated vendor price anchors, engineering allowances, contingency and labor | Complete concept estimate; no supplier quotation or purchase approval implied |

## Technical source requirements

| Presentation requirement | Implementation / acceptance treatment | Remaining evidence |
|---|---|---|
| +15 V ON, −15 V OFF | Loaded supply changes gate rails; calculated settled gate voltages checked against ±1 V assumed tolerance | OEM rail tolerance, impedance, transient limits and clamp behavior |
| Driver supply 100 Vrms / 25 kHz | AC waveform and constant-power source-droop model; frequency and rail checks | Actual converter schematic, transformer, frequency response and efficiency |
| Driver power ≤20 W | Idle + Qg × gate swing × activity frequency, per channel | Measured Qg, actual driver power and whether the 20 W allocation is per driver or assembly |
| Maximum di/dt 5000 A/µs | Full-trace derivative over a declared 10 ns aperture | OEM bandwidth/endpoint definition and measurement uncertainty |
| Diode forward 0.2–0.8 V, reverse “open” | Separate 1 mA forward and 100 V reverse leakage screens; independent of power-current VF | OEM low-current stimulus, temperature, permissible reverse leakage and breakdown conditions |
| Saturation-fault shutdown ~10 µs | Explicit companion RL short; comparator, blanking and delay; detection-to-10% current ≤10 µs; additional prototype fault-onset ≤5 µs screen | OEM fault origin/endpoint, full short-circuit SOA, validated soft shutdown and fault network |
| Insulation leakage ≤2 mA | RC charging, attained-voltage check, dwell leakage, separate discharge | OEM test voltage, dwell, connections, environmental conditions, dielectric-withstand procedure |
| Upper and lower switches with antiparallel diodes | Independent device property overrides; mirrored DPT terminal references; opposite device's diode used for freewheeling | Simultaneous leg operation, common-mode coupling, parasitic turn-on and actual switching matrix |
| Fiber command/status | Command delay enters pulse timing; local fault creates returned-status timestamp; disconnected link inhibits startup | Wavelength, connector, coding, heartbeat, protocol, timeout and receiver circuits |
| Laminated busbar and cooling | Editable loop inductance / insulation RC; lumped thermal network and cooling dwell | CAD-derived parasitics, approved clearances, actual cold-plate and coolant behavior |
| 25 kg phase assembly handling | Sliding fixture concept and load-rating specification | Measured dimensions, center of mass, lifting method, structural calculations and proof test |

The slide statement about being “fully on” around 4–7 V must not become a gate-drive requirement. Threshold conduction is distinct from full enhancement; the project commands +15 V. The model uses a 5.45 V surrogate threshold only inside its conduction law.

## What is finished versus unavailable

Software workflow and design/proposal documents are delivered. A final production decision still needs inputs that were never in the presentation: exact part numbers, OEM limits, interface details, physical traces, calibrated measurement uncertainty and approved construction/protection design. The application cannot manufacture that evidence; its hardware-qualification field is therefore always INCOMPLETE.

There is no hardware-control interface, instrument driver, automatic connection to a locomotive, approved wiring drawing, or implemented semiconductor damage/lifetime predictor. The CAD does not silently replace those missing deliverables.
