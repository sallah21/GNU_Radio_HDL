module multiplier
#(
    parameter dupa =10,
    parameter int dupa2 =10,
    parameter [9:0] dupa3 = 10
)
(
    input wire [31:0] data_in,
    output wire [31:0] data_out
);
    assign data_out = data_in * 2;
endmodule