module multiplier_clk
#(
    parameter dupa =10,
    parameter int dupa2 =10,
    parameter [9:0] dupa3 = 10
)
(
    input wire [31:0] data_in,
    output wire [31:0] data_out,
    input wire clk,
    input wire rst
);
    reg [31:0] data_out_reg;
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            data_out_reg <= 0;
        end else begin
            data_out_reg <= data_in * 2;
        end
    end
    assign data_out = data_out_reg;
endmodule