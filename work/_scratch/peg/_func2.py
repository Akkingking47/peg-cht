# -*- coding: utf-8 -*-
"""只读：找 addr 所属函数的起始——向前找最近的 55 8b ec 序言，用 capstone 正向解码验证能连续覆盖 addr。"""
import sys

sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\peg")
import hint_pe as H

d = H.load(H.SRC)
addr = int(sys.argv[1], 16)
span = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x60
fo = H.va_to_fo(addr)

best = None
for back in range(1, 0x1200):
    va = addr - back
    if va < 0x401000:
        break
    if H.blob(d, va, 3) == bytes([0x55, 0x8B, 0xEC]):
        ins = H.dis_all(va, addr + span, d)
        addrs = [x.address for x in ins]
        sizes = [x.size for x in ins]
        if addrs and addrs[0] == va:
            # check contiguous coverage
            ok = all(addrs[i] + sizes[i] == addrs[i + 1] for i in range(len(addrs) - 1))
            if ok and any(a <= addr < a + s for a, s in zip(addrs, sizes)):
                best = va
                break

print("target VA=0x%06X" % addr)
if best is None:
    print("no clean prologue found")
    sys.exit(0)
print("func start VA=0x%06X" % best)
for ins in H.dis_all(best, addr + span, d):
    b = H.blob(d, ins.address, ins.size)
    mark = "  <<<" if ins.address <= addr < ins.address + ins.size else ""
    print("0x%06X  %-26s %s %s%s" % (ins.address, b.hex(" "), ins.mnemonic, ins.op_str, mark))
