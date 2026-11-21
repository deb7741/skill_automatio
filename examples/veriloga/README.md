# Verilog-A model library (PDK-free)

| File | Module | Ports |
|---|---|---|
| `opamp_1pole.va` | `opamp_1pole` | inp inn out vdd vss |
| `comparator.va` | `comparator` | inp inn out |
| `dac_nbit.va` | `dac4` | b3 b2 b1 b0 out |
| `adc_nbit.va` | `adc4` | vin clk b3 b2 b1 b0 |
| `vco.va` | `vco` | vctrl out |
| `sample_hold.va` | `sample_hold` | vin clk out |
| `meas_period.va` | `meas_period` | sig (writes `period.txt`) |

Smoke test of all models:

```bash
spectre tb_models.scs +escchars =log tb.log -format psfascii -raw psf
python3 ../python/read_psf.py psf/tran1.tran --list
cat vco_period.txt
```

Use in Virtuoso: create a cell with a `veriloga` view, paste the module, let Virtuoso generate the symbol. Or reference the file with `ahdl_include` in a netlist.

Modeling rules are summarized in [docs/10](../../docs/10-behavioral-modeling.md).
