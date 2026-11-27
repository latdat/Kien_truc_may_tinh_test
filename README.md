# Bộ tăng tốc SIMD đa lane cho lọc ảnh 3×3: trung bình và Gaussian (Verilog)

Đồ án nhóm môn MI4344 – Kiến trúc máy tính, Khoa Toán-Tin, Đại học Bách khoa Hà Nội.

Kho mã này chứa mã Verilog của bộ lọc ảnh 3×3 theo kiểu SIMD với P lane, gồm lọc trung bình và lọc Gaussian (nhân 1-2-1 / 2-4-2 / 1-2-1, chia 16) chọn lúc chạy bằng tín hiệu `op_mode`, ảnh chuẩn lấy từ thư viện SciPy (`scipy.signal.convolve2d`), testbench tự kiểm, các script chạy thí nghiệm, kết quả đo và báo cáo. Mỗi lane là một pipeline 5 stage; hệ thống nhận P pixel mỗi chu kỳ và cho ra P pixel đã lọc khi pipeline đã đầy.

## Kết quả chính

Mọi số liệu đo bằng mô phỏng Icarus Verilog ở cùng chu kỳ xung nhịp, ảnh 256×256 (chi tiết trong báo cáo `Do_an_SIMD_Verilog.pdf` và `results/tables.md`).

| Số lane | Throughput ổn định (pixel/chu kỳ) | Tổng chu kỳ | Speedup so với 1 lane |
| --- | --- | --- | --- |
| 1 | 0,992 | 65.542 | 1,000 |
| 2 | 1,984 | 32.774 | 2,000 |
| 4 | 3,969 | 16.390 | 3,999 |

- Không có pixel sai nào so với ảnh chuẩn SciPy ở mọi ảnh thử và mọi cấu hình lane đã kiểm tra.
- Tổng số chu kỳ khớp công thức ⌈W·H/P⌉ + 6, trong đó 6 là độ sâu pipeline.
- Nếu nguồn chỉ cấp B < P pixel mỗi chu kỳ thì throughput chỉ xấp xỉ B·(W−2)/W, thêm lane vượt quá B không giúp gì.
- Chưa có số đo chu kỳ xung nhịp của mạch thật; mọi so sánh hiệu năng là theo số chu kỳ mô phỏng.
- Báo cáo còn có phần thử trên ảnh radar Sentinel-1 thật. Ảnh và script chuẩn bị ảnh không nằm trong kho này; nếu không có thư mục `data/` thì `run_experiments.py` tự bỏ qua các ca ảnh thật.

## Cấu trúc thư mục

| Đường dẫn | Nội dung |
| --- | --- |
| `rtl/` | 8 module Verilog: `top`, `line_buffer`, `window_3x3`, `controller`, `simd_array`, `simd_lane` (lọc trung bình), `gauss_lane` (lọc Gaussian), `pipe_reg` |
| `tb/` | `tb_lane.v` (kiểm lane lọc trung bình), `tb_gauss.v` (kiểm lane Gaussian) và `tb_top.v` (kiểm toàn hệ thống, tự so với ảnh chuẩn) |
| `scripts/` | `simd_sim.py` (ảnh chuẩn SciPy và trình chạy mô phỏng), `run_experiments.py`, `thu_tham_so.py`, `demo_dau_vao.py` |
| `demo/` | Demo hệ thống bằng Icarus Verilog thuần: `in_8x8.hex`, `exp_8x8.hex` (do SciPy tính sẵn) và `filelist.f` (danh sách file RTL và `tb_top.v`) |
| `results/` | Kết quả thô (`exp_*.json`) và các bảng đã sinh (`tables.md`) |
| `Do_an_SIMD_Verilog.pdf` | Báo cáo |

Module `top` có ba tham số: `P` (số lane), `W` và `H` (kích thước ảnh), với `W` chia hết cho `P`. Đầu vào `in_pixels` rộng 8·P bit, mỗi chu kỳ có `in_valid = 1` là một từ gồm P pixel liên tiếp của một dòng ảnh. Đầu vào `op_mode` (1 bit, đi kèm từng từ) chọn phép lọc cho từ đó: 0 lọc trung bình, 1 lọc Gaussian; chỉ nên đổi giữa các khung ảnh, không đổi giữa một khung. Đầu ra `out_valid[s]` báo lane `s` có pixel hợp lệ; ảnh ra có kích thước (W−2)×(H−2) theo thứ tự từng dòng.

## Yêu cầu

