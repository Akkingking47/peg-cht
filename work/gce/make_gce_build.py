# -*- coding: utf-8 -*-
r"""为 GCE 生成本地 `build_xscn_map.py`（只改输入/输出文件名与 OWN 标记）。

用法: python make_gce_build.py
产出: work\gce\build_xscn_map.py（其余判据/守卫**逐字沿用** COMWW2 版）
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
src = io.open(os.path.join(r"D:\DSH\军事游戏汉化\work\comww2", "build_xscn_map.py"),
              encoding="utf-8").read()

src = src.replace('"""合成 COMWW2 `.xscn` 映射表', '"""合成 GCE `.xscn` 映射表')
src = src.replace('comww2-xscn-map.tsv', 'gce-xscn-map.tsv')
assert "gce-xscn-map.tsv" in src

with io.open(os.path.join(HERE, "build_xscn_map.py"), "w", encoding="utf-8", newline="") as f:
    f.write(src)
print("已写 work\\gce\\build_xscn_map.py")
