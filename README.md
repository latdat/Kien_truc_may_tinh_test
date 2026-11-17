# Bộ tăng tốc SIMD đa lane cho bộ lọc trung bình 3×3 (Verilog)

Đồ án nhóm môn MI4344 – Kiến trúc máy tính, Khoa Toán-Tin, Đại học Bách khoa Hà Nội.

Kho mã này chứa mã Verilog của bộ lọc trung bình 3×3 theo kiểu SIMD với P lane (đã chạy thử P = 1, 2, 4, 8), mô hình tham chiếu bằng Python và NumPy, testbench tự kiểm, các script chạy thí nghiệm, kết quả đo, hình vẽ và báo cáo. Mỗi lane là một pipeline 5 stage; hệ thống nhận P pixel mỗi chu kỳ và cho ra P pixel đã lọc khi pipeline đã đầy.

## Kết quả chính

Mọi số liệu đo bằng mô phỏng Icarus Verilog ở cùng chu kỳ xung nhịp, ảnh 256×256 (chi tiết trong báo cáo `Do_an_SIMD_Verilog.pdf` và `results/tables.md`).

| Số lane | Throughput ổn định (pixel/chu kỳ) | Tổng chu kỳ | Speedup so với 1 lane |
| --- | --- | --- | --- |
| 1 | 0,992 | 65.542 | 1,000 |
| 2 | 1,984 | 32.774 | 2,000 |
| 4 | 3,969 | 16.390 | 3,999 |
| 8 | 7,938 | 8.198 | 7,995 |

Báo cáo trình bày 1, 2 và 4 lane. Hàng 8 lane lấy từ `results/exp_ac.json`, là phần chạy thêm.

- Không có pixel sai nào so với mô hình tham chiếu ở mọi ảnh thử và mọi cấu hình lane đã kiểm tra.
- Tổng số chu kỳ khớp công thức ⌈W·H/P⌉ + 6, trong đó 6 là độ sâu pipeline.
- Nếu nguồn chỉ cấp B < P pixel mỗi chu kỳ thì throughput chỉ xấp xỉ B·(W−2)/W, thêm lane vượt quá B không giúp gì.
- Chưa có số đo chu kỳ xung nhịp của mạch thật; mọi so sánh hiệu năng là theo số chu kỳ mô phỏng.

## Cấu trúc thư mục

| Đường dẫn | Nội dung |
| --- | --- |
| `rtl/` | 7 module Verilog: `top`, `line_buffer`, `window_3x3`, `controller`, `simd_array`, `simd_lane`, `pipe_reg` |
| `tb/` | `tb_lane.v` (kiểm một lane) và `tb_top.v` (kiểm toàn hệ thống, tự so với ảnh chuẩn) |
| `scripts/` | Mô hình tham chiếu và trình chạy mô phỏng (`simd_sim.py`), thí nghiệm, vẽ hình, dựng báo cáo |
| `scripts/gtkwave/` | File cấu hình để xem dạng sóng bằng GTKWave |
| `results/` | Kết quả thô (`exp_*.json`) và các bảng đã sinh (`tables.md`) |
| `figures/` | Đồ thị và ảnh chụp màn hình dùng trong báo cáo |
| `bao_cao.md` | Mã nguồn báo cáo (định dạng riêng, dựng thành PDF bằng `scripts/build_thesis.py`) |
| `Do_an_SIMD_Verilog.pdf` | Báo cáo đã dựng |

Module `top` có ba tham số: `P` (số lane), `W` và `H` (kích thước ảnh), với `W` chia hết cho `P`. Đầu vào `in_pixels` rộng 8·P bit, mỗi chu kỳ có `in_valid = 1` là một từ gồm P pixel liên tiếp của một dòng ảnh. Đầu ra `out_valid[s]` báo lane `s` có pixel hợp lệ; ảnh ra có kích thước (W−2)×(H−2) theo thứ tự từng dòng.

## Yêu cầu

