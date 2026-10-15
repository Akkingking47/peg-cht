# -*- coding: utf-8 -*-
"""转储写入后的 .xscn 全部条目（智能解码），便于人工抽检。"""
import sys

sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\efile-nashornpbem")
from verify_xscn import parse, decode_smart, han_count  # noqa

p = sys.argv[1]
x = parse(p)
print("标题: %r   组: %s   条目: %d" % (x["title"], x["groups"], len(x["items"])))
print("=" * 78)
nonhan = []
for g, i, raw, old in x["items"]:
    enc, s = decode_smart(raw)
    if han_count(s) == 0:
        nonhan.append((g, i, enc, s))
    print("[g%d.%03d] (%s) %s" % (g, i, enc, s))
print("=" * 78)
print("无汉字条目: %d" % len(nonhan))
for g, i, enc, s in nonhan:
    print("   g%d.%03d (%s) %r" % (g, i, enc, s))
