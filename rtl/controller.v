// Controller: đếm vị trí từ đầu vào (cột nhóm g, dòng r) và tạo mặt nạ valid cho P cửa sổ.
// Cửa sổ s của từ hiện tại có cột trái x = g*P - 2 + s. Chỉ xuất khi đủ 3 dòng (r >= 2)
// và đủ 3 cột trong ảnh (0 <= x <= W-3), nên ảnh ra có kích thước (W-2) x (H-2).
module controller #(
    parameter P = 4,
    parameter W = 64,
    parameter H = 64
) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         in_valid,
    output reg  [P-1:0] mask
);
    localparam WP = W / P;
    localparam GW = $clog2(WP + 1);
    localparam RW = $clog2(H + 1);

    reg [GW-1:0] g;
    reg [RW-1:0] r;
    integer s, x, gi, ri;

    always @(posedge clk) begin
        if (!rst_n) begin
            g <= {GW{1'b0}};
            r <= {RW{1'b0}};
        end else if (in_valid) begin
            if (g == WP - 1) begin
                g <= {GW{1'b0}};
                r <= (r == H - 1) ? {RW{1'b0}} : r + 1'b1;
            end else begin
                g <= g + 1'b1;
            end
        end
    end

    always @* begin
        gi = g;
        ri = r;
        for (s = 0; s < P; s = s + 1) begin
            x       = gi * P - 2 + s;
            mask[s] = (ri >= 2) && (x >= 0) && (x <= W - 3);
        end
    end
endmodule
