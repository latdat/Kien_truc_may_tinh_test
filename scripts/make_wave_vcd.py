"""Chạy mô phỏng ảnh 8x8, 4 lane và ghi dạng sóng build/wave_p4.vcd để mở bằng GTKWave:
    gtkwave build/wave_p4.vcd scripts/gtkwave/wave.gtkw -S scripts/gtkwave/wave.tcl"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import simd_sim as S

S.BUILD.mkdir(exist_ok=True)
img = S.make_image("noise", 8, 8)
res, st = S.simulate(img, 4, tag="wave_gui", vcd=str(S.BUILD / "wave_p4.vcd"))
print("da ghi build/wave_p4.vcd; do tre =", st["latency"], "chu ky, tong =", st["total"], "chu ky")
