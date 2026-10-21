# -*- coding: utf-8 -*-
"""_immfind2.py — 只读：在 .text 全量线性反汇编里找**操作数值**等于给定数值的指令。

稳健线性扫描：遇到非法字节只前进 1 字节继续，不会提前终止。

覆盖两类：
  A. IMM  —— 立即数（mov eax,0x320 / cmp eax,0x258 / push 0x1F4 ...）
  B. DISP —— 内存操作数位移（mov edx,word ptr [ecx+0x490474] 这类表访问）

用法：
    python _immfind2.py 0x320 0x258 0x23C 0x31C 0x226 0x2BC 0x2FA 0x313 0x1F4 0x780
    python _immfind2.py --only-disp 0x490470 0x490474 0x490472
    python _immfind2.py --count 0x320        # 只要计数
"""
import sys
import collections
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM
from capstone.x86 import X86_OP_MEM

SRC = r"D:\Program Files\PeG\PeG030.exe"
TEXT_VA, TEXT_FO, TEXT_RAW = 0x401000, 0x400, 0x8A136


def sweep(md, blob, va):
    off = 0
    n = len(blob)
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
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    only_disp = "--only-disp" in sys.argv
    only_imm = "--only-imm" in sys.argv
    count_only = "--count" in sys.argv
    want = set(int(a, 16) for a in args)
    d = open(SRC, "rb").read()
    blob = d[TEXT_FO:TEXT_FO + TEXT_RAW]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    hits = []
    total = 0
    for ins in sweep(md, blob, TEXT_VA):
        total += 1
        src = []
        if not only_disp:
            for op in ins.operands:
                if op.type == CS_OP_IMM and op.imm >= 0 and (op.imm & 0xFFFFFFFF) in want:
                    src.append("IMM")
        if not only_imm:
            for op in ins.operands:
                if op.type == X86_OP_MEM and (op.mem.disp & 0xFFFFFFFF) in want:
                    src.append("DISP")
        if src:
            hits.append((ins.address, sorted(set(src)), "%s %s" % (ins.mnemonic, ins.op_str),
                         ins.bytes.hex(" ")))
    print("扫描字节 = 0x%X  成功解码指令 = %d  命中 = %d" % (TEXT_RAW, total, len(hits)))
    if count_only:
        c = collections.Counter()
        for _a, s, _t, _h in hits:
            c[",".join(s)] += 1
        for k in sorted(c):
            print("   %-12s %d" % (k, c[k]))
        return
    for a, s, t, h in hits:
        print("  0x%06X  [%-9s] %-38s | %s" % (a, ",".join(s), t, h))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
