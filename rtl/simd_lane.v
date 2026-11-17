// Một lane: cộng 9 pixel bằng cây cộng 4 tầng (8 bộ cộng), chia 9 bằng nhân hằng số rồi dịch.
// Pipeline 5 stage: 4 tầng cộng + 1 stage chuẩn hóa, y = (sum * 7282) >> 16 = floor(sum / 9).
module simd_lane (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [71:0] pix,     // 9 pixel 8 bit, pixel k ở bit [8k +: 8]
    input  wire        vin,
    output wire [7:0]  y,
    output wire        vout
);
    localparam [12:0] INV9 = 13'd7282;

    wire [7:0] p [0:8];
    genvar k;
    generate
        for (k = 0; k < 9; k = k + 1) begin : unpack
            assign p[k] = pix[8*k +: 8];
        end
    endgenerate

    // Tầng 1: 4 phép cộng, pixel thứ 9 đi thẳng
    wire [8:0] a1 = p[0] + p[1];
    wire [8:0] a2 = p[2] + p[3];
    wire [8:0] a3 = p[4] + p[5];
    wire [8:0] a4 = p[6] + p[7];
    wire [8:0] a5 = {1'b0, p[8]};
    wire [44:0] s1_d;
    wire        s1_v;
    pipe_reg #(.WIDTH(45)) st1 (clk, rst_n, {a5, a4, a3, a2, a1}, vin, s1_d, s1_v);

    // Tầng 2: 2 phép cộng
    wire [9:0] b1 = s1_d[8:0]   + s1_d[17:9];
    wire [9:0] b2 = s1_d[26:18] + s1_d[35:27];
    wire [9:0] b3 = {1'b0, s1_d[44:36]};
    wire [29:0] s2_d;
    wire        s2_v;
    pipe_reg #(.WIDTH(30)) st2 (clk, rst_n, {b3, b2, b1}, s1_v, s2_d, s2_v);

    // Tầng 3: 1 phép cộng
    wire [10:0] c1 = s2_d[9:0] + s2_d[19:10];
    wire [10:0] c2 = {1'b0, s2_d[29:20]};
    wire [21:0] s3_d;
    wire        s3_v;
    pipe_reg #(.WIDTH(22)) st3 (clk, rst_n, {c2, c1}, s2_v, s3_d, s3_v);

    // Tầng 4: 1 phép cộng, tổng tối đa 9 * 255 = 2295 (12 bit)
    wire [11:0] sum = s3_d[10:0] + s3_d[21:11];
    wire [11:0] s4_d;
    wire        s4_v;
    pipe_reg #(.WIDTH(12)) st4 (clk, rst_n, sum, s3_v, s4_d, s4_v);

    // Stage chuẩn hóa
    wire [24:0] prod = s4_d * INV9;
    wire [7:0]  s5_d;
    pipe_reg #(.WIDTH(8)) st5 (clk, rst_n, prod[23:16], s4_v, s5_d, vout);

    assign y = s5_d;
endmodule
