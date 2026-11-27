// Bộ lọc trung bình 3x3 SIMD P lane. Nhận P pixel liên tiếp của một dòng mỗi lần in_valid = 1.
// Đầu ra: out_valid[s] báo lane s có pixel hợp lệ. Các pixel hợp lệ theo thứ tự lane tăng dần
// và theo thời gian tạo thành ảnh ra (W-2) x (H-2) theo thứ tự raster.
// op_mode chọn phép lọc cho từng từ vào (0 trung bình, 1 Gaussian), chung cho mọi lane.
// Yêu cầu W chia hết cho P.
module top #(
    parameter P = 4,
    parameter W = 64,
    parameter H = 64
) (
    input  wire           clk,
    input  wire           rst_n,
    input  wire           in_valid,
    input  wire           op_mode,    // chế độ lọc của từ đang vào: 0 trung bình, 1 Gaussian
    input  wire [8*P-1:0] in_pixels,
    output wire [P-1:0]   out_valid,
    output wire [8*P-1:0] out_pixels
);
    wire [8*P-1:0]     row1;   // dòng r-1
    wire [8*P-1:0]     row0;   // dòng r-2
    wire [P-1:0]       mask;
    wire [8*(P+2)-1:0] w0, w1, w2;
    wire [P-1:0]       w_valid;
    wire               op_win;

    line_buffer #(.DW(8*P), .DEPTH(W/P)) lb1 (
        .clk(clk), .rst_n(rst_n), .en(in_valid), .din(in_pixels), .dout(row1));
    line_buffer #(.DW(8*P), .DEPTH(W/P)) lb2 (
        .clk(clk), .rst_n(rst_n), .en(in_valid), .din(row1), .dout(row0));

    controller #(.P(P), .W(W), .H(H)) ctrl (
        .clk(clk), .rst_n(rst_n), .in_valid(in_valid), .mask(mask));

    window_3x3 #(.P(P)) win (
        .clk(clk), .rst_n(rst_n), .en(in_valid), .mask(mask), .op_in(op_mode),
        .row0_in(row0), .row1_in(row1), .row2_in(in_pixels),
        .row0_win(w0), .row1_win(w1), .row2_win(w2), .valid(w_valid), .op_win(op_win));

    simd_array #(.P(P)) arr (
        .clk(clk), .rst_n(rst_n),
        .row0_win(w0), .row1_win(w1), .row2_win(w2), .valid_in(w_valid), .op_in(op_win),
        .pix_out(out_pixels), .valid_out(out_valid));
endmodule
