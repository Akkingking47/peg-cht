# -*- coding: utf-8 -*-
"""COMWW2 根级四件套量测 + 跨 efile 行对齐复用率。

跨 efile 复用（MECHANICS §16）：某 efile 的根级文件若有 `TEXT-ZH` 版本，
则「根级原文行 → TEXT-ZH 译文行」按**行号对齐**构成字典（前提：两侧行数一致）。
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
GAME = r"D:\OpenPG2"
TGT = "EFILE_COMWW2"
FILES = ["equip.txt", "names.txt", "nations.txt", "strings_efile.txt"]
HAN = re.compile(r"[\u4e00-\u9fff]")
LAT = re.compile(r"[A-Za-z]")


def dec(b, enc):
    try:
        return b.decode(enc)
    except UnicodeDecodeError:
        return b.decode(enc, "replace")


def split_lines(b):
    return dec(b, "cp1252").replace("\r\n", "\n").split("\n")


# ---- 1. 建跨 efile 字典 ----
donors = {}
for d in sorted(os.listdir(GAME)):
    if not d.upper().startswith("EFILE_") or d == TGT:
        continue
    z = os.path.join(GAME, d, "TEXT-ZH")
    if not os.path.isdir(z):
        continue
    for fn in FILES:
        sp, tp = os.path.join(GAME, d, fn), os.path.join(z, fn)
        if not (os.path.exists(sp) and os.path.exists(tp)):
            continue
        s = split_lines(open(sp, "rb").read())
        t = split_lines(open(tp, "rb").read())
        if len(s) != len(t):
            print("  !! 行数不等，跳过：%s/%s (src %d vs zh %d)" % (d, fn, len(s), len(t)))
            continue
        dd = donors.setdefault(fn, {})
        n = 0
        for a, b_ in zip(s, t):
            if a.strip() and b_ and b_ != a:
                dd.setdefault(a, b_)
                n += 1
        print("  donor %-22s %-18s 行 %d -> 词条 %d" % (d, fn, len(s), n))

print()
# ---- 2. 量测 COMWW2 目标文件 ----
base = os.path.join(GAME, TGT)
grand = [0, 0, 0, 0]
for fn in FILES:
    p = os.path.join(base, fn)
    if not os.path.exists(p):
        print("%-18s 不存在" % fn)
        continue
    raw = open(p, "rb").read()
    lines = split_lines(raw)
    nonblank = [l for l in lines if l.strip()]
    uniq = set(nonblank)
    dd = donors.get(fn, {})
    # 已含汉字（不该有）
    has_han = sum(1 for l in nonblank if HAN.search(l))
    # 复用命中
    hit = [l for l in nonblank if l in dd]
    # 无字母（纯数字/符号 -> 无需译）
    noletter = [l for l in nonblank if not LAT.search(l)]
    need = [l for l in uniq if LAT.search(l) and l not in dd]
    print("%-18s %6dB 行 %-5d 非空 %-5d 唯一 %-5d | 已含汉字 %d | 复用命中 %-4d | 纯数字 %-4d | 待译唯一 %-5d (%d 字符)"
          % (fn, len(raw), len(lines), len(nonblank), len(uniq), has_han,
             len(hit), len(noletter), len(need), sum(len(x) for x in need)))
    grand[0] += len(nonblank)
    grand[1] += len(hit)
    grand[2] += len(noletter)
    grand[3] += len(need)
    if need:
        out = os.path.join(r"D:\DSH\军事游戏汉化\work\comww2", "_todo_" + fn.replace(".txt", "") + ".txt")
        with io.open(out, "w", encoding="utf-8", newline="\n") as f:
            for x in sorted(need):
                f.write(x + "\n")
print()
print("合计：非空 %d | 复用命中 %d | 纯数字 %d | 待译唯一 %d" % tuple(grand))
