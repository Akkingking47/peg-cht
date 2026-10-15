# -*- coding: utf-8 -*-
"""独立取证：各 efile `.xscn` 里「明显未译」的串（德/法/英 词形，与假汉字启发式无关）。

判据（高置信、宁缺勿滥）：
  A) 整串纯 ASCII（无高位字节）且含拉丁字母 —— 不可能是中文译文
  B) 含 cp1252 变音符字节，且 cp1252 解读下匹配典型德/法/英 词形
"""
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

UM = set(b"\xe4\xf6\xfc\xdf\xe9\xe8\xea\xeb\xe0\xe2\xef\xf4\xfb\xf1\xe7\xc9\xd6\xdc\xc4\xd6")
WORD = re.compile(
    rb"(Division|Regiment|Regt|Abteilung|Abt|Brigade|Bde|Korps|River|Div\b|Fallschirm|"
    rb"Infanterie|Panz|Kavallerie|Artillerie|Bataillon|Btl|Gruppe|Armee|Grenadier|"
    rb"d'Infanterie|de |Division |Regiment )")

rows = []
for d in sorted(os.listdir(GAME)):
    if not d.upper().startswith("EFILE_"):
        continue
    A = B = n = 0
    for f in glob.glob(os.path.join(GAME, d, "SCENARIO", "*.xscn")):
        try:
            _t, ent = prog.parse_xscn(open(f, "rb").read())
        except Exception:
            continue
        for e in ent:
            if not e.strip():
                continue
            n += 1
            if re.fullmatch(rb"[\x20-\x7e]+", e) and re.search(rb"[A-Za-z]{2,}", e):
                A += 1
            elif any(c in UM for c in e) and WORD.search(e):
                B += 1
    rows.append((d[6:], n, A, B, A + B))

print("%-14s %8s %8s %8s %8s" % ("efile", "串数", "A纯ASCII", "B变音符词形", "明显未译"))
for r in sorted(rows, key=lambda x: -x[4]):
    print("%-14s %8d %8d %8d %8d" % r)
