// Testbench toàn hệ thống.
// Tham số: P (số lane), W, H, F (số khung ảnh liên tiếp), B (pixel cấp mỗi chu kỳ, B <= P),
// STALL (xác suất %, mỗi chu kỳ bộ cấp dữ liệu bị ngắt quãng), SEED (hạt giống bộ sinh ngẫu nhiên),
// OPS (mặt nạ chế độ lọc theo khung: bit f = 0 lọc trung bình, 1 lọc Gaussian cho khung f; F <= 32).
// Chế độ chỉ đổi giữa các khung, không đổi trong một khung.
// Plusarg: +in=<hex ảnh vào> +out=<hex ảnh ra> [+exp=<hex ảnh chuẩn, để tự kiểm>] [+vcd=<file dạng sóng>].
// Đếm chu kỳ ở một bộ theo dõi riêng, lấy mẫu in_valid/out_valid ở cùng cạnh clock.
`timescale 1ns/1ps
module tb_top;
    parameter P     = 4;
    parameter W     = 64;
    parameter H     = 64;
    parameter F     = 1;
    parameter B     = P;
    parameter STALL = 0;
    parameter SEED  = 32'h1234abcd;
    parameter OPS   = 0;

    localparam NIN   = W * H * F;
    localparam NOUT  = (W - 2) * (H - 2) * F;
    localparam NWORD = NIN / P;

    reg                clk = 0;
    reg                rst_n = 0;
    reg                in_valid = 0;
    reg                op_mode = 0;
    reg  [8*P-1:0]     in_pixels = 0;
    wire [P-1:0]       out_valid;
    wire [8*P-1:0]     out_pixels;

    top #(.P(P), .W(W), .H(H)) dut (
        .clk(clk), .rst_n(rst_n), .in_valid(in_valid), .op_mode(op_mode), .in_pixels(in_pixels),
        .out_valid(out_valid), .out_pixels(out_pixels));

    always #5 clk = ~clk;

    reg [7:0] img [0:NIN-1];
    reg [7:0] res [0:NOUT-1];
    reg [7:0] ref_img [0:NOUT-1];
    reg [1023:0] fin, fout, fexp, fvcd;
    reg have_exp;

    integer word_idx, credit, k, n;
    integer cyc, first_in, first_out, last_out, nout, extra, sc_err;
    integer fd;
    reg [31:0] rng;
    wire [31:0] opsv = OPS;
    reg        stall_now;

    // Bộ cấp dữ liệu: mỗi chu kỳ cộng B pixel vào "tín dụng"; đủ P pixel thì phát một từ.
    // Chu kỳ bị ngắt quãng (STALL) thì không cấp và không cộng tín dụng.
    always @(posedge clk) begin
        if (!rst_n) begin
            in_valid <= 0;
            word_idx = 0;
            credit   = 0;
            rng      = SEED;
        end else begin
            rng = rng ^ (rng << 13);
            rng = rng ^ (rng >> 17);
            rng = rng ^ (rng << 5);
            stall_now = ((rng % 100) < STALL);
            if (!stall_now) credit = credit + B;
            if (!stall_now && word_idx < NWORD && credit >= P) begin
                in_valid <= 1;
                op_mode  <= opsv[word_idx / (NWORD / F)];
                for (k = 0; k < P; k = k + 1)
                    in_pixels[8*k +: 8] <= img[word_idx*P + k];
                word_idx = word_idx + 1;
                credit   = credit - P;
            end else begin
                in_valid <= 0;
            end
        end
    end

    // Bộ theo dõi: thu pixel ra theo thứ tự lane, đếm chu kỳ, tự kiểm với ảnh chuẩn nếu có
    always @(posedge clk) begin
        if (!rst_n) begin
            cyc = 0; first_in = -1; first_out = -1; last_out = -1; nout = 0; extra = 0; sc_err = 0;
        end else begin
            cyc = cyc + 1;
            if (in_valid && first_in < 0) first_in = cyc;
            if (|out_valid) begin
                if (first_out < 0) first_out = cyc;
                for (k = 0; k < P; k = k + 1) begin
                    if (out_valid[k]) begin
                        if (nout < NOUT) begin
                            res[nout] = out_pixels[8*k +: 8];
                            if (have_exp && out_pixels[8*k +: 8] !== ref_img[nout]) sc_err = sc_err + 1;
                        end else begin
                            extra = extra + 1;
                        end
                        nout = nout + 1;
                    end
                end
                if (nout >= NOUT && last_out < 0) last_out = cyc;
            end
        end
    end

    initial begin
        if (!$value$plusargs("in=%s", fin))   begin $display("thieu +in");  $finish; end
        if (!$value$plusargs("out=%s", fout)) begin $display("thieu +out"); $finish; end
        have_exp = $value$plusargs("exp=%s", fexp);
        if ($value$plusargs("vcd=%s", fvcd)) begin
            $dumpfile(fvcd);
            $dumpvars(0, tb_top);
        end
        $readmemh(fin, img);
        if (have_exp) $readmemh(fexp, ref_img);
        repeat (4) @(posedge clk);
        rst_n <= 1;
        // Chờ đủ pixel ra hoặc hết thời gian
        n = 0;
        while (last_out < 0 && n < 50 * NIN / B + 100000) begin
            @(posedge clk);
            n = n + 1;
        end
        repeat (20) @(posedge clk);   // chờ thêm để bắt pixel thừa nếu có
        fd = $fopen(fout, "w");
        for (k = 0; k < NOUT; k = k + 1) $fdisplay(fd, "%02x", res[k]);
        $fclose(fd);
        $display("RESULT P=%0d W=%0d H=%0d F=%0d B=%0d stall=%0d ops=%0d first_in=%0d first_out=%0d last_out=%0d nout=%0d extra=%0d sc_err=%0d have_exp=%0d latency=%0d total=%0d",
                 P, W, H, F, B, STALL, OPS, first_in, first_out, last_out, nout, extra, sc_err, have_exp,
                 first_out - first_in, last_out - first_in + 1);
        $finish;
    end
endmodule
