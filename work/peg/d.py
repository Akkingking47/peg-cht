# -*- coding: utf-8 -*-
"""d.py — 反汇编工具：
  d.py <lo> <hi> [--exe SRC|PORT] [--grep re] [--imm minhex]
"""
import re
import sys
sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\peg")
import hint_pe as H

argv = sys.argv[1:]
d = None
lo = int(argv[0], 16)
hi = int(argv[1], 16)
grep = None
minimm = None
if "--exe" in argv:
    i = argv.index("--exe")
    d = H.load(H.SRC if argv[i + 1].upper() == "SRC" else H.PORT)
    del argv[i:i + 2]
if "--grep" in argv:
    i = argv.index("--grep")
    grep = re.compile(argv[i + 1])
    del argv[i:i + 2]
if "--imm" in argv:
    i = argv.index("--imm")
    minimm = int(argv[i + 1], 16)
    del argv[i:i + 2]
if d is None:
    d = H.load(H.SRC)

for ins in H.dis_all(lo, hi, d):
    txt = "%s %s" % (ins.mnemonic, ins.op_str)
    if grep and not grep.search(txt):
        continue
    if minimm is not None:
        nums = [int(x, 16) for x in re.findall(r"0x([0-9a-f]+)", ins.op_str)]
        if not any(x >= minimm for x in nums):
            continue
    b = H.blob(d, ins.address, ins.size)
    print("0x%06X  %-26s %s" % (ins.address, b.hex(" "), txt))
