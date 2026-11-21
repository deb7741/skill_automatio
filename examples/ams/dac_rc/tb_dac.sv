// tb_dac.sv : SystemVerilog testbench for an analog block simulated by Spectre.
// Drives a 4-bit code into the Verilog-A DAC + RC filter (subckt dac_rc in
// dac_rc.scs, bound through the amsd block in amscf.scs), reads the analog
// output with $cds_get_analog_value, and checks it against the ideal value.
// Also receives the analog comparator output back as a digital signal.
`timescale 1ns/1ps

module tb_dac;
  localparam real VREF = 1.8;
  localparam real TOL  = 0.05;          // V, after settling

  logic [3:0] code = '0;
  wire        aout;                     // electrical node; connect modules inserted by AMS
  wire        cmp;                      // analog comparator -> digital (E2L)
  real        vout, expected;
  int         errors = 0;

  // Instance of the Spectre subckt (ports matched by name via amsd portmap)
  dac_rc dut (.b3(code[3]), .b2(code[2]), .b1(code[1]), .b0(code[0]),
              .out(aout), .cmp(cmp));

  initial begin
    #100;
    for (int c = 0; c < 16; c++) begin
      code = c[3:0];
      #400;                              // RC tau = 10 ns, plenty of settling
      vout     = $cds_get_analog_value("tb_dac.dut.out");
      expected = VREF * c / 15.0;
      if ((vout - expected) > TOL || (expected - vout) > TOL) begin
        errors++;
        $display("ERROR code=%0d vout=%f expected=%f", c, vout, expected);
      end else
        $display("ok    code=%0d vout=%f cmp=%b", c, vout, cmp);
    end
    if (errors == 0) $display("TEST PASSED");
    else             $display("TEST FAILED (%0d errors)", errors);
    $finish;
  end
endmodule
