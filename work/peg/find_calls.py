# -*- coding: utf-8 -*-
"""find_calls.py —— 找 .text 里所有 `call <目标VA>` 的调用点，并打印前后各 N 条指令上下文。

用法：
    python find_calls.py 0x43fe70            # 默认上下文 6
    python find_calls.py 0x43fe70 10         # 上下文 10
"""
import sys

import capstone

EXE = r"D:\Program Files\PeG\PeG030.exe"
TEXT_VA, TEXT_RAW, TEXT_RS = 0x401000, 0x400, 0x8A200

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False


def disasm_all(md, blob, va0):
    out = []
    off = 0
    n = len(blob)
    nbad = 0
    while off < n:
        got = False
        for ins in md.disasm(blob[off:], va0 + off):
            out.append(ins)
            off += ins.size
            got = True
        if not got:
            off += 1
            nbad += 1
    return out, nbad


def main():
    target = int(sys.argv[1], 16)
    ctxn = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    blob = open(EXE, "rb").read()[TEXT_RAW:TEXT_RAW + TEXT_RS]
    ins_list, nbad = disasm_all(md, blob, TEXT_VA)
    print("反汇编 %d 条（坏字节跳过 %d），目标 call 0x%08X" % (len(ins_list), nbad, target))
    hits = []
    for i, ins in enumerate(ins_list):
        if ins.mnemonic != "call":
            continue
        op = ins.op_str
        if not op.startswith("0x"):
            continue
        try:
            tgt = int(op, 16)
        except ValueError:
            continue
        if tgt == target:
            hits.append(i)
    print("命中 %d 处" % len(hits))
    for i in hits:
        ins = ins_list[i]
        print("\n--- call @0x%06X ---" % ins.address)
        for j in range(max(0, i - ctxn), min(len(ins_list), i + 2)):
            mark = " >> " if j == i else "    "
            a = ins_list[j]
            print("%s0x%06X  %-8s %s" % (mark, a.address, a.mnemonic, a.op_str))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
