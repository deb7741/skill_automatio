# 08 · Xcelium and `xrun`

`xrun` is the single-command front end to Xcelium: it compiles, elaborates and simulates Verilog, SystemVerilog, VHDL, SystemC, and (with Spectre) mixed-signal designs. It replaced `irun`. The underlying 3-step tools were renamed `ncvlog/ncelab/ncsim` → `xmvlog/xmelab/xmsim`.

## 1. Single-step basics

```bash
xrun -sv rtl/counter.sv tb/tb_counter.sv -top tb_counter -access +r -l xrun.log
```

With a filelist (recommended):

```bash
xrun -f files.f -top tb_counter -l xrun.log
```

`files.f`:

```text
-sv
-timescale 1ns/1ps
+incdir+./rtl
+define+SIM
./rtl/counter.sv
./tb/tb_counter.sv
```

Runnable: [`examples/xrun/counter`](../examples/xrun/counter).

## 2. Options you'll use every day

| Option | Purpose |
|---|---|
| `-f file` | Read options/files from a filelist (nestable) |
| `-sv` | Treat `.v` files as SystemVerilog (`.sv` is auto-detected) |
| `-top name` | Top-level design unit (repeatable) |
| `-timescale 1ns/1ps` | Default timescale for modules without one |
| `+incdir+dir`, `+define+NAME[=val]` | Include dirs, macros |
| `-v file`, `-y dir +libext+.v+.sv` | Library files/dirs (resolve modules on demand) |
| `-access +rwc` | Debug visibility (read/write/connectivity). Costs performance, so restrict in regressions |
| `-linedebug` | Line-level breakpoints in SimVision |
| `-gui` | Launch SimVision |
| `-input script.tcl` | Run Tcl commands at simulation start (probes, `run`, `exit`) |
| `-l file` | Log file (default `xrun.log`) |
| `-clean` | Delete `xcelium.d` and rebuild from scratch |
| `-elaborate` | Compile + elaborate only (no simulation) |
| `-R` | Run the last elaborated snapshot (skip compile/elab) |
| `-snapshot name` | Name the snapshot (for reusing one build across many tests) |
| `-seed N` / `-svseed random` | Randomization seed |
| `-uvm` / `-uvmhome CDNS-1.2` | Use the UVM library shipped with Xcelium |
| `+UVM_TESTNAME=my_test`, `+UVM_VERBOSITY=UVM_LOW` | Plusargs passed to the testbench |
| `-coverage all` (`b:e:f:t:u` subsets) | Collect code/functional coverage |
| `-covtest name`, `-covoverwrite` | Name the coverage run, overwrite old |
| `-xprop C\|F` | X-propagation (compute / forward) mode |
| `-licqueue` | Wait for a license instead of failing |
| `-helpall`, `-helpsubject ams` | Built-in help |

## 3. Tcl probing and waveforms

`probe.tcl`:

```tcl
database -open waves -shm -default
probe -create tb_counter -all -depth all -database waves
run
exit
```

```bash
xrun -f files.f -access +r -input probe.tcl
simvision waves.shm &
```

- SHM (`.shm` directories) is Xcelium's native waveform format.
- VCD via `$dumpfile/$dumpvars` works everywhere but is big and slow.
- Probing everything (`-all -depth all`) is fine for small designs. Be selective in big ones.

## 4. Build once, run many (regressions)

```bash
# Build once
xrun -f files.f -elaborate -snapshot tb_snap -access +r -l build.log

# Run many seeds/tests against the same snapshot
for seed in 1 2 3 4; do
  xrun -R -snapshot tb_snap -svseed $seed +UVM_TESTNAME=smoke_test -l run_$seed.log &
done; wait
```

Each run needs its own log. Parallel runs that **write** into the same `xcelium.d` (e.g. different compile options) must use separate work directories (`-xmlibdirname`/separate run dirs).

## 5. Coverage flow

```bash
xrun -f files.f -coverage all -covtest test_seed1 -covoverwrite -svseed 1
xrun -f files.f -coverage all -covtest test_seed2 -covoverwrite -svseed 2

# merge & report with IMC
imc -execcmd "merge cov_work/scope/test_* -out merged -overwrite; load -run merged; report -summary"
```

Or put IMC commands in `merge.tcl` and use `imc -exec merge.tcl`. The GUI is `imc` with no arguments.

## 6. Pass/fail detection

`xrun` exits non-zero for compile/elab errors and `$fatal`, but **a testbench that only prints "FAILED" or raises `UVM_ERROR` usually still exits 0**. Always parse the log:

| Pattern | Meaning |
|---|---|
| `*E,` / `*F,` | Tool error / fatal (e.g. `xmvlog: *E,...`) |
| `*W,` | Tool warning |
| `UVM_ERROR :    N`, `UVM_FATAL :    N` | UVM report summary counts |
| Your own `TEST PASSED` / `TEST FAILED` banner | Recommended for non-UVM benches |

[`examples/python/xrun_regression.py`](../examples/python/xrun_regression.py) runs a list of tests in parallel, applies these rules and writes JUnit XML for Jenkins/GitLab.

## 7. Mixed-language and libraries

```bash
xrun -sv top.sv -vhdl2008 sub.vhd       # SV + VHDL
xrun -f files.f -v ./lib/cells.v        # behavioral cell library (generic only!)
```

## 8. Three-step mode (when you need it)

```bash
xmvlog -sv -f files.f         # compile
xmelab -access +r tb_counter  # elaborate → snapshot worklib.tb_counter:sv
xmsim tb_counter -input probe.tcl
```

Single-step `xrun` is easier and is what Cadence recommends for new flows. You'll still see 3-step in legacy scripts and older AMS flows (`cds.lib` + `hdl.var`).

## 9. Real-number and AMS hooks

- SystemVerilog `real` and user-defined nettypes (SV-RNM) run in plain Xcelium: no analog license, very fast. See [10](10-behavioral-modeling.md) and [`examples/rnm`](../examples/rnm).
- Add Spectre into the same `xrun` call and you have **AMS Designer**. See [09](09-ams-designer.md).

Next: [09 · Spectre AMS Designer](09-ams-designer.md)
