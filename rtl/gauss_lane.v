// Một lane lọc Gaussian 3x3 với nhân [1 2 1; 2 4 2; 1 2 1] / 16. Cùng cổng và cùng độ sâu 5 stage với simd_lane.
// Trọng số 2 và 4 làm bằng dịch bit, chia 16 cũng là dịch bit (lấy bit 11 đến 4 của tổng), không cần bộ nhân.
// Tổng có trọng số tối đa 16 * 255 = 4080 < 4096 nên vẫn vừa 12 bit.
module gauss_lane (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [71:0] pix,     // 9 pixel 8 bit, pixel k ở bit [8k +: 8]; p[4] là tâm cửa sổ
    input  wire        vin,
    output wire [7:0]  y,
    output wire        vout
);
    wire [7:0] p [0:8];
    genvar k;
    generate
        for (k = 0; k < 9; k = k + 1) begin : unpack
            assign p[k] = pix[8*k +: 8];
        end
    endgenerate

    // Tầng 1: góc x1, cạnh x2 (dịch 1 bit), tâm x4 (dịch 2 bit); pixel thứ 9 (góc) đi thẳng
    wire [10:0] a1 = p[0] + {p[1], 1'b0};
    wire [10:0] a2 = p[2] + {p[3], 1'b0};
    wire [10:0] a3 = {p[4], 2'b00} + {p[5], 1'b0};
    wire [10:0] a4 = p[6] + {p[7], 1'b0};
    wire [10:0] a5 = {3'b000, p[8]};
    wire [54:0] s1_d;
    wire        s1_v;
    pipe_reg #(.WIDTH(55)) st1 (clk, rst_n, {a5, a4, a3, a2, a1}, vin, s1_d, s1_v);

    // Tầng 2: 2 phép cộng
    wire [11:0] b1 = s1_d[10:0]  + s1_d[21:11];
    wire [11:0] b2 = s1_d[32:22] + s1_d[43:33];
    wire [11:0] b3 = {1'b0, s1_d[54:44]};
    wire [35:0] s2_d;
    wire        s2_v;
    pipe_reg #(.WIDTH(36)) st2 (clk, rst_n, {b3, b2, b1}, s1_v, s2_d, s2_v);

    // Tầng 3: 1 phép cộng
    wire [11:0] c1 = s2_d[11:0] + s2_d[23:12];
    wire [11:0] c2 = s2_d[35:24];
    wire [23:0] s3_d;
    wire        s3_v;
    pipe_reg #(.WIDTH(24)) st3 (clk, rst_n, {c2, c1}, s2_v, s3_d, s3_v);

    // Tầng 4: tổng có trọng số, tối đa 16 * 255 = 4080 (12 bit)
    wire [11:0] sum = s3_d[11:0] + s3_d[23:12];
    wire [11:0] s4_d;
    wire        s4_v;
    pipe_reg #(.WIDTH(12)) st4 (clk, rst_n, sum, s3_v, s4_d, s4_v);

    // Stage chuẩn hóa: chia 16 bằng dịch phải 4 bit
    wire [7:0] s5_d;
    pipe_reg #(.WIDTH(8)) st5 (clk, rst_n, s4_d[11:4], s4_v, s5_d, vout);

    assign y = s5_d;
endmodule
