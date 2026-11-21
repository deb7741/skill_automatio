// tb_dac_rnm.sv : same checks as ../ams/dac_rc/tb_dac.sv, against the RNM model
`timescale 1ns/1ps

module tb_dac_rnm;
  localparam real VREF = 1.8;
  localparam real TOL  = 0.05;

  logic [3:0] code = '0;
  real        out, expected;
  logic       cmp;
  int         errors = 0;

  dac_rc_rnm dut (.code(code), .out(out), .cmp(cmp));

  initial begin
    #100;
    for (int c = 0; c < 16; c++) begin
      code = c[3:0];
      #400;
      expected = VREF * c / 15.0;
      if ((out - expected) > TOL || (expected - out) > TOL) begin
        errors++;
        $display("ERROR code=%0d out=%f expected=%f", c, out, expected);
      end else
        $display("ok    code=%0d out=%f cmp=%b", c, out, cmp);
      // comparator sanity: above threshold -> 1
      if ((out > 0.95) && (cmp !== 1'b1)) begin
        errors++;
        $display("ERROR cmp should be 1 at out=%f", out);
      end
    end
    if (errors == 0) $display("TEST PASSED");
    else             $display("TEST FAILED (%0d errors)", errors);
    $finish;
  end
endmodule
