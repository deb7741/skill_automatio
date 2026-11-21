// rnm_models.sv : real-number models (plain SystemVerilog `real`), portable to
// any IEEE-1800 simulator. They mirror the electrical dac_rc block of the AMS
// example so the same test can run 100x faster in pure Xcelium.
`timescale 1ns/1ps

// Ideal 4-bit DAC: output updates immediately on code change
module dac4_rnm #(parameter real VREF = 1.8) (
  input  logic [3:0] code,
  output real        vout
);
  always_comb vout = VREF * code / 15.0;
endmodule

// First-order low-pass, discretized with time step TS (ns)
//   y[n+1] = y[n] + a * (x[n] - y[n]),   a = TS / (TAU + TS)
module lpf1_rnm #(parameter real TAU_NS = 10.0, parameter real TS_NS = 0.5) (
  input  real vin,
  output real vout
);
  localparam real A = TS_NS / (TAU_NS + TS_NS);
  initial vout = 0.0;
  always #(TS_NS) vout = vout + A * (vin - vout);
endmodule

// Comparator with hysteresis, real input -> logic output
module comparator_rnm #(parameter real VTH = 0.9, parameter real HYST = 0.02) (
  input  real  vin,
  output logic out
);
  initial out = 1'b0;
  always @(vin) begin
    if      (vin > VTH + HYST/2) out = 1'b1;
    else if (vin < VTH - HYST/2) out = 1'b0;
  end
endmodule

// Top-level RNM equivalent of the electrical dac_rc subckt
module dac_rc_rnm (
  input  logic [3:0] code,
  output real        out,
  output logic       cmp
);
  real vdac;
  dac4_rnm       u_dac (.code(code), .vout(vdac));
  lpf1_rnm       u_lpf (.vin(vdac), .vout(out));
  comparator_rnm u_cmp (.vin(out),  .out(cmp));
endmodule
