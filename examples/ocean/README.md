# Ocean examples

| Script | Shows |
|---|---|
| `01_basic_tran_ac.ocn` | Simulate a stand-alone netlist, measure bandwidth/rise time, print a machine-readable line |
| `02_param_sweep.ocn` | Nested `paramAnalysis` + `paramRun`, families, `ocnPrint` |
| `03_pvt_loop_csv.ocn` | Explicit voltage × temperature loops, per-point result dirs, CSV output, placeholder for model corners |
| `04_waveform_export.ocn` | `openResults` on existing data, export waveforms with `ocnPrint` and raw vectors |
| `05_from_schematic.ocn` | Netlist and simulate a schematic from a library (`design(lib cell view)`) |

```bash
./run_ocean.sh 01_basic_tran_ac.ocn
./run_ocean.sh 02_param_sweep.ocn
./run_ocean.sh 03_pvt_loop_csv.ocn
./run_ocean.sh 04_waveform_export.ocn     # after 01
```

Scripts 01–04 use the circuit-only netlist in `netlist/rc_circuit.scs` (Ocean adds analyses and design variables itself), so no library setup is needed. They print `OCEAN_RESULT key=value` lines that `../python/cadence_batch.py ocean <script>` collects.
