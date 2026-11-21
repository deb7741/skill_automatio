# Spectre examples

| Folder | Shows | Expected result |
|---|---|---|
| `01_rc_lowpass` | Netlist basics, tran + AC, psfascii output, Python bandwidth check | f-3dB ≈ 159.2 kHz |
| `02_sweeps_montecarlo` | `sweep` over values, `paramset` corner table, temperature sweep, generic Monte Carlo | One AC file per point; bandwidth spread in MC |
| `03_veriloga_opamp` | `ahdl_include`, Verilog-A opamp in a non-inverting amplifier | Closed-loop gain ≈ 20 dB, BW ≈ 1 MHz |

```bash
cd 01_rc_lowpass && ./run.sh            # baseline Spectre
./run.sh +aps                           # Spectre APS
./run.sh +preset=mx +mt=4               # Spectre X
```

All runs write `-format psfascii` so `../python/read_psf.py` can read the results without extra libraries.
