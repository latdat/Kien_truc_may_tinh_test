// Kiểm một lane Gaussian 3x3 (nhân [1 2 1; 2 4 2; 1 2 1] / 16), gauss_lane.v:
//  (a) từng vị trí pixel: pixel k nhận giá trị 0..255, 8 pixel còn lại bằng 0, mong đợi (v * w_k) >> 4: 9 x 256 ca;
//  (b) toàn 255: tổng có trọng số lớn nhất 16 * 255 = 4080, mong đợi 255: 1 ca;
//  (c) 4096 vector ngẫu nhiên (xorshift, hạt giống cố định), mong đợi (tổng w_k * p_k) >> 4.
// Ca (a) bắt lỗi trọng số và lỗi nối nhầm vị trí; ca (c) bắt lỗi khi nhiều pixel cùng khác 0 (cây cộng, độ rộng bit).
`timescale 1ns/1ps
module tb_gauss;
    localparam NCASE = 9 * 256 + 1 + 4096;

    reg         clk = 0;
    reg         rst_n = 0;
    reg  [71:0] pix;
    reg         vin;
    wire [7:0]  y;
    wire        vout;

    gauss_lane dut (.clk(clk), .rst_n(rst_n), .pix(pix), .vin(vin), .y(y), .vout(vout));

    always #5 clk = ~clk;

    integer k, v, i, errors, checked, head, tail, wsum;
    integer exp_q [0:8191];
    reg [31:0] rng;
    reg [71:0] vec;

    // Trọng số của pixel k trong cửa sổ: tâm (k = 4) x4, bốn cạnh (k = 1, 3, 5, 7) x2, bốn góc x1
    function integer wk;
        input integer idx;
        begin
            if (idx == 4)                                           wk = 4;
            else if (idx == 1 || idx == 3 || idx == 5 || idx == 7)  wk = 2;
            else                                                    wk = 1;
        end
    endfunction

    task send;
        input [71:0] pv;
        input integer expv;
        begin
            @(posedge clk);
            vin <= 1;
            pix <= pv;
            exp_q[tail] = expv;
            tail = tail + 1;
        end
    endtask

    task rnd32;
        begin
            rng = rng ^ (rng << 13);
            rng = rng ^ (rng >> 17);
            rng = rng ^ (rng << 5);
        end
    endtask

    initial begin
        errors = 0; checked = 0; head = 0; tail = 0;
        vin = 0; pix = 0; rng = 32'h2026ABCD;
        repeat (3) @(posedge clk);
        rst_n <= 1;

        for (k = 0; k < 9; k = k + 1)
            for (v = 0; v < 256; v = v + 1) begin
                vec = 72'd0;
                vec[8*k +: 8] = v[7:0];
                send(vec, (v * wk(k)) >> 4);
            end

        send({9{8'hFF}}, 255);

        for (i = 0; i < 4096; i = i + 1) begin
            rnd32; vec[31:0]  = rng;
            rnd32; vec[63:32] = rng;
            rnd32; vec[71:64] = rng[7:0];
            wsum = 0;
            for (k = 0; k < 9; k = k + 1) wsum = wsum + wk(k) * vec[8*k +: 8];
            send(vec, wsum >> 4);
        end

        @(posedge clk);
        vin <= 0;
        repeat (10) @(posedge clk);
        $display("GAUSS_TEST cases=%0d checked=%0d errors=%0d", NCASE, checked, errors);
        $finish;
    end

    always @(posedge clk) begin
        if (vout) begin
            if (y !== exp_q[head][7:0]) begin
                errors = errors + 1;
                if (errors <= 10) $display("MISMATCH idx=%0d y=%0d exp=%0d", head, y, exp_q[head]);
            end
            checked = checked + 1;
            head = head + 1;
        end
    end
endmodule
