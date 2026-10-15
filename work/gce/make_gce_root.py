# -*- coding: utf-8 -*-
r"""为 GCE 生成本地 `gen_root_zh.py`（只改 GAME/TGT/HERE 与清空 COMWW2 专用人工表）。

用法: python make_gce_root.py
产出: work\gce\gen_root_zh.py（判据/守卫**逐字沿用** COMWW2 版）
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
src = io.open(os.path.join(r"D:\DSH\军事游戏汉化\work\comww2", "gen_root_zh.py"),
              encoding="utf-8").read()

src = src.replace('"""COMWW2 根级四件套汉化生成器', '"""GCE 根级四件套汉化生成器')
src = src.replace('TGT = "EFILE_COMWW2"', 'TGT = "EFILE_GCE"')
assert 'TGT = "EFILE_GCE"' in src

# 清空 COMWW2 专用人工表（GCE 用 root-manual.tsv，见下）
src = re.sub(r"MANUAL = \{.*?\n\}\n", "MANUAL = {}\n", src, count=1, flags=re.S)
assert "MANUAL = {}\n" in src

# 词表剔除项：COMWW2 专用（Class / Kevyt）改为 GCE 需注意的
src = src.replace('for _w in ("Class", "Kevyt"):', 'for _w in ("Class",):')

# ⭐ GCE 专属补丁：西语变音符折写（POLICY §五）
#    `'Légion'.encode('gbk')` 直接抛异常 ⇒ 原文的大量 ñ/é/á/í/ó/ú/ü 会把生成器打断。
#    折写规则：仅对 **GBK 编不了的字符** 取 NFKD 的 ASCII 残形（ñ→n · é→e · ü→u），
#    汉字与原样可编码字符一律不动。
src = src.replace(
    'LAT = re.compile(r"[A-Za-z]")',
    'LAT = re.compile(r"[A-Za-z]")\nimport unicodedata\n\n\n'
    'def gbk_safe(s):\n'
    '    """GBK 装不下的字符 → NFKD ASCII 折写（ñ→n / é→e / ü→u）。汉字不动。"""\n'
    '    out = []\n'
    '    for ch in s:\n'
    '        try:\n'
    '            ch.encode("gbk")\n'
    '            out.append(ch)\n'
    '        except UnicodeEncodeError:\n'
    '            a = "".join(c for c in unicodedata.normalize("NFKD", ch) if ord(c) < 128)\n'
    '            out.append(a if a else "?")\n'
    '    return "".join(out)')
assert "def gbk_safe(s):" in src

src = src.replace("        d, how = translate_line(fn, s)",
                  "        d, how = translate_line(fn, s)\n        d = gbk_safe(d)")
assert "d = gbk_safe(d)" in src

# ⭐ GCE 专属补丁 2：人工表命中时**保留原行的首尾空白**（更忠实的「逐行对齐」）
src = src.replace(
    '    if fn in MANUAL and s.strip() in MANUAL[fn]:\n'
    '        return MANUAL[fn][s.strip()], "人工"',
    '    if fn in MANUAL and s.strip() in MANUAL[fn]:\n'
    '        _lead = s[:len(s) - len(s.lstrip())]\n'
    '        _trail = s[len(s.rstrip()):]\n'
    '        return _lead + MANUAL[fn][s.strip()] + _trail, "人工"')
assert "_lead + MANUAL[fn][s.strip()] + _trail" in src

with io.open(os.path.join(HERE, "gen_root_zh.py"), "w", encoding="utf-8", newline="") as f:
    f.write(src)
print("已写 work\\gce\\gen_root_zh.py（%d B）" % len(src.encode("utf-8")))
