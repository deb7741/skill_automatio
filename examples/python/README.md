# Python helpers

Standard-library-only helpers (`vautil/`) plus CLI scripts. Everything here can be unit-tested **without Cadence tools**; the scripts call `spectre`, `xrun`, `ocean` or `virtuoso` only when you run them for real.

```bash
pip install -r requirements.txt      # optional extras; core needs nothing
pytest -q                            # 45 tests, runs anywhere
```

## Scripts

| Script | What it does |
|---|---|
| `read_psf.py` | List signals, export CSV, measure bandwidth/rise time from a PSF ASCII file |
| `spectre_sweep.py` | Render a netlist template over a parameter grid, run Spectre in parallel, measure, write `summary.csv` + JUnit |
| `parse_spectre_log.py` | PASS/FAIL summary of Spectre logs (errors, fatal messages, analysis times) |
| `xrun_regression.py` | Parallel xrun regression from a JSON test list; per-test `xcelium.d`; log-based verdicts; JUnit |
| `cadence_batch.py` | Run Ocean / SKILL / maestro jobs in batch and collect `OCEAN_RESULT` / `BATCH_STATUS` markers |
| `check_specs.py` | Compare a results CSV (wide or long/maestro format) against JSON specs → Markdown report + JUnit + exit code |
| `skillbridge_demo.py` | Read-only demo of driving a live Virtuoso session from Python |

## Library (`vautil/`)

| Module | Highlights |
|---|---|
| `psf_ascii` | `read_psf_ascii(path)` → `PsfData` (sweep, real/complex traces, DC-op scalars); `write_psf_ascii` for fixtures |
| `measure` | `bandwidth`, `cross`, `rise_time`, `value_at`, `average`, `rms`, `db20` (mirroring Ocean calculator functions) |
| `logparse` | `parse_spectre_log`, `parse_xrun_log` → structured verdicts |
| `junit` | `write_junit([TestResult, ...], path)` |
| `units` | `parse_si("2.5n")`, `format_si(159154.9)` |

## End-to-end example

```bash
# 1. Sweep R and C (needs Spectre)
python3 spectre_sweep.py templates/rc_lowpass.scs.tmpl \
    --param rval=500,1k,2k,5k --param cval=1n,2n \
    --measure bw:ac1.ac:out --measure tr:tran1.tran:out \
    --jobs 4 --out runs/rc --junit runs/rc/junit.xml

# 2. Check against specs (no tools needed)
python3 check_specs.py runs/rc/summary.csv tests/fixtures/specs.json --report runs/rc/report.md
```
