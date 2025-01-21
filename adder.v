module adder
#(
    parameter dupa,
    parameter int dupa2,
    parameter [9:0] dupa3 = ;
)
(
    input wire [31:0] data_in,
    input wire [31:0] data_in2,
    output wire [31:0] data_out
);
    assign data_out = data_in + data_in2;
endmodule