// Line buffer: trễ dữ liệu đúng DEPTH từ (một dòng ảnh = W/P từ), đọc không đồng bộ.
// Khi en = 1, dout là từ đã nhận cách đây DEPTH lần en, và din được ghi thay vào chỗ đó.
module line_buffer #(
    parameter DW    = 8,
    parameter DEPTH = 64
) (
    input  wire          clk,
    input  wire          rst_n,
    input  wire          en,
    input  wire [DW-1:0] din,
    output wire [DW-1:0] dout
);
    localparam AW = (DEPTH > 1) ? $clog2(DEPTH) : 1;

    reg [DW-1:0] mem [0:DEPTH-1];
    reg [AW-1:0] ptr;
    integer i;

    initial for (i = 0; i < DEPTH; i = i + 1) mem[i] = {DW{1'b0}};

    assign dout = mem[ptr];

    always @(posedge clk) begin
        if (!rst_n) begin
            ptr <= {AW{1'b0}};
        end else if (en) begin
            mem[ptr] <= din;
            ptr      <= (ptr == DEPTH - 1) ? {AW{1'b0}} : ptr + 1'b1;
        end
    end
endmodule
