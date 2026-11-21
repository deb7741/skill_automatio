# 02 · Tool landscape

## The big picture

```
                       ┌──────────────────────── Virtuoso (IC6.1.8 / IC23.1+) ───────────────────────┐
                       │  Schematic / Symbol / Config views      CIW (SKILL console)                 │
                       │  ADE Explorer (single test)  ADE Assembler (many tests, corners, MC)        │
                       │  ADE L / ADE XL (legacy)     ViVA (waveform viewer + calculator)            │
                       └──────┬───────────────────────────────┬───────────────────────────┬──────────┘
                              │ netlist (si / OSS)            │ AMS netlist (UNL)         │ SKILL / Ocean
                              ▼                               ▼                           ▼
                   ┌────────────────────┐        ┌───────────────────────┐      ┌──────────────────┐
                   │ Spectre            │        │ xrun                  │      │ ocean / virtuoso │
                   │  APS / X / FX      │◄───────┤  Xcelium (digital)    │      │  -nograph        │
                   │  Verilog-A         │ analog │  + Spectre (analog)   │      │  batch scripts   │
                   └────────┬───────────┘ solver │  = AMS Designer       │      └──────────────────┘
                            │ PSF / PSF-XL       └──────────┬────────────┘
                            ▼                               ▼ SHM / PSF / UDB
                     ViVA, Ocean, Python              SimVision, ViVA, Python
```

## Who does what

| Tool | What it is | Automate it with |
|---|---|---|
| **Spectre** | SPICE-class analog simulator, Cadence netlist syntax (`.scs`) plus SPICE compatibility | Shell/Python + netlists; Ocean |
| **Spectre APS** | Faster, multithreaded Spectre engine (same accuracy class) | `+aps`, `++aps` |
| **Spectre X** | Newer engine replacing APS for most uses, with presets `cx/ax/mx/lx/vx` | `+preset=mx` etc. |
| **Spectre FX** | FastSPICE engine (transient only), SPICE syntax by default | `spectrefx` or `+fx` |
| **Verilog-A** | Analog behavioral language compiled by Spectre (AHDL) | `ahdl_include` in netlist |
| **Ocean** | SKILL-based scripting interface to ADE's simulation and post-processing functions | `ocean -nograph`, or `load()` in CIW |
| **SKILL / SKILL++** | Virtuoso's Lisp-family scripting language; access to everything in Virtuoso | CIW, `.cdsinit`, `virtuoso -nograph` |
| **ADE Explorer** | Single-testbench simulation environment (replaces ADE L) | `mae*` SKILL functions |
| **ADE Assembler** | Multi-test, corners, sweeps, Monte Carlo, specs (replaces ADE XL) | `mae*` SKILL, Ocean XL (`ocnxl*`) |
| **ADE L / ADE XL** | Legacy environments. Still in IC6.1.8, removed in newer releases | `asi*`/`sev*`, `axl*` SKILL (legacy) |
| **Xcelium / `xrun`** | Digital simulator for Verilog, SystemVerilog, VHDL, UVM | `xrun` command line, Tcl |
| **Spectre AMS Designer** | Mixed-signal: Xcelium + Spectre in one run, launched with `xrun` | `xrun` + `amsd` control file; ADE with AMS simulator |
| **SimVision** | Waveform/debug GUI for Xcelium & AMS | Tcl |
| **ViVA** | Virtuoso Visualization & Analysis: waveforms, calculator | Ocean/SKILL calculator functions |
| **IMC** | Coverage analysis/merging for Xcelium | `imc -exec script.tcl` |
| **`si`** | Batch netlister ("simulation interface") | `si -batch -command netlist` + `si.env` |

## Choosing the right automation entry point

| You want to… | Best tool | Why |
|---|---|---|
| Run the same netlist with 1,000 parameter combinations | **Spectre CLI + Python** (or Spectre `sweep`) | No GUI/license overhead per run, trivially parallel |
| Re-run a testbench someone built in ADE, in batch | **ADE Assembler + `mae*` SKILL** | Keeps one source of truth (the maestro view) |
| Quick one-off measurement loops with ADE-style functions | **Ocean** | Calculator functions like `bandwidth`, `cross`, `phaseMargin` |
| Generate or check hundreds of schematics/cells | **SKILL** | Only SKILL has full database access |
| Drive Virtuoso from Python | **skillbridge** or files + `virtuoso -nograph` | Python ecosystem for data and reporting |
| Verify digital logic around analog | **`xrun` + RNM** | 10×–1000× faster than electrical AMS |
| Check analog/digital interfaces at electrical level | **AMS Designer** | Real connect modules, real loading |
| Nightly regression with pass/fail dashboard | **Python orchestrator** calling Spectre/xrun/virtuoso | JUnit XML → Jenkins/GitLab |

## A rule of thumb

1. **Model in the GUI, automate the boring parts.** Build the first testbench interactively. Then script the repetition.
2. **Keep one source of truth.** Either the maestro view *or* a netlist generator, never two hand-maintained copies.
3. **Netlist once, simulate many.** Netlisting needs Virtuoso; simulation doesn't. Separate the two steps in regressions.
4. **Post-process outside the simulator** when the analysis is complex. Python + NumPy is easier to test than calculator expressions.

Next: [03 · Spectre from the command line](03-spectre-command-line.md)
