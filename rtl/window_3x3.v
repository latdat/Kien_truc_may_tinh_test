// Cửa sổ 3 dòng x (P+2) cột, có thanh ghi. Pixel k của từ vào nằm ở bit [8k +: 8].
// Cột 0 và 1 của cửa sổ là hai pixel cuối của từ trước; cột 2..P+1 là từ hiện tại.
// row0 là dòng cũ nhất (r-2), row2 là dòng mới nhất (r).
module window_3x3 #(
    parameter P = 4
) (
    input  wire                clk,
    input  wire                rst_n,
    input  wire                en,
    input  wire [P-1:0]        mask,
    input  wire                op_in,      // chế độ lọc của từ đang vào: 0 trung bình, 1 Gaussian
    input  wire [8*P-1:0]      row0_in,
    input  wire [8*P-1:0]      row1_in,
    input  wire [8*P-1:0]      row2_in,
    output reg  [8*(P+2)-1:0]  row0_win,
    output reg  [8*(P+2)-1:0]  row1_win,
    output reg  [8*(P+2)-1:0]  row2_win,
    output reg  [P-1:0]        valid,
    output reg                 op_win      // chế độ lọc, chốt cùng nhịp với dữ liệu cửa sổ
);
    always @(posedge clk) begin
        if (en) begin
            row0_win <= {row0_in, row0_win[8*P +: 16]};
            row1_win <= {row1_in, row1_win[8*P +: 16]};
            row2_win <= {row2_in, row2_win[8*P +: 16]};
            op_win   <= op_in;
        end
        if (!rst_n) valid <= {P{1'b0}};
        else        valid <= en ? mask : {P{1'b0}};
    end
endmodule
