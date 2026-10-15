# -*- coding: utf-8 -*-
"""扫「原文含非 ASCII 字节 ⇒ 走 latin-1 解码、与 UTF-8 映射表键永远对不上 ⇒ 静默未译」这一类缺陷。
判据：备份原文（latin-1 解码）该行含 ≥1 个高位字节，且已投放成品同一行不含任何汉字。"""
import io, os, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BK = r"D:\DSH\军事游戏汉化\pegww2\testbed\backup"
GAME = r"D:\Program Files\PeG-WW2"
CJK = re.compile(r"[\u4e00-\u9fff]")
WORD = re.compile(r"[A-Za-z]{2,}")
EX = re.compile(r"(?i)(^info\.txt$|read ?me|report|\.LOG$)")
hits = []
for sub in ("SCENARIO", "USERSCEN"):
    b = os.path.join(BK, sub)
    if not os.path.isdir(b):
        continue
    for fn in sorted(os.listdir(b)):
        if not fn.lower().endswith(".txt") or EX.search(fn):
            continue
        bp, gp = os.path.join(b, fn), os.path.join(GAME, sub, fn)
        if not os.path.isfile(gp):
            continue
        bl = io.open(bp, "rb").read().split(b"\n")
        gl = io.open(gp, "rb").read().split(b"\n")
        if len(bl) != len(gl):
            continue
        for i, (x, y) in enumerate(zip(bl, gl)):
            if not any(c > 127 for c in x):
                continue
            o = x.decode("latin-1").strip()
            if len(o) < 3 or not WORD.search(o):
                continue
            try:
                z = y.decode("gbk", errors="strict")
            except Exception:
                z = y.decode("gbk", errors="replace")
            if not CJK.search(z) and WORD.search(z.replace("\x00", "")):
                hits.append((sub, fn, i, o[:60], z.strip()[:30]))
print("原文含高位字节且成品仍未译：**%d 行 / %d 文件**" % (len(hits), len(set(h[1] for h in hits))))
for h in hits[:40]:
    print("   %s/%s:%d  %r  →  %r" % h)
