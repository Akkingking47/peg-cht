# -*- coding: utf-8 -*-
"""为 PzLIGA 生成场景 .txt 汉化器（从 KAISER gen_txt_zh.py 派生）。"""
import io, os
HERE = os.path.dirname(os.path.abspath(__file__))
src = io.open(r"D:/DSH/军事游戏汉化/work/kaiser/gen_txt_zh.py", encoding="utf-8").read()

src = src.replace('KAISER 场景 `.txt` 层汉化生成器（2,203 个文件）。',
                  'PzLIGA 场景 `.txt` 层汉化生成器（378 个文件）。')
src = src.replace('EFILE_KAISER', 'EFILE_PzLIGA')
src = src.replace('XSCN_MAP = os.path.join(HERE, "xscn-map.tsv")',
                  'XSCN_MAP = os.path.join(HERE, "pzliga-xscn-map.tsv")')
assert 'EFILE_PzLIGA' in src
assert 'pzliga-xscn-map.tsv' in src
with io.open(os.path.join(HERE, "gen_txt_zh.py"), "w", encoding="utf-8", newline="") as f:
    f.write(src)
print("已写 work/efile_pzliga/gen_txt_zh.py")
