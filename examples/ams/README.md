# AMS Designer example: SystemVerilog ↔ Spectre

```
 tb_dac.sv (Xcelium)                      dac_rc.scs (Spectre)
 ┌────────────────────┐   L2E (ie vsup=1.8)   ┌──────────────────────────────┐
 │ code[3:0] ─────────┼──────────────────────►│ dac4.va ─► R ─► out ──┐       │
 │                    │                       │                 C    comparator.va
 │ $cds_get_analog_   │◄───── analog read ────┤ out                    │      │
 │ value("...out")    │                       │                        ▼      │
 │ cmp ◄──────────────┼──────── E2L ──────────┤◄────────────────────── cmp    │
 └────────────────────┘                       └──────────────────────────────┘
```

```bash
cd dac_rc
./run.sh          # Spectre APS as analog engine
./run.sh x        # Spectre X
```

What to look at:

1. `xrun_ams.log`: elaboration messages, the IE report (`-iereport`), and the `ok`/`ERROR` lines from the testbench
2. `TEST PASSED` / `TEST FAILED` banner
3. Waves: `simvision waves.shm` (digital), analog results per the `save` statement in `amscf.scs`

Things to try:

- Change `ie vsup=1.8` to `ie vsup=1.0` and watch the checks fail. This is the classic supply-mismatch bug.
- Replace the electrical `dac_rc` with an RNM model (see `../rnm`) for a 100× faster regression version of the same test.

The exact hierarchical-name format for `$cds_get_analog_value` and the available `ie` parameters can vary by release; see the *Spectre AMS Designer and Xcelium Simulator Mixed-Signal User Guide* for yours.
