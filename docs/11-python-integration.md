# 11 · Python integration

Python is the best glue language for simulation flows: parallel job control, data analysis (NumPy/pandas), plotting, reports, CI integration. Cadence tools don't need to "support Python" for this to work. You connect them in one of four ways.

```
 ┌─────────────────────────┐   1. subprocess: spectre / xrun / ocean / virtuoso -nograph
 │        Python           │──────────────────────────────────────────────────────────►  tools
 │  (orchestration, data,  │   2. files: netlists & .il/.ocn in, PSF/CSV/logs out
 │   reports, CI)          │◄──────────────────────────────────────────────────────────  results
 │                         │   3. skillbridge: live RPC into a running Virtuoso
 └─────────────────────────┘◄─────────────────────────────────────────────────────────►  Virtuoso
                               4. Virtuoso calls Python: system() / ipcBeginProcess()
```

## 1. Driving batch tools with `subprocess`

```python
import subprocess, pathlib

def run_spectre(netlist: pathlib.Path, rawdir: pathlib.Path, extra=()):
    cmd = ["spectre", str(netlist), "+escchars", "-format", "psfascii",
           "-raw", str(rawdir), "=log", str(rawdir.with_suffix(".log")), *extra]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode
```

The full, parallel version ([`examples/python/spectre_sweep.py`](../examples/python/spectre_sweep.py)) does this:

1. Renders a netlist template with parameter values (`string.Template`, no extra deps)
2. Runs N simulations in parallel (`concurrent.futures`), each in its own directory
3. Parses each log for errors ([`parse_spectre_log.py`](../examples/python/parse_spectre_log.py))
4. Reads results ([`vautil/psf_ascii.py`](../examples/python/vautil/psf_ascii.py)), measures bandwidth and writes a CSV summary

The same pattern drives:

| Tool | Command | Example |
|---|---|---|
| Ocean | `ocean -nograph -restore script.ocn` | [`cadence_batch.py ocean`](../examples/python/cadence_batch.py) |
| Virtuoso SKILL / maestro | `virtuoso -nograph -restore script.il -log x.log` | [`cadence_batch.py skill`/`maestro`](../examples/python/cadence_batch.py) |
| Xcelium | `xrun -f files.f ...` | [`xrun_regression.py`](../examples/python/xrun_regression.py) |

**Passing parameters into SKILL/Ocean:** generate the script from a template, or set environment variables and read them with `getShellEnvVar("NAME")`.

## 2. Reading simulation results

| Format | How to read it in Python |
|---|---|
| **PSF ASCII** (`-format psfascii`) | [`psf_utils`](https://pypi.org/project/psf-utils/) (`pip install psf_utils`), or this repo's dependency-free `vautil.psf_ascii` |
| **PSF binary** (default from ADE) | `libpsf` Python bindings, or convert with Cadence's `psf` tool: `psf -i tran.tran -o tran.psfascii` |
| **PSF-XL** | Convert via Ocean (`ocnPrint`) or ViVA export to CSV; or simulate with `-format psfascii` for scripted flows |
| **nutascii** (`-format nutascii`) | Simple text format (SPICE raw). Many open-source readers exist |
| **CSV from ADE/maestro** | `csv` / `pandas.read_csv` |

Example with `psf_utils`:

```python
from psf_utils import PSF
psf = PSF("psf/ac1.ac")
f   = psf.get_sweep().abscissa
out = psf.get_signal("out").ordinate          # complex NumPy array for AC
```

Example with this repo's reader (no dependencies besides the standard library):

```python
from vautil.psf_ascii import read_psf_ascii
data = read_psf_ascii("psf/tran1.tran")
t, vout = data.sweep_values, data.traces["out"]
```

CLI: [`read_psf.py`](../examples/python/read_psf.py) lists signals and exports any PSF ASCII file to CSV.

## 3. skillbridge: Python ↔ live Virtuoso

[skillbridge](https://github.com/unihd-cag/skillbridge) is an open-source package that runs SKILL functions from Python and converts objects both ways.

```bash
pip install skillbridge
skillbridge path          # prints the path of the SKILL server file
```

In the Virtuoso CIW:

```lisp
load("<path printed above>")
pyStartServer
```

In Python:

```python
from skillbridge import Workspace
ws = Workspace.open()
cv = ws.ge.get_edit_cell_view()          # SKILL geGetEditCellView()
print(cv.cell_name, len(cv.instances))
ws["plus"](3, 4)                         # call any SKILL function by name
```

- Python names are snake_case versions of SKILL names (`dbOpenCellViewByType` → `ws.db.open_cell_view_by_type`).
- Optional: `skillbridge generate` creates stub files for IDE auto-completion.
- Check the project README for supported Python/Virtuoso versions (it targets IC6.1.7+).
- skillbridge is great for interactive tools and notebooks. For unattended CI, plain batch runs (`virtuoso -nograph`) are simpler and more robust.

Demo: [`examples/python/skillbridge_demo.py`](../examples/python/skillbridge_demo.py).

## 4. Virtuoso calling Python

```lisp
; blocking
status = system("python3 /path/to/check_specs.py results.csv specs.json > report.txt")

; non-blocking with callbacks
procedure(vagPyDone(pid status) printf("python finished with %d\n" status))
pid = ipcBeginProcess("python3 /path/to/long_job.py" "" nil nil 'vagPyDone)
```

Use this to add a "Generate report" menu item or a post-run hook to Assembler.

## 5. Specs and reports

[`check_specs.py`](../examples/python/check_specs.py) reads a results CSV (from maestro export, or from `spectre_sweep.py`) and a JSON spec file:

```json
{
  "bw_hz":   {"min": 100e3},
  "gain_db": {"min": 40, "max": 60},
  "tr_s":    {"max": 2e-6}
}
```

It produces a Markdown report and a JUnit XML file, and exits non-zero if any spec fails, which is exactly what CI needs.

## 6. Recommended Python environment

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r examples/python/requirements.txt
```

- Keep the tool environment (Cadence `PATH`) and the Python venv independent. Activate both in your setup script.
- Some Cadence installs bundle their own Python on `PATH`. Call `python3` from your venv explicitly in scripts (`#!/usr/bin/env python3` after activating).

Next: [12 · Regression, batch and CI](12-regression-ci-batch.md)
