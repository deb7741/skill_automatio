# 06 · SKILL for design automation

This chapter covers the SKILL APIs that matter for simulation and verification work: reading libraries, opening cellviews, building testbench schematics, setting CDF parameters, netlisting and running Virtuoso without a GUI.

All examples use only Cadence-supplied generic libraries (`analogLib`, `basic`).

## 1. The object model in 60 seconds

```
Library (ddGetObj)  ──► Cell ──► View ──► (files)
                                   │
                    dbOpenCellViewByType()
                                   ▼
                            CellView (dbObject)
          ┌─────────────┬──────────┼───────────┬──────────────┐
       instances       nets     terminals    shapes        props
          │              │          │
      instTerms ◄──────► (connectivity)
```

- `dd*` functions = the **library/file layer** (libraries, cells, views as files)
- `db*` functions = the **design database** inside a cellview (OpenAccess)
- `sch*` = schematic-specific editing, `le*` = layout, `ge*`/`hi*` = GUI/windows
- Access attributes with `~>`: `cv~>instances`, `inst~>cellName`, `net~>instTerms`

## 2. Browsing libraries

```lisp
ddGetLibList()~>name                       ; all library names
lib = ddGetObj("myLib")
lib~>cells~>name                           ; cell names
cell = ddGetObj("myLib" "myCell")
cell~>views~>name                          ; ("schematic" "symbol" "maestro" ...)
ddGetObj("myLib" "myCell" "schematic")~>readPath   ; path on disk
```

Utility functions for this live in [`examples/skill/lib_utils.il`](../examples/skill/lib_utils.il): `vagListCells`, `vagCellsWithView`, `vagReportLibrary` (CSV).

## 3. Opening and saving cellviews

```lisp
cv = dbOpenCellViewByType("myLib" "myCell" "schematic" "schematic" "r")   ; read
cv = dbOpenCellViewByType("myLib" "newTb"  "schematic" "schematic" "w")   ; create/overwrite
cv = dbOpenCellViewByType("myLib" "myCell" "schematic" nil "a")           ; append/edit
; ... edit ...
schCheck(cv)          ; schematics: check & extract connectivity (sets the "extracted" state)
dbSave(cv)
dbClose(cv)
```

| Mode | Meaning |
|---|---|
| `"r"` | Read-only |
| `"a"` | Edit existing (lock) |
| `"w"` | Create new / overwrite |

Rules: always `dbClose` what you open, and always `schCheck` schematics before saving, otherwise netlisting complains the schematic needs to be checked and saved.

## 4. Walking a design

```lisp
cv = dbOpenCellViewByType("myLib" "myCell" "schematic" nil "r")
foreach(inst cv~>instances
  printf("%-10s %s/%s\n" inst~>name inst~>libName inst~>cellName))
foreach(net cv~>nets
  printf("%-10s %d connections\n" net~>name length(net~>instTerms)))
foreach(term cv~>terminals
  printf("pin %s  %s\n" term~>name term~>direction))
dbClose(cv)
```

Hierarchy traversal (recursive, de-duplicated) is in [`examples/skill/design_checks.il`](../examples/skill/design_checks.il) → `vagWalkHierarchy`.

## 5. Generating a testbench schematic

```lisp
cv   = dbOpenCellViewByType("myLib" "rc_tb" "schematic" "schematic" "w")
rMst = dbOpenCellViewByType("analogLib" "res" "symbol")
cMst = dbOpenCellViewByType("analogLib" "cap" "symbol")
r1   = schCreateInst(cv rMst "R1" 0:0 "R0")
c1   = schCreateInst(cv cMst "C1" 1:0 "R0")
```

Connecting instances by drawing wires at exact pin coordinates is fragile. A much more robust pattern is **stub wire + wire label at every terminal**: nets connect by name.

```lisp
procedure(vagTermPoint(inst termName)
  ;; absolute location of a terminal's pin on an instance
  let((term pinFig)
    term   = car(setof(x inst~>master~>terminals x~>name == termName))
    pinFig = car(term~>pins)~>fig
    dbTransformPoint(centerBox(pinFig~>bBox) inst~>transform)))
```

The complete, tested generator (RC low-pass testbench with `vsource`, `res`, `cap`, ground and labels, CDF values, `schCheck`, save) is [`examples/skill/create_testbench.il`](../examples/skill/create_testbench.il).

