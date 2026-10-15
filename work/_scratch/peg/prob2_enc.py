# -*- coding: utf-8 -*-
"""prob2_enc.py — 试各种编码/变体定位提示串。"""
import sys
sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\peg")
import hint_pe as H

base = H.load(H.SRC)
port = H.load(H.PORT)

S = "\u6b65\u5175"   # 步兵
T = "\u5e03\u96f7\u5fb7\u5229"  # 布雷德利

print("--- 步兵 variants ---")
pats = {
    "cp936": H.cp936(S),
    "utf16le": S.encode("utf-16-le"),
    "utf8": S.encode("utf-8"),
    "cp950": None,
}
for k, v in pats.items():
    if v is None:
        continue
    for tag, d in (("SRC", base), ("PORT", port)):
        hits = H.find_bytes(d, v)
        print("  %-8s %-4s %d" % (k, tag, len(hits)), ["0x%06X" % va for _, va in hits[:8]])

print("--- 布雷德利 variants ---")
for k, enc in (("cp936", "cp936"), ("utf16le", "utf-16-le"), ("utf8", "utf-8")):
    v = T.encode(enc)
    for tag, d in (("SRC", base), ("PORT", port)):
        hits = H.find_bytes(d, v)
        print("  %-8s %-4s %d" % (k, tag, len(hits)), ["0x%06X" % va for _, va in hits[:8]])

# 单独字 步 (0xB2BD) / 兵 (0xB1F8)
print("--- single chars cp936 ---")
for ch in "\u6b65\u5175\u5e03\u96f7\u5fb7\u5229":
    v = H.cp936(ch)
    h1 = H.find_bytes(base, v)
    h2 = H.find_bytes(port, v)
    print("  %s %s  SRC=%d PORT=%d  first SRC va=%s" % (
        ch, v.hex(" "), len(h1), len(h2),
        ["0x%06X" % va for _, va in h1[:5]]))
