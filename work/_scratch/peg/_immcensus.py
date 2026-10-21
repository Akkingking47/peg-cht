# -*- coding: utf-8 -*-
"""_immcensus.py — 只读：.text 全量立即数频次普查（聚焦几何/尺寸嫌疑区间）。

用法：
    python _immcensus.py [lo] [hi] [--top N] [--only v1,v2]
"""
import sys
import collections
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM

SRC = r"D:\Program Files\PeG\PeG030.exe"
TEXT_VA, TEXT_FO, TEXT_RAW = 0x401000, 0x400, 0x8A200


def main():
    lo = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x100
    hi = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x1000
    top = 200
    only = None
    if "--top" in sys.argv:
        top = int(sys.argv[sys.argv.index("--top") + 1])
    if "--only" in sys.argv:
        only = set(int(x, 0) for x in sys.argv[sys.argv.index("--only") + 1].split(","))

    data = open(SRC, "rb").read()
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    blob = data[TEXT_FO:TEXT_FO + TEXT_RAW]
    cnt = collections.Counter()
    sites = collections.defaultdict(list)
    off = 0
    while off < len(blob):
        got = False
        for ins in md.disasm(blob[off:off + 16], TEXT_VA + off):
            got = True
            for op in ins.operands:
                if op.type == CS_OP_IMM and lo <= (op.imm & 0xFFFFFFFF) < hi:
                    v = op.imm & 0xFFFFFFFF
                    cnt[v] += 1
                    sites[v].append((ins.address, ins.mnemonic, ins.op_str))
            off += ins.size
        if not got:
            off += 1

    print("区间 0x%X..0x%X   不同值 %d 个" % (lo, hi, len(cnt)))
    if only:
        for v in sorted(only):
            print("\n### %d (0x%X)  命中 %d" % (v, v, cnt.get(v, 0)))
            for a, m, o in sites.get(v, []):
                print("   0x%06X  %-8s %s" % (a, m, o))
        return
    for v, c in cnt.most_common(top):
        print("%6d (0x%04X)  x%d" % (v, v, c))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
