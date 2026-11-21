"""Chạy các thí nghiệm A, C, D, E, kiểm chứng mở rộng (V) và phép thử đối chứng (M); ghi results/*.json."""
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import simd_sim as S

OUT = S.ROOT / "results"
OUT.mkdir(exist_ok=True)
LANES = [1, 2, 4, 8]          # 8 lane là phần mở rộng (mức 3)


def metrics(st, p):
    steady = st["nout"] / (st["last_out"] - st["first_out"] + 1)
    return {"latency": st["latency"], "total": st["total"], "nout": st["nout"], "extra": st["extra"],
            "pix_per_cycle_steady": steady, "cycles_per_pixel": st["total"] / st["nout"]}


def exp_d():
    """Correctness: nhiều loại ảnh, nhiều kích thước, mọi cấu hình lane. Có cả tự kiểm trong testbench."""
    cases = [("gradient", 64, 64, "gia_lap"), ("checker", 64, 64, "gia_lap"), ("noise", 64, 64, "gia_lap"),
             ("zero", 64, 64, "gia_lap"), ("full", 64, 64, "gia_lap"), ("noise", 256, 256, "gia_lap"),
             ("gradient", 48, 20, "gia_lap"), ("noise", 48, 20, "gia_lap"),
             ("speckle", 64, 64, "speckle"), ("speckle", 256, 256, "speckle"),
             ("sar_hanoi_urban", 256, 256, "sar_that"), ("sar_hanoi_urban", 512, 512, "sar_that"),
             ("sar_coastline", 256, 256, "sar_that"), ("sar_coastline", 512, 512, "sar_that")]
    rows = []
    for kind, w, h, group in cases:
        if group == "sar_that" and not (S.ROOT / "data" / f"{kind}_{w}.npy").exists():
            print("D bỏ qua (không có ảnh SAR trong data/):", kind, w, h, flush=True)
            continue
        img = S.make_image(kind, w, h)
        ref = S.golden(img)
        for p in LANES:
            res, st = S.simulate(img, p, tag="d")
            bad, mx, mean = S.compare(res, ref)
            rows.append({"image": kind, "group": group, "w": w, "h": h, "p": p, "pixels": int(ref.size),
                         "bad": bad, "max_err": mx, "mean_err": mean, "extra": st["extra"], "nout": st["nout"],
                         "sc_err": st["sc_err"]})
            print("D", kind, w, h, p, "bad", bad, "sc_err", st["sc_err"], flush=True)
    return rows


def exp_a_c():
    """Scaling theo lane (A, ảnh 256x256) và theo kích thước ảnh (C); cùng một vòng chạy."""
    rows = []
    for n in [64, 256, 512, 1024]:
        img = S.make_image("noise", n, n)
        for p in LANES:
            t0 = time.time()
            _, st = S.simulate(img, p, tag="c")
            m = metrics(st, p)
            m.update({"size": n, "p": p, "model_total": -(-n * n // p) + 6, "sc_err": st["sc_err"]})
            rows.append(m)
            print("C", n, p, m["total"], f"{time.time() - t0:.1f}s", flush=True)
    return rows


def exp_e():
    """Giới hạn băng thông vào: cấp B pixel mỗi chu kỳ, B <= P, ảnh 256x256."""
    img = S.make_image("noise", 256, 256)
    ref = S.golden(img)
    plan = {2: [1, 2], 4: [1, 2, 3, 4], 8: [1, 2, 4, 6, 8]}
    rows = []
    for p, bs in plan.items():
        for b in bs:
            res, st = S.simulate(img, p, b=b, tag="e")
            bad, _, _ = S.compare(res, ref)
            m = metrics(st, p)
            m.update({"p": p, "b": b, "bad": bad, "sc_err": st["sc_err"]})
            rows.append(m)
            print("E", p, b, m["total"], "bad", bad, flush=True)
    return rows


def exp_v():
    """Kiểm chứng mở rộng: (1) stall ngẫu nhiên, (2) nhiều khung liên tiếp, (3) kết hợp băng thông thấp và stall."""
    rows = []

    def run(label, kinds, p, b=None, stall=0, size=64):
        imgs = [S.make_image(k, size, size, seed=2026 + i) for i, k in enumerate(kinds)]
        res, st, refs = S.simulate_frames(imgs, p, b=b, stall=stall, tag="v")
        bad = sum(S.compare(r, f)[0] for r, f in zip(res, refs))
        m = metrics(st, p)
        m.update({"label": label, "p": p, "b": b or p, "stall": stall, "frames": len(imgs), "size": size,
                  "pixels": int(sum(r.size for r in refs)), "bad": bad, "sc_err": st["sc_err"]})
        rows.append(m)
        print("V", label, p, b, stall, len(imgs), "bad", bad, "sc_err", st["sc_err"], flush=True)

    for p in LANES:
        for stall in (30, 70):
            run("stall", ["noise"], p, stall=stall)
            run("stall", ["speckle"], p, stall=stall)
    for p in LANES:
        for stall in (0, 50):
            run("nhieu_khung", ["gradient", "noise", "speckle"], p, stall=stall)
    run("bang_thong+stall", ["noise", "speckle"], 4, b=2, stall=50)
    run("bang_thong+stall", ["noise", "speckle"], 8, b=3, stall=40)
    return rows


def exp_m():
    """Phép thử đối chứng: chèn lỗi có chủ đích vào bản sao RTL, testbench phải báo lỗi."""
    mutants = {
        "hang_so_7281": ("simd_lane.v", "13'd7282", "13'd7281"),
        "mat_na_cot_tu_-1": ("controller.v", "(x >= 0)", "(x >= -1)"),
        "mat_na_dong_tu_1": ("controller.v", "(ri >= 2)", "(ri >= 1)"),
        "line_buffer_thieu_1_tu": ("top.v", ".DEPTH(W/P)) lb1", ".DEPTH(W/P - 1)) lb1"),
        "cua_so_lech_cot": ("window_3x3.v", "row1_win[8*P +: 16]", "row1_win[8*P-8 +: 16]"),
    }
    img = S.make_image("noise", 32, 32)
    rows = []
    tmp = S.BUILD / "mut"
    for name, (fname, old, new) in mutants.items():
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.copytree(S.ROOT / "rtl", tmp)
        src = (tmp / fname).read_text(encoding="utf-8")
        assert old in src, (name, old)
        (tmp / fname).write_text(src.replace(old, new), encoding="utf-8")
        res, st, refs = S.simulate_frames([img], 4, tag="m", rtl_dir=tmp)
        bad = S.compare(res[0], refs[0])[0] if st["nout"] == refs[0].size else -1
        rows.append({"mutant": name, "file": fname, "bad": bad, "sc_err": st["sc_err"], "extra": st["extra"],
                     "nout": st["nout"], "expected": int(refs[0].size)})
        print("M", name, rows[-1], flush=True)
    shutil.rmtree(tmp, ignore_errors=True)
    return rows


if __name__ == "__main__":
    which = sys.argv[1:] or ["d", "ac", "e", "v", "m"]
    if "d" in which:
        (OUT / "exp_d.json").write_text(json.dumps(exp_d(), indent=1))
    if "ac" in which:
        (OUT / "exp_ac.json").write_text(json.dumps(exp_a_c(), indent=1))
    if "e" in which:
        (OUT / "exp_e.json").write_text(json.dumps(exp_e(), indent=1))
    if "v" in which:
        (OUT / "exp_v.json").write_text(json.dumps(exp_v(), indent=1))
    if "m" in which:
        (OUT / "exp_m.json").write_text(json.dumps(exp_m(), indent=1))
