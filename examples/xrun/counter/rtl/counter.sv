// counter.sv : parameterized up-counter with synchronous enable/clear
// and a terminal-count flag.
`timescale 1ns/1ps

module counter #(
  parameter int WIDTH = 8
) (
  input  logic             clk,
  input  logic             rst_n,   // async active-low reset
  input  logic             en,
  input  logic             clr,     // synchronous clear
  output logic [WIDTH-1:0] count,
  output logic             tc       // terminal count (all ones)
);

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)      count <= '0;
    else if (clr)    count <= '0;
    else if (en)     count <= count + 1'b1;
  end

  assign tc = &count;

endmodule
