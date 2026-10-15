# -*- coding: utf-8 -*-
r"""从 COMWW2 的量测器派生 GCE 版（只改「排除自身」的规则，不动判据）。

用法: python make_gce_cov.py
产出: work\gce\measure_xscn_cov.py
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
COM = r"D:\DSH\军事游戏汉化\work\comww2"
OUT = os.path.join(HERE, "measure_xscn_cov.py")

src = io.open(os.path.join(COM, "measure_xscn_cov.py"), encoding="utf-8").read()

# 1) 「排除自身」由 comww2 改成 gce（COMWW2 的映射表对 GCE 是**合法 donor**）
old = 'os.path.dirname(p).lower().endswith("comww2")'
new = 'os.path.dirname(p).lower().endswith("gce")'
assert old in src, "未找到排除规则"
src = src.replace(old, new)

# 2) 文案
src = src.replace('"""COMWW2 `.xscn` 覆盖率', '"""GCE `.xscn` 覆盖率')
src = src.replace('print("COMWW2 .xscn 唯一串 %d" % len(uniq))',
                  'print("GCE .xscn 唯一串 %d" % len(uniq))')

# 3) 工作目录：本目录（work\gce）读写 xscn-uniq.tsv 等
src = src.replace('HERE = os.path.dirname(os.path.abspath(__file__))',
                  'HERE = os.path.dirname(os.path.abspath(__file__))  # = work\\gce')

with io.open(OUT, "w", encoding="utf-8", newline="") as f:
    f.write(src)
print("已写 %s（%d B）" % (OUT, len(src.encode("utf-8"))))
