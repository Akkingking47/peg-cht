# -*- coding: utf-8 -*-
"""读取 PowerShell 重定向输出（可能是 UTF-16LE 或 ASCII）。"""
import sys

p = sys.argv[1] if len(sys.argv) > 1 else r"D:\DSH\军事游戏汉化\work\efile-nashornpbem\dryrun-raw.txt"
raw = open(p, "rb").read()
print("bytes = %d" % len(raw))
for enc in ("utf-16", "utf-8-sig", "gbk", "latin-1"):
    try:
        txt = raw.decode(enc)
        print("== decoded as %s ==" % enc)
        print(txt)
        break
    except Exception as e:
        print("  fail %s: %s" % (enc, e))
