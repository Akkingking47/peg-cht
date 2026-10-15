# -*- coding: utf-8 -*-
"""静态交叉引用：找出 .text 里引用了给定地址区间（默认＝v4 补丁动过的 .data 站点）
的指令，并打印上下文。

为什么需要：v4 的 82 条「工具列按钮矩形」是 .data 记录（x 在 +0、right 在 +4、
记录步长 36 字节），代码怎么读它们决定了右移能不能生效。只看数据改了什么不够，
必须看**谁在读**。

用法：
    python xref_data.py                # 用 res_diff_v4.tsv 里 .data 站点的地址区间
    python xref_data.py 0x490496 0x491000 [前后行数]
"""
import os
import sys

import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_MEM, Cs

ROOT = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG"
EXE = os.path.join(GAME, "PeG030.exe")
TSV = os.path.join(ROOT, r"work\peg\out\res_diff_v4.tsv")
OUT = os.path.join(ROOT, r"work\peg\out")


def load_site_range():
    lo, hi = None, None
    with open(TSV, "r", encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 8 or p[1] != ".data":
                continue
            va = int(p[2], 16)
            lo = va if lo is None else min(lo, va)
            hi = va if hi is None else max(hi, va)
    return lo, hi


def main():
    if len(sys.argv) >= 3:
        lo, hi = int(sys.argv[1], 16), int(sys.argv[2], 16)
    else:
        lo, hi = load_site_range()
    ctx = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    print("地址区间 0x%x .. 0x%x" % (lo, hi))

    pe = pefile.PE(EXE, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    sec = None
    for s in pe.sections:
        if s.Name.rstrip(b"\x00") == b".text":
            sec = s
    code = sec.get_data()
    va0 = base + sec.VirtualAddress

    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    hits = []          # (va, disp, kind, text)
    insns = []         # (va, size, text) 全部指令，供打印上下文
    off = 0
    n = len(code)
    while off < n - 15:
        got = False
        for ins in md.disasm(code[off:off + 16], va0 + off):
            got = True
            refs = []
            for op in ins.operands:
                if op.type == CS_OP_MEM and lo <= op.mem.disp <= hi:
                    refs.append((op.mem.disp, "mem"))
                elif op.type == CS_OP_IMM and lo <= op.imm <= hi:
                    refs.append((op.imm, "imm"))
            txt = "%s %s" % (ins.mnemonic, ins.op_str)
            insns.append((ins.address, ins.size, txt))
            for d, k in refs:
                hits.append((ins.address, d, k, txt))
            off += ins.size
        if not got:
            off += 1

    print("反汇编 %d 条，命中 %d 处引用" % (len(insns), len(hits)))
    if not hits:
        print("（没有任何指令直接引用这个区间——说明记录是按「基址+变址」访问的，"
              "需要换招：找 36 字节步长的乘法/imul 与记录基址来源）")
        return 1

    idx = {}
    for i, (a, _s, _t) in enumerate(insns):
        idx[a] = i
    seen = set()
    shown = 0
    for a, d, k, txt in hits:
        if a in seen:
            continue
        seen.add(a)
        shown += 1
        if shown > 24:
            print("\n（引用过多，只打印前 24 处；完整列表见本文件开头的命中统计）")
            break
        i = idx[a]
        print("\n--- 引用 @0x%x  字段 0x%x (%s) ---" % (a, d, k))
        for j in range(max(0, i - ctx), min(len(insns), i + ctx + 1)):
            mark = ">>" if insns[j][0] == a else "  "
            print("  %s 0x%x  %s" % (mark, insns[j][0], insns[j][2]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
