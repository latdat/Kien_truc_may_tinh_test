"""Dựng báo cáo theo định dạng đồ án (bìa, lời cảm ơn, tóm tắt, mục lục, danh mục, chương, kết luận, tài liệu
tham khảo, phụ lục) từ báo cáo markdown và xuất PDF. Cần: pandoc, PyMuPDF, Microsoft Edge."""
import html
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pymupdf as fitz

ROOT = Path(__file__).resolve().parent.parent                      # simd_filter/
OUT = ROOT / "Do_an_SIMD_Verilog.pdf"
TMP = ROOT / "build_thesis"


def find_browser() -> str:
    """Tìm trình duyệt Chromium (Edge, Chrome, Chromium) để in PDF. Đặt biến môi trường BROWSER để chỉ định thủ công."""
    cands = [os.environ.get("BROWSER", ""),
             r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
             r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
             r"C:\Program Files\Google\Chrome\Application\chrome.exe",
             "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    for c in cands:
        if c and Path(c).exists():
            return c
    for name in ("microsoft-edge", "msedge", "google-chrome", "chromium", "chromium-browser", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    raise SystemExit("Không tìm thấy Edge, Chrome hoặc Chromium. Đặt biến môi trường BROWSER trỏ tới trình duyệt.")


TITLE = "Tăng tốc SIMD đa luồng cho xử lý ảnh sử dụng Verilog"
DATE = "10/2026"
COVER = False        # đặt True để thêm hai trang bìa
INCLUDE_QA = False   # True: chèn phần ôn tập vấn đáp vào cuối đồ án; mặc định tách thành file riêng (python scripts/build_thesis.py --qa)
OUT_QA = ROOT / "On_tap_van_dap.pdf"
QA_FILE = ROOT / "ontap_van_dap.md"
TEMPLATE = ROOT / "bao_cao.md"
TABLES = ROOT / "results" / "tables.md"

# ---------------------------------------------------------------- CSS (đo từ đồ án mẫu: A4, lề trái 3,5 cm, phải 2,5 cm)
CSS = """
@page { size: A4; margin: 2.1cm 2.5cm 3.0cm 3.5cm; }
html { font-family: "Times New Roman", Times, serif; font-size: 13pt; line-height: 18.65pt; color: #000; }
body { margin: 0; }
p { margin: 0 0 9pt; text-align: justify; text-indent: 1cm; }
.mk { position: absolute; font-size: 1px; color: #fff; }
h1.chap { break-before: page; text-align: center; font-size: 15.9pt; line-height: 1.3; margin: 0 0 30pt; font-weight: bold; }
h1.chap.nobreak { break-before: auto; }
h2.sec { font-size: 13.9pt; line-height: 1.35; font-weight: bold; margin: 12pt 0 7pt; text-align: left; break-after: avoid; }
h2.sec .num { display: inline-block; width: 1.0cm; }
h3.sub { font-size: 13pt; line-height: 1.35; font-weight: bold; font-style: italic; margin: 9pt 0 6pt; break-after: avoid; }
h3.sub .num { display: inline-block; width: 1.4cm; }
h2.app { font-size: 13.9pt; font-weight: bold; margin: 18pt 0 8pt; break-after: avoid; }
ul { margin: 9pt 0; padding: 0 0 0 11pt; list-style: none; }
ul li { position: relative; text-align: justify; margin: 0; }
ul li::before { content: "\\2022"; position: absolute; left: -10pt; }
ul li.chk::before { content: "\\2611"; font-family: "Segoe UI Symbol", serif; font-size: 11pt; left: -12pt; }
ul li.chk0::before { content: "\\2610"; font-family: "Segoe UI Symbol", serif; font-size: 11pt; left: -12pt; }
ol { margin: 9pt 0; padding: 0 0 0 1.0cm; }
li p { margin: 0; text-indent: 0; }
table { border-collapse: collapse; width: 100%; margin: 0 0 12pt; font-size: 13pt; line-height: 1.3; }
table.t5 { font-size: 11pt; }
table.t7 { font-size: 9.2pt; }
table.short { break-inside: avoid; }
th, td { border: 0.5pt solid #000; padding: 3pt 5pt; text-align: left; vertical-align: top; }
th { font-weight: bold; }
tr { break-inside: avoid; }
thead { display: table-header-group; }
td p, th p { margin: 0; text-indent: 0; }
figure { margin: 12pt 0 8pt; text-align: center; break-inside: avoid; }
figure img { max-width: 100%; max-height: 15cm; height: auto; }
.cap { font-size: 13pt; text-align: center; text-indent: 0; line-height: 1.35; margin: 8pt 0 0; }
.cap em { font-size: 12pt; }
.cap-table { margin: 10pt 0 6pt; break-after: avoid; }
pre { font-family: "Consolas", "Courier New", monospace; font-size: 8.6pt; line-height: 1.22; border: 0.5pt solid #000;
      padding: 5pt 7pt; margin: 6pt 0 10pt; white-space: pre; overflow: hidden; }
pre code { font-family: inherit; font-size: inherit; }
code { font-family: "Consolas", "Courier New", monospace; font-size: 11pt; }
math[display="block"] { margin: 6pt 0 10pt; }
.ref { padding-left: 1.0cm; text-indent: -1.0cm; margin: 0 0 8pt; text-align: justify; }
.q { text-indent: 0; margin: 12pt 0 3pt; break-after: avoid; }
.hint { text-indent: 0; margin: 0 0 1pt; font-size: 12pt; break-after: avoid; }
.hint + ul { font-size: 12pt; margin: 2pt 0 8pt; }
blockquote { margin: 2pt 0 8pt; padding: 2pt 0 2pt 10pt; border-left: 1.5pt solid #777; font-size: 12pt; }
blockquote p { text-indent: 0; margin: 0 0 5pt; }
.note { text-indent: 0; font-size: 12pt; border: 0.5pt solid #000; padding: 5pt 8pt; }
.center { text-align: center; text-indent: 0; }
.front-title { text-align: center; font-weight: bold; font-size: 13.9pt; margin: 0 0 12pt; }
.sig { margin: 30pt 0 0 52%; text-align: center; text-indent: 0; }
.sig small { font-size: 10.5pt; font-style: italic; }
.pageb { break-before: page; }
.toc-row { display: flex; align-items: baseline; margin: 0 0 4pt; line-height: 1.25; }
.toc-row .n { flex: none; }
.toc-row .t { flex: 0 1 auto; }
.dots { flex: 1; align-self: flex-end; height: 3pt; margin: 0 4pt 4pt; min-width: 14pt;
        background-image: radial-gradient(circle at center, #000 0.55pt, transparent 0.75pt);
        background-size: 4.4pt 3pt; background-repeat: repeat-x; }
.toc-row .pg { flex: none; }
.lvl0 { padding-left: 19.4pt; font-weight: bold; margin-top: 8pt; }
.lvl0 .dots { background: none; }
.lvl1 { padding-left: 19.4pt; } .lvl1 .n { width: 30pt; }
.lvl2 { padding-left: 49pt; } .lvl2 .n { width: 40pt; }
.lst-row { display: flex; align-items: baseline; margin: 0 0 8pt; line-height: 1.25; }
.lst-row .lab { flex: none; width: 56pt; font-size: 12pt; }
.lst-row .t { flex: 0 1 auto; }
table.sym { width: 100%; border-collapse: collapse; font-size: 13pt; margin-top: 18pt; }
table.sym td { border: none; padding: 1pt 6pt 5pt 0; vertical-align: top; }
table.sym td:first-child { width: 90pt; }
"""

COVER_CSS = """
@page { size: A4; margin: 0; }
html, body { margin: 0; padding: 0; font-family: "Times New Roman", Times, serif; color: #000; }
.pg { position: relative; width: 595pt; height: 841pt; overflow: hidden; break-after: page; }
.pg:last-child { break-after: auto; }
.abs { position: absolute; left: 99.2pt; width: 425.2pt; text-align: center; margin: 0; }
.sans { font-family: Arial, Helvetica, sans-serif; font-weight: bold; }
.row { position: absolute; margin: 0; font-size: 13pt; }
.b { font-weight: bold; }
"""


# ---------------------------------------------------------------- phân tích markdown nguồn
def parse(md: str):
    chunks, cur, code = [], {"level": 0, "title": "", "lines": []}, False
    for line in md.split("\n"):
        if line.startswith("```"):
            code = not code
        m = None if code else re.match(r"^(#{1,4}) (.*)$", line)
        if m:
            chunks.append(cur)
            cur = {"level": len(m.group(1)), "title": m.group(2).strip(), "lines": []}
        else:
            cur["lines"].append(line)
    chunks.append(cur)
    return {c["title"]: c["lines"] for c in chunks}


def trim(lines):
    lines = list(lines)
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


# Tham chiếu chéo "mục X.Y" đổi sang cách đánh số mới. Các trường hợp đặc biệt được thay bằng ký hiệu giữ chỗ trước.
MANUAL = [
    ("(mục 5.4 đến 5.6, 6)", "(mục 4.4 đến 4.6 và 4.8)"),
    ("mục 6.3 (cấu hình nên chọn) và mục 7 (kết luận)", "mục 4.8.3 (cấu hình nên chọn) và phần Kết luận"),
    ("hàng tương ứng trong mục 1.3", "mục Tiến độ thực hiện ở phần Mở đầu"),
    ("bảng 5.5 và 5.6 bằng số liệu thật", "các bảng ở mục 4.5 và 4.6 bằng số liệu thật"),
    ("mục 6.3, 7 bản cuối", "mục 4.8.3 và phần Kết luận bản cuối"),
    ("mục 4, 5.1, 5.7, tài liệu tham khảo", "Chương 3, mục 4.1, 4.7, tài liệu tham khảo"),
    ("| 4, 5.1, 5.7, tài liệu tham khảo,", "| Chương 3, 4.1, 4.7, tài liệu tham khảo,"),
    ("Hoàn thiện mục 2 và 3.3; đọc phản biện mục 6.2", "Hoàn thiện Chương 1 và mục 2.3; đọc phản biện mục 4.8.2"),
    ("Sản phẩm: mục 2 và 3.3 bản cuối", "Sản phẩm: Chương 1 và mục 2.3 bản cuối"),
    ("| 2, 3.3, 6.2 (hàng pipeline và latency) |", "| Chương 1, 2.3, 4.8.2 (hàng pipeline và latency) |"),
    ("| 3.1, 3.4, 5.2 đến 5.4, 6.1 |", "| 2.1, 2.4, 4.2 đến 4.4, 4.8.1 |"),
    ("| 5.5, 5.6, 6.3, 7, tóm tắt |", "| 4.5, 4.6, 4.8.3, Kết luận, tóm tắt |"),
    ("(mục 5.4 đến 5.6, 6)", "(mục 4.4 đến 4.6 và 4.8)"),
    ("mục 5.4 đến 5.6, 6", "mục 4.4 đến 4.6 và 4.8"),
    ("mục 6.3 và kết luận", "mục 4.8.3 và phần Kết luận"),
    ("Chạy lại toàn bộ lệnh ở phụ lục B", "Chạy lại toàn bộ lệnh ở phụ lục B"),
    ("mục 3.2 và", "mục 2.2 và"),
    ("Cập nhật 6.3, 7 và tóm tắt", "Cập nhật mục 4.8.3, phần Kết luận và tóm tắt"),
]
NUMMAP = {"3.1": "2.1", "3.2": "2.2", "3.3": "2.3", "3.4": "2.4", "4.1": "3.1", "4.2": "3.2", "4.3": "3.3",
          "4.4": "3.4", "5.1": "4.1", "5.2": "4.2", "5.3": "4.3", "5.4": "4.4", "5.5": "4.5", "5.6": "4.6",
          "5.7": "4.7", "6.1": "4.8.1", "6.2": "4.8.2", "6.3": "4.8.3", "6.4": "4.9"}
REFRE = re.compile(r"((?:[Mm]ục|bảng) )(\d+(?:\.\d+)?(?:(?:, | và | đến )\d+(?:\.\d+)?)*)")


def remap(text: str) -> str:
    holders = []
    for i, (old, new) in enumerate(MANUAL):
        if old in text:
            text = text.replace(old, f"@@M{i}@@")
            holders.append((f"@@M{i}@@", new))

    def one(m):
        return m.group(1) + re.sub(r"\d+\.\d+", lambda n: NUMMAP.get(n.group(0), n.group(0)), m.group(2))

    text = REFRE.sub(one, text)
    for k, v in holders:
        text = text.replace(k, v)
    return text


# ---------------------------------------------------------------- bảng: độ rộng cột theo nội dung
def fix_tables(lines):
    out, i = [], 0
    while i < len(lines):
        if lines[i].startswith("|") and i + 1 < len(lines) and re.match(r"^\|(\s*:?-+:?\s*\|)+\s*$", lines[i + 1]):
            j = i
            while j < len(lines) and lines[j].startswith("|"):
                j += 1
            rows = [re.split(r"(?<!\\)\|", ln.strip().strip("|")) for k, ln in enumerate(lines[i:j]) if k != 1]
            ncol = len(rows[0])
            widths = []
            for c in range(ncol):
                cells = [len(r[c].strip()) for r in rows if c < len(r)]
                widths.append(max(5, min(50, max(len(rows[0][c].strip()) // 2 + 2, int(sum(cells) / len(cells)) + 2,
                                                  max(cells) // 2))))
            out.append(lines[i])
            out.append("|" + "|".join("-" * w for w in widths) + "|")
            out.extend(lines[i + 2:j])
            i = j
        else:
            out.append(lines[i])
            i += 1
    return out


CAPTIONS = [
    ("Bài giảng | Khái niệm", "Các kiến thức của học phần được vận dụng trong đồ án"),
    ("Module | Chức năng", "Các module Verilog của hệ thống"),
    ("Stage | Phép tính", "Các stage của một lane"),
    ("Thí nghiệm | Mục tiêu", "Các thí nghiệm thực hiện trong đồ án"),
    ("Ảnh thử | Số lane", "Kết quả kiểm chứng tính đúng đắn theo số lane"),
    ("Lỗi chèn vào | File", "Kết quả phép thử đối chứng (P = 4, ảnh nhiễu 32×32, 900 pixel ra)"),
    ("Số lane | Độ trễ", "Hiệu năng theo số lane (ảnh 256×256)"),
    ("Kích thước ảnh | Chu kỳ", "Số chu kỳ và chu kỳ trên pixel theo kích thước ảnh"),
    ("Kích thước ảnh | 2 lane", "Speedup so với 1 lane theo kích thước ảnh"),
    ("Số lane P | Pixel cấp", "Throughput khi giới hạn tốc độ cấp dữ liệu (ảnh 256×256)"),
    ("Đánh đổi | Biểu hiện", "Các điểm đánh đổi của thiết kế"),
    ("Ảnh | Kích thước", "Số pixel sai theo từng ảnh thử"),
    ("Điều kiện | Số lane", "Kết quả kiểm chứng mở rộng"),
    ("Thư mục | Nội dung", "Cấu trúc thư mục mã nguồn"),
    ("Vai | Thành viên", "Phân vai trong nhóm"),
    ("Người đọc | Đọc", "Lịch đọc chéo giữa các thành viên"),
]
DROP_LINES = set()   # các dòng dẫn cần bỏ khỏi bản dựng (hiện không có)


class Composer:
    """Gom nội dung theo cấu trúc đồ án: sinh markdown (có HTML thô cho tiêu đề, chú thích) và ghi nhận mục lục."""

    def __init__(self):
        self.md = []
        self.toc = []        # (level, num, title, mark)
        self.figs = []       # (label, caption, mark)
        self.tabs = []
        self.mark = 0
        self.ch = self.sec = self.sub = 0
        self.app = ""        # chữ cái phụ lục hiện tại
        self.app_sec = 0
        self.fig_n = self.tab_n = 0
        self.tab_i = 0
        self.pending_caps = []
        self.use_remap = False

    def newmark(self):
        self.mark += 1
        return f"@@{self.mark}@@"

    def emit(self, *lines):
        self.md.extend(lines)

    def chapter(self, title, numbered=True, toc=True, nobreak=False):
        mk = self.newmark()
        if numbered:
            self.ch += 1
            self.sec = self.sub = 0
            self.fig_n = self.tab_n = 0
            text = f"CHƯƠNG {self.ch}. {title.upper()}"
        else:
            text = title.upper()
        cls = "chap nobreak" if nobreak else "chap"
        self.emit("", f'<h1 class="{cls}"><span class="mk">{mk}</span>{html.escape(text)}</h1>', "")
        if toc:
            self.toc.append((0, "", text, mk))
        return mk

    def section(self, title, numbered=True):
        mk = self.newmark()
        if numbered:
            self.sec += 1
            self.sub = 0
            num = f"{self.ch}.{self.sec}"
            self.toc.append((1, num, title, mk))
            self.emit("", f'<h2 class="sec"><span class="mk">{mk}</span><span class="num">{num}</span>{html.escape(title)}</h2>', "")
        else:
            self.emit("", f'<h2 class="sec"><span class="mk">{mk}</span>{html.escape(title)}</h2>', "")

    def subsection(self, title):
        mk = self.newmark()
        self.sub += 1
        num = f"{self.ch}.{self.sec}.{self.sub}"
        self.toc.append((2, num, title, mk))
        self.emit("", f'<h3 class="sub"><span class="mk">{mk}</span><span class="num">{num}</span>{html.escape(title)}</h3>', "")

    def app_head(self, letter, title):
        self.app, self.app_sec = letter, 0
        self.fig_n = self.tab_n = 0
        self.emit("", f'<h2 class="app">Phụ lục {letter}: {html.escape(title)}</h2>', "")

    def app_sub(self, title):
        self.app_sec += 1
        self.emit("", f'<h3 class="sub"><span class="num">{self.app}.{self.app_sec}</span>{html.escape(title)}</h3>', "")

    def prefix(self):
        return self.app if self.app else str(self.ch)

    def caption_table(self, header, cap=None):
        key = " | ".join(c.strip() for c in re.split(r"(?<!\\)\|", header.strip().strip("|")))
        if cap is None:
            for pre, cap in CAPTIONS:
                if key.startswith(pre):
                    break
            else:
                raise SystemExit(f"Thiếu chú thích bảng: {key}")
        self.tab_n += 1
        label = f"Bảng {self.prefix()}.{self.tab_n}"
        mk = self.newmark()
        self.tabs.append((label, cap, mk))
        self.emit("", f'<p class="cap cap-table"><span class="mk">{mk}</span><em>{label}</em> {html.escape(cap)}</p>', "")

    def figure(self, alt, src):
        self.fig_n += 1
        label = f"Hình {self.prefix()}.{self.fig_n}"
        mk = self.newmark()
        self.figs.append((label, alt, mk))
        uri = (ROOT / src.replace("simd_filter/", "")).as_uri()
        self.emit("", f'<figure><img src="{uri}" alt="{html.escape(alt)}"><p class="cap"><span class="mk">{mk}</span>'
                      f'<em>{label}</em> {html.escape(alt)}</p></figure>', "")

    def text(self, lines):
        """Chèn đoạn markdown: đổi tham chiếu, thêm chú thích cho bảng và hình, bỏ các dòng dẫn không cần."""
        text = "\n".join(trim(lines))
        text = remap(text) if self.use_remap else text
        text = re.sub(r"```latex\n(.*?)\n```", lambda m: "$$\n" + m.group(1) + "\n$$", text, flags=re.S)
        text = re.sub(r"^(\s*)- \[ \] ", r"\1- □ ", text, flags=re.M)
        text = re.sub(r"^(\s*)- \[[xX]\] ", r"\1- ☑ ", text, flags=re.M)
        lines = [ln for ln in text.split("\n") if ln.strip() not in DROP_LINES]
        lines = fix_tables(lines)
        i = 0
        while i < len(lines):
            ln = lines[i]
            if ln.startswith("Bảng: "):
                self.pending_caps.append(ln[6:].strip())
                i += 1
                continue
            m = re.match(r"^!\[(.*)\]\((.*)\)\s*$", ln)
            if m:
                self.figure(m.group(1), m.group(2))
            elif ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|(\s*:?-+:?\s*\|)+\s*$", lines[i + 1]):
                self.caption_table(ln, self.pending_caps.pop(0) if self.pending_caps else None)
                while i < len(lines) and lines[i].startswith("|"):
                    self.emit(lines[i])
                    i += 1
                self.emit("")
                continue
            else:
                self.emit(ln)
            i += 1
        self.emit("")


def expand_template(tpl: str) -> str:
    tables = {}
    for block in re.split(r"^### ", TABLES.read_text(encoding="utf-8"), flags=re.M)[1:]:
        head, body = block.split("\n", 1)
        tables[head.split()[0]] = body.strip("\n")
    tpl = re.sub(r"\{\{T:([\w.]+)\}\}", lambda m: tables[m.group(1)], tpl)

    def code(m):
        rel = m.group(1)
        lang = {"v": "verilog", "py": "python"}[rel.rsplit(".", 1)[1]]
        return f"```{lang}\n{(ROOT / rel).read_text(encoding='utf-8').rstrip()}\n```"

    return re.sub(r"\{\{CODE:([^}]+)\}\}", code, tpl)


def compose_template():
    """Dựng đồ án từ bao_cao.md: các dòng @chapter, @section, @sub, @apphead, @appsec, @ref và markdown thường."""
    tpl = expand_template(TEMPLATE.read_text(encoding="utf-8"))
    c = Composer()
    buf, nref = [], [0]

    def flush():
        if buf:
            c.text(buf)
            buf.clear()

    for ln in tpl.split("\n"):
        m = re.match(r"^@(chapter!?|section!?|sub|apphead|appsec|ref)\s+(.*)$", ln)
        if not m:
            buf.append(ln)
            continue
        flush()
        cmd, arg = m.groups()
        arg = arg.strip()
        if cmd == "chapter":
            c.chapter(arg)
        elif cmd == "chapter!":
            c.chapter(arg, numbered=False)
        elif cmd == "section":
            c.section(arg)
        elif cmd == "section!":
            c.section(arg, numbered=False)
        elif cmd == "sub":
            c.subsection(arg)
        elif cmd == "apphead":
            letter, title = [x.strip() for x in arg.split("|", 1)]
            c.app_head(letter, title)
        elif cmd == "appsec":
            c.app_sub(arg)
        elif cmd == "ref":
            nref[0] += 1
            c.emit("", f'<div class="ref">[{nref[0]}]&nbsp;&nbsp;{arg}</div>', "")
    flush()
    c.qa_mark = None
    if INCLUDE_QA:
        c.qa_mark = c.chapter("Ôn tập vấn đáp (tài liệu nội bộ nhóm)", numbered=False, toc=False)
        out = []
        for ln in QA_FILE.read_text(encoding="utf-8").splitlines():
            if ln.startswith("### "):
                out.append(f'<h3 class="sub">{html.escape(ln[4:].strip())}</h3>')
            elif ln.startswith("## "):
                out.append(f'<h2 class="app">{html.escape(ln[3:].strip())}</h2>')
            else:
                out.append(ln)
        c.emit("", *out, "")
    return c


# ---------------------------------------------------------------- HTML và PDF
def run_pandoc(md_text: str) -> str:
    p = subprocess.run(["pandoc", "-f", "gfm+tex_math_dollars+raw_html", "-t", "html5", "--mathml",
                        "--syntax-highlighting=none"], input=md_text, capture_output=True, text=True,
                       encoding="utf-8", check=True)
    h = p.stdout
    h = re.sub(r"<li>(?:<p>)?☑ ", '<li class="chk">', h)
    h = re.sub(r"<li>(?:<p>)?□ ", '<li class="chk0">', h)
    h = re.sub(r"<p><strong>(Câu [A-Z0-9.]+)</strong>", r'<p class="q"><strong>\1</strong>', h)
    h = re.sub(r"<p><em>([^<]{3,70}:)</em></p>", r'<p class="hint"><em>\1</em></p>', h)

    def tclass(m):
        n = len(re.findall(r"<th", m.group(0).split("</tr>")[0]))
        rows = m.group(0).count("<tr")
        cls = ("t7" if n >= 6 else "t5" if n >= 4 else "") + (" short" if rows <= 13 else "")
        cls = cls.strip()
        return m.group(0).replace("<table", f'<table class="{cls}"' if cls else "<table", 1)

    h = re.sub(r"<table.*?</table>", tclass, h, flags=re.S)
    h = re.sub(r'(<table[^>]*>)\s*<colgroup>.*?</colgroup>', r"\1", h, flags=re.S) if False else h
    return h


def page_html(body: str, css=CSS) -> str:
    return f'<!doctype html><html lang="vi"><head><meta charset="utf-8"><style>{css}</style></head><body>{body}</body></html>'


def edge_pdf(html_text: str, name: str) -> Path:
    hp, pp = TMP / f"{name}.html", TMP / f"{name}.pdf"
    hp.write_text(html_text, encoding="utf-8")
    pp.unlink(missing_ok=True)
    # Hồ sơ riêng để Edge không giao việc cho một phiên Edge đang chạy rồi thoát sớm (làm PDF chưa kịp ghi)
    subprocess.run([find_browser(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--user-data-dir={TMP / 'edge_profile'}", f"--print-to-pdf={pp}", hp.as_uri()],
                   check=True, timeout=240)
    for _ in range(240):                       # chờ tối đa 2 phút cho PDF được ghi xong
        if pp.exists() and pp.stat().st_size > 0:
            break
        time.sleep(0.5)
    return pp


def roman(n):
    out = ""
    for v, s in [(10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]:
        while n >= v:
            out += s
            n -= v
    return out


def cover_html():
    def one():
        return f"""
<div class="pg">
  <p class="abs b" style="top:59pt;font-size:14.9pt;">ĐẠI HỌC BÁCH KHOA HÀ NỘI</p>
  <div style="position:absolute;left:258pt;top:80pt;width:108pt;border-top:0.8pt solid #000"></div>
  <p class="abs sans" style="top:219pt;font-size:21.9pt;">ĐỒ ÁN MÔN HỌC</p>
  <p class="abs sans" style="top:283pt;font-size:16.9pt;line-height:26.3pt;">TĂNG TỐC SIMD ĐA LUỒNG CHO XỬ LÝ ẢNH<br>SỬ DỤNG VERILOG</p>
  <p class="abs b" style="top:372pt;font-size:12pt;">Nhóm sinh viên thực hiện</p>
  <p class="abs" style="top:396pt;font-size:12pt;line-height:22pt;">[Họ tên 1] – [MSSV]<br>[Họ tên 2] – [MSSV]<br>[Họ tên 3] – [MSSV]<br>[Họ tên 4] – [MSSV]</p>
  <p class="abs b" style="top:498pt;font-size:13pt;">Học phần MI4344 – Kiến trúc máy tính</p>
  <p class="row b" style="left:149pt;top:548pt;">Giảng viên hướng dẫn:</p>
  <p class="row" style="left:288pt;top:548pt;">Nguyễn Đình Hân</p>
  <div style="position:absolute;left:385pt;top:566pt;width:100pt;border-top:0.4pt solid #000"></div>
  <p class="row" style="left:396pt;top:569pt;font-size:10pt;">Chữ ký của GVHD</p>
  <p class="row b" style="left:149pt;top:610pt;">Bộ môn:</p>
  <p class="row" style="left:288pt;top:610pt;">Kiến trúc máy tính</p>
  <p class="row b" style="left:149pt;top:637pt;">Khoa:</p>
  <p class="row" style="left:288pt;top:637pt;">Toán-Tin</p>
  <p class="abs b" style="top:758pt;font-size:13pt;">HÀ NỘI {DATE}</p>
</div>"""
    return page_html(one() + one(), COVER_CSS)


def front_html():
    return page_html(f"""
<div class="front-title">Lời cảm ơn</div>
<p>Trước hết, nhóm xin gửi lời cảm ơn chân thành đến giảng viên Nguyễn Đình Hân, giảng viên học phần MI4344 – Kiến trúc máy tính, đã giảng dạy và định hướng cho nhóm trong suốt quá trình học tập và thực hiện đồ án. Những kiến thức về hiệu năng, số học máy tính và pipeline trong học phần là nền tảng trực tiếp của đề tài này.</p>
<p>Nhóm cũng xin cảm ơn Khoa Toán-Tin, Đại học Bách khoa Hà Nội đã tạo điều kiện học tập và môi trường để nhóm thực hiện đồ án.</p>
<p>Do kiến thức và thời gian còn hạn chế, đồ án không tránh khỏi thiếu sót. Nhóm rất mong nhận được sự góp ý để đề tài được hoàn thiện hơn.</p>
<p>Nhóm xin chân thành cảm ơn!</p>
<p class="sig">Nhóm sinh viên thực hiện<br><small>Ký và ghi rõ họ tên</small></p>
<div class="front-title pageb">Tóm tắt nội dung đồ án</div>
<p>Nhóm thiết kế bằng Verilog một bộ tăng tốc kiểu SIMD đa lane cho bộ lọc trung bình 3×3 và mô phỏng với 1, 2 và 4 lane. Bộ tăng tốc nhận luồng pixel, giữ hai dòng ảnh trong bộ đệm dòng, tạo P cửa sổ 3×3 mỗi chu kỳ và chuyển cho P lane giống hệt nhau; mỗi lane cộng 9 pixel bằng cây cộng, chia cho 9 bằng nhân hằng số rồi dịch bit, và được chia thành 5 stage pipeline. Đồ án vận dụng kiến thức của học phần: hiệu năng và định luật Amdahl (LN01), số học máy tính (LN04) và pipeline (LN06).</p>
<p>Kết quả được đối chiếu với mô hình tham chiếu viết bằng Python: không có pixel nào sai ở mọi cấu hình và mọi ảnh thử. Tổng số chu kỳ khớp mô hình T = ⌈W·H/P⌉ + 6, trong đó 6 là độ sâu pipeline. Ở cùng chu kỳ xung nhịp, số pixel ra mỗi chu kỳ (throughput) tăng gần tuyến tính theo số lane, đạt 3,969 pixel/chu kỳ và speedup 3,999 lần ở 4 lane; phần cố định chỉ là thời gian làm đầy pipeline nên theo định luật Amdahl nó gần như không giới hạn speedup.</p>
<p>Một thí nghiệm mở rộng cho thấy giới hạn thật là tốc độ cấp dữ liệu: nếu chỉ cấp B nhỏ hơn P pixel mỗi chu kỳ thì throughput chỉ xấp xỉ B, thêm lane vượt quá B không giúp gì. Đồ án chưa có số đo chu kỳ xung nhịp của mạch thật, nên việc so sánh hiệu năng được làm ở cùng chu kỳ xung nhịp.</p>
<p class="sig">Nhóm sinh viên thực hiện<br><small>Ký và ghi rõ họ tên</small></p>
""")


def symbols_html():
    rows = [("SIMD", "Single Instruction, Multiple Data (một thao tác trên nhiều dữ liệu)"),
            ("TB", "Testbench (mô-đun Verilog chỉ dùng để mô phỏng)"),
            ("CPI", "Cycles Per Instruction (số chu kỳ trung bình mỗi lệnh)"),
            ("CLO", "Course Learning Outcome (chuẩn đầu ra học phần)"),
            ("P", "Số lane (số cửa sổ xử lý song song mỗi chu kỳ)"), ("W, H", "Chiều rộng và chiều cao ảnh (pixel)"),
            ("B", "Số pixel cấp vào mỗi chu kỳ"), ("D", "Độ sâu pipeline (số chu kỳ từ vào đến ra, D = 6)"),
            ("T_P", "Tổng số chu kỳ xử lý một ảnh với P lane"), ("L_P", "Độ trễ tới pixel ra đầu tiên với P lane")]
    t = "".join(f"<tr><td>{html.escape(a)}</td><td>{html.escape(b)}</td></tr>" for a, b in rows)
    return page_html(f'<h1 class="chap nobreak">DANH MỤC KÝ HIỆU VÀ CHỮ VIẾT TẮT</h1><table class="sym">{t}</table>')


def list_html(title, entries, pages):
    rows = "".join(
        f'<div class="lst-row"><span class="lab"><em>{html.escape(l)}</em></span><span class="t">{html.escape(cap)}</span>'
        f'<span class="dots"></span><span class="pg">{pages[mk]}</span></div>' for l, cap, mk in entries)
    return page_html(f'<h1 class="chap nobreak">{title}</h1>{rows}')


def toc_html(entries, pages, lead):
    rows = "".join(f'<div class="toc-row lvl0"><span class="t">{html.escape(t)}</span><span class="dots"></span><span class="pg">{p}</span></div>'
                   for t, p in lead)
    out = ""
    for lvl, num, title, mk in entries:
        p = pages[mk]
        if lvl == 0:
            out += (f'<div class="toc-row lvl0"><span class="t">{html.escape(title)}</span>'
                    f'<span class="dots"></span><span class="pg">{p}</span></div>')
        else:
            out += (f'<div class="toc-row lvl{lvl}"><span class="n">{num}</span><span class="t">{html.escape(title)}</span>'
                    f'<span class="dots"></span><span class="pg">{p}</span></div>')
    return page_html(f'<h1 class="chap nobreak">MỤC LỤC</h1>{rows}{out}')


def find_pages(pdf: Path, marks):
    d = fitz.open(str(pdf))
    pages, texts = {}, [pg.get_text() for pg in d]
    for mk in marks:
        for i, t in enumerate(texts):
            if mk in t:
                pages[mk] = i + 1
                break
        else:
            raise SystemExit(f"Không tìm thấy dấu {mk} trong PDF thân bài")
    return pages, len(d)


def build_qa():
    """Dựng riêng file ôn tập vấn đáp (tài liệu nội bộ nhóm) thành PDF."""
    if not QA_FILE.exists():
        raise SystemExit(f"Không có {QA_FILE.name}: file ôn tập là tài liệu nội bộ, không nằm trong kho mã.")
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir()
    out = ['<h1 class="chap nobreak">Ôn tập vấn đáp (tài liệu nội bộ nhóm)</h1>']
    for ln in QA_FILE.read_text(encoding="utf-8").splitlines():
        if ln.startswith("### "):
            out.append(f'<h3 class="sub">{html.escape(ln[4:].strip())}</h3>')
        elif ln.startswith("## "):
            out.append(f'<h2 class="app">{html.escape(ln[3:].strip())}</h2>')
        else:
            out.append(ln)
    pdf = edge_pdf(page_html(run_pandoc("\n".join(out))), "qa")
    d = fitz.open(str(pdf))
    for i, pg in enumerate(d):
        text = str(i + 1)
        w = fitz.get_text_length(text, fontname="tiro", fontsize=12)
        pg.insert_text((311.8 - w / 2, 812), text, fontname="tiro", fontsize=12)
    d.set_metadata({"title": "Ôn tập vấn đáp MI4344", "author": "Nhóm sinh viên MI4344"})
    d.save(str(OUT_QA), garbage=3, deflate=True)
    print("ok", OUT_QA.name, len(d), "trang")


def main():
    if "--qa" in sys.argv[1:]:
        return build_qa()
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir()
    comp = compose_template()
    body_md = "\n".join(comp.md)
    (TMP / "body.md").write_text(body_md, encoding="utf-8")
    body = run_pandoc(body_md)
    body_pdf = edge_pdf(page_html(body), "body")
    marks = [t[3] for t in comp.toc] + [t[2] for t in comp.figs] + [t[2] for t in comp.tabs]
    if comp.qa_mark:
        marks.append(comp.qa_mark)
    pages, nbody = find_pages(body_pdf, marks)
    # Render lần hai không có dấu định vị để lớp văn bản của PDF sạch; bố cục giữ nguyên vì dấu không chiếm chỗ
    clean = re.sub(r'<span class="mk">@@\d+@@</span>', "", body)
    body_pdf = edge_pdf(page_html(clean), "body_final")
    assert len(fitz.open(str(body_pdf))) == nbody, "Số trang thân bài đổi sau khi bỏ dấu"

    sym_pdf = edge_pdf(symbols_html(), "sym")
    figs_pdf = edge_pdf(list_html("DANH MỤC HÌNH VẼ", comp.figs, pages), "figs")
    tabs_pdf = edge_pdf(list_html("DANH MỤC BẢNG BIỂU", comp.tabs, pages), "tabs")
    n_sym, n_fig, n_tab = (len(fitz.open(str(p))) for p in (sym_pdf, figs_pdf, tabs_pdf))
    r_sym, r_fig, r_tab = 1, 1 + n_sym, 1 + n_sym + n_fig
    lead = [("DANH MỤC KÝ HIỆU VÀ CHỮ VIẾT TẮT", roman(r_sym)), ("DANH MỤC HÌNH VẼ", roman(r_fig)),
            ("DANH MỤC BẢNG BIỂU", roman(r_tab))]
    toc_pdf = edge_pdf(toc_html(comp.toc, pages, lead), "toc")
    front_pdf = edge_pdf(front_html(), "front")

    out = fitz.open()
    labels = []                                    # (nhãn số trang hoặc None) theo thứ tự trang
    parts = [(front_pdf, None), (toc_pdf, None), (sym_pdf, "r"), (figs_pdf, "r"), (tabs_pdf, "r"), (body_pdf, "a")]
    if COVER:
        parts.insert(0, (edge_pdf(cover_html(), "cover"), None))
    for pdf, kind in parts:
        d = fitz.open(str(pdf))
        out.insert_pdf(d)
        for i in range(len(d)):
            labels.append((kind, i))
    roman_counter = 0
    first_body = None
    for idx, (kind, i) in enumerate(labels):
        if kind == "r":
            roman_counter += 1
            text = roman(roman_counter)
        elif kind == "a":
            first_body = idx if first_body is None else first_body
            text = str(idx - first_body + 1)
        else:
            continue
        pg = out[idx]
        w = fitz.get_text_length(text, fontname="tiro", fontsize=12)
        pg.insert_text((311.8 - w / 2, 812), text, fontname="tiro", fontsize=12)
    toc_items = []
    for lvl, num, title, mk in comp.toc:
        label = (f"{num} {title}" if num else title)
        toc_items.append([lvl + 1, label, first_body + pages[mk]])
    if comp.qa_mark:
        toc_items.append([1, "ÔN TẬP VẤN ĐÁP (nội bộ nhóm, gỡ trước khi nộp)", first_body + pages[comp.qa_mark]])
    out.set_toc(toc_items)
    out.set_metadata({"title": TITLE, "author": "Nhóm sinh viên MI4344", "subject": "Đồ án môn học MI4344 – Kiến trúc máy tính"})
    out.save(str(OUT), garbage=3, deflate=True)
    print("ok", OUT.name, len(out), "trang; thân bài", nbody, "trang")


if __name__ == "__main__":
    main()
