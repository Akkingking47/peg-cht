# -*- coding: utf-8 -*-
"""只读：给定函数内部的某个 VA，回溯找函数起始（靠 cc 填充/c3 cc 边界），并反汇编到该 VA 之后。"""
import sys

sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\peg")
import hint_pe as H

d = H.load(H.SRC)
addr = int(sys.argv[1], 16)
span = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x6A
fo = H.va_to_fo(addr)

start_fo = None
i = fo - 1
limit = max(0x400, fo - 0x3000)
while i > limit:
    if d[i] == 0xCC and d[i + 1] == 0xCC and d[i + 2] == 0xCC:
        start_fo = i + 1
        while start_fo < fo and d[start_fo] == 0xCC:
            start_fo += 1
        break
    i -= 1

print("target VA=0x%06X fo=0x%X" % (addr, fo))
if start_fo is None:
    print("no cc padding found; try --off")
    sys.exit(0)
start_va = H.fo_to_va(start_fo)
print("func start VA=0x%06X (bytes before: %s)" % (start_va, d[start_fo - 8:start_fo].hex(" ")))
for ins in H.dis_all(start_va, addr + span, d):
    txt = "%s %s" % (ins.mnemonic, ins.op_str)
    b = H.blob(d, ins.address, ins.size)
    mark = "  <<<" if ins.address <= addr < ins.address + ins.size else ""
    print("0x%06X  %-26s %s%s" % (ins.address, b.hex(" "), txt, mark))
