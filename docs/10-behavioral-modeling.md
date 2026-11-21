# 10 · Behavioral modeling: Verilog-A, Verilog-AMS and RNM

Behavioral models make automation practical: they simulate in milliseconds, contain no PDK data, and let you test the testbench before the transistor-level design exists.

| Language | Simulator | Speed | Typical use |
|---|---|---|---|
| **Verilog-A** | Spectre (analog solver) | Fast vs transistor-level | Ideal opamps, comparators, data converters, sources, checkers |
| **Verilog-AMS** | AMS Designer | Medium | Mixed analog + event-driven code in one module, custom connect modules |
| **`wreal` (Verilog-AMS)** | Xcelium (with AMS licensing) | Very fast | Legacy real-number models |
| **SV-RNM** (`real`, `nettype`) | Xcelium | Very fast | Modern real-number models for digital-centric verification |

## 1. Verilog-A essentials

```verilog
`include "constants.vams"
`include "disciplines.vams"

module comparator(inp, inn, out);
  input inp, inn; output out;
  electrical inp, inn, out;
  parameter real vhigh = 1.0;
  parameter real vlow  = 0.0;
  parameter real vth   = 0.0;          // input offset
  parameter real tr    = 100p from (0:inf);
  real target;

  analog begin
    @(cross(V(inp,inn) - vth, 0))  ;  // force timestep at crossing
    target = (V(inp,inn) > vth) ? vhigh : vlow;
    V(out) <+ transition(target, 0, tr);
  end
endmodule
```

Key constructs:

| Construct | Purpose |
|---|---|
| `V(a,b) <+ expr` / `I(a,b) <+ expr` | Contribute voltage/current (branch equations) |
| `ddt()`, `idt()` | Time derivative / integral |
| `laplace_nd()`, `laplace_zp()` | Transfer functions (filters, opamp poles) |
| `transition(x, td, tr, tf)` | Smooth piecewise-constant signals: **always** use it on discrete outputs |
| `@(cross(expr, dir))` | Detect threshold crossings precisely |
| `@(timer(t0, period))` | Periodic events (clocks, sampling) |
| `@(initial_step)`, `@(final_step)` | Init/cleanup, e.g. writing results with `$fopen/$fstrobe` |
| `$bound_step(dt)` | Limit simulator timestep |
| `parameter real x = 1 from [0:inf)` | Parameter with legal range (checked at elaboration) |

Use in Spectre:

```spectre
ahdl_include "comparator.va"
X1 (inp inn out) comparator vhigh=1.2 vth=1m
```

In Virtuoso, create a cell with a `veriloga` view (**File → New → Cellview**, type `VerilogA-Editor`), paste the code, and Virtuoso generates the symbol.

### Library in this repo: [`examples/veriloga/`](../examples/veriloga)

| Model | Notes |
|---|---|
| `comparator.va` | Offset, hysteresis, output transition |
| `opamp_1pole.va` | DC gain, GBW, output clamp |
| `dac_nbit.va` | N-bit binary DAC with logic threshold on inputs |
| `adc_nbit.va` | Clocked N-bit ADC (ideal quantizer) |
| `vco.va` | Voltage-controlled oscillator with `$bound_step` |
| `sample_hold.va` | Clocked track/hold |
| `meas_period.va` | Measurement module that writes edge times to a file |

## 2. Model-writing rules that save hours

1. **Every discrete output goes through `transition()`**. Discontinuities kill convergence and timestep control.
2. **Use `@(cross())` for every threshold** you act on, so the simulator lands exactly on the event.
3. **No `ddt()`/`idt()`/`transition()` inside conditionals** that switch at runtime (analog operators must be evaluated every timestep).
4. **Give parameters ranges** (`from (0:inf)`) so typos fail early.
5. **Model only what the test needs.** An ideal block with the right behavior beats a complicated one with wrong behavior.
6. **Validate models against the real circuit** (same testbench, overlay waveforms, compare key metrics). Store that comparison as a regression.

## 3. Verilog-AMS (analog + digital in one module)

```verilog
`include "disciplines.vams"
module dac_ams(input [3:0] code, output out);
  electrical out;
  parameter real vref = 1.0;
  real vtarget;
  always @(code) vtarget = vref * code / 15.0;     // digital (event) part
  analog V(out) <+ transition(vtarget, 0, 1n);       // analog part
endmodule
```

Compile with `xrun -ams` (forces AMS parsing). Don't use `-ams` on legacy Verilog files that use AMS keywords as identifiers.

## 4. Real-number modeling (RNM)

RNM replaces electrical behavior with **real values that change at events**. No matrix solve means digital-simulator speed.

### SystemVerilog `real` (portable, works in any SV simulator)

```systemverilog
module rc_lpf_rnm #(parameter real TAU = 1e-6, parameter real TS = 1e-9)
                   (input real vin, output real vout);
  // Discrete-time first-order low-pass, updated every TS seconds
  real alpha = TS / (TAU + TS);
  initial vout = 0.0;
  always #(TS * 1s) vout = vout + alpha * (vin - vout);
endmodule
```

### SV user-defined nettypes (SV-RNM, IEEE 1800-2012)

```systemverilog
typedef struct { real V; real I; real R; } EEstruct;
// Use a resolution function, or the EEnet package shipped with Xcelium, to resolve multiple drivers
```

Cadence ships packages (e.g. `cds_rnm_pkg`, `EE_pkg`) with predefined nettypes and resolution functions. Check your Xcelium installation's docs for names and paths.

### `wreal` (Verilog-AMS)

```verilog
module vsrc_wreal(output wreal v);
  real val = 1.2;
  assign v = val;
endmodule
```

Older but still common. New projects usually choose SV-RNM.

Example with self-checking testbench: [`examples/rnm`](../examples/rnm).

## 5. Choosing an abstraction per block

```
           accuracy ▲
transistor │  ■ Spectre / Spectre X
           │  ■ AMS (electrical + digital)
Verilog-A  │  ■
SV-RNM     │                  ■
pure logic │                           ■
           └────────────────────────────────► speed / regression size
```

Typical verification plan: **RNM everywhere** for the digital regression (thousands of tests), **AMS with Verilog-A or transistor-level** for a handful of interface tests, and **Spectre** for analog performance specs.

Next: [11 · Python integration](11-python-integration.md)
