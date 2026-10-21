# -*- coding: utf-8 -*-
"""按 VA 区间线性反汇编（只读）。

用法：
    python disasm_range.py 0x43fe70 0x43ff70
"""
import sys

import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, Cs

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
import os
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


EXE = os.path.join(GAME, "PeG030.exe")


def main():
    lo, hi = int(sys.argv[1], 16), int(sys.argv[2], 16)
    pe = pefile.PE(EXE, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    code = va0 = None
    for s in pe.sections:
        va = base + s.VirtualAddress
        if va <= lo < va + max(s.Misc_VirtualSize, s.SizeOfRawData):
            code, va0 = s.get_data(), va
            break
    if code is None:
        print("VA 不在任何节内")
        return 1
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = False
    for ins in md.disasm(code[lo - va0:hi - va0], lo):
        print("0x%-8x %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
