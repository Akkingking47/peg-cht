# -*- coding: utf-8 -*-
"""prob1_strings.py — 在母本/v10b 里定位提示串，并找引用它的指针。
中文一律用 \\uXXXX 转义，避免控制台/编码把脚本字面量弄坏。"""
import sys
sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\peg")
import hint_pe as H

base = H.load(H.SRC)
port = H.load(H.PORT)

CANDS = [
    "\u6b65\u5175\u5728\u57ce\u5e02",            # 步兵在城市
    "\u5e03\u96f7\u5fb7\u5229",                  # 布雷德利
    "\u54c8\u5df4\u7f57\u592b\u65af\u514b",      # 哈巴罗夫斯克
    "\u8fd1\u6218\u5730\u5f62\u4e2d\u653b\u9632\u6700\u4f73",  # 近战地形中攻防最佳
    "\u6b65\u5175",                              # 步兵
]

for s in CANDS:
    pat = H.cp936(s)
    print("=== U+%s  cp936=%s" % ("+".join("%04X" % ord(c) for c in s), pat.hex(" ")))
    for tag, d in (("SRC", base), ("PORT", port)):
        hits = H.find_bytes(d, pat)
        print("   %-4s %d hit(s)" % (tag, len(hits)))
        for fo, va in hits[:12]:
            sec = H.sec_of(va)
            print("      fo=0x%06X va=0x%06X %s" % (fo, va, sec))
