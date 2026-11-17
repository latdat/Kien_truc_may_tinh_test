### 5.1 Correctness

| Ảnh thử | Số lane | Số pixel kiểm tra | Số pixel sai | Sai số tuyệt đối lớn nhất | Sai số trung bình |
| --- | --- | --- | --- | --- | --- |
| Giả lập | 1 | 85.392 | 0 | 0 | 0,0 |
| Giả lập | 2 | 85.392 | 0 | 0 | 0,0 |
| Giả lập | 4 | 85.392 | 0 | 0 | 0,0 |
| Ảnh nền nhân nhiễu (mô phỏng) | 1 | 68.360 | 0 | 0 | 0,0 |
| Ảnh nền nhân nhiễu (mô phỏng) | 2 | 68.360 | 0 | 0 | 0,0 |
| Ảnh nền nhân nhiễu (mô phỏng) | 4 | 68.360 | 0 | 0 | 0,0 |

### 5.1b Từng ảnh

| Ảnh | Kích thước | Số pixel ra | Số pixel sai (1 / 2 / 4 lane) | Pixel thừa |
| --- | --- | --- | --- | --- |
| gradient | 64×64 | 3.844 | 0 / 0 / 0 | 0 |
| checker | 64×64 | 3.844 | 0 / 0 / 0 | 0 |
| noise | 64×64 | 3.844 | 0 / 0 / 0 | 0 |
| zero | 64×64 | 3.844 | 0 / 0 / 0 | 0 |
| full | 64×64 | 3.844 | 0 / 0 / 0 | 0 |
| noise | 256×256 | 64.516 | 0 / 0 / 0 | 0 |
| gradient | 48×20 | 828 | 0 / 0 / 0 | 0 |
| noise | 48×20 | 828 | 0 / 0 / 0 | 0 |
| nền nhân nhiễu | 64×64 | 3.844 | 0 / 0 / 0 | 0 |
| nền nhân nhiễu | 256×256 | 64.516 | 0 / 0 / 0 | 0 |

### 5.2 Hiệu năng (256×256)

| Số lane | Độ trễ (chu kỳ) | Tổng chu kỳ | Mô hình ⌈WH/P⌉+6 | Pixel/chu kỳ (ổn định) | Chu kỳ/pixel | Speedup thực tế | Speedup lý tưởng | Hiệu suất song song |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 520 | 65.542 | 65.542 | 0,992 | 1,0159 | 1,000 | 1 | 100,00% |
| 2 | 263 | 32.774 | 32.774 | 1,984 | 0,5080 | 2,000 | 2 | 99,99% |
| 4 | 134 | 16.390 | 16.390 | 3,969 | 0,2540 | 3,999 | 4 | 99,97% |

### 5.3 Kích thước ảnh

| Kích thước ảnh | Chu kỳ (1 lane) | Chu kỳ (2 lane) | Chu kỳ (4 lane) | Chu kỳ/pixel (1 lane) | Chu kỳ/pixel (2 lane) | Chu kỳ/pixel (4 lane) |
| --- | --- | --- | --- | --- | --- | --- |
| 64×64 | 4.102 | 2.054 | 1.030 | 1,0671 | 0,5343 | 0,2680 |
| 256×256 | 65.542 | 32.774 | 16.390 | 1,0159 | 0,5080 | 0,2540 |
| 512×512 | 262.150 | 131.078 | 65.542 | 1,0079 | 0,5040 | 0,2520 |
| 1024×1024 | 1.048.582 | 524.294 | 262.150 | 1,0039 | 0,5020 | 0,2510 |

| Kích thước ảnh | 2 lane | 4 lane |
| --- | --- | --- |
| 64×64 | 1,997 | 3,983 |
| 256×256 | 2,000 | 3,999 |
| 512×512 | 2,000 | 4,000 |
| 1024×1024 | 2,000 | 4,000 |

### 5.4 Giới hạn băng thông vào (256×256)

| Số lane P | Pixel cấp mỗi chu kỳ B | Tổng chu kỳ | Pixel/chu kỳ (ổn định) | Số pixel sai |
| --- | --- | --- | --- | --- |
| 2 | 1 | 65.541 | 0,992 | 0 |
| 2 | 2 | 32.774 | 1,984 | 0 |
| 4 | 1 | 65.539 | 0,992 | 0 |
| 4 | 2 | 32.773 | 1,984 | 0 |
| 4 | 3 | 21.851 | 2,977 | 0 |
| 4 | 4 | 16.390 | 3,969 | 0 |

### 5.7 Kiểm chứng mở rộng

Ngắt quãng ngẫu nhiên: mỗi chu kỳ, bộ cấp dữ liệu bị ngắt với xác suất cho trước (ảnh nhiễu ngẫu nhiên và ảnh nền nhân nhiễu 64×64, chạy qua testbench tự kiểm).

| Điều kiện | Số lane | Số lần chạy | Pixel kiểm tra | Pixel sai (Python) | Lỗi tự kiểm (testbench) | Pixel/chu kỳ (số pixel ra / tổng chu kỳ) |
| --- | --- | --- | --- | --- | --- | --- |
| Ngắt quãng, 30% | 1 | 2 | 7.688 | 0 | 0 | 0,67 |
| Ngắt quãng, 70% | 1 | 2 | 7.688 | 0 | 0 | 0,29 |
| Ngắt quãng, 30% | 2 | 2 | 7.688 | 0 | 0 | 1,34 |
| Ngắt quãng, 70% | 2 | 2 | 7.688 | 0 | 0 | 0,58 |
| Ngắt quãng, 30% | 4 | 2 | 7.688 | 0 | 0 | 2,64 |
| Ngắt quãng, 70% | 4 | 2 | 7.688 | 0 | 0 | 1,23 |
| B thấp và ngắt quãng, 50%, B = 2 | 4 | 1 | 7.688 | 0 | 0 | 0,95 |
| 3 khung liên tiếp, 0% | 1 | 1 | 11.532 | 0 | 0 | 0,94 |
| 3 khung liên tiếp, 50% | 1 | 1 | 11.532 | 0 | 0 | 0,47 |
| 3 khung liên tiếp, 0% | 2 | 1 | 11.532 | 0 | 0 | 1,88 |
| 3 khung liên tiếp, 50% | 2 | 1 | 11.532 | 0 | 0 | 0,95 |
| 3 khung liên tiếp, 0% | 4 | 1 | 11.532 | 0 | 0 | 3,75 |
| 3 khung liên tiếp, 50% | 4 | 1 | 11.532 | 0 | 0 | 1,92 |

### 5.7b Phép thử đối chứng

Phép thử đối chứng: chèn một lỗi vào bản sao mã Verilog (P = 4, ảnh nhiễu 32×32, 900 pixel ra). Mọi lỗi đều phải bị phát hiện.

| Lỗi chèn vào | File | Pixel sai hoặc lệch số lượng (Python) | Lỗi tự kiểm (testbench) | Pixel thừa |
| --- | --- | --- | --- | --- |
| Hằng số chia 7282 → 7281 | simd_lane.v | 111 | 111 | 0 |
| Mặt nạ cột: x ≥ 0 → x ≥ −1 | controller.v | lệch số lượng pixel ra | 888 | 30 |
| Mặt nạ dòng: r ≥ 2 → r ≥ 1 | controller.v | lệch số lượng pixel ra | 881 | 30 |
| Line buffer ngắn hơn 1 từ | top.v | 883 | 883 | 0 |
| Cửa sổ dịch sai một pixel | window_3x3.v | 406 | 406 | 0 |
