
        module multiplier_wrapper
        #(
dupa,
dupa2,
dupa3
)

        (
             input [31:0] data_in,
             output [31:0] data_out
        );
        
        multiplier
        #(.dupa(dupa),
.dupa2(dupa2),
.dupa3(dupa3))
        multiplier_inst
        (
             .data_in(data_in),
             .data_out(data_out)
        );
        
        endmodule
        