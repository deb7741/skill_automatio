# 04 · Ocean scripting

**Ocean** (Open Command Environment for Analysis) is the SKILL-based scripting layer behind ADE. Anything you do in ADE L/Explorer (choose simulator, set analyses and variables, run, measure, plot) has an Ocean function. Ocean is SKILL, so all of chapter 05 applies.

## 1. Three ways to run Ocean

```bash
# 1. Stand-alone, non-graphical (best for batch / CI)
ocean -nograph -restore my_script.ocn | tee ocean.log

# 2. Pipe the script in
ocean -nograph < my_script.ocn > ocean.log 2>&1

# 3. From an interactive Virtuoso CIW (plots will open in ViVA)
> load("my_script.ocn")
```

End batch scripts with `exit()` so the process terminates.

> **Get a free starting script:** in ADE Explorer/L choose **Session → Save Ocean Script** (or **File → Save Ocean Script**). You get a complete script for the current setup that you can then parameterize.

## 2. Anatomy of a script

```lisp
;; ---------- user settings ----------
simDir   = "./sim/rc_ocean"
netlist  = "./netlist/rc_circuit.scs" ; circuit only, or use design(lib cell view)

;; ---------- setup ----------
simulator('spectre)
design(netlist)                        ; or: design("myLib" "myTb" "schematic")
resultsDir(simDir)
; modelFile('("/path/to/models.scs" "tt"))   ; your PDK, kept out of this repo

analysis('tran ?stop "40u" ?errpreset "moderate")
analysis('ac   ?start "1" ?stop "100M" ?dec "20")
desVar("rval" 1k)
desVar("cval" 1n)
temp(27)
option('reltol "1e-4")
save('v "/out" "/in")                 ; net names: "/out" for schematics, "out" for netlist files

;; ---------- run ----------
run()

;; ---------- measure ----------
selectResult('ac)
bw = bandwidth(v("/out") 3 "low")
selectResult('tran)
tr = riseTime(v("/out") 0 nil 1.0 nil 10 90)
printf("BW = %g Hz, tr = %g s\n" bw tr)

exit()
```

Runnable version: [`examples/ocean/01_basic_tran_ac.ocn`](../examples/ocean/01_basic_tran_ac.ocn).

### `design()` options

