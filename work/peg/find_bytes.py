# -*- coding: utf-8 -*-
"""在 exe 某节里按字节模式搜索（支持 .. 通配一个字节）。只读。

用法：
    python find_bytes.py "ff .. 14"          # 默认 .text
    python find_bytes.py "68 00 00 00 01" .text
    python find_bytes.py "ff .. 44" .text --ctx 6
"""
import sys

import pefile

EXE = r"D:\Program Files\PeG\PeG030.exe"
SECTIONS = {".text": (0x401000, 0x400, 565760), ".rdata": (0x48C000, 0x8A600, 4608),
            ".data": (0x48E000, 0x8B800, 136192), ".idata": (0x6AA000, 0xACC00, 5632),
            ".rsrc": (0x6AC000, 0xAE200, 21504)}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    pat = [None if t == ".." else int(t, 16) for t in sys.argv[1].split()]
    sec = ".text"
    ctx = 0
    args = sys.argv[2:]
    for i, a in enumerate(args):
        if a in SECTIONS:
            sec = a
        elif a == "--ctx":
            ctx = int(args[i + 1])
    va0, raw, size = SECTIONS[sec]
    with open(EXE, "rb") as f:
        data = f.read()
    buf = data[raw:raw + size]
    n = len(pat)
    hits = []
    for i in range(len(buf) - n):
        ok = True
        for k in range(n):
            if pat[k] is not None and buf[i + k] != pat[k]:
                ok = False
                break
        if ok:
            hits.append(i)
    print("模式 %s 在 %s 命中 %d 处" % (" ".join(".." if b is None else "%02x" % b for b in pat),
                                     sec, len(hits)))
    for i in hits:
        line = "  VA 0x%06x  FO 0x%06x  %s" % (
            va0 + i, raw + i, buf[max(0, i - ctx):i + n + ctx].hex(" "))
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
