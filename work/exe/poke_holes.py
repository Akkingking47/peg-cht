# -*- coding: utf-8 -*-
"""扫描 OpenGen.exe 可用空洞（连续 NUL 区）并给出**安全性判定**。

⚠️ 只报「连续 NUL」是不够的（曾把 IMAGE_LOAD_CONFIG_DIRECTORY 当空洞，
   写入其 GlobalFlagsSet 字段 ⇒ 加载器打开调试标志 ⇒ 进程初始化 0xC0000005）。
   判定必须含：① 全 NUL ② 不与任何 PE 数据目录相交 ③ 区内 4B 对齐点 0 引用。

用法: python poke_holes.py [最小长度，默认16]
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pelib

EXE = sys.argv[2] if len(sys.argv) > 2 else r"D:/OpenPG2/OpenGen.exe"


def main():
    mn = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    d = open(EXE, "rb").read()
    p = pelib.PE(d)
    print("文件 %s  %d B" % (EXE, len(d)))
    print(pelib.describe(d))

    L = len(d)
    holes = []
    i = 0
    while i < L:
        if d[i] == 0:
            j = i
            while j < L and d[j] == 0:
                j += 1
            if j - i >= mn:
                holes.append((i, j - i))
            i = j
        else:
            i += 1

    print("\n>=%d 字节、且落在已映射区内的 NUL 段（按长度降序，前 40 个）：" % mn)
    rows = []
    for fo, ln in holes:
        sec, rva = p.fo2sec(fo)
        if rva is None or sec == "?":
            continue
        rows.append((ln, fo, sec, rva))
    rows.sort(reverse=True)
    for ln, fo, sec, rva in rows[:40]:
        probs = p.check_hole(fo, ln)
        sub = [x for x in probs if "相交" not in x]
        verdict = "✅ 安全" if not probs else ("❌ 目录相交" if len(sub) < len(probs) else "⚠ " + "; ".join(sub))
        print("  len %-6d FO 0x%06X VA 0x%08X %-7s %s"
              % (ln, fo, 0x400000 + rva, sec, verdict))


if __name__ == "__main__":
    main()