| Call | Use when |
|---|---|
| `design("myLib" "myTb" "schematic")` | Ocean netlists the schematic for you (needs `cds.lib`) |
| `design("/path/to/netlist/rc_circuit.scs")` | Netlist already exists (from ADE's `netlist` file or a generator) |

When you design from a netlist file:

- The file must contain **only the circuit**: no analyses, no `parameters` for variables you set with `desVar` (Ocean writes those itself), otherwise you get duplicates.
- Signal names are the netlist names: `v("out")`, not `v("/out")`. Schematic designs use hierarchical names (`/out`, `/I0/net3`).

When designing from a schematic, `createNetlist(?recreateAll t)` forces a fresh netlist.

## 3. Key functions

### Setup
| Function | Example |
|---|---|
| `simulator` | `simulator('spectre)` |
| `design` | `design("lib" "cell" "schematic")` |
| `resultsDir` | `resultsDir("./sim/run1")` |
| `modelFile` | `modelFile('("models.scs" "tt") '("other.scs" ""))` |
| `analysis` | `analysis('dc ?saveOppoint t)` |
| `desVar` | `desVar("vdd" 1.2)` |
| `temp` | `temp(85)` |
| `option` | `option('gmin "1e-12")` |
| `envOption` | `envOption('analysisOrder list("dc" "tran"))` |
| `save` / `saveOption` | `save('i "/V1/PLUS")`, `saveOption('save "allpub")` |
| `converge` / `ic` / `nodeset` | `ic("/out" 0)` |

### Running
| Function | Notes |
|---|---|
| `run()` | Single run |
| `paramAnalysis(...)` + `paramRun()` | Parametric sweep (ADE L-style) |
| `openResults(dir)` | Open existing results without re-simulating |
| `selectResult('tran)` | Choose which analysis subsequent `v()`/`i()` read |
| `results()` | List available result types |

### Accessing data
| Function | Returns |
|---|---|
| `v("/net")`, `i("/V1/PLUS")` | Waveform object |
| `VT("/net")`, `IT(...)` | Transient shortcuts used in ADE expressions |
| `VF`, `VDC`, `VS` | AC, DC, sweep results |
| `getData("/net" ?result 'tran)` | Generic accessor |
| `drGetWaveformXVec` / `drGetWaveformYVec` | Underlying vectors (for loops) |

### Measurement (calculator) functions
| Function | Example |
|---|---|
| `value(w x)` | Value at x |
| `ymax`, `ymin`, `average`, `rms`, `peakToPeak` | Scalars |
| `cross(w th n 'rising)` | Time of n-th crossing |
| `delay(?wf1 a ?value1 0.5 ?edge1 'rising ?wf2 b ?value2 0.5 ?edge2 'rising)` | Delay between edges |
| `riseTime(w v0 nil v1 nil 10 90)`, `fallTime(...)` | Edge times |
| `bandwidth(w 3 "low")` | -3 dB bandwidth |
| `dB20`, `phase`, `mag`, `real`, `imag` | Complex math |
| `phaseMargin(loopGain)`, `gainMargin(loopGain)` | Stability (`stb` analysis) |
| `frequency(w)`, `dutyCycle(w)` | Periodic signals |
| `clip(w from to)` | Restrict range |
| `deriv`, `integ` | Calculus |
| `settlingTime(...)`, `overshoot(...)` | Step response |

Use `ocnHelp('functionName)` at the Ocean prompt for argument details.

## 4. Parametric sweeps

```lisp
desVar("rval" 1k)
paramAnalysis("rval" ?values '(500 1k 2k 5k)
    paramAnalysis("temp" ?values '(-40 27 125)))
paramRun()

selectResult('ac)
bwFamily = bandwidth(v("/out") 3 "low")     ; a "family": one value per sweep point
ocnPrint(?output "bw.txt" bwFamily)
```

- Values can also be `?start ?stop ?step` or `?lin`/`?log` point counts.
- `?sweepType 'paramset` lets you give rows of parameters together.
- In some setups nested `paramRun()` behaves better in batch control mode: add
  `envSetVal("spectre.envOpts" "controlMode" 'string "batch")` **before** `simulator('spectre)`.

`paramAnalysis` is an ADE L-style feature. For Assembler-style sweeps + corners, build them in Assembler and use the `mae*` API (chapter 07) or the exported Ocean XL script.

## 5. Loops for PVT corners (plain SKILL)

When you need full control (custom file names, early exit, adaptive sweeps), loop yourself:

```lisp
results = nil
foreach(vdd '(0.9 1.0 1.1)
  foreach(tc '(-40 27 125)
    desVar("vdd" vdd)
    temp(tc)
    resultsDir(sprintf(nil "./sim/pvt_v%g_t%g" vdd tc))
    run()
    selectResult('ac)
    bw = bandwidth(v("/out") 3 "low")
    results = cons(list(vdd tc bw) results)))

out = outfile("pvt.csv" "w")
fprintf(out "vdd,temp,bw\n")
foreach(r reverse(results) fprintf(out "%g,%g,%g\n" car(r) cadr(r) caddr(r)))
close(out)
```

Runnable: [`examples/ocean/03_pvt_loop_csv.ocn`](../examples/ocean/03_pvt_loop_csv.ocn).

To switch model corners, change `modelFile(list("models.scs" sectionName))` inside the loop. Section names come from your PDK.

## 6. Exporting data

```lisp
; Formatted table of waveforms
ocnPrint(?output "out.txt" ?numberNotation 'scientific ?from 0 ?to 40u ?step 100n v("/in") v("/out"))

; Scalars to CSV, manually
fp = outfile("meas.csv" "a")
fprintf(fp "%s,%g\n" "bw" bw)
close(fp)

; Waveform vectors element by element
w  = v("/out" ?result 'tran)
xv = drGetWaveformXVec(w)  yv = drGetWaveformYVec(w)
for(k 0 drVectorLength(xv)-1
  printf("%g %g\n" drGetElem(xv k) drGetElem(yv k)))
```

For heavy post-processing, write PSF directly and read it in Python ([11](11-python-integration.md)).

## 7. Ocean and ADE Assembler (Ocean XL)

Assembler can export an **Ocean XL** script (**File → Save Ocean Script** inside Assembler). It uses `ocnxl*` functions (`ocnxlTargetCellView`, `ocnxlBeginTest`, `ocnxlSweepVar`, `ocnxlCorner`, `ocnxlRun`, ...). It reproduces tests, sweeps and corners in batch. For newer releases the `mae*` API is usually cleaner. See [07](07-ade-assembler-automation.md).

## 8. Gotchas

- **Paths**: relative paths resolve from where `ocean` was started, not from the script location.
- **`v()` returns `nil`** when the net wasn't saved or the wrong `selectResult` is active. Check `outputs()` and `results()`.
- **Families vs scalars**: after `paramRun()`, measurement functions return families. `ocnPrint` handles them; `printf("%g")` doesn't.
- **Numbers in `desVar`**: you can pass `1k` (SKILL scaled number) or `"1k"` (string). Be consistent.
- **Plots**: `plot()` does nothing useful under `-nograph`. Write data to files instead.

Next: [05 · SKILL fundamentals](05-skill-fundamentals.md)
