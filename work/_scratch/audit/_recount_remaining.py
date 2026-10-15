# -*- coding: utf-8 -*-
"""重算「其余 efile 的实测工作量」——供 docs\\00 §三 手写投影更新。"""
import io
import os
import re
import sys
import glob
import importlib.util

sys.stdout.reconfigure(encoding="utf-8")
GAME = r"D:\OpenPG2"
spec = importlib.util.spec_from_file_location("prog", r"D:\DSH\军事游戏汉化\work\audit\progress.py")
prog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prog)

DONE = {"AG", "AO", "ATOMIC_NOT", "BASEKORP", "NASHORNPBEM", "OLGWW2", "OPENPG"}
DONE = {"AG", "AO", "BASEKORP", "NASHORNPBEM", "OLGWW2", "OPENPG"}

all_ef = sorted(d for d in os.listdir(GAME) if d.upper().startswith("EFILE_"))
rem = [d for d in all_ef if d[6:] not in DONE]
print("efile 合计 %d | 已完成 %d | 其余 %d" % (len(all_ef), len(all_ef) - len(rem), len(rem)))
print("其余：", ", ".join(d[6:] for d in rem))

LAT = re.compile(r"[A-Za-z]")

# --- .xscn 条数 + 唯一串 ---
n = 0
uniq = set()
for d in rem:
    for f in glob.glob(os.path.join(GAME, d, "SCENARIO", "*.xscn")):
        try:
            _t, ent = prog.parse_xscn(open(f, "rb").read())
        except Exception:
            continue
        for e in ent:
            n += 1
            uniq.add(e)
print("\n.xscn 条 %d | 唯一串 %d" % (n, len(uniq)))

# --- 根级四件套唯一串（含拉丁字母的非空行） ---
tot_root = 0
per = []
for fn in ["equip.txt", "names.txt", "nations.txt", "strings_efile.txt"]:
    u = set()
    used = []
    for d in rem:
        p = os.path.join(GAME, d, fn)
        if not os.path.exists(p):
            continue
        used.append(d[6:])
        for ln in open(p, "rb").read().decode("cp1252", "replace").replace("\r\n", "\n").split("\n"):
            s = ln.strip()
            if s and LAT.search(s):
                u.add(s)
    per.append("%s %s" % (fn.split(".")[0], format(len(u), ",")))
    tot_root += len(u)
print("根级四件套唯一串合计 %s（%s）" % (format(tot_root, ","), " · ".join(per)))
print("  覆盖 efile 数：equip %s" % [d for d in rem])

# --- 场景 .txt ---
nf = kb = 0
for d in rem:
    for f in glob.glob(os.path.join(GAME, d, "SCENARIO", "*.txt")):
        nf += 1
        kb += os.path.getsize(f)
print("\n场景 .txt %d 个 / %d KB" % (nf, kb // 1024))

# --- .ply 有正文 ---
pb = 0
for d in rem:
    for f in glob.glob(os.path.join(GAME, d, "SCENARIO", "*.ply")):
        b = open(f, "rb").read().replace(b"\x00", b"")
        s = b.decode("cp1252", "replace")
        if len(s.strip()) > 30 and "Intro text" not in s:
            pb += 1
print(".ply 有正文 %d" % pb)
