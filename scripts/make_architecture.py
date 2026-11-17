"""Sơ đồ khối kiến trúc: line buffer, cửa sổ 3x3, mảng P lane. Ghi figures/fig_architecture.png."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

FIG = Path(__file__).resolve().parent.parent / "figures"
FIG.mkdir(exist_ok=True)
MUTED, BLUE, ORANGE = "#52514e", "#2a78d6", "#eb6834"

fig, ax = plt.subplots(figsize=(7.6, 3.6))
ax.set_xlim(0, 10.2)
ax.set_ylim(0, 4.2)
ax.axis("off")


def box(x, y, w, h, text, fc="#e8eef5", ec=BLUE, fs=9.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=1.6))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)


def arrow(x0, y0, x1, y1, label=None, dy=0.1, ha="center"):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.3))
    if label:
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + dy, label, ha=ha, va="bottom", fontsize=8.5, color=MUTED)


box(0.1, 1.6, 1.5, 0.9, "in_pixels\n(8P bit mỗi\nchu kỳ)", fc="#f3f2ef", ec=MUTED)
box(2.3, 3.0, 1.6, 0.7, "line_buffer 1\n(trễ 1 dòng)")
box(2.3, 1.95, 1.6, 0.7, "line_buffer 2\n(trễ 1 dòng)")
box(5.0, 1.1, 2.0, 2.6, "window_3x3\n3 dòng × (P+2) cột\n(thanh ghi)")
box(7.7, 1.1, 2.1, 2.6, "simd_array\nP × simd_lane\n(5 stage pipeline)", fc="#fbeadf", ec=ORANGE)
box(5.0, 0.1, 2.0, 0.6, "controller", fc="#f3f2ef", ec=MUTED)
ax.text(8.75, 0.55, "chỉ phần này\nnhân bản P lần", ha="center", va="center", fontsize=8.5, color=ORANGE)

arrow(1.6, 2.2, 2.3, 3.3)
arrow(3.1, 3.0, 3.1, 2.65)
arrow(3.9, 3.35, 5.0, 3.35, "dòng r−1")
arrow(3.9, 2.3, 5.0, 2.3, "dòng r−2")
ax.plot([0.85, 0.85, 4.6], [1.6, 1.3, 1.3], color=MUTED, lw=1.3)
arrow(4.6, 1.3, 5.0, 1.3)
ax.text(2.7, 1.36, "dòng r", ha="center", va="bottom", fontsize=8.5, color=MUTED)
arrow(7.0, 2.4, 7.7, 2.4, "P cửa sổ")
arrow(9.8, 2.4, 10.1, 2.4)
ax.text(9.8, 3.95, "out_pixels (8P bit), out_valid[P]", ha="right", va="center", fontsize=8.5, color=MUTED)
arrow(0.1, 0.4, 5.0, 0.4, "in_valid", dy=0.04)
arrow(6.0, 0.7, 6.0, 1.1, "mask[P]", dy=-0.05, ha="left")
fig.tight_layout()
fig.savefig(FIG / "fig_architecture.png", dpi=170)
print("ok")
