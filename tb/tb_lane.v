// Kiểm tra một lane: duyệt toàn bộ 2296 giá trị tổng (0..2295), so với floor(sum / 9).
`timescale 1ns/1ps
module tb_lane;
    reg         clk = 0;
    reg         rst_n = 0;
    reg  [71:0] pix;
    reg         vin;
    wire [7:0]  y;
    wire        vout;

    simd_lane dut (.clk(clk), .rst_n(rst_n), .pix(pix), .vin(vin), .y(y), .vout(vout));

    always #5 clk = ~clk;

    integer x, k, rem, errors, checked, head, tail;
    integer exp_q [0:4095];

    // Phân rã tổng x thành 9 pixel: lần lượt gán min(255, phần còn lại)
    function [71:0] split;
        input integer total;
        integer i, left, v;
        begin
            left = total;
            split = 72'd0;
            for (i = 0; i < 9; i = i + 1) begin
                v = (left > 255) ? 255 : left;
                split[8*i +: 8] = v[7:0];
                left = left - v;
            end
        end
    endfunction

    initial begin
        errors = 0; checked = 0; head = 0; tail = 0;
        vin = 0; pix = 0;
        repeat (3) @(posedge clk);
        rst_n <= 1;
        for (x = 0; x <= 2295; x = x + 1) begin
            @(posedge clk);
            vin <= 1;
            pix <= split(x);
            exp_q[tail] = x / 9;
            tail = tail + 1;
        end
        @(posedge clk);
        vin <= 0;
        repeat (10) @(posedge clk);
        $display("LANE_TEST sums=2296 checked=%0d errors=%0d", checked, errors);
        $finish;
    end

    always @(posedge clk) begin
        if (vout) begin
            if (y !== exp_q[head][7:0]) begin
                errors = errors + 1;
                $display("MISMATCH idx=%0d y=%0d exp=%0d", head, y, exp_q[head]);
            end
            checked = checked + 1;
            head = head + 1;
        end
    end
endmodule
