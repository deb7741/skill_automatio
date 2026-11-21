# 03 · Spectre from the command line

Running Spectre directly is the fastest, most scriptable way to simulate. ADE itself just writes a netlist (`input.scs`) and calls `spectre` with options, so anything ADE does, you can do in a shell.

## 1. Minimal netlist

```spectre
// rc_lowpass.scs  — Spectre native syntax
simulator lang=spectre
global 0

parameters rval=1k cval=1n vdd=1.0

V1  (in 0)   vsource type=pulse val0=0 val1=vdd period=20u width=10u rise=1n fall=1n mag=1
R1  (in out) resistor r=rval
C1  (out 0)  capacitor c=cval

simOpts options reltol=1e-4 vabstol=1e-6 iabstol=1e-12 temp=27 save=selected
save in out

tran1 tran stop=40u errpreset=moderate
ac1   ac   start=1 stop=100M dec=20
```

Run it:

```bash
spectre rc_lowpass.scs +escchars =log spectre.log -format psfxl -raw ./psf
```

Full runnable version: [`examples/spectre/01_rc_lowpass`](../examples/spectre/01_rc_lowpass).

### Syntax reminders

| Topic | Spectre syntax |
|---|---|
| Language switch | `simulator lang=spectre` / `simulator lang=spice` (can switch mid-file) |
| Instance | `name (node1 node2 ...) master param=value ...` |
| Ground | `0` (or `gnd!` if declared `global 0 gnd!`) |
| Comments | `//` or `*` at line start (spectre mode) |
| Continuation | `\` at end of line |
| Include | `include "file.scs"` / `include "models.scs" section=tt` |
| Verilog-A | `ahdl_include "opamp.va"` |
| Subcircuit | `subckt name (ports) ... ends name` |
| Parameters | `parameters a=1 b=a*2` (expressions allowed) |
| Scale suffixes | `T G M K k _ m u n p f a` (`M` = mega in Spectre mode, milli in SPICE mode!) |

> **Watch out:** in `lang=spice`, `M`/`m` means milli; use `MEG` for mega. In `lang=spectre`, `M` = mega and `m` = milli. Mixing files from both worlds is a classic source of 10⁹ errors.

## 2. Command-line options you'll actually use

| Option | Meaning |
|---|---|
| `=log file` | Write log to `file` only (quiet console) |
| `+log file` | Write log to `file` *and* console |
| `-raw dir` | Results directory (default `<netlist>.raw`) |
| `-format psfxl\|psfbin\|psfascii\|nutascii\|sst2` | Output format (see [13](13-results-waveforms.md)) |
| `+escchars` | Treat escaped characters in node names correctly (ADE always sets this) |
| `-I dir` | Include search path |
| `+aps` / `++aps` | Spectre APS / APS with more aggressive settings |
| `+preset=cx\|ax\|mx\|lx\|vx` | Spectre X accuracy/performance presets (`cx` most accurate, `vx` fastest) |
| `+mt=N` | Multithreading with N threads |
| `+lqtimeout N` | Wait at most N seconds for a license (0 = wait forever) |
| `+diagnose` | Extra convergence diagnostics in the log |
| `-param name=value` | Override a top-level parameter without editing the netlist (check `spectre -h` on your version) |
| `+checklimitdest=psf` | Write device-check violations to PSF |
| `-h [topic]` | Built-in help, e.g. `spectre -h tran`, `spectre -h vsource`, `spectre -h options` |

> `spectre -h <component>` is the fastest documentation you have. It works offline and always matches your installed version.

## 3. Analyses

```spectre
dcop   dc  oppoint=rawfile                          // operating point
dcsw   dc  param=vdd start=0 stop=1.2 step=10m      // DC sweep of a parameter
tran1  tran stop=1u maxstep=1n errpreset=conservative
ac1    ac  start=1 stop=10G dec=20
noise1 noise start=1 stop=1G dec=10 oprobe=V0 iprobe=V1   // or oprobe=out-node pair
stb1   stb start=1 stop=10G dec=20 probe=IPRB0       // loop stability (needs iprobe instance)
xf1    xf  start=1 stop=1G dec=10 probe=V0
pss1   pss fund=1G harms=10 errpreset=moderate       // RF: periodic steady state
info1  info what=oppoint where=rawfile              // dump operating points
```

## 4. Sweeps and alters (inside one Spectre run)

```spectre
// Sweep a parameter over a list, run tran and ac for each value
swp1 sweep param=rval values=[500 1k 2k 5k] {
    t1 tran stop=40u
    a1 ac   start=1 stop=100M dec=20
}

// Temperature sweep
swpT sweep param=temp values=[-40 27 125] {
    a2 ac start=1 stop=100M dec=20
}

// Change something between analyses
alt1 alter param=vdd value=1.2
tran2 tran stop=40u
```

`paramset` lets you sweep several parameters together, row by row (a table of "corners"):

```spectre
corners paramset {
    vdd   temp
    0.9   -40
    1.0    27
    1.1   125
}
swpC sweep paramset=corners { t1 tran stop=40u }
```

## 5. Monte Carlo (generic, PDK-free)

Real Monte Carlo uses the statistics block shipped in your PDK. To learn the mechanics without one, define your own `statistics` block on ordinary parameters:

```spectre
parameters rval=1k cval=1n
statistics {
    process {
        vary rval dist=gauss std=5 percent=yes
        vary cval dist=gauss std=10 percent=yes
    }
}
mc1 montecarlo numruns=200 seed=1234 variations=process savefamilyplots=yes {
    a1 ac start=1 stop=100M dec=20
}
```

See [`examples/spectre/02_sweeps_montecarlo`](../examples/spectre/02_sweeps_montecarlo). Post-process the per-run results with Python ([11](11-python-integration.md)).

## 6. Choosing an engine

| Situation | Suggestion |
|---|---|
| Small analog block, need reference accuracy | Spectre baseline, or Spectre X `+preset=cx` |
| Medium/large analog, transient-heavy | Spectre X `+preset=ax` or `mx` with `+mt=N` |
| Post-layout with many parasitics | Spectre X (add `+postlpreset=...` if needed) |
| Huge mixed blocks, functional checks | Spectre FX (`spectrefx`, FastSPICE) |
| Thousands of tiny runs | Plain Spectre, many parallel jobs, `+mt=1` |

Presets trade accuracy for speed. **Always compare against a reference run** on a representative testbench before switching engines in a regression.

## 7. Batch-friendly habits

- Put **all knobs in `parameters`**. Python then only has to change one line (or use `-param` / an `alter`).
- Use `save` statements: saving everything (`save=allpub`) on large circuits bloats results and slows runs.
- Give every run its **own `-raw` directory**. Parallel runs must never share one.
- Check the **exit code** *and* grep the log (`spectre` returns non-zero on fatal errors, but convergence warnings may still mean garbage results). See [`examples/python/parse_spectre_log.py`](../examples/python/parse_spectre_log.py).
- Keep `+lqtimeout` set in CI so jobs don't hang forever waiting for licenses.

## 8. Reusing an ADE netlist

After running once in ADE Explorer, the run directory contains everything needed:

```text
<projectDir>/<cell>/spectre/schematic/netlist/
    input.scs       # top netlist (includes netlist + controls)
    netlist         # circuit
    runSimulation   # exact spectre command ADE used, very useful!
    si.env          # netlister settings (see chapter 06)
```

Copy `runSimulation` into your scripts as the reference command line.

Next: [04 · Ocean scripting](04-ocean-scripting.md)
