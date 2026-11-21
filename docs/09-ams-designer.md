# 09 · Spectre AMS Designer (mixed-signal with `xrun`)

**Spectre AMS Designer** couples Xcelium (digital/behavioral) and Spectre (analog, electrical) in one simulation, launched with `xrun`. Use it when digital and analog must interact at the **electrical** level: real loading, supply-dependent thresholds, analog feedback into logic.

## 1. Concepts you need first

| Term | Meaning |
|---|---|
| **Discipline** | The "type" of a net: `logic` (digital), `electrical` (analog), `wreal` / real (event-driven real) |
| **Connect module (CM)** | Converter inserted where nets of different disciplines meet, e.g. logic→electrical (L2E) and electrical→logic (E2L) |
| **Connect rules (CR)** | Which CM to insert where, with what parameters (supply, thresholds, rise/fall) |
| **IE (interface element) card** | Simplified way to configure the built-in connect modules from the `amsd` block (`ie vsup=1.8 ...`) |
| **`amsd` block** | Section in a Spectre-syntax control file that binds cells to SPICE/Spectre netlists, sets port mapping and IE cards |
| **AMS control file** | `.scs` file that includes the analog netlist, models, analysis/options, and the `amsd` block. Passed straight to `xrun` |
| **UNL / OSS** | The two netlisting approaches Virtuoso uses to create AMS netlists. UNL ("unified netlister") is the modern default |

## 2. Two ways to run AMS

### A. From Virtuoso (ADE Explorer/Assembler, simulator = `ams`)
Build a **config view** that selects `schematic`/`spectre`/`veriloga`/`systemVerilog` views per cell, set up connect rules or IE in **Setup → Connect Rules/IE Setup**, run. ADE writes an `xrun` command and control file into the run directory. **Copy those as the start of your batch flow.**

### B. Pure command line (the single-step flow)
No `cds.lib`/`hdl.var`/worklib needed. All inputs go on one `xrun` line:

```bash
xrun -timescale 1ns/1ps \
     ./tb/tb_dac.sv \
     ./amscf.scs \
     -access +r -iereport \
     -spectre_args "+aps" \
     -input probe.tcl -l xrun_ams.log
```

`amscf.scs` (AMS control file):

```spectre
simulator lang=spectre
// analog side
ahdl_include "./dac4.va"
include "./dac_rc.scs"              // Spectre netlist with subckt dac_rc
// include "/path/to/models.scs" section=tt   // your PDK models, never in a public repo

tran1 tran stop=2u                   // analog analysis must match digital run length
simOpts options reltol=1e-4

amsd {
    portmap subckt=dac_rc autobus=yes      // map SV port names onto subckt ports by name
    config  cell=dac_rc use=spice          // bind SV instance of dac_rc to the Spectre subckt
    ie vsup=1.8                            // built-in connect modules use a 1.8 V supply
}
```

Runnable: [`examples/ams/dac_rc`](../examples/ams/dac_rc).

> When an `ie` statement is present in the `amsd` block, you do **not** need `-amsconnrules`. A custom connect-rules Verilog-AMS file can also be passed as a normal input file on the `xrun` line.

## 3. Reading analog values from SystemVerilog

```systemverilog
real vout;
always #10ns vout = $cds_get_analog_value("tb_dac.dut.out");
```

`$cds_get_analog_value` samples an analog node from the digital side. It's ideal for self-checking testbenches (compare against expected value, count errors, print `TEST PASSED`). Check your release's AMS reference for the exact hierarchical-name format.

## 4. IE / connect-module parameters (typical)

| Parameter | What it sets |
|---|---|
| `vsup` | Supply used for L2E high level and E2L thresholds |
| `vthi`, `vtlo` | E2L thresholds (above = 1, below = 0) |
| `tr`, `tf` | L2E output rise/fall time |
| `rlo`, `rhi` | L2E output resistance |
| `cell=`, `inst=`, `port=` | Scope an IE card to part of the design |
| `discipline=` | Apply only to a given discipline |

`-iereport` writes a report of which interface elements were inserted, with what parameters. **Always look at it** the first time you bring up a testbench. 90% of "wrong results" are wrong IE settings (wrong supply, thresholds or direction).

## 5. Analog engine selection inside AMS

```bash
xrun ... -spectre_args "+aps"                              # Spectre APS
xrun ... -spectre_args "+preset=mx +mt=4"                  # Spectre X
xrun ... -spectre_args "+fx +spectre +preset=lx +mt=8"     # Spectre FX (FastSPICE)
```

Spectre FX expects SPICE syntax by default, which is why `+spectre` is added when the netlist is Spectre syntax.

## 6. Probing

```tcl
# probe.tcl
database -open waves -shm -default
probe -create tb_dac -all -depth all
run
exit
```

Analog nodes are saved according to the analog `save` statements / options in the control file, while digital signals go through the Tcl `probe`. View both together in SimVision.

## 7. Debug checklist

1. **Does it elaborate?** Look for `*E` in `xrun.log`: unresolved modules usually mean a missing file or wrong `config cell=` name.
2. **Are the right IEs inserted?** Read the `-iereport` output.
3. **Do supplies match?** `vsup` must match the analog supply the cells actually see.
4. **Timescale:** modules without `` `timescale `` need `-timescale`.
5. **Analysis length:** the analog `tran stop=` should cover the digital run time.
6. **Port mapping:** SV port names must match subckt port names (or use positional `porttype=order`). Buses need `autobus=yes` and consistent naming.
7. **Start small:** first replace the analog block with an RNM model, get the testbench passing, then swap in the electrical netlist.

## 8. When *not* to use AMS

| Question | Use |
|---|---|
| Is this a functional check of digital control logic? | RNM in pure Xcelium (`xrun`, no Spectre) |
| Do I need analog accuracy but digital is trivial (a few control bits)? | Spectre alone with `vsource type=pwl`/`bit` stimuli |
| Do I need both electrical accuracy and complex digital? | **AMS Designer** |

Next: [10 · Behavioral modeling](10-behavioral-modeling.md)
