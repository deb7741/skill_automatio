# Real-number model (RNM) example

`rnm_models.sv` holds plain-SystemVerilog `real` models of the same DAC → RC → comparator chain used in `../ams/dac_rc`. `tb_dac_rnm.sv` runs the same checks.

```bash
./run.sh       # xrun, no Spectre, no analog license
```

Compare runtimes with the AMS version to see why digital regressions use RNM, with AMS reserved for a few interface tests. See [docs/10](../../docs/10-behavioral-modeling.md).
