# -*- coding: utf-8 -*-
"""COMWW2 开工前全 efile 量测（对齐 docs\\32 AO 盘点口径）。"""
import io
import os
import re
import sys
import glob
import collections

sys.stdout.reconfigure(encoding="utf-8")

GAME = r"D:\OpenPG2"
EF = os.path.join(GAME, "EFILE_COMWW2")
HAN = re.compile(r"[\u4e00-\u9fff]")
LAT = re.compile(r"[A-Za-z]")


def gbk(b):
    try:
        return b.decode("gbk")
    except UnicodeDecodeError:
        return b.decode("gbk", "replace")


def cp(b):
    try:
        return b.decode("cp1252")
    except UnicodeDecodeError:
        return b.decode("cp1252", "replace")


print("=" * 72)
print("EFILE_COMWW2 全层量测")
print("=" * 72)

# ---- .xscn（复用 progress.py 的 parse_xscn，返回 (title, [bytes,...])） ----
import importlib.util
spec = importlib.util.spec_from_file_location("prog", r"D:\DSH\军事游戏汉化\work\audit\progress.py")
prog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prog)

n = nz = 0
uniq = set()
files_ok = 0
bad = []
for f in sorted(glob.glob(os.path.join(EF, "SCENARIO", "*.xscn"))):
    try:
        _t, ent = prog.parse_xscn(open(f, "rb").read())
    except Exception as e:
        bad.append((os.path.basename(f), str(e)[:60]))
        continue
    files_ok += 1
    for e in ent:
        n += 1
        s = gbk(e)
        uniq.add(s)
        if HAN.search(s):
            nz += 1
print("[L9 .xscn] 文件 %d（解析失败 %d）| 串 %d | 含汉字 %d | 唯一串 %d | 唯一含字母 %d"
      % (files_ok, len(bad), n, nz, len(uniq), sum(1 for s in uniq if LAT.search(s))))
if bad:
    for b in bad[:5]:
        print("   !! ", b)

# ---- .txt（SCENARIO） ----
tx = sorted(glob.glob(os.path.join(EF, "SCENARIO", "*.txt")))
lines = uniq_t = 0
han_t = 0
for f in tx:
    b = open(f, "rb").read()
    t = cp(b)
    for l in t.split("\r\n"):
        if l.strip():
            lines += 1
            uniq_t += 0  # 稍后去重
            if HAN.search(l):
                han_t += 1
print("[.txt] 文件 %d | 非空行 %d | 已含汉字行 %d" % (len(tx), lines, han_t))

# 唯一行
U = set()
for f in tx:
    t = cp(open(f, "rb").read())
    for l in t.split("\r\n"):
        if l.strip():
            U.add(l)
print("       唯一行 %d | 唯一含字母 %d | 唯一纯数字/符号 %d | 字符 %d"
      % (len(U), sum(1 for s in U if LAT.search(s)),
         sum(1 for s in U if not LAT.search(s)), sum(len(s) for s in U)))

# ---- .ply / .tmsg / .front / .xcam ----
grp = collections.Counter()
for sub in ["SCENARIO"]:
    for f in os.listdir(os.path.join(EF, sub)):
        grp[os.path.splitext(f)[1].lower()] += 1
print("[其它] " + "  ".join("%s=%d" % (k, v) for k, v in sorted(grp.items())))

# ---- 根级文件 ----
print("[根级]")
for fn in sorted(os.listdir(EF)):
    p = os.path.join(EF, fn)
    if not os.path.isfile(p):
        continue
    b = open(p, "rb").read()
    t = cp(b)
    nline = sum(1 for l in t.split("\r\n") if l.strip())
    nhan = len(HAN.findall(t))
    print("   %-20s %7dB  非空行 %-5d 汉字 %d" % (fn, len(b), nline, nhan))

# ---- OPENGUI / OPENDAT ----
for sub in ["OPENGUI", "OPENDAT"]:
    d = os.path.join(EF, sub)
    if os.path.isdir(d):
        fs = [f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))]
        print("[%s] %d 个文件: %s" % (sub, len(fs), ", ".join(sorted(fs)[:20])))

# ---- TEXT-ZH ----
print("[TEXT-ZH] 存在:", os.path.isdir(os.path.join(EF, "TEXT-ZH")))
