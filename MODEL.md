# Model, equations and interpretation

Version **2.0.0**. SI units internally; explicit V, A, W, µs, s, °C and mJ in the interface. The Python runtime uses only its standard library.

## Scope and provenance

The model is a custom reduced-order circuit solver, not a vendor SPICE model. Selected values come from the **1200 V half-bridge IGBT portion** of onsemi NXH80T120L2Q0S2G, a T-type NPC module. That part is a public surrogate, not the unidentified 25 kg locomotive assembly. The source presentation provides requirements; it does not supply a complete device or driver model.

| Parameter | Model value / origin |
|---|---|
| Gate targets; current slew; insulation leakage; fault delay | ±15 V, 5000 A/µs, 2 mA, ~10 µs: project brief |
| Collector and gate absolute ratings | 1200 V, ±20 V: surrogate; necessary boundaries, not complete SOA |
| Normal pulsed collector / diode screens | 201 A / 84 A: conditional surrogate ratings |
| Static conduction | Typical 2.05 V at 80 A, +15 V, 25 °C; maximum screen 2.85 V: surrogate |
| Threshold | Typical 5.45 V: surrogate; not full enhancement |
| Gate / blocking leakage | 300 nA at 20 V; 300 µA at 1200 V, gate 0 V: surrogate maxima |
| Cies / Coes / Cres | 19.4 / 0.40 / 0.34 nF at 20 V: surrogate, held constant |
| Gate charge / thermal resistance | 800 nC and 0.6 K/W: selected surrogate values used in simplified models |
| Thermal capacitance | 0.1 J/K: explicit engineering assumption |
| Transconductance and carrier response | 25 A/V; 20 ns rising / 100 ns falling: assumptions |
| Diode law | 0.7 V + 0.03525 Ω × I; assumed line through 2.11 V / 40 A typical point |
| DC link / load / pulses | 400 V, 470 µF, 500 µH, 0.1 Ω, 75/8/3 µs: illustrative, not presentation values |
| All other stimuli, tolerances and timing allowances | Identified as prototype assumptions in profile, report and test plan |

Full criteria and provenance are in `profiles/prototype.json`. Each report includes that profile and its SHA-256 hash. Editing a profile does not authorize hardware qualification.

## Dynamic circuit

For each switch position the emitter is the local reference. Upper-position testing uses mirrored terminal references and a separately selected load connection; it is not simultaneous half-bridge PWM. The opposite device's diode properties determine freewheeling. The active device has its own antiparallel clamp and C–E leakage path.

States: gate voltage Vg, collector voltage Vc, DC-link voltage Vb, load current IL, freewheel current ID, optional companion-fault current IF, carrier capacity S and estimated junction temperature T.

```text
(Cge+Cgc) dVg/dt − Cgc dVc/dt = (Vdrive−Vg)/Rg − Vg/Rge
Cce dVc/dt + Cgc(dVc/dt−dVg/dt) + IC + ID − IL − IF + (Vc−Vb)/Rdiode_shunt = 0
L dIL/dt = Vb − Vc − Rload IL
Cbus dVb/dt = −IL − IF + ID + (Vc−Vb)/Rdiode_shunt
Ls dID/dt = Vc − Vb − Vf − Rd ID   (unilateral forward branch)
Lf dIF/dt = Vb − Vc − Rf IF        (only after companion-short insertion)
```

The DC source is disconnected during the captured pulses: energy comes from the finite capacitor. The reverse diode shunt is an explicit resistor; ID itself cannot go negative. The short branch is bidirectional after insertion, so a negative IF later in the trace represents circulating load/fault-loop current, not a clipped or discarded state.

Capacitances are Cge=19.06 nF, Cgc=0.34 nF, Cce=0.06 nF. Constant small-signal capacitances over a large voltage swing are a major approximation. There is gate–collector coupling, but no calibrated nonlinear gate-charge curve or diode reverse-recovery storage.

## Semiconductor and thermal laws

```text
Starget = gm(T) × max(Vg − Vth(T), 0)
dS/dt = (Starget − S) / tau
Ichannel = S × [1 − exp(−max(Vc−Voffset(T),0)/Vknee(T))]
IC = Ichannel + Vc/Rce + negative-voltage antiparallel clamp
Cthermal dT/dt = Vc×IC − (T−Tsink)/Rthermal
```

At 25 °C, Vknee is calibrated to the 80 A / 2.05 V / +15 V point. The editable slope factor multiplies it. It is not an identified bond-wire resistance. Thermal assumptions are Vth=5.45−0.005(T−25), gm=25/[1+0.002(T−25)], Voffset=0.7−0.0015(T−25); Vknee is re-anchored to 2.05+0.0004(T−25) V at 80 A/+15 V. These approximate coefficients are not a validated temperature model. Sink temperature remains the configured starting temperature; there is no coolant flow or multi-layer thermal impedance simulation.

Temperature affects the next electrical solve, and terminal power drives the thermal state. Reset dwell is Rthermal Cthermal ln(temperature rise / 0.05 K), clipped at zero. Each independent acquisition then starts from the declared baseline; this small allowed reset residual is not propagated. This is appropriate only as a bounded prototype approximation.

No avalanche, bond-wire fusing, thermal runaway, material damage, aging or destruction is calculated. Results outside rating boundaries are mathematical extrapolations; a failure does not prove irreversible physical damage.

## Supply, static instruments and insulation

Driver input power is idle power + 800 nC × gate swing × configured gate-activity frequency. Its AC source is a constant-power load behind the selected source resistance. Loaded Vrms is the high-voltage quadratic root, or zero if no root exists. Ideal isolated rails scale with loaded Vrms/100. The 25 kHz AC excitation and gate activity are different frequencies. Converter switching, transformer loss, efficiency, supply ripple and frequency-dependent regulation are absent.

