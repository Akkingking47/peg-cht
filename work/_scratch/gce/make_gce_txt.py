# -*- coding: utf-8 -*-
r"""为 GCE 生成本地 `txt_workbench.py`（只改 EFILE 与先例表路径）。

用法: python make_gce_txt.py
产出: work\gce\txt_workbench.py
⚠️ 先例表＝**本 efile 自己的** `gce-xscn-map.tsv`（MECHANICS §19.2：`.xscn` 组 0 就是
   场景 `.txt` 名单的镜像）⇒ 复用即自动满足跨层一致，且覆盖率远高于跨 efile 借先例。
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
src = io.open(os.path.join(r"D:\DSH\军事游戏汉化\work\comww2", "txt_workbench.py"),
              encoding="utf-8").read()

src = src.replace('EFILE = "EFILE_COMWW2"', 'EFILE = "EFILE_GCE"')
src = src.replace('PRE = os.path.join(HERE, "comww2-xscn-map.tsv")',
                  'PRE = os.path.join(HERE, "gce-xscn-map.tsv")')
src = src.replace('"""COMWW2 场景 `.txt` 层工作台', '"""GCE 场景 `.txt` 层工作台')
assert 'EFILE = "EFILE_GCE"' in src and "gce-xscn-map.tsv" in src

with io.open(os.path.join(HERE, "txt_workbench.py"), "w", encoding="utf-8", newline="") as f:
    f.write(src)
print("已写 work\\gce\\txt_workbench.py（%d B）" % len(src.encode("utf-8")))
