# Examples

Every example is **PDK-free**: only ideal elements, Cadence generic libraries (`analogLib`, `basic`) and Verilog-A / SystemVerilog written for this repo.

| Folder | Needs | Start here |
|---|---|---|
| [`spectre/01_rc_lowpass`](spectre/01_rc_lowpass) | Spectre | `./run.sh` |
| [`spectre/02_sweeps_montecarlo`](spectre/02_sweeps_montecarlo) | Spectre | `./run.sh` |
| [`spectre/03_veriloga_opamp`](spectre/03_veriloga_opamp) | Spectre (AHDL) | `./run.sh` |
| [`ocean/`](ocean) | Virtuoso/Ocean + Spectre | `./run_ocean.sh 01_basic_tran_ac.ocn` |
| [`skill/`](skill) | Virtuoso | `load("lib_utils.il")` in the CIW, or batch (see README) |
| [`xrun/counter`](xrun/counter) | Xcelium | `./run.sh` |
| [`ams/dac_rc`](ams/dac_rc) | Xcelium + Spectre (AMS) | `./run.sh` |
| [`rnm/`](rnm) | Xcelium (or any SV simulator) | `./run.sh` |
| [`veriloga/`](veriloga) | Spectre | Model library + `tb_models.scs` |
| [`python/`](python) | Python 3.8+ (tools optional) | `pytest -q` |

Run the examples from inside their own folder. Results go into local `psf/`, `xcelium.d/`, etc., which `.gitignore` excludes.
