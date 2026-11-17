"""Hình minh họa cho demo: dạng sóng pipeline (từ VCD của mô phỏng thật) và ảnh vào / ảnh ra RTL / sai khác."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import simd_sim as S

FIG = S.ROOT / "figures"
FIG.mkdir(exist_ok=True)
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e3e2de"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({"font.size": 10, "text.color": INK, "axes.edgecolor": GRID})

PERIOD = 10   # ns, khớp tb_top.v


def parse_vcd(path):
    """Đọc VCD, trả về {tên đầy đủ: [(thời điểm, giá trị chuỗi bit), ...]}."""
    ids, scope, sigs = {}, [], {}
    t = 0
    with open(path, encoding="utf-8") as f:
        in_defs = True
        for line in f:
            tok = line.split()
            if not tok:
                continue
            if in_defs:
                if tok[0] == "$scope":
                    scope.append(tok[2])
                elif tok[0] == "$upscope":
                    scope.pop()
                elif tok[0] == "$var":
                    name = ".".join(scope + [tok[4]])
                    ids.setdefault(tok[3], []).append(name)
                    sigs[name] = [(0, "x")]
                elif tok[0] == "$enddefinitions":
                    in_defs = False
                continue
            if tok[0].startswith("#"):
                t = int(tok[0][1:])
            elif tok[0][0] == "b":
                for n in ids.get(tok[1], []):
                    sigs[n].append((t, tok[0][1:]))
            elif tok[0][0] in "01xzXZ" and len(tok[0]) > 1:
                for n in ids.get(tok[0][1:], []):
                    sigs[n].append((t, tok[0][0]))
    return sigs


def value_at(series, t):
    v = "x"
    for ts, val in series:
        if ts <= t:
            v = val
        else:
            break
    return v


def waveform():
    """Ảnh 8x8, P = 4 (W/P = 2 từ mỗi dòng): theo dõi một từ đi qua cửa sổ và 5 stage của lane 2."""
    p, w, h = 4, 8, 8
    img = S.make_image("noise", w, h)
    vcd = S.BUILD / "wave.vcd"
    S.BUILD.mkdir(exist_ok=True)
    _, st = S.simulate(img, p, tag="wave", vcd=str(vcd))
    sg = parse_vcd(vcd)
    # Thời điểm lấy mẫu: ngay trước mỗi cạnh lên (cạnh lên ở 5, 15, 25, ... ns), nên giá trị là của chu kỳ trước đó
    first_edge = 5 + PERIOD * 4  # 4 cạnh reset đầu tiên
    n_cyc = st["last_out"] + 3
    ts = [(first_edge + PERIOD * k - 1) * 1000 for k in range(n_cyc)]   # VCD tính bằng ps

    def bits(name, k):
        return value_at(sg[name], ts[k])

    rows = [
        ("in_valid", "tb_top.in_valid", 1),
        ("mask (cửa sổ hợp lệ)", "tb_top.dut.ctrl.mask", p),
        ("window.valid", "tb_top.dut.win.valid", p),
        ("lane 2 · stage 1", "tb_top.dut.arr.lane[2].u.st1.vout", 1),
        ("lane 2 · stage 2", "tb_top.dut.arr.lane[2].u.st2.vout", 1),
        ("lane 2 · stage 3", "tb_top.dut.arr.lane[2].u.st3.vout", 1),
        ("lane 2 · stage 4", "tb_top.dut.arr.lane[2].u.st4.vout", 1),
        ("lane 2 · stage 5", "tb_top.dut.arr.lane[2].u.st5.vout", 1),
        ("out_valid", "tb_top.out_valid", p),
    ]
    c0 = st["first_in"] - 1    # chỉ số chu kỳ (từ 0) mà pixel đầu tiên được cấp
    k_lo, k_hi = c0, min(n_cyc, c0 + 18)
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    for i, (label, name, width) in enumerate(rows):
        y = len(rows) - 1 - i
        for k in range(k_lo, k_hi):
            b = bits(name, k)
            on = any(ch == "1" for ch in b)
            x0 = k - k_lo
            ax.add_patch(plt.Rectangle((x0 + 0.04, y + 0.12), 0.92, 0.7, fc=(BLUE if on else "#f3f2ef"),
                                       ec=GRID, lw=0.6))
            if width > 1 and on:
                ax.text(x0 + 0.5, y + 0.47, b.zfill(width), ha="center", va="center", fontsize=6, color="white")
    ax.set_yticks([len(rows) - 1 - i + 0.47 for i in range(len(rows))])
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_xticks([k + 0.5 for k in range(k_hi - k_lo)])
    ax.set_xticklabels([str(k) for k in range(k_hi - k_lo)], fontsize=8)
    ax.set_xlim(0, k_hi - k_lo)
    ax.set_ylim(0, len(rows))
    ax.set_xlabel("Chu kỳ tính từ pixel vào đầu tiên")
    ax.tick_params(length=0)
    for s_ in ax.spines.values():
        s_.set_visible(False)
    ax.set_title(f"P = 4, ảnh 8×8: pixel ra đầu tiên sau {st['latency']} chu kỳ "
                 f"({2 * w // p} chờ hai dòng đầu + 6 pipeline)", loc="left", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "fig_waveform.png", dpi=170)
    plt.close(fig)
    vcd.unlink()
    return st


def images():
    """Ảnh vào, ảnh ra của RTL 4 lane, ảnh chuẩn Python và sai khác cho hai loại ảnh 128x128."""
    fig, axes = plt.subplots(2, 4, figsize=(7.4, 4.0))
    for r, (kind, name) in enumerate([("speckle", "Nền nhân nhiễu"), ("checker", "Bàn cờ")]):
        img = S.make_image(kind, 128, 128)
        res, st = S.simulate(img, 4, tag="img")
        ref = S.golden(img)
        bad = S.compare(res, ref)[0]
        diff = np.abs(res.astype(int) - ref.astype(int))
        panels = [(img, f"{name}: ảnh vào"), (res, "Ảnh ra của mạch (4 lane)"),
                  (ref, "Ảnh chuẩn (Python)"), (diff, f"Sai khác: {bad} pixel sai")]
        for c, (a, title) in enumerate(panels):
            ax = axes[r, c]
            ax.imshow(a, cmap="gray", vmin=0, vmax=255)
            ax.set_title(title, fontsize=7.5, loc="left")
            ax.set_xticks([])
            ax.set_yticks([])
    fig.tight_layout()
    fig.savefig(FIG / "fig_images.png", dpi=170)
    plt.close(fig)


if __name__ == "__main__":
    print(waveform())
    images()
    print("ok")