- [Icarus Verilog](https://steveicarus.github.io/iverilog/) có `iverilog` và `vvp` trong `PATH`. Nhóm đã chạy với bản 14.0 (devel) trên Windows 11, các bản khác chưa thử. Bản cài cho Windows kèm GTKWave.
- Python với NumPy và Matplotlib. Nhóm đã chạy với Python 3.12.9, NumPy 2.3.4 và Matplotlib 3.10.6.
- Chỉ để dựng PDF báo cáo: PyMuPDF, [pandoc](https://pandoc.org/) (nhóm dùng bản 3.10, cờ `--syntax-highlighting` cần pandoc mới) và một trình duyệt Chromium (Edge, Chrome hoặc Chromium). Đặt biến môi trường `BROWSER` nếu script không tự tìm thấy. Bước dựng PDF nhóm chỉ thử trên Windows với Edge; phông chữ và ngắt trang có thể khác trên hệ điều hành khác.
- Trên Linux hoặc macOS, dùng `python3` thay cho `python` trong các lệnh dưới đây nếu máy không có lệnh `python`.

Cài thư viện Python:

```bash
pip install -r requirements.txt
```

Trên Ubuntu hoặc Debian, cài Icarus Verilog và GTKWave bằng:

```bash
sudo apt install iverilog gtkwave
```

## Bắt đầu nhanh

Chạy tất cả lệnh ở thư mục gốc của kho mã.

```bash
git clone https://github.com/latdat/Kien_truc_may_tinh_test.git
cd Kien_truc_may_tinh_test
pip install -r requirements.txt
```

Kiểm riêng một lane, duyệt toàn bộ 2296 giá trị tổng (kết quả mong đợi `LANE_TEST sums=2296 checked=2296 errors=0`):

```bash
python scripts/test_lane.py
```

Chạy nhanh toàn hệ thống với ảnh nhỏ ở 1, 2 và 4 lane (mọi dòng phải có `bad=0`):

```bash
python scripts/smoke.py
```

Thử với kích thước ảnh, số lane, tốc độ cấp dữ liệu hoặc xác suất ngắt quãng tùy chọn (xem `PHAN_CONG.md`):

```bash
python scripts/thu_tham_so.py --w 32 --h 16 --p 1 2 4 8
```

## Chạy lại các thí nghiệm

`run_experiments.py` ghi kết quả vào `results/*.json`; không đối số thì chạy tất cả. Các tên thí nghiệm: `d` (đúng đắn), `ac` (số lane và kích thước ảnh), `e` (giới hạn cấp dữ liệu), `v` (nguồn ngắt quãng, nhiều khung), `m` (phép thử đối chứng, chèn lỗi vào bản sao mã).

```bash
python scripts/run_experiments.py
python scripts/run_experiments.py ac e
```

Vẽ lại đồ thị và bảng từ file kết quả (không cần chạy lại mô phỏng):

```bash
python scripts/make_figures.py
python scripts/make_demo.py
python scripts/make_architecture.py
```

## Xem dạng sóng

```bash
python scripts/make_wave_vcd.py
gtkwave build/wave_p4.vcd scripts/gtkwave/wave.gtkw -S scripts/gtkwave/wave.tcl
```

## Dựng báo cáo PDF

```bash
python scripts/build_thesis.py
```

Lệnh này đọc `bao_cao.md`, các bảng trong `results/tables.md` và hình trong `figures/`, rồi ghi `Do_an_SIMD_Verilog.pdf`. Cần pandoc, PyMuPDF và một trình duyệt Chromium như ở mục Yêu cầu.

## Hạn chế

- Chỉ mô phỏng ở mức Verilog, chưa có số đo chu kỳ xung nhịp hay tài nguyên của mạch thật.
- Mọi ảnh thử là ảnh mô phỏng.
- Chỉ có một bộ lọc (trung bình 3×3), và chiều rộng ảnh phải chia hết cho số lane.

## Giấy phép

Mã nguồn và tài liệu trong kho này dùng giấy phép MIT, xem file `LICENSE`.