Fiber timing is a logical delay model: command delay moves both pulse edges; status delay offsets the detected-fault timestamp. Fiber loss is a startup inhibit. It is not optical hardware or a protocol stack, and it does not model a mid-run optical dropout. Local protection does not depend on the laptop receiving status.

Static checks apply separate virtual current-limited instruments: gate leakage V/Rge, blocking leakage V/Rce, fixed-current VCE from the nonlinear conduction law, low-current diode VF, and reverse diode V/R. The 80 A static point is an independent brief measurement at fixed temperature, not a continuous thermal load. Instrument bandwidth, noise, breakdown, absorption and measurement loading are not simulated.

For insulation resistance Ri, source resistance Rs, capacitance Ci:

```text
Vfinal = Vtest Ri / (Ri+Rs)
tau = Ci (Ri || Rs)
V(t) = Vfinal [1−exp(−t/tau)]
Ileak(t) = V(t)/Ri
```

The program checks attained voltage as well as leakage; a low reading caused by source-voltage collapse cannot quietly pass. After dwell, the insulation node discharges through the declared resistor. Test voltage/dwell/connections await OEM approval. The presentation's 0.2–0.8 V diode range is used only for the assumed 1 mA static test, not for tens-of-amperes freewheeling.

## Protection and shutdown

The first gate pulse begins at 2 µs plus command propagation delay. A normal DPT must complete without a desaturation trip. In the distinct protection experiment, a declared RL path shorts the load-side companion at first-ON +2 µs. VCE above threshold after blanking latches a fault; a configurable delay commands OFF and suppresses later pulses.

Two metrics are retained: comparator detection to IC below 10% of detection current, and short insertion to the same endpoint. A 1 A detection-current floor prevents a no-current event being treated as an interruption. The former is compared with the project's 10 µs target; the latter with an additional provisional 5 µs deadline. The surrogate's 5 µs short-circuit rating has specified voltage, gate and temperature conditions. Meeting a timing deadline does not calculate short-circuit survival. Normal 201/84 A screens are not misapplied as short-circuit acceptance limits.

After every powered run, a separate passive-network calculation models source isolation, DC-capacitor discharge and a conservative magnetic-current envelope:

```text
Vbus(t) = Vend exp[−t/(Rdump Cbus)]
Ibound(t) = sqrt(2 Emagnetic / Lloop) exp[−Rloop t/Lloop]
Estored(t) = 0.5 Cbus Vbus² + 0.5 Lloop Ibound² + capacitor-energy upper bound
```

The envelope includes signed IF through its squared energy. It omits the forward diode's constant voltage, which slows the estimated decay conservatively. This is not a nanosecond solver continuation. Access requires all three provisional bounds: ≤30 V, ≤0.1 A and ≤0.25 J, plus isolation feedback, before a 10 s timeout. These are prototype thresholds, not an approved general safe-touch rule. An open/very resistive discharge path fails and retains the virtual access block.

A stop request during calculation forces the gate OFF at the next polling point, completes the numerical trace and discharge, marks the suite ABORTED and skips remaining tests. The request is a software workflow control, not an emergency-stop device or a real-time hardware command. A graphical replay never operates power hardware.

## Numerical method and measurements

Backward Euler with safeguarded scalar Newton iteration solves collector KCL after eliminating the other electrical nodes. The default step is 0.5 ns near edges and 20 ns otherwise. At least 2 µs, or six gate RC constants, is refined after a pulse/fault/stop edge. Nonconvergence or failed energy conservation yields no valid verdict.

Accounting includes finite DC-link storage, all modeled losses, gate-source energy, inductor/capacitor energy and explicit backward-Euler numerical dissipation. Conservation proves internal arithmetic consistency, not physical fidelity. Half-step convergence checks peak voltage/current and integrated energies; the recorded evidence is in `verification/`.

Slew uses a declared 10 ns aperture. ON and OFF energy checks use fixed 2 µs windows after the second ON and first OFF edges. They include any conduction portion and are not standardized datasheet Eon/Eoff. A second pulse shorter than the window makes energy acceptance INCOMPLETE. Prototype budgets scale with requested bus voltage and ideal-RL target current, not with a faulty measured current that could relax its own limit.

All criteria use the full numerical trace. Graphs retain per-pixel extrema; CSV files retain every nonuniform timestep. There is no instrument noise model or uncertainty applied to simulated values.

## Decisions

- **PASS:** every required prototype group and every executed shutdown passed.
- **FAIL:** at least one evaluated requirement failed. Reports also show any tests skipped by the failure.
- **INCOMPLETE:** no failing check, but required tests or valid comparison conditions are missing.
- **ABORTED:** a precondition or operator stop prevented the full workflow.
- **NO VALID RESULT / INVALID:** malformed input, numerical, server, network or saving failure; never a pass.

Hardware qualification is always **INCOMPLETE** in this release. Numerical results, estimates and a correct workflow cannot substitute for OEM limits and measured correlation.

## Sources

- User presentation: `NU IEEE 2026 IGBT test cell_AK_Final`, slides 5–6 and 8–11.
- [onsemi NXH80T120L2Q0S2G datasheet](https://www.onsemi.com/download/data-sheet/pdf/nxh80t120l2q0s2g-d.pdf): half-bridge device ratings and selected typical points. No vendor model validation implied.
- [Tektronix double-pulse measurement application note](https://www.tek.com/en/documents/application-note/double-pulse-test-tektronix-afg31000-arbitrary-function-generator): DPT topology, pulse sequence and voltage/current measurement context.
