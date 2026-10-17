# Equipment and approximate cost

**Concept estimate in USD, prepared 2026-10-17.** Three vendor prices were checked on their official North American pages; all other line items are explicitly engineering allowances. Prices exclude tax, shipping, import duty and local installation. This is a planning budget, not a quote or purchase recommendation for an unidentified OEM assembly.

The selected architecture is a modular enclosed static + double-pulse cell. Candidate instruments serve the 400 V prototype and reviewed extensions up to 600 V; they do not establish a final locomotive-voltage rating. Existing suitable laboratory equipment can reduce the incremental cost.

| Item | Candidate / specification | Qty | Unit estimate | Extended | Basis |
|---|---|---:|---:|---:|---|
| DC-link charging supply | B&K 9185B candidate: 0–400 V/0.5 A or 0–600 V/0.35 A | 1 | $1,797 | $1,797 | Published USD price; source 1 |
| Oscilloscope | SIGLENT SDS3034X HD candidate, 350 MHz / four channels | 1 | $4,244 | $4,244 | Published USD price; source 2 |
| Collector differential probe | SIGLENT DPB5150A candidate, 100 MHz / 1500 V differential | 1 | $1,392 | $1,392 | Published USD price; source 3; common-mode installation must be reviewed |
| Isolated gate measurement | Wideband optical/isolated probe with suitable high-side CMRR | 1 | $8,000 | $8,000 | Engineering allowance; obtain quotation |
| Pulse current measurement | Qualified low-inductance shunt / sensor and isolated acquisition | 1 | $3,000 | $3,000 | Engineering allowance; review bandwidth and fault pulse rating |
| Deskew / calibration fixture | Voltage-current timing alignment fixture | 1 | $350 | $350 | Engineering allowance |
| Pulse generator / sequencer | Hardware timing, bounded pulse width, independent gate inhibit | 1 | $1,800 | $1,800 | Engineering allowance |
| 100 Vrms / 25 kHz driver source | Custom isolated excitation, two driver channels with margin | 1 | $3,500 | $3,500 | Engineering allowance; OEM details required |
| Fiber interfaces / adapters | Command/status transmitters, receivers and keyed interface | 1 | $1,200 | $1,200 | Engineering allowance; protocol and optics unknown |
| HV static / insulation instrumentation | Guarded current-limited 1200 V source and leakage measurement | 1 | $4,500 | $4,500 | Engineering allowance; separate from 600 V charger |
| Static conduction pulse source | 80 A brief-current capability and Kelvin measurement fixture | 1 | $2,000 | $2,000 | Engineering allowance; may share an approved pulse stage |
| Bench DMM / auxiliary metrology | Low-energy diode, rails and continuity measurements | 1 | $650 | $650 | Engineering allowance |
| Pulse power components | DC capacitors, load inductor, busbar and limited-energy fault fixture | 1 | $2,500 | $2,500 | Engineering allowance; pulse ratings need review |
| Independent safety hardware | Contactors, fuses, interlocks, dump resistors, voltage monitor, E-stop | 1 | $2,500 | $2,500 | Engineering allowance; no safety certification assumed |
| Cabinet / fixture / handling | Guarded enclosure, slide, restraint and lifting aid provision | 1 | $4,000 | $4,000 | Engineering allowance for prototype fabrication |
| Cooling and sensors | Cold-plate interface, coolant hardware, flow and temperature sensing | 1 | $1,500 | $1,500 | Engineering allowance |
| Local controller / I/O | Isolated sequencing and feedback I/O, separate from safety logic | 1 | $800 | $800 | Engineering allowance |
| Laptop | Local sequencing/report workstation | 1 | $1,000 | $1,000 | Engineering allowance; subtract if already available |
| Wiring / adapters / labels | Rated cables, connectors, guards, terminals and identification | 1 | $1,000 | $1,000 | Engineering allowance |
| Initial calibration / verification | Instrument checks and metrology services | 1 | $1,200 | $1,200 | Engineering allowance; annual cost not included |

| Cost summary | Estimate |
|---|---:|
| Equipment / initial services subtotal | **$46,933** |
| Concept contingency, 20% | **$9,387** |
| Equipment budget including contingency | **$56,320** |
| Engineering/integration/commissioning allowance, 200 h × $80/h | **$16,000** |
| Total prototype planning budget | **$72,320** |

Allow roughly **$60k–$90k overall** until actual interfaces, quotations and instrument reuse are established. That range is a judgment-based planning range, not a statistical confidence interval. Reusing an approved scope, probes and laptop may reduce costs substantially. Labor rate and hours are assumptions and should be replaced with local estimates.

## Procurement and scope checks

- The 9185B's ranges are **400 V/0.5 A** and **600 V/0.35 A**. Do not assume 600 V at 0.5 A. The app's default 0.5 A charge allowance applies to its 400 V default; reduce the setting when using the 600 V range.
- The DPB5150A page listed $1,392 and availability around 2026-12-16 at review. Obtain current lead time before scheduling. Its differential voltage and bandwidth do not alone establish suitable common-mode performance, insulation category, transient derating or gate-voltage resolution.
- Upper-device gate measurements need an appropriate isolated probe. A standard grounded oscilloscope probe is not a substitute. The isolated-probe allowance is deliberately separate from the collector probe.
- Probe, current sensor, scope and fixture form one measurement chain. Verify simultaneous sample rate, bandwidth, loading, current range, pulse energy and deskew at the actual measurement configuration.
- The 1200 V static leakage instrument, 80 A brief conduction measurement and 100 Vrms/25 kHz driver source are separate capabilities. The ordinary DC charging supply does not provide all three.
- An optional physical fault-injection fixture needs its own energy/protection review. Do not purchase or build it solely from simulated current peaks.
- Cabinet dimensions, fixture load ratings, insulation distances, cooling and adapter pinouts must be finalized from actual OEM drawings. No exact connector or power-component ordering number is invented here.

Excluded: destructive qualification samples, OEM licenses/data procurement, production certification, facility upgrades, recurring calibration/maintenance, spare modules, taxes/delivery and locomotive installation work. The provided software has no recurring runtime-package requirement; deployment support and long-term maintenance remain project costs.

## Official price sources

1. [B&K Precision 9185B](https://www.bkprecision.com/products/power-supplies/9185B): $1,797; dual-range specifications.
2. [SIGLENT SDS3000X HD series](https://siglentna.com/digital-oscilloscopes/sds3000x-hd-digital-storage-oscilloscope/): SDS3034X HD $4,244, 350 MHz, four channels, up to 4 GSa/s.
3. [SIGLENT DPB5150A](https://siglentna.com/product/dpb5150a-differential-high-voltage-probe/): $1,392, 100 MHz, 1500 V maximum differential input; application suitability still requires detailed review.

Checked 2026-10-17. The manufacturer pages can change; request regional quotes before procurement. Model-specific safety/rating decisions must use the current manuals, not the price table.
