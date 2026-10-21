# -*- coding: utf-8 -*-
"""PeG 研究档案 · 素材抽取
产出（写到 peg/research/evidence/）：
  gui-languages.tsv     7 个 GUI 文本文件逐行对照（行号 → 各语言）
  ply-narrative.txt     全部 *.ply 原文（定长 501 B 记录）
  exe-hardcoded.tsv     exe 内硬编码串 + 文件偏移
  gui030-lines.tsv      Gui030.txt 全文带行号 + 分区标注
"""
import os, re, glob, struct, collections

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


OUT = os.path.join(WS, "peg", "research", "evidence")
os.makedirs(OUT, exist_ok=True)

def readlines_cp(p):
    d = open(p, "rb").read()
    t = d.decode("cp1252")
    return t.split("\r\n")

# ---------------- 1. GUI 文件逐行对照 ----------------
GUIS = ["GUI97.TXT", "GUI97.DEU", "GUI97.FRA", "GUI98.TXT",
        "GUISA.txt", "GUISP.TXT", "Gui030.txt", "Gui031.txt"]
cols = {}
for g in GUIS:
    p = os.path.join(GAME, g)
    cols[g] = readlines_cp(p) if os.path.exists(p) else None
n = max(len(v) for v in cols.values() if v)
with open(os.path.join(OUT, "gui-languages.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("line\t" + "\t".join(GUIS) + "\n")
    for i in range(n):
        row = []
        for g in GUIS:
            v = cols[g]
            row.append(v[i] if v and i < len(v) else "")
        f.write(f"{i+1}\t" + "\t".join(x.replace("\t", " ") for x in row) + "\n")
print("gui-languages.tsv:", n, "rows")

# ---------------- 2. 全部 .ply ----------------
plies = sorted(glob.glob(os.path.join(GAME, "Scenario", "*.ply")) +
               glob.glob(os.path.join(GAME, "Userscen", "*.ply")))
lines = ["PEeG *.ply 定长记录原文（每文件 501 B）", "=" * 70, ""]
for p in plies:
    d = open(p, "rb").read()
    body = d.split(b"\x00")[0]
    lines.append(f"--- {os.path.basename(p)}   ({len(d)} B)   [非空 {len(body)} B]")
    lines.append(body.decode("cp1252", "replace"))
    lines.append("")
open(os.path.join(OUT, "ply-narrative.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print("ply-narrative.txt:", len(plies), "files")

# ---------------- 3. exe 硬编码串 ----------------
exe = os.path.join(GAME, "PeG030.exe")
d = open(exe, "rb").read()
# .data 段 FO 0x8b800, VA 0x48e000
def va(fo): return fo - 0x8b800 + 0x48e000
gui = [l for l in cols["Gui030.txt"]]
rows = []
for l in gui:
    if len(l) < 3:
        continue
    b = l.encode("cp1252", "replace") + b"\x00"
    for m in re.finditer(re.escape(b), d):
        rows.append((l, hex(m.start()), hex(va(m.start())) if 0x8b800 <= m.start() < 0x8b800 + 0x21400 else ""))
with open(os.path.join(OUT, "exe-hardcoded.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("string\tfile_offset\tva\n")
    for a, b, c in rows:
        f.write(f"{a}\t{b}\t{c}\n")
print("exe-hardcoded.tsv:", len(rows), "hits /", len(gui), "gui lines")

# ---------------- 4. Gui030.txt 带行号 ----------------
SEC = {}
sec = ""
for i, l in enumerate(cols["Gui030.txt"], 1):
    if not l.strip():
        continue
    # 分区：首行/全大写且无小写字母 视为分区头
    if l.strip() == l.strip().upper() and len(l.strip()) > 3 and not re.search(r"\d", l):
        sec = l.strip()
    SEC[i] = sec
with open(os.path.join(OUT, "gui030-lines.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("line\tsection\ttext\n")
    for i, l in enumerate(cols["Gui030.txt"], 1):
        f.write(f"{i}\t{SEC.get(i,'')}\t{l}\n")
print("gui030-lines.tsv:", len(cols["Gui030.txt"]), "rows")
# 打印分区头
seen = []
for i, s in SEC.items():
    if s and (not seen or seen[-1] != s):
        seen.append(s)
print("sections:", seen)
