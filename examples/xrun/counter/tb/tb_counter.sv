// tb_counter.sv : self-checking testbench with a reference model,
// random enable/clear, functional coverage and a PASS/FAIL banner that
// regression scripts can grep for.
`timescale 1ns/1ps

module tb_counter;
  localparam int WIDTH = 4;

  logic clk = 0, rst_n = 0, en = 0, clr = 0;
  logic [WIDTH-1:0] count;
  logic tc;
  int   errors = 0;
  int   cycles = 200;
  logic [WIDTH-1:0] model;

  counter #(.WIDTH(WIDTH)) dut (.*);

  always #5 clk = ~clk;   // 100 MHz

  // Functional coverage: did we see every count value, and tc?
  covergroup cg @(posedge clk iff rst_n);
    cp_count : coverpoint count;
    cp_tc    : coverpoint tc { bins hit = {1}; }
    cp_ctrl  : coverpoint {en, clr};
  endgroup
  cg cov = new();

  // Reference model
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)   model <= '0;
    else if (clr) model <= '0;
    else if (en)  model <= model + 1'b1;
  end

  // Checker (sample just before the next active edge)
  always @(negedge clk) if (rst_n) begin
    if (count !== model) begin
      errors++;
      $error("t=%0t count=%0d expected=%0d", $time, count, model);
    end
    if (tc !== (&model)) begin
      errors++;
      $error("t=%0t tc=%0b expected=%0b", $time, tc, &model);
    end
  end

  initial begin
    if ($value$plusargs("CYCLES=%d", cycles))
      $display("CYCLES overridden to %0d", cycles);

    repeat (3) @(posedge clk);
    rst_n = 1;

    repeat (cycles) begin
      @(posedge clk);
      en  <= ($urandom_range(0, 9) < 8);   // mostly enabled
      clr <= ($urandom_range(0, 49) == 0); // occasional clear
    end

    @(posedge clk);
    $display("Coverage: %0.1f%%", cov.get_coverage());
    if (errors == 0) $display("TEST PASSED");
    else             $display("TEST FAILED (%0d errors)", errors);
    $finish;
  end
endmodule
