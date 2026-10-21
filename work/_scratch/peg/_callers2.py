# -*- coding: utf-8 -*-
"""_callers2.py — 只读：稳健线性扫描，列出 `call/jmp 目标` 落在给定地址/区间的位置。

用法：
    python _callers2.py 0x43D680
    python _callers2.py 0x43D680 0x43D690
    python _callers2.py --in 0x43D500 0x43D800
"""
import sys
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
    inside = "--in" in sys.argv
    if inside:
        i = sys.argv.index("--in")
        lo, hi = int(sys.argv[i + 1], 16), int(sys.argv[i + 2], 16)
    else:
        lo = int(sys.argv[1], 16)
        hi = int(sys.argv[2], 16) if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else lo + 1
    d = open(SRC, "rb").read()
    blob = d[TEXT_FO:TEXT_FO + TEXT_RAW]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    n = 0
    for ins in sweep(md, blob, TEXT_VA):
        if ins.mnemonic not in ("call", "jmp"):
            continue
        if not ins.operands:
            continue
        op = ins.operands[0]
        if op.type != CS_OP_IMM:
            continue
        t = op.imm & 0xFFFFFFFF
        if lo <= t < hi:
            print("   0x%06X  %-6s -> 0x%06X" % (ins.address, ins.mnemonic, t))
            n += 1
    print("命中 %d 处  (区间 0x%06X..0x%06X)" % (n, lo, hi))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
