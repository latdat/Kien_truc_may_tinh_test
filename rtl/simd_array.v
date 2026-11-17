// Mảng P lane giống hệt nhau. Lane s nhận cột s, s+1, s+2 của cả ba dòng trong cửa sổ.
module simd_array #(
    parameter P = 4
) (
    input  wire               clk,
    input  wire               rst_n,
    input  wire [8*(P+2)-1:0] row0_win,
    input  wire [8*(P+2)-1:0] row1_win,
    input  wire [8*(P+2)-1:0] row2_win,
    input  wire [P-1:0]       valid_in,
    output wire [8*P-1:0]     pix_out,
    output wire [P-1:0]       valid_out
);
    genvar s;
    generate
        for (s = 0; s < P; s = s + 1) begin : lane
            wire [71:0] pix = {
                row2_win[8*(s+2) +: 8], row2_win[8*(s+1) +: 8], row2_win[8*s +: 8],
                row1_win[8*(s+2) +: 8], row1_win[8*(s+1) +: 8], row1_win[8*s +: 8],
                row0_win[8*(s+2) +: 8], row0_win[8*(s+1) +: 8], row0_win[8*s +: 8]
            };
            simd_lane u (
                .clk  (clk),
                .rst_n(rst_n),
                .pix  (pix),
                .vin  (valid_in[s]),
                .y    (pix_out[8*s +: 8]),
                .vout (valid_out[s])
            );
        end
    endgenerate
endmodule
