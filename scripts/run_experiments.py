"""Chạy các thí nghiệm A, C, D, E, kiểm chứng mở rộng (V), phép thử đối chứng (M), biên (G) và lọc Gaussian (GA); ghi results/*.json."""
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


D_CASES = [("gradient", 64, 64, "gia_lap"), ("checker", 64, 64, "gia_lap"), ("noise", 64, 64, "gia_lap"),
           ("zero", 64, 64, "gia_lap"), ("full", 64, 64, "gia_lap"), ("noise", 256, 256, "gia_lap"),
           ("gradient", 48, 20, "gia_lap"), ("noise", 48, 20, "gia_lap"),
           ("speckle", 64, 64, "speckle"), ("speckle", 256, 256, "speckle"),
           ("sar_hanoi_urban", 256, 256, "sar_that"), ("sar_hanoi_urban", 512, 512, "sar_that"),
           ("sar_coastline", 256, 256, "sar_that"), ("sar_coastline", 512, 512, "sar_that")]


def exp_d():
    """Correctness: nhiều loại ảnh, nhiều kích thước, mọi cấu hình lane. Có cả tự kiểm trong testbench."""
    rows = []
    for kind, w, h, group in D_CASES:
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
    """Phép thử đối chứng: chèn lỗi có chủ đích vào bản sao RTL, testbench phải báo lỗi.
    Mặc định chạy 1 khung nhiễu 32x32, P = 4, lọc trung bình. Lỗi Gaussian chạy ở chế độ Gaussian; lỗi lệch nhịp
    của op_pipe chỉ lộ ra khi đổi chế độ giữa các khung nên chạy 3 khung liên tiếp Mean, Gaussian, Mean."""
    mutants = {
        "hang_so_7281": ("simd_lane.v", "13'd7282", "13'd7281"),
        "mat_na_cot_tu_-1": ("controller.v", "(x >= 0)", "(x >= -1)"),
        "mat_na_dong_tu_1": ("controller.v", "(ri >= 2)", "(ri >= 1)"),
        "line_buffer_thieu_1_tu": ("top.v", ".DEPTH(W/P)) lb1", ".DEPTH(W/P - 1)) lb1"),
        "cua_so_lech_cot": ("window_3x3.v", "row1_win[8*P +: 16]", "row1_win[8*P-8 +: 16]"),
        # Lane đọc nhầm cột s+1 thay cho cột s+2 ở dòng mới nhất. (Chỉ hoán vị thứ tự 9 pixel trong pix thì là
        # lỗi tương đương: tổng giao hoán nên đầu ra không đổi, không bộ kiểm tra nào bắt được.)
        "simd_array_lap_cot": ("simd_array.v", "row2_win[8*(s+2) +: 8]", "row2_win[8*(s+1) +: 8]"),
        # Thanh ghi pipeline luôn báo valid sau reset
        "pipe_reg_valid_luon_1": ("pipe_reg.v", "vout <= vin;", "vout <= 1'b1;"),
        # Lọc Gaussian: tâm nhân 2 thay vì 4; dịch phải 3 thay vì 4; chế độ đến lệch 1 nhịp so với dữ liệu
        "gauss_tam_nhan_2": ("gauss_lane.v", "{p[4], 2'b00}", "{1'b0, p[4], 1'b0}", {"ops": [1]}),
        "gauss_dich_3": ("gauss_lane.v", "s4_d[11:4]", "s4_d[10:3]", {"ops": [1]}),
        "op_pipe_lech_1_nhip": ("simd_array.v", "op_pipe[4]", "op_pipe[3]", {"ops": [0, 1, 0]}),
    }
    rows = []
    tmp = S.BUILD / "mut"
    for name, (fname, old, new, *cfg) in mutants.items():
        ops = cfg[0]["ops"] if cfg else [0]
        imgs = [S.make_image("noise", 32, 32, seed=2026 + i) for i in range(len(ops))]
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.copytree(S.ROOT / "rtl", tmp)
        src = (tmp / fname).read_text(encoding="utf-8")
        assert src.count(old) == 1, (name, old)
        (tmp / fname).write_text(src.replace(old, new), encoding="utf-8")
        res, st, refs = S.simulate_frames(imgs, 4, tag="m", rtl_dir=tmp, ops=ops)
        expected = int(sum(r.size for r in refs))
        bad = sum(S.compare(a, b)[0] for a, b in zip(res, refs)) if st["nout"] == expected else -1
        row = {"mutant": name, "file": fname, "bad": bad, "sc_err": st["sc_err"], "extra": st["extra"],
               "nout": st["nout"], "expected": expected, "x_out": st["x_out"]}
        if cfg:
            row["ops"] = ops
        rows.append(row)
        caught = bad > 0 or st["sc_err"] > 0 or st["extra"] > 0 or st["nout"] != expected
        print("M", name, row, flush=True)
        assert caught, ("lỗi chèn không bị phát hiện", name)
    shutil.rmtree(tmp, ignore_errors=True)
    return rows


