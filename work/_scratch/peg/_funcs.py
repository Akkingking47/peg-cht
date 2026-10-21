# -*- coding: utf-8 -*-
"""_funcs.py — 只读：推断函数边界。

规则：
  * 起始锚：`push ebp; mov ebp,esp`（55 8B EC，含 8B EC 的变体）
    或前一条指令是 ret / int3 / 填充字节
  * 结束锚：`ret`(C2/C3) 或 `int3`(CC) 之后紧跟函数起始或填充
用法：
    python _funcs.py 0x43B220          # 该地址所属函数
    python _funcs.py --list 0x43B000 0x43C000
    python _funcs.py --check 0x43B220  # 打印所属函数完整反汇编
"""
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

SRC = r"D:\Program Files\PeG\PeG030.exe"
TEXT_VA, TEXT_FO, TEXT_RAW = 0x401000, 0x400, 0x8A136
TEXT_END = TEXT_VA + TEXT_RAW


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


def build():
    d = open(SRC, "rb").read()
    blob = d[TEXT_FO:TEXT_FO + TEXT_RAW]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    insns = list(sweep(md, blob, TEXT_VA))
    starts = []
    n = len(insns)
    for i, ins in enumerate(insns):
        if ins.mnemonic == "push" and ins.op_str == "ebp":
            if i + 1 < n and insns[i + 1].mnemonic == "mov" and \
               insns[i + 1].op_str.replace(" ", "") == "ebp,esp":
                starts.append(ins.address)
        elif ins.mnemonic in ("ret", "int3"):
            if i + 1 < n:
                nxt = insns[i + 1]
                if not (nxt.mnemonic == "push" and nxt.op_str == "ebp"):
                    starts.append(nxt.address)
    starts = sorted(set(starts))
    return insns, starts


def func_of(addr, starts):
    lo = None
    for s in starts:
        if s <= addr:
            lo = s
        else:
            break
    return lo


def main():
    insns, starts = build()
    if "--list" in sys.argv:
        lo = int(sys.argv[1], 16)
        hi = int(sys.argv[2], 16)
        sel = [s for s in starts if lo <= s < hi]
        for i, s in enumerate(sel):
            nxt = sel[i + 1] if i + 1 < len(sel) else hi
            kind = "?" 
            print("  0x%06X .. 0x%06X" % (s, nxt))
        print("共 %d 个起点" % len(sel))
        return
    if "--count" in sys.argv:
        print("推测函数起点数 = %d  指令数 = %d" % (len(starts), len(insns)))
        return
    addr = int([a for a in sys.argv[1:] if not a.startswith("--")][0], 16)
    s = func_of(addr, starts)
    i = [k for k, v in enumerate(insns) if v.address == s][0]
    # 找结尾
    j = i
    while j < len(insns) - 1:
        if insns[j].mnemonic == "ret":
            break
        if insns[j].mnemonic == "int3" and insns[j + 1].address in starts:
            break
        j += 1
    print("地址 0x%06X 属于函数 0x%06X .. 0x%06X  (含 %d 条指令, 偏移 +0x%X)"
          % (addr, s, insns[j].address, j - i + 1, addr - s))
    if "--check" in sys.argv:
        for k in range(i, j + 1):
            print("  0x%06X  %-8s %s" % (insns[k].address, insns[k].mnemonic, insns[k].op_str))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
