# 14 · Troubleshooting

Symptom → likely cause → fix. Start with the log file: Cadence logs are verbose, but the first error is usually the real one.

## Environment & startup

| Symptom | Likely cause | Fix |
|---|---|---|
| `command not found: virtuoso/spectre/xrun` | `PATH` not set | Source the setup script; check `which` |
| Wrong version runs | Several releases on `PATH` | Order `PATH` explicitly; print `-W`/`-version` at job start |
| License checkout failed / queued forever | No free license, wrong server | `lmstat -a -c $CDS_LIC_FILE`; `+lqtimeout`/`-licqueue`; reduce parallel jobs |
| `Library "xyz" is not defined` | `cds.lib` not found or missing `DEFINE` | Start from the project dir; `ddGetLibList()~>name`; check `INCLUDE` paths |
| `.cdsinit` errors at startup | Bad SKILL in init file | Start with `virtuoso -nocdsinit`, then `load` pieces until it breaks |
| Batch Virtuoso tries to open a display | GUI call in script, or no `-nograph` | Use `-nograph`; remove `hi*`/`ge*` window calls from batch code |
| Cellview locked (`.cdslck`) | Crashed session left edit lock | Use `clsAdminTool` to list/remove stale locks (see `clsAdminTool -h`) rather than deleting lock files manually |

## SKILL

| Symptom | Cause | Fix |
|---|---|---|
| `*Error* eval: undefined function - foo` | Not loaded, or typo, or space before `(` | `load` the file; check `isCallable('foo)`; no space between name and `(` |
| `*Error* eval: unbound variable - x` | Used before assignment / scope issue | Declare in `let`; initialize |
| Function works in CIW but not in batch | Depends on GUI state (current window, `geGetEditCellView()`) | Pass lib/cell/view explicitly; open cellviews with `dbOpenCellViewByType` |
| Variables mysteriously change | Global variable collision | Use `let`, prefix globals; run SKILL Lint |
| `dbSave` fails | Cellview opened `"r"`, or no write permission | Open with `"a"`/`"w"`; check file permissions/DM checkout |
| Netlister says schematic needs check & save | Edited from SKILL without `schCheck` | `schCheck(cv)` then `dbSave(cv)` |

## Netlisting

| Symptom | Cause | Fix |
|---|---|---|
| `Cannot find switch master` / no netlistable view | View not in `simViewList` / switch list | Add view to switch list (`spectre`, `schematic`, `veriloga`, ...) |
| Hierarchy stops too early/late | Stop list wrong | Adjust `simStopList` / config view |
| Instance parameters missing | Set via `dbReplaceProp` instead of CDF; callbacks not run | Use CDF API; trigger callbacks per your PDK's method |
| Different netlist in batch vs GUI | Different `.cdsenv`/`si.env`/`CDS_Netlisting_Mode` | Copy `si.env` from the ADE run dir; set the same env vars |

## Spectre convergence & results

| Symptom | Cause | Fix |
|---|---|---|
| `No convergence achieved` at DC | Floating nodes, bad initial point, ideal switches | Check for floating nodes; add `nodeset`/`ic`; `+diagnose`; `gmin` stepping options; homotopy settings (see `spectre -h options`) |
| `Time step too small` in transient | Discontinuities, missing `transition()` in Verilog-A | Fix models; `maxstep`; `errpreset=conservative` for diagnosis |
| Singular matrix | Floating node, loop of voltage sources, capacitor-only node | Find the node in log; add a large resistor to ground (diagnostic only) |
| Results look wrong by 10⁶–10⁹ | `M` vs `MEG` (SPICE vs Spectre syntax) | Check `simulator lang=`; use `meg` in SPICE files |
| Results differ APS vs Spectre X vs baseline | Accuracy preset too loose | Compare with `+preset=cx`/baseline; tighten preset |
| Verilog-A compile error | Syntax, missing include | Read the `ahdlcmi` messages in the log; `` `include "disciplines.vams" `` |
| Verilog-A changes ignored | Cached compiled model | Delete the `*.ahdlSimDB` / AHDL cache dir and rerun |

## Ocean

| Symptom | Cause | Fix |
|---|---|---|
| `v("/out")` returns `nil` | Not saved, wrong `selectResult`, wrong net name | `save('v "/out")`; `results()`; `outputs()`; check hierarchy separator `/` |
| `paramRun` produced nothing | Interactive control mode in batch | `envSetVal("spectre.envOpts" "controlMode" 'string "batch")` before `simulator()` |
| `printf` error on measurement | Value is a family (after sweeps) or `nil` | Use `ocnPrint`, or check `numberp(x)` first |

## ADE Assembler / maestro

| Symptom | Cause | Fix |
|---|---|---|
| `maeOpenSetup` fails | View locked or opened elsewhere | Open `?mode "r"` for read-only, or close the GUI session |
| Batch run uses different settings than GUI | Unsaved GUI changes | Save in GUI; `maeSaveSetup` after scripted edits you want to keep |
| Script exits before simulation ends | No wait | `maeWaitUntilDone('All)` or `?waitUntilDone t` |
| Exported CSV empty | Wrong history/view name | Pass `?historyName` returned by `maeRunSimulation` |

## Xcelium / xrun

| Symptom | Cause | Fix |
|---|---|---|
| `*E,CUVMUR` (unresolved module) | File missing from filelist or library | Add file/`-v`/`-y`; check spelling and `-top` |
| Timescale errors | Some modules lack `` `timescale `` | Add `-timescale 1ns/1ps` |
| Can't see signals in waves | No access visibility | `-access +r` (or `+rwc`), probe in Tcl |
| Stale behavior after edits | Reusing old snapshot | `-clean`, or don't use `-R` after source changes |
| Test "passed" but log has `UVM_ERROR` | Exit code 0 despite errors | Parse log (see `xrun_regression.py`) |

## AMS Designer

| Symptom | Cause | Fix |
|---|---|---|
| "Connect rules are not found" (ADE) | Built-in connect rules not compiled/available for this install | Ask CAD to compile the built-in rules for your AMS install, or switch to IE cards in an `amsd` block |
| Digital sees X at analog boundary | Wrong IE thresholds/supply | Check `-iereport`; fix `vsup`, `vthi/vtlo` |
| Analog sees wrong high level | L2E supply wrong | `ie vsup=...` per domain (scope with `cell=`/`inst=`) |
| `config cell=` binding not applied | Name mismatch between SV instance's module and subckt | Use exact subckt name; check portmap |
| Simulation ends early | Analog `tran stop` shorter than digital run | Increase `stop`, or control the end from the digital side |
| Very slow | Too many IEs, electrical where RNM would do | Convert pure-digital-interface blocks to RNM |

## Getting good help

When posting on the Cadence Community forums or opening a support case, include: tool versions (`-W` output), the exact command, the first error lines from the log, and a **minimal** testcase built only from generic components (like the examples in this repo). Never post PDK content publicly, and replace host names, user names, install paths and license servers in logs with placeholders (see [SECURITY.md](../SECURITY.md)).
