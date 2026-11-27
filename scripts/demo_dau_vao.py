"""Demo trực tiếp: nạp đầu vào chọn tay vào mạch (mô phỏng Icarus Verilog) và in giá trị mong đợi
cạnh đầu ra của mạch. Giá trị mong đợi tính tay, ghi sẵn trong mã, và được đối chiếu thêm với ảnh chuẩn SciPy.

Ví dụ:
    python scripts/demo_dau_vao.py              # lọc trung bình, mỗi ca dùng P = 4 nếu W chia hết cho 4, ngược lại P = 1
    python scripts/demo_dau_vao.py --op 1       # lọc Gaussian [1 2 1; 2 4 2; 1 2 1] / 16
    python scripts/demo_dau_vao.py --p 2
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import simd_sim as S

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--p", type=int, default=4, help="số lane (dùng P = 1 nếu W không chia hết)")
ap.add_argument("--op", type=int, default=0, choices=[0, 1], help="phép lọc: 0 trung bình 3x3, 1 Gaussian 3x3")
args = ap.parse_args()


def grid(a):
    return "\n".join("    " + " ".join(f"{v:3d}" for v in row) for row in a)


one = np.zeros((8, 8), dtype=np.uint8)
one[3, 3] = 255
cases = []
if args.op == 0:
    # Lọc trung bình. 1. Cửa sổ 1..9: tổng 45, 45 / 9 = 5
    cases.append(("Cua so 3x3 gia tri 1..9 (tong 45)", np.arange(1, 10, dtype=np.uint8).reshape(3, 3),
                  np.array([[5]], dtype=np.uint8)))
    # 2. Một pixel 255 lẻ loi trên nền 0: mọi cửa sổ chứa nó có tổng 255, 255 / 9 = 28 (phần nguyên)
    exp = np.zeros((6, 6), dtype=np.uint8)
    exp[1:4, 1:4] = 28   # pixel ra (i, j) phủ dòng i..i+2, cột j..j+2 của ảnh vào
    cases.append(("Mot pixel 255 o (3,3) tren nen 0", one, exp))
else:
    # Lọc Gaussian, trọng số góc 1, cạnh 2, tâm 4, chia 16.
    # 1. Cửa sổ 1..9: 1+4+3 + 8+20+12 + 7+16+9 = 80, 80 / 16 = 5
    cases.append(("Cua so 3x3 gia tri 1..9 (tong co trong so 80)", np.arange(1, 10, dtype=np.uint8).reshape(3, 3),
                  np.array([[5]], dtype=np.uint8)))
    # 2. Một pixel 255: ở tâm cửa sổ nhận trọng số 4 -> 1020/16 = 63; ở cạnh trọng số 2 -> 510/16 = 31; ở góc 1 -> 255/16 = 15
    exp = np.zeros((6, 6), dtype=np.uint8)
    exp[1:4, 1:4] = np.array([[15, 31, 15], [31, 63, 31], [15, 31, 15]], dtype=np.uint8)
    cases.append(("Mot pixel 255 o (3,3) tren nen 0 (trong so 1, 2, 4)", one, exp))
# 3, 4. Toàn 0 và toàn 255 (tổng lớn nhất: 9 * 255 = 2295 cho trung bình, 16 * 255 = 4080 cho Gaussian)
cases.append(("Toan 0", np.zeros((8, 8), dtype=np.uint8), np.zeros((6, 6), dtype=np.uint8)))
cases.append(("Toan 255 (tong lon nhat)", np.full((8, 8), 255, dtype=np.uint8), np.full((6, 6), 255, dtype=np.uint8)))

print("Phep loc:", "Gaussian 3x3 [1 2 1; 2 4 2; 1 2 1] / 16" if args.op else "trung binh 3x3 (tong 9 pixel / 9)")
fail = 0
for i, (name, img, exp) in enumerate(cases, 1):
    h, w = img.shape
    p = args.p if w % args.p == 0 else 1
    assert np.array_equal(S.golden(img, args.op), exp), "gia tri tinh tay lech anh chuan"
    out, st = S.simulate(img, p, tag="demo", op=args.op)
    ok = np.array_equal(out, exp) and st["extra"] == 0 and st["nout"] == exp.size
    fail += not ok
    print(f"=== Ca {i}: {name}  (anh {w}x{h}, P={p})")
    print("  Dau vao:")
    print(grid(img))
    print("  Mong doi (tinh tay):")
    print(grid(exp))
    print("  Dau ra cua mach:")
    print(grid(out))
    print(f"  nout={st['nout']} extra={st['extra']} sc_err={st['sc_err']} do_tre={st['latency']} "
          f"tong_chu_ky={st['total']}  ->  {'DAT' if ok else 'SAI'}\n")

print("KET QUA:", "DAT ca 4 ca" if not fail else f"{fail} ca SAI")
sys.exit(1 if fail else 0)
