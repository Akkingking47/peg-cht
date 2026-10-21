# -*- coding: utf-8 -*-
"""_immrange.py — 只读：列出 .text 里所有立即数落在给定区间的指令（即代码直接引用的数据地址）。

用法：
    python _immrange.py 0x4A0000 0x4D0000
    python _immrange.py 0x4A0000 0x4D0000 --norep
"""
import struct
import sys
import collections
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM

SRC = r"D:\Program Files\PeG\PeG030.exe"
TEXT_VA, TEXT_FO, TEXT_RAW = 0x401000, 0x400, 0x8A200
SECS = [(".text", 0x401000, 0x400, 0x8A136),
        (".rdata", 0x48C000, 0x8A600, 0x1017),
        (".data", 0x48E000, 0x8B800, 0x21BF3C),
        (".idata", 0x6AA000, 0xACC00, 0x1434),
        (".rsrc", 0x6AC000, 0xAE200, 0x52DC)]


def fo_to_va(fo):
    for _n, sva, raw, size in SECS:
        if raw <= fo < raw + size:
            return sva + (fo - raw)
    return None


def main():
    lo = int(sys.argv[1], 16)
    hi = int(sys.argv[2], 16)
    group = "--group" in sys.argv
    data = open(SRC, "rb").read()
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    blob = data[TEXT_FO:TEXT_FO + TEXT_RAW]
    hits = []
    off = 0
    while off < len(blob):
        got = False
        for ins in md.disasm(blob[off:off + 16], TEXT_VA + off):
            got = True
            for op in ins.operands:
                if op.type == CS_OP_IMM and lo <= (op.imm & 0xFFFFFFFF) < hi:
                    hits.append((ins.address, op.imm & 0xFFFFFFFF, ins.mnemonic, ins.op_str))
            off += ins.size
        if not got:
            off += 1
    print("区间 0x%X..0x%X  命中 %d 处" % (lo, hi, len(hits)))
    if group:
        g = collections.defaultdict(list)
        for a, t, m, o in hits:
            g[t].append(a)
        for t in sorted(g):
            print("  0x%06X x%-3d  %s" % (t, len(g[t]), " ".join("0x%06X" % a for a in g[t][:14])))
        return
    for a, t, m, o in hits:
        print("   0x%06X  -> 0x%06X  %-8s %s" % (a, t, m, o))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
