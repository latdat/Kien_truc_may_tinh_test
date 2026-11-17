"""Chạy thử nhanh: ảnh nhỏ 8x8 và 16x16, P = 1, 2, 4."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import simd_sim as S

for (w, h) in [(8, 8), (16, 16), (16, 8)]:
    for kind in ["gradient", "noise"]:
        img = S.make_image(kind, w, h)
        ref = S.golden(img)
        for p in [1, 2, 4]:
            res, st = S.simulate(img, p, tag="smoke")
            bad, mx, mean = S.compare(res, ref)
            print(f"{kind:9s} {w}x{h} P={p} bad={bad} max={mx} nout={st['nout']} extra={st['extra']} "
                  f"lat={st['latency']} total={st['total']}")
