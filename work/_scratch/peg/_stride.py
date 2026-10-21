# -*- coding: utf-8 -*-
"""_stride.py — 只读：找出所有 imul r,r,Imm 与 lea 组合，按乘数分组，用于发现表步长。

用法：
    python _stride.py 0x41 0x58 0x18 0x24 0x41 0x58
    python _stride.py --all          # 列出所有 0x10..0x200 的乘数
"""
import sys
import collections
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM

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
    allm = "--all" in sys.argv
    want = set(int(a, 16) for a in sys.argv[1:] if not a.startswith("--"))
    d = open(SRC, "rb").read()
    blob = d[TEXT_FO:TEXT_FO + TEXT_RAW]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    g = collections.defaultdict(list)
    for ins in sweep(md, blob, TEXT_VA):
        if ins.mnemonic != "imul":
            continue
        if len(ins.operands) == 3 and ins.operands[2].type == CS_OP_IMM:
            m = ins.operands[2].imm & 0xFFFFFFFF
        else:
            continue
        if allm:
            if not (0x10 <= m <= 0x200):
                continue
        else:
            if m not in want:
                continue
        g[m].append(ins.address)
    for m in sorted(g):
        print("\n步长 0x%X (%d)  x%d" % (m, m, len(g[m])))
        print("   " + " ".join("0x%06X" % a for a in g[m]))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
