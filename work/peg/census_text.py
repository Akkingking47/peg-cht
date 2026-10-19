# -*- coding: utf-8 -*-
"""PeG 文本层普查：按扩展名统计文件数 / 内嵌可打印串 / 是否含拉丁字母文本"""
import os, re, glob, collections

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


WORD = re.compile(rb"[\x20-\x7e]{4,}")
LETTERS = re.compile(rb"[A-Za-z]{4,}")

stats = collections.defaultdict(lambda: {"files": 0, "bytes": 0, "strs": 0,
                                         "wordstrs": 0, "maxstr": 0})
samples = collections.defaultdict(list)
for root, dirs, files in os.walk(GAME):
    for fn in files:
        p = os.path.join(root, fn)
        ext = os.path.splitext(fn)[1].lower() or "<none>"
        try:
            sz = os.path.getsize(p)
        except OSError:
            continue
        s = stats[ext]
        s["files"] += 1; s["bytes"] += sz
        if ext in (".exe", ".dll", ".dat") or sz > 2_000_000:
            continue  # 二进制大件跳过（已单独分析）
        try:
            d = open(p, "rb").read()
        except OSError:
            continue
        for m in WORD.finditer(d):
            s["strs"] += 1
            L = len(m.group())
            if L > s["maxstr"]:
                s["maxstr"] = L
            if LETTERS.search(m.group()):
                s["wordstrs"] += 1
                if len(samples[ext]) < 6:
                    samples[ext].append((os.path.basename(p), m.group().decode("latin-1")))

print(f"{'ext':8s} {'files':>6s} {'MB':>8s} {'strs':>8s} {'有字母串':>8s} {'最长':>5s}")
for ext, s in sorted(stats.items(), key=lambda kv: -kv[1]["wordstrs"]):
    print(f"{ext:8s} {s['files']:>6d} {s['bytes']/1048576:>8.2f} {s['strs']:>8d} "
          f"{s['wordstrs']:>8d} {s['maxstr']:>5d}")
print()
for ext in (".scn", ".cam", ".ply", ".map", ".eqp", ".int", ".aux", ".txt", ".csv", ".sav"):
    if samples.get(ext):
        print(f"--- {ext} 样例 ---")
        for a, b in samples[ext][:6]:
            print(f"    {a:<28s} {b[:70]!r}")
