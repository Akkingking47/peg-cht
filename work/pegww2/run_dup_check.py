#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 `dup_check.py` 的完整输出落盘（沙箱禁止 PowerShell 管道包裹原生 exe，故用本包装器）。

用法: python run_dup_check.py [topN]   → 写 pegww2\research\evidence\dup-check.txt
"""
import io
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
sys.path.insert(0, os.path.join(WS, "work", "pegww2"))
sys.argv = ["dup_check.py", sys.argv[1] if len(sys.argv) > 1 else "200"]
import dup_check  # noqa: E402

REPORT = os.path.join(WS, "pegww2", "research", "evidence", "dup-check.txt")


class Tee:
    def __init__(self, *s):
        self.s = s

    def write(self, x):
        for t in self.s:
            t.write(x)
        return len(x)

    def flush(self):
        for t in self.s:
            t.flush()


buf = io.StringIO()
sys.stdout = Tee(sys.stdout, buf)
dup_check.main()
sys.stdout = sys.__stdout__
with open(REPORT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(buf.getvalue())
print(f"[落盘] {REPORT}")
