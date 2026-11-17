"""Đọc results/*.json, vẽ đồ thị vào figures/ và ghi các bảng markdown vào results/tables.md."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RES, FIG = ROOT / "results", ROOT / "figures"
FIG.mkdir(exist_ok=True)

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e3e2de"
COL = {1: "#2a78d6", 2: "#eb6834", 4: "#1baf7a", 8: "#eda100"}   # thứ tự cố định theo số lane
plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK, "text.color": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6})

ac = json.loads((RES / "exp_ac.json").read_text())
d = json.loads((RES / "exp_d.json").read_text())
e = json.loads((RES / "exp_e.json").read_text())
v = json.loads((RES / "exp_v.json").read_text())
m = json.loads((RES / "exp_m.json").read_text())
# Phạm vi báo cáo: chỉ 1, 2, 4 lane (8 lane vẫn nằm trong file kết quả như phần chạy thêm)
MAXP = 4
ac, d, e, v = ([r for r in x if r["p"] <= MAXP] for x in (ac, d, e, v))
LANES = sorted({r["p"] for r in ac})


def pick(size, p):
    return next(r for r in ac if r["size"] == size and r["p"] == p)


def fmt(x, nd=2):
    return f"{x:.{nd}f}".replace(".", ",")


def num(x):
    """Số nguyên kiểu Việt: dấu chấm phân nghìn."""
    return f"{x:,}".replace(",", ".")


# ---- Hình 1: throughput và speedup theo số lane (256x256) ----
base = pick(256, 1)["total"]
fig, ax = plt.subplots(1, 2, figsize=(7.4, 3.5))
ps = LANES
ax[0].plot(ps, ps, color=MUTED, ls="--", lw=1.5)
ax[0].plot(ps, [pick(256, p)["pix_per_cycle_steady"] for p in ps], color=COL[1], marker="o", lw=2, ms=7)
ax[0].text(ps[-1], ps[-1] + 0.3, "lý tưởng", color=MUTED, ha="right", fontsize=9)
ax[0].text(ps[-1] - 0.3, pick(256, ps[-1])["pix_per_cycle_steady"] - 1.2, "đo được", color=COL[1], ha="right", fontsize=9)
ax[0].set_xlabel("Số lane"); ax[0].set_ylabel("Pixel ra mỗi chu kỳ (ổn định)")
ax[0].set_xticks(ps); ax[0].set_title("Throughput", loc="left", fontsize=11)
ax[1].plot(ps, ps, color=MUTED, ls="--", lw=1.5)
ax[1].plot(ps, [base / pick(256, p)["total"] for p in ps], color=COL[2], marker="o", lw=2, ms=7)
ax[1].text(ps[-1], ps[-1] + 0.3, "lý tưởng", color=MUTED, ha="right", fontsize=9)
ax[1].text(ps[-1] - 0.3, base / pick(256, ps[-1])["total"] - 1.2, "đo được", color=COL[2], ha="right", fontsize=9)
ax[1].set_xlabel("Số lane"); ax[1].set_ylabel("Speedup so với 1 lane")
ax[1].set_xticks(ps); ax[1].set_title("Speedup theo số chu kỳ", loc="left", fontsize=11)
for a in ax:
    a.set_ylim(0, ps[-1] + 1.5)
fig.tight_layout(); fig.savefig(FIG / "fig_throughput.png", dpi=170); plt.close(fig)

# ---- Hình 2: cycles/pixel theo kích thước ảnh ----
sizes = sorted({r["size"] for r in ac})
fig, ax = plt.subplots(figsize=(6.4, 3.8))
for p in ps:
    ys = [pick(n, p)["cycles_per_pixel"] for n in sizes]
    ax.plot(sizes, ys, color=COL[p], marker="o", lw=2, ms=6)
    ax.text(sizes[-1] * 1.08, ys[-1], f"{p} lane", color=COL[p], va="center", fontsize=9)
ax.set_xscale("log", base=2); ax.set_yscale("log", base=2)
ax.set_xticks(sizes); ax.set_xticklabels([f"{n}×{n}" for n in sizes])
ax.set_xlim(sizes[0] * 0.85, sizes[-1] * 1.6)
ax.set_xlabel("Kích thước ảnh"); ax.set_ylabel("Chu kỳ trên mỗi pixel ra")
ax.set_title("Phần cố định của pipeline giảm khi ảnh lớn", loc="left", fontsize=11)
fig.tight_layout(); fig.savefig(FIG / "fig_size.png", dpi=170); plt.close(fig)

# ---- Hình 3: giới hạn băng thông vào (thí nghiệm E): throughput theo số lane với B cố định ----
fig, ax = plt.subplots(figsize=(6.4, 3.8))
ax.plot(ps, ps, color=MUTED, ls="--", lw=1.2)
ax.text(ps[-1], ps[-1] + 0.35, "cấp đủ (B = P)", color=MUTED, ha="right", fontsize=9)
for b_, c in [(1, COL[1]), (2, COL[2]), (4, COL[4])]:
    pts = sorted((r["p"], r["pix_per_cycle_steady"]) for r in e if r["b"] == b_)
    ax.plot(*zip(*pts), color=c, marker="o", lw=2, ms=6)
    ax.text(pts[-1][0] - 0.2, pts[-1][1] - 0.75, f"B = {b_}", color=c, ha="right", fontsize=9)
ax.set_xticks(ps); ax.set_ylim(0, 5)
ax.set_xlabel("Số lane P"); ax.set_ylabel("Pixel ra mỗi chu kỳ (ổn định)")
ax.set_title("Thêm lane không giúp khi tốc độ cấp dữ liệu cố định", loc="left", fontsize=11)
fig.tight_layout(); fig.savefig(FIG / "fig_bandwidth.png", dpi=170); plt.close(fig)

# ---- Bảng markdown ----
L = []
L.append("### 5.1 Correctness\n")
L.append("| Ảnh thử | Số lane | Số pixel kiểm tra | Số pixel sai | Sai số tuyệt đối lớn nhất | Sai số trung bình |")
L.append("| --- | --- | --- | --- | --- | --- |")
for group, name in [("gia_lap", "Giả lập"), ("speckle", "Ảnh nền nhân nhiễu (mô phỏng)")]:
    for p in LANES:
        rs = [r for r in d if r["group"] == group and r["p"] == p]
        n = sum(r["pixels"] for r in rs)
        bad = sum(r["bad"] for r in rs)
        mx = max(r["max_err"] for r in rs)
        mean = sum(r["mean_err"] * r["pixels"] for r in rs) / n
        n_txt = f"{n:,}".replace(",", ".")
        L.append(f"| {name} | {p} | {n_txt} | {bad} | {mx} | {fmt(mean, 1)} |")
L.append("\n### 5.1b Từng ảnh\n")
L.append("| Ảnh | Kích thước | Số pixel ra | Số pixel sai (1 / 2 / 4 lane) | Pixel thừa |")
L.append("| --- | --- | --- | --- | --- |")
cases = []
for r in d:
    k = (r["image"], r["w"], r["h"])
    if k not in cases:
        cases.append(k)
for k in cases:
    rs = [r for r in d if (r["image"], r["w"], r["h"]) == k]
    bads = " / ".join(str(next(r for r in rs if r["p"] == p)["bad"]) for p in LANES)
    name = {"speckle": "nền nhân nhiễu"}.get(k[0], k[0])
    L.append(f"| {name} | {k[1]}×{k[2]} | {num(rs[0]['pixels'])} | {bads} | {sum(r['extra'] for r in rs)} |")

L.append("\n### 5.2 Hiệu năng (256×256)\n")
L.append("| Số lane | Độ trễ (chu kỳ) | Tổng chu kỳ | Mô hình ⌈WH/P⌉+6 | Pixel/chu kỳ (ổn định) | Chu kỳ/pixel | Speedup thực tế | Speedup lý tưởng | Hiệu suất song song |")
L.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
for p in LANES:
    r = pick(256, p)
    sp = base / r["total"]
    L.append(f"| {p} | {r['latency']} | {num(r['total'])} | {num(r['model_total'])} | {fmt(r['pix_per_cycle_steady'], 3)} | "
             f"{fmt(r['cycles_per_pixel'], 4)} | {fmt(sp, 3)} | {p} | {fmt(sp / p * 100, 2)}% |")

L.append("\n### 5.3 Kích thước ảnh\n")
L.append("| Kích thước ảnh | " + " | ".join(f"Chu kỳ ({p} lane)" for p in LANES) + " | " + " | ".join(f"Chu kỳ/pixel ({p} lane)" for p in LANES) + " |")
L.append("| --- |" + " --- |" * (2 * len(LANES)))
for n in sizes:
    L.append(f"| {n}×{n} | " + " | ".join(num(pick(n, p)["total"]) for p in LANES) + " | "
             + " | ".join(fmt(pick(n, p)["cycles_per_pixel"], 4) for p in LANES) + " |")
L.append("")
L.append("| Kích thước ảnh | " + " | ".join(f"{p} lane" for p in LANES[1:]) + " |")
L.append("| --- |" + " --- |" * (len(LANES) - 1))
for n in sizes:
    L.append(f"| {n}×{n} | " + " | ".join(fmt(pick(n, 1)["total"] / pick(n, p)["total"], 3) for p in LANES[1:]) + " |")

L.append("\n### 5.4 Giới hạn băng thông vào (256×256)\n")
L.append("| Số lane P | Pixel cấp mỗi chu kỳ B | Tổng chu kỳ | Pixel/chu kỳ (ổn định) | Số pixel sai |")
L.append("| --- | --- | --- | --- | --- |")
for r in e:
    L.append(f"| {r['p']} | {r['b']} | {num(r['total'])} | {fmt(r['pix_per_cycle_steady'], 3)} | {r['bad']} |")


L.append("\n### 5.7 Kiểm chứng mở rộng\n")
L.append("Ngắt quãng ngẫu nhiên: mỗi chu kỳ, bộ cấp dữ liệu bị ngắt với xác suất cho trước (ảnh nhiễu ngẫu nhiên và ảnh nền nhân nhiễu 64×64, chạy qua testbench tự kiểm).\n")
L.append("| Điều kiện | Số lane | Số lần chạy | Pixel kiểm tra | Pixel sai (Python) | Lỗi tự kiểm (testbench) | Pixel/chu kỳ (số pixel ra / tổng chu kỳ) |")
L.append("| --- | --- | --- | --- | --- | --- | --- |")
groups = {}
for r in v:
    groups.setdefault((r["label"], r["stall"], r["frames"], r["b"] != r["p"], r["p"], r["b"]), []).append(r)
names = {"stall": "Ngắt quãng", "nhieu_khung": "3 khung liên tiếp", "bang_thong+stall": "B thấp và ngắt quãng"}
for (label, stall, frames, lowb, p, b_), rs_ in sorted(groups.items(), key=lambda kv: (kv[0][0] != "stall", kv[0][0], kv[0][4], kv[0][1])):
    cond = f"{names[label]}, {stall}%" + (f", B = {b_}" if lowb else "")
    pix = sum(r["pixels"] for r in rs_)
    tot = sum(r["total"] for r in rs_)
    L.append(f"| {cond} | {p} | {len(rs_)} | {num(pix)} | {sum(r['bad'] for r in rs_)} | {sum(r['sc_err'] for r in rs_)} | {fmt(pix / tot, 2)} |")
L.append("\n### 5.7b Phép thử đối chứng\n")
L.append("Phép thử đối chứng: chèn một lỗi vào bản sao mã Verilog (P = 4, ảnh nhiễu 32×32, 900 pixel ra). "
         "Mọi lỗi đều phải bị phát hiện.\n")
L.append("| Lỗi chèn vào | File | Pixel sai hoặc lệch số lượng (Python) | Lỗi tự kiểm (testbench) | Pixel thừa |")
L.append("| --- | --- | --- | --- | --- |")
mdesc = {"hang_so_7281": "Hằng số chia 7282 → 7281", "mat_na_cot_tu_-1": "Mặt nạ cột: x ≥ 0 → x ≥ −1",
         "mat_na_dong_tu_1": "Mặt nạ dòng: r ≥ 2 → r ≥ 1", "line_buffer_thieu_1_tu": "Line buffer ngắn hơn 1 từ",
         "cua_so_lech_cot": "Cửa sổ dịch sai một pixel"}
for r in m:
    bad = "lệch số lượng pixel ra" if r["bad"] < 0 else str(r["bad"])
    L.append(f"| {mdesc[r['mutant']]} | {r['file']} | {bad} | {r['sc_err']} | {r['extra']} |")

(RES / "tables.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("ok")
