# -*- coding: utf-8 -*-
"""定位 DirectDraw Blt / BltFast 调用点，并打印上下文（只读）。

判据（来自 pg-cht 方法论）：
    IDirectDrawSurface::Blt      vtable +0x14  ->  call dword ptr [reg + 0x14]
    IDirectDrawSurface::BltFast  vtable +0x18  ->  call dword ptr [reg + 0x18]
    DDBLT_WAIT 的字节指纹        68 00 00 00 01  (push 0x1000000)

用法：
    python probe_blt.py            # 列出所有命中点 + 上下文
    python probe_blt.py --list     # 只列 VA
"""
import sys

import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, Cs
from capstone.x86 import X86_OP_MEM, X86_REG_ESP, X86_REG_EBP

EXE = r"D:\Program Files\PeG\PeG030.exe"
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x401000, 0x400, 565760


def main():
    listonly = "--list" in sys.argv
    pe = pefile.PE(EXE, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    code = None
    for s in pe.sections:
        if base + s.VirtualAddress == TEXT_VA:
            code = s.get_data()
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    insns = list(md.disasm(code[:TEXT_SIZE], TEXT_VA))
    hits = []
    for i, ins in enumerate(insns):
        if ins.mnemonic != "call" or not ins.operands:
            continue
        op = ins.operands[0]
        if op.type != X86_OP_MEM or op.mem.base == 0:
            continue
        d = op.mem.disp
        if d in (0x14, 0x18):
            hits.append((i, ins, "Blt" if d == 0x14 else "BltFast"))
    print("Blt 命中 %d 处，BltFast 命中 %d 处" % (
        sum(1 for h in hits if h[2] == "Blt"), sum(1 for h in hits if h[2] == "BltFast")))
    if listonly:
        for _i, ins, kind in hits:
            print("  0x%x  %s  %s" % (ins.address, kind, ins.op_str))
        return 0
    for i, ins, kind in hits:
        print("\n=== %s @0x%x  %s" % (kind, ins.address, ins.op_str))
        lo = max(0, i - 14)
        for j in range(lo, min(len(insns), i + 3)):
            mark = " >>" if j == i else "   "
            s = "0x%-8x %-8s %s" % (insns[j].address, insns[j].mnemonic, insns[j].op_str)
            if j < i and any(t in s for t in ("0x4cce2c", "0x4904", "0x48f3", "0x493b",
                                              "0x4a03", "0x4cce30", "0x4904")):
                mark = " !!"
            print(mark + s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