- [Icarus Verilog](https://steveicarus.github.io/iverilog/) có `iverilog` và `vvp` trong `PATH`. Nhóm đã chạy với bản 14.0 (devel) trên Windows 11, các bản khác chưa thử.
- Python với NumPy và SciPy. Nhóm đã chạy với Python 3.12.9, NumPy 2.3.4 và SciPy 1.16.2.
- Trên Linux hoặc macOS, dùng `python3` thay cho `python` trong các lệnh dưới đây nếu máy không có lệnh `python`.

Cài thư viện Python:

```bash
pip install -r requirements.txt
```

Trên Ubuntu hoặc Debian, cài Icarus Verilog bằng:

```bash
sudo apt install iverilog
```

## Bắt đầu nhanh

Chạy tất cả lệnh ở thư mục gốc của kho mã.

```bash
git clone https://github.com/latdat/Kien_truc_may_tinh_test.git
cd Kien_truc_may_tinh_test
pip install -r requirements.txt
```

Tạo thư mục `build/` một lần (thư mục này không nằm trong kho; các script Python tự tạo, nhưng lệnh `iverilog -o build/...` gõ trực tiếp thì không):

```bash
mkdir build
```

Chạy thẳng Icarus Verilog cho lane lọc trung bình, không cần Python; testbench duyệt toàn bộ 2296 giá trị tổng (kết quả mong đợi `LANE_TEST sums=2296 checked=2296 errors=0`):

```bash
iverilog -g2012 -o build/lane.vvp rtl/pipe_reg.v rtl/simd_lane.v tb/tb_lane.v
vvp build/lane.vvp
```

Lane Gaussian kiểm từng vị trí pixel, ca toàn 255 và 4096 vector ngẫu nhiên (kết quả mong đợi `GAUSS_TEST cases=6401 checked=6401 errors=0`):

```bash
iverilog -g2012 -o build/gauss.vvp rtl/pipe_reg.v rtl/gauss_lane.v tb/tb_gauss.v
vvp build/gauss.vvp
```

Demo toàn hệ thống chỉ bằng Icarus Verilog (không cần Python): ảnh 8×8 có một pixel 255, hai khung liên tiếp, 4 lane; `OPS=2` nghĩa là khung 1 lọc trung bình, khung 2 lọc Gaussian. Hai file `.hex` trong `demo/` đã tạo sẵn (ảnh chuẩn do `simd_sim.golden` tính bằng SciPy), nên lúc chạy không dùng Python:

```bash
iverilog -g2012 "-Ptb_top.P=4" "-Ptb_top.W=8" "-Ptb_top.H=8" "-Ptb_top.F=2" "-Ptb_top.OPS=2" -c demo/filelist.f -o build/demo.vvp
vvp build/demo.vvp +in=demo/in_8x8.hex +out=build/demo_out.hex +exp=demo/exp_8x8.hex
```

Trong Windows PowerShell phải để các tham số `-P` trong ngoặc kép như trên (không có ngoặc kép, PowerShell tách dấu chấm và `iverilog` báo lỗi); bash và CMD chạy được cả hai cách.

Kết quả mong đợi ở dòng `RESULT`: `nout=72 extra=0 sc_err=0 latency=10 total=38`. Nếu có dòng `ERROR` về `$readmemh` thì sai đường dẫn file, khi đó đừng đọc `sc_err`. So pixel ra với file mong đợi: `fc.exe build\demo_out.hex demo\exp_8x8.hex` (PowerShell; trong bash dùng `diff`), kết quả `no differences encountered`. Thêm `+vcd=build/demo.vcd` vào lệnh `vvp` nếu muốn xem dạng sóng bằng GTKWave.

Thử với kích thước ảnh, số lane, tốc độ cấp dữ liệu hoặc xác suất ngắt quãng tùy chọn (script Python gọi `iverilog`/`vvp` và so với ảnh chuẩn SciPy):

```bash
python scripts/thu_tham_so.py --w 32 --h 16 --p 1 2 4
python scripts/thu_tham_so.py --w 32 --h 16 --p 4 --b 2
python scripts/thu_tham_so.py --w 32 --h 16 --p 4 --stall 30
python scripts/thu_tham_so.py --w 32 --h 16 --p 4 --op 1
```

Nạp bốn đầu vào chọn tay và so với giá trị tính nhẩm (thêm `--op 1` cho lọc Gaussian):

```bash
python scripts/demo_dau_vao.py
python scripts/demo_dau_vao.py --op 1
```

Khi cấp thiếu hoặc ngắt quãng, cột công thức không còn áp dụng. Chiều rộng không chia hết cho số lane thì script bỏ qua cấu hình đó.

## Chạy lại các thí nghiệm

`run_experiments.py` ghi kết quả vào `results/*.json`; không đối số thì chạy tất cả. Các tên thí nghiệm: `d` (đúng đắn), `ac` (số lane và kích thước ảnh), `e` (giới hạn cấp dữ liệu), `v` (nguồn ngắt quãng, nhiều khung), `m` (phép thử đối chứng, chèn 10 lỗi vào bản sao mã), `g` (ca biên: ảnh rất nhỏ, W = P, ảnh không có pixel ra), `ga` (lọc Gaussian, kể cả đổi chế độ giữa các khung).

```bash
python scripts/run_experiments.py
python scripts/run_experiments.py ac e
```

## Hạn chế

- Chỉ mô phỏng ở mức Verilog, chưa có số đo chu kỳ xung nhịp hay tài nguyên của mạch thật.
- Chỉ có hai phép lọc 3×3 (trung bình và Gaussian); hai khối tính luôn cùng chạy trong mỗi lane (số bộ cộng 16·P) và `op_mode` chỉ chọn đầu ra.
- Chiều rộng ảnh phải chia hết cho số lane.

## Giấy phép

Mã nguồn và tài liệu trong kho này dùng giấy phép MIT, xem file `LICENSE`.
