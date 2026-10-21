# -*- coding: utf-8 -*-
"""_xrefcall.py — 只读：.text 里所有 call/jmp 到给定目标区间的点（含条件跳转）。

用法：
    python _xrefcall.py 0x43D680 0x43D690
    python _xrefcall.py 0x41F000 0x420000 --max 200
"""
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM

SRC = r"D:\Program Files\PeG\PeG030.exe"
TEXT_VA, TEXT_FO, TEXT_RAW = 0x401000, 0x400, 0x8A200


def main():
    lo = int(sys.argv[1], 16)
    hi = int(sys.argv[2], 16)
    mx = 500
    if "--max" in sys.argv:
        mx = int(sys.argv[sys.argv.index("--max") + 1])
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
            if ins.mnemonic.startswith(("call", "j")) and ins.operands and ins.operands[0].type == CS_OP_IMM:
                t = ins.operands[0].imm & 0xFFFFFFFF
                if lo <= t < hi:
                    hits.append((ins.address, ins.mnemonic, t))
            off += ins.size
        if not got:
            off += 1
    print("区间 0x%X..0x%X  命中 %d" % (lo, hi, len(hits)))
    for a, m, t in hits[:mx]:
        print("   0x%06X  %-6s -> 0x%06X" % (a, m, t))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
