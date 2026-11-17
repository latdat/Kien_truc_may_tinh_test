// Thanh ghi pipeline: dữ liệu đi kèm tín hiệu valid
module pipe_reg #(
    parameter WIDTH = 8
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire [WIDTH-1:0] din,
    input  wire             vin,
    output reg  [WIDTH-1:0] dout,
    output reg              vout
);
    always @(posedge clk) begin
        dout <= din;
        if (!rst_n) vout <= 1'b0;
        else        vout <= vin;
    end
endmodule
