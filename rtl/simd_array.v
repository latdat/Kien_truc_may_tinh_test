// Mảng P lane giống hệt nhau. Lane s nhận cột s, s+1, s+2 của cả ba dòng trong cửa sổ.
// Mỗi lane có hai khối tính chạy song song trên cùng 9 pixel: simd_lane (trung bình) và gauss_lane (Gaussian).
// op_in chọn đầu ra ở cuối pipeline: 0 trung bình, 1 Gaussian. op_in chung cho cả P lane và đi qua thanh ghi dịch
// 5 bit, cùng độ sâu với lane, nên chế độ của một cửa sổ luôn đến cùng lúc với kết quả của chính cửa sổ đó.
module simd_array #(
    parameter P = 4
) (
    input  wire               clk,
    input  wire               rst_n,
    input  wire [8*(P+2)-1:0] row0_win,
    input  wire [8*(P+2)-1:0] row1_win,
    input  wire [8*(P+2)-1:0] row2_win,
    input  wire [P-1:0]       valid_in,
    input  wire               op_in,
    output wire [8*P-1:0]     pix_out,
    output wire [P-1:0]       valid_out
);
    reg [4:0] op_pipe;
    always @(posedge clk) op_pipe <= {op_pipe[3:0], op_in};

    genvar s;
    generate
        for (s = 0; s < P; s = s + 1) begin : lane
            wire [71:0] pix = {
                row2_win[8*(s+2) +: 8], row2_win[8*(s+1) +: 8], row2_win[8*s +: 8],
                row1_win[8*(s+2) +: 8], row1_win[8*(s+1) +: 8], row1_win[8*s +: 8],
                row0_win[8*(s+2) +: 8], row0_win[8*(s+1) +: 8], row0_win[8*s +: 8]
            };
            wire [7:0] y_mean, y_gauss;
            simd_lane u (
                .clk  (clk),
                .rst_n(rst_n),
                .pix  (pix),
                .vin  (valid_in[s]),
                .y    (y_mean),
                .vout (valid_out[s])
            );
            gauss_lane g (
                .clk  (clk),
                .rst_n(rst_n),
                .pix  (pix),
                .vin  (valid_in[s]),
                .y    (y_gauss),
                .vout ()
            );
            assign pix_out[8*s +: 8] = op_pipe[4] ? y_gauss : y_mean;
        end
    endgenerate
endmodule
