"""Golden model, sinh ảnh thử và chạy mô phỏng Icarus Verilog cho bộ lọc trung bình 3x3 SIMD."""
import os
import re
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
RTL = ["pipe_reg.v", "line_buffer.v", "controller.v", "window_3x3.v",
       "simd_lane.v", "simd_array.v", "top.v"]


def make_image(kind, w, h, seed=2026):
    """Ảnh xám 8 bit h x w. Các loại: gradient, checker, noise, zero, full, speckle."""
    rng = np.random.default_rng(seed)
    if kind == "gradient":
        y, x = np.mgrid[0:h, 0:w]
        return ((x * 255 // max(w - 1, 1) + y * 255 // max(h - 1, 1)) // 2).astype(np.uint8)
    if kind == "checker":
        y, x = np.mgrid[0:h, 0:w]
        return (((x // 4 + y // 4) % 2) * 255).astype(np.uint8)
    if kind == "noise":
        return rng.integers(0, 256, size=(h, w), dtype=np.uint8)
    if kind == "zero":
        return np.zeros((h, w), dtype=np.uint8)
    if kind == "full":
        return np.full((h, w), 255, dtype=np.uint8)
    if kind == "speckle":
        # Nền có cấu trúc nhân với nhiễu ngẫu nhiên Rayleigh, tạo bằng chương trình (không phải ảnh thật)
        y, x = np.mgrid[0:h, 0:w]
        base = 90 + 60 * np.sin(x / 11.0) * np.cos(y / 17.0) + 40 * ((x > w // 2) & (y > h // 3))
        speckle = rng.rayleigh(scale=1.0, size=(h, w)) / np.sqrt(np.pi / 2)
        return np.clip(base * speckle, 0, 255).astype(np.uint8)
    raise ValueError(kind)


def golden(img):
    """Trung bình 3x3, chia nguyên cho 9, chỉ giữ pixel đủ 8 lân cận: ảnh ra (h-2) x (w-2)."""
    a = img.astype(np.int32)
    h, w = a.shape
    s = sum(a[i:h - 2 + i, j:w - 2 + j] for i in range(3) for j in range(3))
    return (s // 9).astype(np.uint8)


def write_hex(path, arr):
    Path(path).write_text("\n".join(f"{v:02x}" for v in arr.ravel()) + "\n")


def read_hex(path):
    return np.array([int(t, 16) for t in Path(path).read_text().split()], dtype=np.uint8)


def _rel(path):
    """Đường dẫn tương đối so với ROOT (dùng dấu /); nếu ở ổ đĩa khác thì giữ nguyên."""
    try:
        return os.path.relpath(path, ROOT).replace("\\", "/")
    except ValueError:
        return str(path)


def simulate_frames(imgs, p, b=None, stall=0, seed=0x1234ABCD, tag="run", vcd=None, rtl_dir=None):
    """Chạy RTL với P lane trên một dãy khung ảnh cùng kích thước, đưa liên tiếp không reset giữa các khung.
    b: pixel cấp mỗi chu kỳ (mặc định p); stall: xác suất % mỗi chu kỳ bị ngắt quãng.
    rtl_dir: thư mục RTL khác (dùng cho phép thử đối chứng). Trả về (danh sách ảnh ra, số liệu chu kỳ, danh sách ảnh chuẩn)."""
    h, w = imgs[0].shape
    b = p if b is None else b
    BUILD.mkdir(exist_ok=True)
    f_in, f_out, f_exp = BUILD / f"{tag}_in.hex", BUILD / f"{tag}_out.hex", BUILD / f"{tag}_exp.hex"
    vvp = BUILD / f"{tag}.vvp"
    refs = [golden(im) for im in imgs]
    write_hex(f_in, np.concatenate([im.ravel() for im in imgs]))
    write_hex(f_exp, np.concatenate([r.ravel() for r in refs]))
    cmd = ["iverilog", "-g2012", f"-Ptb_top.P={p}", f"-Ptb_top.W={w}", f"-Ptb_top.H={h}",
           f"-Ptb_top.F={len(imgs)}", f"-Ptb_top.B={b}", f"-Ptb_top.STALL={stall}", f"-Ptb_top.SEED={seed}",
           "-o", str(vvp)] + [str((rtl_dir or ROOT / "rtl") / f) for f in RTL] + [str(ROOT / "tb" / "tb_top.v")]
    subprocess.run(cmd, check=True)
    # Testbench đọc tên file vào thanh ghi 1024 bit (tối đa 128 ký tự), nên truyền đường dẫn tương đối so với ROOT
    run = ["vvp", str(vvp), f"+in={_rel(f_in)}", f"+out={_rel(f_out)}", f"+exp={_rel(f_exp)}"]
    if vcd:
        run.append(f"+vcd={_rel(vcd)}")
    out = subprocess.run(run, check=True, capture_output=True, text=True, cwd=ROOT).stdout
    m = re.search(r"RESULT (.*)", out)
    stats = {k: int(v) for k, v in (t.split("=") for t in m.group(1).split())}
    res = read_hex(f_out).reshape(len(imgs), h - 2, w - 2)
    for f in (f_in, f_out, f_exp, vvp):
        f.unlink()
    return list(res), stats, refs


def simulate(img, p, b=None, tag="run", stall=0, vcd=None):
    """Một khung ảnh. Trả về (ảnh ra, số liệu chu kỳ)."""
    res, stats, _ = simulate_frames([img], p, b=b, stall=stall, tag=tag, vcd=vcd)
    return res[0], stats


def compare(res, ref):
    """Số pixel sai, sai số tuyệt đối lớn nhất, sai số tuyệt đối trung bình."""
    d = np.abs(res.astype(np.int32) - ref.astype(np.int32))
    return int((d != 0).sum()), int(d.max()), float(d.mean())
