"""Chạy thử bộ lọc với kích thước ảnh, số lane, tốc độ cấp dữ liệu và xác suất ngắt quãng tùy chọn.
In số pixel sai so với mô hình tham chiếu, độ trễ và tổng chu kỳ đo được, kèm giá trị theo công thức.

Ví dụ:
    python scripts/thu_tham_so.py --w 32 --h 16 --p 1 2 4 8
    python scripts/thu_tham_so.py --w 64 --h 64 --p 4 --b 2
    python scripts/thu_tham_so.py --w 64 --h 64 --p 4 --stall 30
    python scripts/thu_tham_so.py --w 64 --h 64 --p 4 --op 1      # lọc Gaussian 3x3
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import simd_sim as S

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--w", type=int, default=32, help="chiều rộng ảnh, chia hết cho số lane")
ap.add_argument("--h", type=int, default=16, help="chiều cao ảnh")
ap.add_argument("--p", type=int, nargs="+", default=[1, 2, 4], help="danh sách số lane")
ap.add_argument("--b", type=int, default=None, help="số pixel cấp mỗi chu kỳ (mặc định bằng số lane)")
ap.add_argument("--stall", type=int, default=0, help="xác suất %% mỗi chu kỳ nguồn bị ngắt quãng")
ap.add_argument("--image", default="noise", help="gradient, checker, noise, zero, full hoặc speckle")
ap.add_argument("--op", type=int, default=0, choices=[0, 1], help="phép lọc: 0 trung bình 3x3, 1 Gaussian 3x3")
args = ap.parse_args()

img = S.make_image(args.image, args.w, args.h)
ref = S.golden(img, args.op)
print(f"anh {args.image} {args.w}x{args.h}, b={args.b or 'P'}, stall={args.stall}%, loc={'Gaussian' if args.op else 'trung binh'}")
print("  P  bad  do_tre  tong_chu_ky  (cong_thuc: do_tre, tong; chi dung khi b=P, stall=0)")
for p in args.p:
    if args.w % p:
        print(f"{p:3d}  bo qua: W={args.w} khong chia het cho P={p}")
        continue
    res, st = S.simulate(img, p, b=args.b, stall=args.stall, op=args.op)
    bad = S.compare(res, ref)[0]
    lat = 2 * args.w // p + (math.ceil(3 / p) - 1) + 6
    tot = math.ceil(args.w * args.h / p) + 6
    print(f"{p:3d} {bad:4d} {st['latency']:7d} {st['total']:12d}  ({lat}, {tot})")