## 6. CDF parameters (instance properties ADE uses)

Instance parameters of `analogLib` (and PDK) cells are defined through **CDF**. Set them via CDF, not raw `dbReplaceProp`, so callbacks and netlisting see them correctly:

```lisp
procedure(vagSetCdfParam(inst name value)
  let((cdf param)
    cdf   = cdfGetInstCDF(inst)
    param = cdfFindParamByName(cdf name)
    if(param then param~>value = value t
           else warn("No CDF param %s on %s\n" name inst~>name) nil)))

vagSetCdfParam(r1 "r" "rval")        ; design variable, so ADE sweeps it
vagSetCdfParam(c1 "c" "1n")
```

List a cell's CDF parameters: `cdfGetBaseCellCDF(ddGetObj("analogLib" "vsource"))~>parameters~>name`.

> PDK devices often run **CDF callbacks** (to recompute dependent params). When you set values from SKILL, callbacks don't fire automatically. Look for your PDK's recommended way to trigger them; this guide stays generic.

## 7. Batch netlisting

### Option A: `si` (the batch netlister)

```bash
mkdir -p netlist_run && cd netlist_run
cp /path/to/templates/si.env.template si.env   # edit lib/cell/view
si -batch -command netlist -cdslib /path/to/project/cds.lib
# netlist written to ./netlist (+ input.scs controls if configured)
```

Easiest way to get a correct `si.env`: run once in ADE and copy `<projectDir>/<cell>/spectre/schematic/netlist/si.env`. Template: [`templates/si.env.template`](../templates/si.env.template).

### Option B: Ocean from SKILL/batch

```lisp
simulator('spectre)
design("myLib" "rc_tb" "schematic")
resultsDir("./sim/rc_tb")
createNetlist(?recreateAll t ?display nil)
```

### Option C: Through the maestro view
See chapter 07: `maeRunSimulation` netlists as part of the run.

## 8. Running Virtuoso without a GUI

```bash
virtuoso -nograph -restore my_script.il -log my_script.log
# options:
#   -nograph     no windows (also no X display needed)
#   -restore f   load SKILL file f after startup
#   -replay f    replay a CDS.log-style file
#   -nocdsinit   skip .cdsinit (faster, more reproducible — load what you need explicitly)
#   -log f       log file name
```

Your script must call `exit()` at the end. Wrap the body so that errors still exit with a status your CI can read:

```lisp
; batch_wrapper.il
let((ok)
  ok = errset(load("examples/skill/create_testbench.il") t)
  when(ok ok = errset(vagCreateRcTestbench("myLib" "rc_tb") t))
  printf("BATCH_STATUS: %s\n" if(ok && car(ok) "PASS" "FAIL"))
  exit(if(ok && car(ok) 0 1)))
```

Then grep the log for `BATCH_STATUS: PASS` (exit codes from `virtuoso` are not reliable across releases, so a marker line is safer).

## 9. Talking to the outside world

| Need | SKILL approach |
|---|---|
| Run a Python script and wait | `system("python3 post.py results.csv")` |
| Run and keep GUI responsive | `ipcBeginProcess(cmd "" 'dataCb 'errCb 'exitCb)` |
| Exchange data | Write CSV/JSON with `fprintf`; read back with `infile`/`gets` |
| Be controlled by Python | `skillbridge` (chapter 11) or an `ipc` socket server |

## 10. Useful small utilities (in `examples/skill/`)

| File | Functions |
|---|---|
| `lib_utils.il` | `vagListCells`, `vagCellsWithView`, `vagReportLibrary`, `vagFindInstancesOf` |
| `create_testbench.il` | `vagCreateRcTestbench`, `vagTermPoint`, `vagSetCdfParam` |
| `design_checks.il` | `vagWalkHierarchy`, `vagFindFloatingNets`, `vagCheckAllSchematics` |
| `maestro_batch.il` | `vagMaeRun` (open, set vars, run, wait, export CSV) |
| `ciw_helpers.il` | Bindkeys, quick "open last", log markers |
| `batch_wrapper.il` | Pattern for CI-safe batch Virtuoso runs |

Next: [07 · ADE Explorer/Assembler automation](07-ade-assembler-automation.md)
