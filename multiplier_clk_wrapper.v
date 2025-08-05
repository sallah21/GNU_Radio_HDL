
        module multiplier_clk_wrapper
        #(
dupa,
dupa2,
dupa3
)

        (
             input [31:0] data_in,
  input [0:0] clk,
  input [0:0] rst,
             output [31:0] data_out
        );
        
        multiplier_clk
        #(.dupa(dupa),
.dupa2(dupa2),
.dupa3(dupa3))
        multiplier_clk_inst
        (
             .data_in(data_in),
  .clk(clk),
  .rst(rst),
             .data_out(data_out)
        );
        
        endmodule
        