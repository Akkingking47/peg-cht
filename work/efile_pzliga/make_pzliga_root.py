# -*- coding: utf-8 -*-
"""为 PzLIGA 生成根级三件套汉化器（从 KAISER 版派生；PzLIGA 无 strings_efile.txt）。"""
import io, os
HERE = os.path.dirname(os.path.abspath(__file__))
src = io.open(os.path.join(r"D:/DSH/军事游戏汉化/work/kaiser", "gen_root_zh.py"), encoding="utf-8").read()

src = src.replace('"""KAISER 根级四件套汉化生成器', '"""PzLIGA 根级三件套汉化生成器')
src = src.replace('TGT = "EFILE_KAISER"', 'TGT = "EFILE_PZLIGA"')
src = src.replace('FILES = ["equip.txt", "names.txt", "nations.txt", "strings_efile.txt"]',
                  'FILES = ["equip.txt", "names.txt", "nations.txt"]')
src = src.replace('# ⭐ KAISER：载入多语言词表', '# ⭐ PzLIGA：载入德语 WW2 词表')
assert 'TGT = "EFILE_PZLIGA"' in src
assert 'FILES = ["equip.txt", "names.txt", "nations.txt"]' in src

with io.open(os.path.join(HERE, "gen_root_zh.py"), "w", encoding="utf-8", newline="") as f:
    f.write(src)
print("已写 work/efile_pzliga/gen_root_zh.py (%d B)" % len(src.encode("utf-8")))
