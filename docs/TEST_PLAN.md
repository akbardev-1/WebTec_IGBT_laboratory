# Test selection, acceptance and duration

## Chosen solution

Use one enclosed, interlocked, programmable bench cell with interchangeable keyed DUT adapters, low-energy static instruments and a limited-energy double-pulse power circuit. Test both switch positions separately. A local laptop sequences measurements and stores reports; independent hardware implements protection and energy isolation. The delivered app is the virtual implementation of that proposal.

This combination addresses more failure mechanisms than DPT alone. Static tests catch gross leakage, gate insulation and conduction problems before pulse testing. DPT exposes switching behavior under a declared inductive load. A dedicated protection stimulus demonstrates a shutdown response. Insulation and discharge checks assess the assembly and station, not only the semiconductor.

## Test matrix

| Group | Applied stimulus / measured quantity | Prototype acceptance | Why it matters |
|---|---|---|---|
| Station | Door, clamp, connector, protective earth, E-stop, fiber, cooling and source-isolation feedback | Every declared precondition true | Prevents starting an invalid setup |
| Driver | 100 Vrms, 25 kHz source with modeled load; ±15 V rails | ±5% input, ±1 V rails, ≤20 W per driver | Inadequate drive can mimic device failure |
| Fiber | Configurable command and returned-status delay | ≤1 µs each; link present | Separates local shutdown from laptop notification |
| Gate insulation | +20 V gate, resistive leakage | ≤300 nA surrogate maximum | Screens gate leakage; no oxide-breakdown prediction |
| Collector blocking | 1200 V current-limited static source, gate 0 V | ≤300 µA surrogate maximum | Screens blocking leakage separately from DPT bus voltage |
| On-state conduction | 80 A brief static stimulus, +15 V gate | ≤2.85 V at 25 °C; provisional temperature offset | Detects excessive voltage drop that v1 merely displayed |
| Diode forward / reverse | 1 mA forward; 100 V reverse | 0.2–0.8 V; ≤10 µA reverse | Makes “open” quantitative without confusing it with power-current VF |
| Insulation | Default 500 V through 100 kΩ, 10 nF/100 MΩ DUT, 1 s dwell | Attained voltage within 5%; leakage ≤2 mA; discharge verified | Detects leakage and inadequate test voltage |
| Normal DPT | Default 400 V, 470 µF, 500 µH, 0.1 Ω; 75/8/3 µs | Voltage/current/gate/slew boundaries, current tracking, two energy windows, no unexpected trip | Checks the modeled switching function at an explicit operating point |
| Protection | Companion branch 0.05 Ω / 2 µH applied after first ON +2 µs | Valid fault detection; detection-to-10%-IC ≤10 µs; onset-to-10%-IC ≤5 µs prototype screen | Expected protective action may pass; it is not an ordinary DPT failure |
| Thermal estimate | Calculated terminal loss, 0.1 J/K and 0.6 K/W lumped model | Estimated peak ≤150 °C; reset dwell | Exposes energy/temperature dependencies, pending measured thermal model |
| Shutdown | Source isolated; 1 kΩ dump; passive load-current decay | ≤30 V, ≤0.1 A, ≤0.25 J within 10 s | Prevents treating the end of a 100 µs capture as an energy-free state |

Both IGBTs receive static, switching and protection checks. Their opposite diodes participate in their switching circuits. The source brief does not define a number of repeated trials, statistical confidence level, environmental envelope or manufacturing guard bands. This release runs one declared acquisition per condition; repeatability qualification is a commissioning activity.

## Limits and validity

The complete prototype comparison envelope is 100–600 V and an ideal-RL requested first-pulse current of 20–80 A. Controls permit exploratory values beyond this envelope; those values cannot earn complete model acceptance. Rating violations can still fail. Defaults are illustrative and do not reproduce an unidentified locomotive bus.

The energy budgets are 2 mJ ON and 4 mJ OFF at 400 V / 60 A, scaled by requested V×I and an assumed temperature factor. They are engineering screens, not OEM or datasheet Eon/Eoff limits. Current ceilings also carry pulse/thermal conditions; they do not replace full safe operating area validation.

The 10 µs project shutdown wording and the surrogate's conditional 5 µs withstand rating are not interchangeable. The virtual report keeps both timing measurements visible and never calls their success a survival test.

A failed low-energy screen prevents pulse escalation. Selecting a partial experiment is useful for analysis but always leaves mandatory coverage incomplete. The user cannot certify hardware by ticking an approval checkbox.

## Duration derivation

Default nominal waveform duration is about **100.2 µs**, including 0.2 µs optical command delay. That is only an acquisition window.

| Stage | Duration model / default allowance |
|---|---|
| Station inputs | 0.25 s assumed debounce/verification allowance |
| Driver supply / rail acquisition | 0.25 s assumed settling/acquisition allowance |
| Fiber functional check | 0.10 s assumed transaction allowance |
| Insulation | Selected 1 s dwell plus calculated RC discharge; default approximately 1.008 s |
| Five static checks per position | 0.25 s settle/acquisition allowance each; 1.25 s per position |
| Precharge before each of four powered acquisitions | Cbus×Vbus/Ilimit + 5×Rprecharge×Cbus, a conservative charge-plus-settle allowance; default 0.611 s |
| Powered trace | Exact model end time, ~100.2 µs per acquisition |
| Post-run discharge | Solved threshold time plus 5 ms margin; roughly 1.22 s per default acquisition |
| Thermal reset | Rth×Cth×max[0, ln(temperature rise / 0.05 K)] |
| Operator handling and identification | 90 s assumed for approved handling equipment and a repeatable adapter |
| Report overhead | 2 s assumed physical station allowance |

The app computes the total from each actual run. The reference full suite estimates **about 11.8 s automated**, or **about 104 s including the declared handling/report allowances**. Calculation speed and the six-second graphical replay do not determine experiment duration. A fail-fast or partial suite has a shorter executed timeline; it is not a complete screening-cycle estimate.

For 36 sequential modules, 104 s/module implies roughly 62 minutes before additional batch setup, retests, transport, instrument calibration and operator breaks. This is an arithmetic planning estimate, not a guaranteed throughput claim.

At voltages above 400 V, the candidate B&K supply has a 0.35 A range rather than 0.5 A. Update the charge-limit setting accordingly. Actual precharge and load settling, low-current measurement noise, thermal recovery and fixture handling must be timed during commissioning; use measured 95th-percentile cycle time for production planning.

## Acceptance with measured uncertainty

Before real acceptance, agree measurement uncertainty U for each channel, bandwidth, probe loading, deskew, repeatability and calibration interval. For an upper limit L, a proposed conservative rule is measured value + U ≤ L; overlapping the limit gives INCONCLUSIVE, not automatic pass. For lower limits, use measured value − U ≥ L. This guard-band rule is a proposal for OEM/quality approval and is not applied to synthetic model numbers.

Save nominal and boundary waveforms, measured versus predicted peak values, current ramp, gate plateaus, switching windows, fault endpoints and thermal response. Agree correlation tolerances before fitting; keep hold-out conditions independent from calibration data. Do not tune acceptance thresholds simply to make a module pass.
