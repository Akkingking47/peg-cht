# -*- coding: utf-8 -*-
"""_bufscan.py — 只读：扫描 .text 里所有**直接内存操作数地址**（DISP 且无 base/index），
按地址分组列出引用点。用来发现"谁在读某张表 / 某个全局"。

用法：
    python _bufscan.py 0x620000 0x640000        # 区间内所有被引用的地址
    python _bufscan.py 0x620000 0x640000 --ops  # 带反汇编
    python _bufscan.py --around 0x622D00 0x100  # 中心±范围
"""
import sys
import collections
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM

SRC = r"D:\Program Files\PeG\PeG030.exe"
TEXT_VA, TEXT_FO, TEXT_RAW = 0x401000, 0x400, 0x8A136


def sweep(md, blob, va):
    off, n = 0, len(blob)
    while off < n:
        got = False
        for ins in md.disasm(blob[off:off + 16], va + off):
            got = True
            yield ins
            off += ins.size
            if ins.size == 0:
                break
        if not got:
            off += 1


def main():
    ops = "--ops" in sys.argv
    if "--around" in sys.argv:
        i = sys.argv.index("--around")
        c = int(sys.argv[i + 1], 16)
        r = int(sys.argv[i + 2], 16)
        lo, hi = c - r, c + r
    else:
        lo, hi = int(sys.argv[1], 16), int(sys.argv[2], 16)
    d = open(SRC, "rb").read()
    blob = d[TEXT_FO:TEXT_FO + TEXT_RAW]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    g = collections.defaultdict(list)
    for ins in sweep(md, blob, TEXT_VA):
        for op in ins.operands:
            if op.type != X86_OP_MEM:
                continue
            if op.mem.base != 0 or op.mem.index != 0:
                continue
            t = op.mem.disp & 0xFFFFFFFF
            if lo <= t < hi:
                g[t].append((ins.address, "%s %s" % (ins.mnemonic, ins.op_str)))
    print("区间 0x%06X..0x%06X  不同地址 %d 个" % (lo, hi, len(g)))
    for t in sorted(g):
        rows = g[t]
        print("\n0x%06X  x%d" % (t, len(rows)))
        for a, txt in rows:
            print("   0x%06X  %s" % (a, txt))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
