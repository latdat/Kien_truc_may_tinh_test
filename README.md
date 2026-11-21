# Bộ tăng tốc SIMD đa lane cho bộ lọc trung bình 3×3 (Verilog)

Đồ án nhóm môn MI4344 – Kiến trúc máy tính, Khoa Toán-Tin, Đại học Bách khoa Hà Nội.

Kho mã này chứa mã Verilog của bộ lọc trung bình 3×3 theo kiểu SIMD với P lane, mô hình tham chiếu bằng Python và NumPy, testbench tự kiểm, các script chạy thí nghiệm, kết quả đo và báo cáo. Mỗi lane là một pipeline 5 stage; hệ thống nhận P pixel mỗi chu kỳ và cho ra P pixel đã lọc khi pipeline đã đầy.

## Kết quả chính

Mọi số liệu đo bằng mô phỏng Icarus Verilog ở cùng chu kỳ xung nhịp, ảnh 256×256 (chi tiết trong báo cáo `Do_an_SIMD_Verilog.pdf` và `results/tables.md`).

| Số lane | Throughput ổn định (pixel/chu kỳ) | Tổng chu kỳ | Speedup so với 1 lane |
| --- | --- | --- | --- |
| 1 | 0,992 | 65.542 | 1,000 |
| 2 | 1,984 | 32.774 | 2,000 |
| 4 | 3,969 | 16.390 | 3,999 |

- Không có pixel sai nào so với mô hình tham chiếu ở mọi ảnh thử và mọi cấu hình lane đã kiểm tra.
- Tổng số chu kỳ khớp công thức ⌈W·H/P⌉ + 6, trong đó 6 là độ sâu pipeline.
- Nếu nguồn chỉ cấp B < P pixel mỗi chu kỳ thì throughput chỉ xấp xỉ B·(W−2)/W, thêm lane vượt quá B không giúp gì.
- Chưa có số đo chu kỳ xung nhịp của mạch thật; mọi so sánh hiệu năng là theo số chu kỳ mô phỏng.
- Báo cáo còn có phần thử trên ảnh radar Sentinel-1 thật. Ảnh và script chuẩn bị ảnh không nằm trong kho này; nếu không có thư mục `data/` thì `run_experiments.py` tự bỏ qua các ca ảnh thật.

## Cấu trúc thư mục

| Đường dẫn | Nội dung |
| --- | --- |
| `rtl/` | 7 module Verilog: `top`, `line_buffer`, `window_3x3`, `controller`, `simd_array`, `simd_lane`, `pipe_reg` |
| `tb/` | `tb_lane.v` (kiểm một lane) và `tb_top.v` (kiểm toàn hệ thống, tự so với ảnh chuẩn) |
| `scripts/` | `simd_sim.py` (mô hình tham chiếu và trình chạy mô phỏng), `test_lane.py`, `smoke.py`, `run_experiments.py`, `thu_tham_so.py` |
| `results/` | Kết quả thô (`exp_*.json`) và các bảng đã sinh (`tables.md`) |
| `Do_an_SIMD_Verilog.pdf` | Báo cáo |

Module `top` có ba tham số: `P` (số lane), `W` và `H` (kích thước ảnh), với `W` chia hết cho `P`. Đầu vào `in_pixels` rộng 8·P bit, mỗi chu kỳ có `in_valid = 1` là một từ gồm P pixel liên tiếp của một dòng ảnh. Đầu ra `out_valid[s]` báo lane `s` có pixel hợp lệ; ảnh ra có kích thước (W−2)×(H−2) theo thứ tự từng dòng.

## Yêu cầu

- [Icarus Verilog](https://steveicarus.github.io/iverilog/) có `iverilog` và `vvp` trong `PATH`. Nhóm đã chạy với bản 14.0 (devel) trên Windows 11, các bản khác chưa thử.
- Python với NumPy. Nhóm đã chạy với Python 3.12.9 và NumPy 2.3.4.
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

Kiểm riêng một lane, duyệt toàn bộ 2296 giá trị tổng (kết quả mong đợi `LANE_TEST sums=2296 checked=2296 errors=0`):

```bash
python scripts/test_lane.py
```

Chạy nhanh toàn hệ thống với ảnh nhỏ ở 1, 2 và 4 lane (mọi dòng phải có `bad=0`):

```bash
python scripts/smoke.py
```

Thử với kích thước ảnh, số lane, tốc độ cấp dữ liệu hoặc xác suất ngắt quãng tùy chọn:

```bash
python scripts/thu_tham_so.py --w 32 --h 16 --p 1 2 4
python scripts/thu_tham_so.py --w 32 --h 16 --p 4 --b 2
python scripts/thu_tham_so.py --w 32 --h 16 --p 4 --stall 30
```

Khi cấp thiếu hoặc ngắt quãng, cột công thức không còn áp dụng. Chiều rộng không chia hết cho số lane thì script bỏ qua cấu hình đó.

## Chạy lại các thí nghiệm

`run_experiments.py` ghi kết quả vào `results/*.json`; không đối số thì chạy tất cả. Các tên thí nghiệm: `d` (đúng đắn), `ac` (số lane và kích thước ảnh), `e` (giới hạn cấp dữ liệu), `v` (nguồn ngắt quãng, nhiều khung), `m` (phép thử đối chứng, chèn lỗi vào bản sao mã).

```bash
python scripts/run_experiments.py
python scripts/run_experiments.py ac e
```

## Hạn chế

- Chỉ mô phỏng ở mức Verilog, chưa có số đo chu kỳ xung nhịp hay tài nguyên của mạch thật.
- Chỉ có một bộ lọc (trung bình 3×3), và chiều rộng ảnh phải chia hết cho số lane.

## Giấy phép

Mã nguồn và tài liệu trong kho này dùng giấy phép MIT, xem file `LICENSE`.
