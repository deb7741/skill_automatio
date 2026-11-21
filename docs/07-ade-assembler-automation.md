# 07 · ADE Explorer / Assembler automation

ADE Explorer and ADE Assembler store their setup in a **`maestro` cellview**. The `mae*` SKILL API lets you open that view, change variables, enable tests/corners, run, wait and export results, all without touching the GUI. It is the recommended way to automate ADE in IC6.1.8 and later. ADE L/XL are legacy, and newer releases support only Explorer/Assembler.

## 1. Why automate through maestro?

- **One source of truth**: designers keep editing the testbench in the GUI; your script just runs it.
- Corners, Monte Carlo, sweeps, specs and job distribution are already configured.
- Results land in the normal history, so anyone can open them in the GUI afterwards.

## 2. The core sequence

```lisp
sess = maeOpenSetup("myLib" "myTb" "maestro" ?mode "a")   ; "a" = editable, "r" = read-only
maeSetVar("rval" "2k" ?session sess)                       ; global design variable
maeSetSetup(?tests '("myLib:myTb:1") ?enabled t ?session sess)
hist = maeRunSimulation(?session sess)                     ; returns history name, e.g. "Interactive.3"
maeWaitUntilDone('All)                                     ; block until runs finish
maeExportOutputView(?session sess ?fileName "./results.csv" ?view "Detail" ?historyName hist)
maeSaveSetup(?session sess)                                ; only if you want to keep changes
maeCloseSession(?session sess ?forceClose t)
```

Notes:

- The test-selection keyword is `?tests` in recent references (some older examples show `?test`). Default test names look like `"myLib:myTb:1"`.
- `maeRunSimulation` also accepts `?waitUntilDone t` as an alternative to `maeWaitUntilDone`.
- `?runMode` selects the run mode, e.g. `"Single Run, Sweeps and Corners"` or `"Monte Carlo Sampling"`. Mode names must match the GUI wording of your release.
- `?callback "fnName"` registers a function called with `(session historyName)` after each run.
- `maeExportOutputView` views include `"Detail"`, `"Summary"`, `"Yield"`, `"Checks/Asserts"` (names depend on release).
- Use the SKILL API Finder (search `mae`) to see every function your release offers.

A complete, parameterized script: [`examples/skill/maestro_batch.il`](../examples/skill/maestro_batch.il).

## 3. Running it in batch

```bash
virtuoso -nograph -restore run_maestro.il -log run_maestro.log
```

`run_maestro.il`:

```lisp
load("/path/to/examples/skill/maestro_batch.il")
vagMaeRun(?lib "myLib" ?cell "myTb"
          ?vars '(("rval" "2k") ("cval" "1n"))
          ?csv  "./results/myTb.csv")
exit()
```

Then post-process the CSV in Python: [`examples/python/check_specs.py`](../examples/python/check_specs.py) turns it into a pass/fail report against a JSON spec file.

## 4. Commonly used `mae*` functions (by task)

| Task | Functions |
|---|---|
| Sessions | `maeOpenSetup`, `maeCloseSession`, `maeSaveSetup` |
| Variables | `maeSetVar`, `maeGetVar` |
| Tests | `maeGetSetup`, `maeSetSetup`, `maeGetEnabledAnalysis`, `maeSetAnalysis` |
| Corners | `maeSetSetup(?corners ...)`, `maeSetCorner`; import/export helpers vary by release (search "Corner" in the API Finder) |
| Running | `maeRunSimulation`, `maeWaitUntilDone`, `maeStopSimulation` |
| Results | `maeExportOutputView`, `maeGetOutputValue`, `maeOpenResults`, `maeCloseResults` |
| Outputs/specs | `maeAddOutput`, `maeSetSpec` |
| Scripts | `maeWriteScript` (write a replayable SKILL script of the current setup) |

Availability and exact keyword arguments vary by ISR. Treat this table as a map, not a contract.

> **Tip:** `maeWriteScript("setup.il")` dumps the current maestro setup as `mae*` calls. It's the Assembler equivalent of "Save Ocean Script", and a great way to learn the API.

## 5. Corners as data

Keep corners in a CSV under version control and load them into maestro, instead of hand-editing in the GUI:

1. Build corners once in the GUI.
2. Export: Assembler **Corners** pane → export to CSV.
3. Commit the CSV. In batch, load it before running.

Corner *contents* (model sections) come from your PDK and belong in your private repo. Here they only appear as placeholders.

## 6. Legacy: ADE L / ADE XL / Ocean XL

| Legacy | Modern equivalent |
|---|---|
| ADE L `asi*` / `sev*` functions | ADE Explorer + `mae*` |
| ADE XL `axl*` functions | ADE Assembler + `mae*` (many `axl*` still work) |
| `ocnxl*` (Ocean XL) scripts | Still supported for batch; generate with "Save Ocean Script" in Assembler |
| `.adexl` views | Converted to `maestro` views when opened in Assembler |

If you inherit ADE XL scripts, migrate gradually: open the view in Assembler (converted copy), then replace `axl*` calls with `mae*` equivalents one by one.

## 7. Job distribution and licenses

- Assembler's **Job Setup** (local, LSF, SGE, ...) controls parallelism. Batch runs use the same job policy as the GUI.
- `maeRunSimulation` returns immediately. Parallel jobs are managed by Assembler, so don't fork your own.
- Make sure batch hosts can see the same `cds.lib`, model paths and job queue as the GUI.

## 8. Patterns that work well

**Nightly regression of every testbench in a library**

```lisp
foreach(cell vagCellsWithView("myLib" "maestro")
  vagMaeRun(?lib "myLib" ?cell cell ?csv sprintf(nil "./nightly/%s.csv" cell)))
```

**Parameter scan from Python** (each point = a batch Virtuoso call)

```python
for rval in ["1k", "2k", "5k"]:
    run_virtuoso_batch(script="run_maestro.il", env={"RVAL": rval})
```

In SKILL read it with `getShellEnvVar("RVAL")`. For big scans, prefer Assembler's own sweep feature (one run, many points).

Next: [08 · Xcelium and `xrun`](08-xcelium-xrun.md)
