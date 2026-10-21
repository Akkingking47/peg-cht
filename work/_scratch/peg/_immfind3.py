# -*- coding: utf-8 -*-
"""_immfind3.py — 只读：按**目标数值分组**列出的稳健线性扫描器。

用法：
    python _immfind3.py 0x320 0x258 ...           # 分组摘要（每组：数量 + 全部地址）
    python _immfind3.py --detail 0x320           # 详表（地址/来源/反汇编/字节）
    python _immfind3.py --detail 0x320 --no-disp  # 只看立即数
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


def collect(want, no_disp=False, no_imm=False):
    d = open(SRC, "rb").read()
    blob = d[TEXT_FO:TEXT_FO + TEXT_RAW]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    res = {t: [] for t in want}
    for ins in sweep(md, blob, TEXT_VA):
        src = []
        if not no_imm:
            for op in ins.operands:
                if op.type == CS_OP_IMM and op.imm >= 0 and (op.imm & 0xFFFFFFFF) in res:
                    src.append("IMM")
        if not no_disp:
            for op in ins.operands:
                if op.type == X86_OP_MEM and (op.mem.disp & 0xFFFFFFFF) in res:
                    src.append("DISP")
        for t in want:
            if t not in res:
                continue
            hit = False
            for op in ins.operands:
                if op.type == CS_OP_IMM and op.imm >= 0 and (op.imm & 0xFFFFFFFF) == t:
                    hit = True
                if op.type == X86_OP_MEM and (op.mem.disp & 0xFFFFFFFF) == t:
                    hit = True
            if hit:
                res[t].append((ins.address, sorted(set(src)),
                               "%s %s" % (ins.mnemonic, ins.op_str), ins.bytes.hex(" ")))
    return res


def main():
    detail = "--detail" in sys.argv
    no_disp = "--no-disp" in sys.argv
    no_imm = "--no-imm" in sys.argv
    want = [int(a, 16) for a in sys.argv[1:] if not a.startswith("--")]
    res = collect(want, no_disp, no_imm)
    for t in want:
        rows = res[t]
        print("\n=== 值 0x%X (%d) === 命中 %d" % (t, t, len(rows)))
        if not detail:
            print("   " + " ".join("0x%06X" % r[0] for r in rows))
        else:
            for a, s, txt, hx in rows:
                print("   0x%06X [%-9s] %-38s | %s" % (a, ",".join(s), txt, hx))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
