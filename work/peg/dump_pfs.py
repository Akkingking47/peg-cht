# -*- coding: utf-8 -*-
"""导出 PeG File Specs 中与本地化相关的表"""
import xlrd, os, sys

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


XL = os.path.join(GAME, "Docs", "File Specs", "00 PeG File Specs (PFS).xls")
OUT = os.path.join(WS, "work", "peg", "pfs")
os.makedirs(OUT, exist_ok=True)
b = xlrd.open_workbook(XL)
want = sys.argv[1:] if len(sys.argv) > 1 else [
    "Introduction", "Table of Contents", "File Load Sequence", "PeG Versions",
    "GUI-Segmented", "GUI-Other Languages", "SCN & CAM text files",
    ".S16", "SCN", "CAM", "Names", "Tips", "Misc", "INT", "MAP",
    "Graphics Color Depths", "CORE GAME FILE BLOCKS", "Version Signature",
    ".DAT", "High.SCR", "Sound Files Overview", "Scenario Types",
]
def cell(sh, r, c):
    v = sh.cell_value(r, c)
    return v.strip() if isinstance(v, str) else v

for name in want:
    try:
        sh = b.sheet_by_name(name)
    except Exception:
        print("MISSING SHEET:", name); continue
    lines = [f"### SHEET: {name}  ({sh.nrows} x {sh.ncols})"]
    for r in range(sh.nrows):
        row = [str(cell(sh, r, c)) for c in range(sh.ncols)]
        while row and row[-1] == "":
            row.pop()
        if any(x != "" for x in row):
            lines.append(f"{r:>4d} | " + " | ".join(row))
    txt = "\n".join(lines) + "\n"
    fn = os.path.join(OUT, name.replace("/", "_").replace("&", "and") + ".txt")
    open(fn, "w", encoding="utf-8").write(txt)
    print(f"wrote {os.path.basename(fn)}  ({len(lines)-1} rows)")
