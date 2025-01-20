module multiplier
#(
    parameter dupa,
    parameter int dupa2,
    parameter [9:0] dupa3 = ;
)
(
    input wire [31:0] data_in,
    output wire [31:0] data_out
);
    assign data_out = data_in * 2;
endmodule