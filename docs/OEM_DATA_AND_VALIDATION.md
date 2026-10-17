# Inputs and evidence required for physical qualification

The software deliverable is complete as a bounded virtual prototype. The following evidence is unavailable from the presentation and cannot be replaced by generated values.

| Required input | Responsible source | How it changes the project |
|---|---|---|
| Exact semiconductor, assembly, driver and diode part numbers / revisions | OEM or asset owner | Replaces the public surrogate and determines actual ratings |
| Approved circuit, connector pinout, terminal torque and assembly dimensions | OEM drawings | Releases electrical adapters, CAD and mechanical fixture |
| Driver 100 Vrms / 25 kHz tolerances, startup, load and isolation requirements | Driver specification | Replaces idealized supply conversion and budget allowance |
| Fiber optics, encoding, timing, status, heartbeat and loss behavior | OEM interface-control document | Enables a real command/status adapter and fault semantics |
| Permitted pulse current/voltage, gate settings, test temperature and repetition | OEM test specification | Defines the safe stimulus envelope and cooling dwell |
| Static leakage, VCE, diode and insulation conditions / limits | OEM acceptance criteria | Replaces provisional stimuli and test tolerances |
| Fault detection origin, blanking, shutdown endpoint, SC withstand / SOA | OEM protection specification | Resolves the project 10 µs target versus actual device survival |
| Nonlinear capacitance, gate charge, tail current and diode recovery data | OEM model or characterized samples | Improves switching-current, overshoot and energy fidelity |
| Transient thermal impedance, cold plate and coolant requirements | OEM thermal specification | Replaces the single assumed thermal capacitance |
| Calibrated measured traces and instrument uncertainty | Commissioning laboratory | Establishes model accuracy and guarded acceptance |

## Correlation plan

1. Agree test conditions and error limits before fitting. Preserve raw measured data and metadata, including probe type/range, sample rate, bandwidth, deskew, calibration dates and ambient/coolant conditions.
2. Calibrate static characteristics and thermal parameters first. Identify gate-loop and commutation-loop parasitics from measured response or approved electromagnetic extraction.
3. Compare time-aligned gate voltage, collector voltage and collector current at several approved currents, voltages and temperatures. Compare peak values, rise/fall time, current ramp, switching-energy endpoints and protection timestamps.
4. Reserve independent operating points and sample modules for validation. A model fitted to one nominal trace is not validated over the assembly envelope.
5. Record residual error and uncertainty by quantity. Establish the regions where the model may predict acceptance, and return INCONCLUSIVE outside them. Do not hide uncertain measurements behind a single overall green badge.
6. Validate the station's measurement and access/protection functions independently from the model. Establish reference checks, calibration intervals, change control and record retention.

## Approval record template

| Field | Value |
|---|---|
| Assembly / device / driver revisions | NOT PROVIDED |
| Released OEM acceptance specification | NOT PROVIDED |
| Measured dataset identifier | NOT PROVIDED |
| Instrument calibration and uncertainty report | NOT PROVIDED |
| Static / dynamic / thermal correlation result | NOT PERFORMED |
| Independent protection and discharge proof test | NOT PERFORMED |
| Fixture mechanical and insulation review | NOT PERFORMED |
| Responsible engineering and quality approval | NOT PROVIDED |
| Hardware release | **BLOCKED / INCOMPLETE** |

Completing this record requires actual engineering evidence. It is deliberately not a user-editable “hardware qualified” checkbox in the virtual application.