def exp_gauss():
    """Lọc Gaussian (op = 1): các ảnh của exp_d ở P = 1, 2, 4; nhiều khung liên tiếp đổi chế độ Mean, Gaussian, Mean
    không reset, có và không có nguồn ngắt quãng; một ca băng thông thấp B = 2 kèm ngắt quãng.
    Báo tổng riêng, không cộng vào tổng kiểm 61 lượt của lọc trung bình."""
    rows = []
    for kind, w, h, group in D_CASES:
        if group == "sar_that" and not (S.ROOT / "data" / f"{kind}_{w}.npy").exists():
            print("GA bỏ qua (không có ảnh SAR trong data/):", kind, w, h, flush=True)
            continue
        img = S.make_image(kind, w, h)
        ref = S.golden(img, 1)
        for p in (1, 2, 4):
            res, st = S.simulate(img, p, tag="ga", op=1)
            bad, mx, mean = S.compare(res, ref)
            rows.append({"kind": "anh", "image": kind, "group": group, "w": w, "h": h, "p": p, "pixels": int(ref.size),
                         "bad": bad, "max_err": mx, "mean_err": mean, "extra": st["extra"], "nout": st["nout"],
                         "sc_err": st["sc_err"]})
            print("GA", kind, w, h, p, "bad", bad, "sc_err", st["sc_err"], flush=True)

    def run(p, stall, b=None):
        imgs = [S.make_image(k, 64, 64, seed=2026 + i) for i, k in enumerate(["noise", "speckle", "gradient"])]
        ops = [0, 1, 0]
        res, st, refs = S.simulate_frames(imgs, p, b=b, stall=stall, tag="ga", ops=ops)
        bad = sum(S.compare(a, c)[0] for a, c in zip(res, refs))
        m = metrics(st, p)
        m.update({"kind": "doi_che_do", "ops": ops, "p": p, "b": b or p, "stall": stall, "frames": len(imgs), "size": 64,
                  "pixels": int(sum(r.size for r in refs)), "bad": bad, "sc_err": st["sc_err"]})
        rows.append(m)
        print("GA doi_che_do", p, b, stall, "bad", bad, "sc_err", st["sc_err"], flush=True)

    for p in (1, 2, 4):
        for stall in (0, 50):
            run(p, stall)
    run(4, 50, b=2)
    return rows


def exp_g():
    """Biên: ảnh rất nhỏ, W = P, ảnh không có pixel ra (W = 2 hoặc H = 2).
    Đạt khi không pixel sai, không thừa, đủ (W-2)(H-2) pixel ra. Không tính vào tổng kiểm 61 lượt."""
    cases = [  # (nhóm, W, H, P)
        ("nho", 3, 3, 1), ("nho", 4, 3, 1), ("nho", 4, 3, 2), ("nho", 6, 5, 2), ("nho", 6, 5, 3),
        ("w_bang_p", 4, 3, 4), ("w_bang_p", 4, 4, 4), ("w_bang_p", 3, 3, 3), ("w_bang_p", 2, 6, 2),
        ("rong", 2, 2, 1), ("rong", 2, 2, 2), ("rong", 4, 2, 1), ("rong", 4, 2, 2), ("rong", 4, 2, 4),
        ("rong", 2, 6, 1),
    ]
    rows = []
    for group, w, h, p in cases:
        assert w % p == 0
        img = S.make_image("noise", w, h)
        ref = S.golden(img)
        res, st = S.simulate(img, p, tag="g")
        bad = S.compare(res, ref)[0]
        expected = max(w - 2, 0) * max(h - 2, 0)
        ok = bad == 0 and st["extra"] == 0 and st["nout"] == expected and st["sc_err"] == 0
        rows.append({"group": group, "w": w, "h": h, "p": p, "expected": expected, "nout": st["nout"],
                     "extra": st["extra"], "bad": bad, "sc_err": st["sc_err"], "ok": ok})
        print("G", group, w, h, p, "expected", expected, "nout", st["nout"], "extra", st["extra"], "bad", bad,
              "OK" if ok else "FAIL", flush=True)
    return rows


if __name__ == "__main__":
    which = sys.argv[1:] or ["d", "ac", "e", "v", "m", "g", "ga"]
    if "g" in which:
        (OUT / "exp_g.json").write_text(json.dumps(exp_g(), indent=1))
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
    if "ga" in which:
        (OUT / "exp_gauss.json").write_text(json.dumps(exp_gauss(), indent=1))
