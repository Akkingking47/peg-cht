# -*- coding: utf-8 -*-
"""_da.py — 只读：反汇编 .text 指定区间（稳健，遇到非法字节前进 1 继续）。

用法：
    python _da.py 0x41F3E0 0x41F420
    python _da.py 0x41F3E0:60            # 从该地址起 60 条
"""
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

SRC = r"D:\Program Files\PeG\PeG030.exe"
TEXT_VA, TEXT_FO, TEXT_RAW = 0x401000, 0x400, 0x8A136
TEXT_END = TEXT_VA + TEXT_RAW


def main():
    a = sys.argv[1]
    if ":" in a:
        lo, n = a.split(":")
        lo, hi = int(lo, 16), None
        limit = int(n)
    else:
        lo, hi = int(sys.argv[1], 16), int(sys.argv[2], 16)
        limit = 10 ** 9
    d = open(SRC, "rb").read()
    off = TEXT_FO + (lo - TEXT_VA)
    blob = d[off:off + (0x8A136 - (lo - TEXT_VA))]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    cnt = 0
    p = 0
    while p < len(blob) and cnt < limit:
        if hi is not None and lo + p >= hi:
            break
        got = False
        for ins in md.disasm(blob[p:p + 16], lo + p):
            got = True
            print("0x%06X  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
            p += ins.size
            cnt += 1
            break
        if not got:
            print("0x%06X  db 0x%02X" % (lo + p, blob[p]))
            p += 1
    print("--- 共 %d 条 ---" % cnt)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
