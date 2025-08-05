
        module memory_fsm_wrapper
        #(

)

        (
             input [0:0] clk,
  input [0:0] rst,
  input [7:0] data_in,
  input [0:0] start,
             output [7:0] data_out,
  output [2:0] state_out,
  output [0:0] done
        );
        
        memory_fsm
        #()
        memory_fsm_inst
        (
             .clk(clk),
  .rst(rst),
  .data_in(data_in),
  .start(start),
             .data_out(data_out),
  .state_out(state_out),
  .done(done)
        );
        
        endmodule
        