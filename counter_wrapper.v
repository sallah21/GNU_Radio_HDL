
        module counter_wrapper
        #(

)

        (
             input [0:0] clk,
  input [0:0] rst,
  input [0:0] enable,
             output [7:0] count
        );
        
        counter
        #()
        counter_inst
        (
             .clk(clk),
  .rst(rst),
  .enable(enable),
             .count(count)
        );
        
        endmodule
        