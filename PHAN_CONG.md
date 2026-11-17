# Phân công nhóm

Repo này chứa toàn bộ mã nguồn của đồ án. Nhóm có dùng AI hỗ trợ; điều kiện của thầy là mỗi người giải thích được phần mình khi thuyết trình và vấn đáp. Vì vậy mỗi thành viên nhận một vai, đọc hiểu phần của vai mình, chạy lại, thử vài thông số, rồi đưa phần đó vào repo mới của nhóm.

## Cách làm cho mỗi vai

1. Clone repo này về máy.
2. Đọc các file thuộc vai mình (bảng bên dưới) và tự giải thích được chúng.
3. Chạy các lệnh của vai mình, thử thêm vài thông số nếu muốn (không bắt buộc sửa mã).
4. Đưa phần của vai mình vào repo mới, mỗi vai một thư mục:

```
vai_1_lane/        các file của vai, README.md, ket_qua_chay.md
vai_2_datapath/    các file của vai, README.md, ket_qua_chay.md
vai_3_kiem_chung/  các file của vai, README.md, ket_qua_chay.md
vai_4_hieu_nang/   các file của vai, README.md, ket_qua_chay.md
```

- `README.md` của vai: vai trò, danh sách file, và 5 điều mình giải thích được về phần đó.
- `ket_qua_chay.md`: lệnh đã chạy, kết quả in ra, nhận xét ngắn. Ghi cả thông số đã thử nếu có.

## Bảng phân công

| Vai | File phụ trách | Cần giải thích được | Chạy và thử |
| --- | --- | --- | --- |
| **1. Lane và số học** | `rtl/simd_lane.v`, `rtl/pipe_reg.v`, `tb/tb_lane.v` | Cây cộng 4 tầng, độ rộng 9 đến 12 bit, chia 9 bằng nhân 7282 rồi dịch, pipeline 5 stage | `python scripts/test_lane.py`. Thử đổi hằng số 7282 thành 7281 trong một bản sao rồi chạy lại để thấy testbench báo lỗi |
| **2. Datapath và mảng SIMD** | `rtl/line_buffer.v`, `rtl/window_3x3.v`, `rtl/controller.v`, `rtl/simd_array.v`, `rtl/top.v` | Bộ đệm hai dòng, cửa sổ P+2 cột, tín hiệu hợp lệ, mô hình ⌈W·H/P⌉ + 6 và độ trễ L_P | `scripts/thu_tham_so.py` với P = 1, 2, 4, 8 và vài kích thước ảnh, so độ trễ và tổng chu kỳ với công thức. Xem dạng sóng bằng GTKWave |
| **3. Kiểm chứng và dữ liệu** | `tb/tb_top.v`, `scripts/simd_sim.py`, `scripts/run_experiments.py` (d, v, m) | Mô hình tham chiếu, hai bộ so sánh độc lập, ảnh thử, nguồn ngắt quãng, chèn lỗi | `python scripts/run_experiments.py d v m`. Thử xác suất ngắt 10%, 50%, 90% bằng `thu_tham_so.py --stall` |
| **4. Hiệu năng và tổng hợp** | `scripts/run_experiments.py` (ac, e), `scripts/make_figures.py`, `bao_cao.md` | Thời gian = số pixel × chu kỳ/pixel × chu kỳ xung nhịp, speedup, Amdahl, giới hạn tốc độ cấp dữ liệu | `python scripts/run_experiments.py ac e`, rồi `python scripts/make_figures.py`. Thử các giá trị B khác nhau bằng `thu_tham_so.py --b` |

## Thử thông số

Script `scripts/thu_tham_so.py` chạy mô phỏng với kích thước ảnh, số lane, tốc độ cấp dữ liệu và xác suất ngắt quãng tùy chọn, rồi in số pixel sai, độ trễ và tổng chu kỳ đo được, kèm giá trị theo công thức. Chạy ở thư mục gốc của repo.

```bash
python scripts/thu_tham_so.py --w 32 --h 16 --p 1 2 4 8
```

Cấp ít pixel hơn số lane (B = 2 với 4 lane), và nguồn ngắt quãng 30%:

```bash
python scripts/thu_tham_so.py --w 32 --h 16 --p 4 --b 2
```

```bash
python scripts/thu_tham_so.py --w 32 --h 16 --p 4 --stall 30
```

Khi cấp thiếu hoặc ngắt quãng, cột công thức không còn áp dụng. Chiều rộng không chia hết cho số lane thì script bỏ qua cấu hình đó.

## Việc chung cả nhóm

- Chốt vai cho mục 1.4 và 2.1 của báo cáo (chưa có người phụ trách trong Phụ lục C).
- Điền họ tên ở Phụ lục C khi nhóm sẵn sàng.
- Đọc chéo: mỗi người đọc phần của người kế tiếp và hỏi một câu.
