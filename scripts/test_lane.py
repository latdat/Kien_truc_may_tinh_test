"""Kiểm tra riêng một lane: biên dịch tb_lane.v bằng Icarus Verilog và chạy, thoát mã khác 0 nếu có lỗi.
Testbench duyệt toàn bộ 2296 giá trị tổng 0..2295 và so với phần nguyên của tổng chia 9."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
BUILD.mkdir(exist_ok=True)
vvp = BUILD / "lane.vvp"
srcs = [ROOT / "rtl" / "pipe_reg.v", ROOT / "rtl" / "simd_lane.v", ROOT / "tb" / "tb_lane.v"]

subprocess.run(["iverilog", "-g2012", "-o", str(vvp)] + [str(s) for s in srcs], check=True)
out = subprocess.run(["vvp", str(vvp)], check=True, capture_output=True, text=True).stdout
print(out.strip())
m = re.search(r"LANE_TEST sums=(\d+) checked=(\d+) errors=(\d+)", out)
if not m or int(m.group(3)) != 0 or int(m.group(1)) != int(m.group(2)):
    sys.exit("LANE_TEST FAIL")
print("LANE_TEST PASS")
