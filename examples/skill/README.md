# SKILL examples

| File | Functions | Writes to libraries? |
|---|---|---|
| `lib_utils.il` | `vagListCells`, `vagCellsWithView`, `vagReportLibrary`, `vagFindInstancesOf`, `vagPrintLibSummary` | No |
| `create_testbench.il` | `vagCreateRcTestbench`, `vagTermPoint`, `vagSetCdfParam`, `vagStubLabel` | **Yes** (creates one cell) |
| `design_checks.il` | `vagWalkHierarchy`, `vagFindFloatingNets`, `vagCheckAllSchematics` | Only with `?save t` |
| `maestro_batch.il` | `vagMaeRun`, `vagMaeRunFromEnv` | Only with `?save t` |
| `run_maestro.il` | Batch entry point (env-var driven) | Results only |
| `batch_wrapper.il` | CI-safe `-nograph` pattern with `BATCH_STATUS` marker | Depends on task |
| `ciw_helpers.il` | `vagPrintSelected` (bindkey), `vagOpen`, `vagReloadSkill`, `vagLogMarker` | No |

## Interactive use

```lisp
; in the CIW, from the directory containing cds.lib
load("/path/to/repo/examples/skill/lib_utils.il")
vagPrintLibSummary("analogLib")
vagListCells("analogLib")
```

Create a scratch library first (Library Manager → File → New → Library, "Don't need process information"), then:

```lisp
load("/path/to/repo/examples/skill/create_testbench.il")
vagCreateRcTestbench("scratchLib" "rc_tb")
```

## Batch use

```bash
export VAG_SKILL_DIR=$PWD/examples/skill
export VAG_LIB=scratchLib
virtuoso -nograph -restore $VAG_SKILL_DIR/batch_wrapper.il -log batch.log
grep BATCH_STATUS batch.log
```

## Safety

- Scripts that write (`create_testbench.il`, `?save t` options) overwrite cellviews of the same name. Use a scratch library.
- All functions use the `vag` prefix to avoid clashing with your site's SKILL.
