# -*- coding: utf-8 -*-
"""_refs2.py — 只读：稳健线性扫描，列出所有**指令操作数**等于给定值的位置。

覆盖 IMM / DISP（内存位移）/ 直接内存地址（如 mov eax,[0x61e928] 走 DISP）。
输出：目标值 -> 地址列表(带反汇编)。

用法：
    python _refs2.py 0x61E928 0x663388 0x6769A8 0x4CCE2C 0x498D74
    python _refs2.py --ops 0x61E928       # 只列反汇编
"""
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM
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
    want = {}
    for a in sys.argv[1:]:
        if a.startswith("--"):
            continue
        want[int(a, 16)] = []
    d = open(SRC, "rb").read()
    blob = d[TEXT_FO:TEXT_FO + TEXT_RAW]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    for ins in sweep(md, blob, TEXT_VA):
        for op in ins.operands:
            t = None
            if op.type == CS_OP_IMM and op.imm >= 0:
                t = op.imm & 0xFFFFFFFF
            elif op.type == X86_OP_MEM:
                t = op.mem.disp & 0xFFFFFFFF
            if t in want:
                want[t].append((ins.address, "%s %s" % (ins.mnemonic, ins.op_str),
                                ins.bytes.hex(" ")))
    for t in sorted(want):
        rows = want[t]
        print("\n=== 0x%06X === 引用 %d 处" % (t, len(rows)))
        for a, txt, hx in rows:
            if ops:
                print("   0x%06X  %s" % (a, txt))
            else:
                print("   0x%06X  %-36s | %s" % (a, txt, hx))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
