# -*- coding: utf-8 -*-
"""_bytepat.py — 只读：在 .text 里按字节模式搜索并反汇编命中点上下文。

用法：
    python _bytepat.py "6b c9 24" [--ctx 6] [--max 40]
"""
import re
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

SRC = r"D:\Program Files\PeG\PeG030.exe"
TEXT_VA, TEXT_FO, TEXT_RAW = 0x401000, 0x400, 0x8A200


def main():
    pat = bytes.fromhex(sys.argv[1].replace(" ", ""))
    ctx = 6
    mx = 60
    if "--ctx" in sys.argv:
        ctx = int(sys.argv[sys.argv.index("--ctx") + 1])
    if "--max" in sys.argv:
        mx = int(sys.argv[sys.argv.index("--max") + 1])
    data = open(SRC, "rb").read()
    blob = data[TEXT_FO:TEXT_FO + TEXT_RAW]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    addrs = []
    i = blob.find(pat)
    while i >= 0:
        addrs.append(TEXT_VA + i)
        i = blob.find(pat, i + 1)
    print("模式 %s  命中 %d 处" % (sys.argv[1], len(addrs)))
    for a in addrs[:mx]:
        print("\n--- 0x%06X ---" % a)
        fo = a - TEXT_VA
        cnt = 0
        for ins in md.disasm(blob[fo:fo + 200], a):
            mark = ">>" if ins.address == a else "  "
            print("  %s 0x%06X  %-8s %s" % (mark, ins.address, ins.mnemonic, ins.op_str))
            cnt += 1
            if cnt >= ctx:
                break


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
