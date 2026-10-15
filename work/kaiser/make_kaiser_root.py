# -*- coding: utf-8 -*-
r"""为 KAISER 生成本地 `gen_root_zh.py`。

基线＝GCE 版（已含 gbk_safe 折写 + 人工表首尾空白保留两个补丁）。
本脚本再加两个 KAISER 专属补丁：
  ① 从 `root-words.tsv` 载入**多语言词表**（本 efile 装备名跨 20 余种语言）
  ② `zh_tight()` —— 收紧「汉字 + 空格 + 汉字」（词级替换会把 `Light Cruiser`→`轻型 巡洋舰`，
     而 GCE/OLGWW2/ATOMIC 的交付件里这种空格为 0）

用法: python make_kaiser_root.py
产出: work\kaiser\gen_root_zh.py

⚠️ 审这个生成器**只能子进程跑 `--dry`**，绝不 import（顶层会落盘）。
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
src = io.open(os.path.join(r"D:\DSH\军事游戏汉化\work\gce", "gen_root_zh.py"),
              encoding="utf-8").read()

src = src.replace('"""GCE 根级四件套汉化生成器', '"""KAISER 根级四件套汉化生成器')
src = src.replace('TGT = "EFILE_GCE"', 'TGT = "EFILE_KAISER"')
assert 'TGT = "EFILE_KAISER"' in src

src = re.sub(r"MANUAL = \{.*?\n\}\n", "MANUAL = {}\n", src, count=1, flags=re.S)
assert "MANUAL = {}\n" in src

# ① 词表载入（放在 Class/Kevyt 剔除之后，避免被误删）
anchor = 'for _w in ("Class",):\n    WORDS.pop(_w, None)\n'
assert anchor in src
src = src.replace(anchor, anchor + '''
# ⭐ KAISER：载入多语言词表（德/俄/波/捷/匈/土/芬/…）
_wp = os.path.join(HERE, "root-words.tsv")
if os.path.exists(_wp):
    with io.open(_wp, encoding="utf-8-sig") as _f:
        _f.readline()
        for _ln in _f:
            _ln = _ln.rstrip("\\r\\n")
            if not _ln:
                continue
            _c = _ln.split("\\t")
            if len(_c) >= 2 and _c[0].strip() and _c[1].strip():
                WORDS[_c[0].strip()] = _c[1].strip()
    print("KAISER 词表合计 %d 条" % len(WORDS))
''')

# ② 汉字空格收紧
anchor2 = "def sp_cp(b):"
assert anchor2 in src
src = src.replace(anchor2, '''ZH_GAP = re.compile(r"(?<=[\\u4e00-\\u9fff]) +(?=[\\u4e00-\\u9fff])")


def zh_tight(s):
    """收紧「汉字 空格 汉字」——词级替换留下的复合词空隙（`轻型 巡洋舰`→`轻型巡洋舰`）。"""
    return ZH_GAP.sub("", s)


def sp_cp(b):''', 1)

src = src.replace("        d = gbk_safe(d)", "        d = gbk_safe(d)\n        d = zh_tight(d)")
assert "d = zh_tight(d)" in src

# ①-b tokenizer 支持重音字母（KAISER 装备名跨 20 余种语言，`Cañón` `Peça` `Jääkäri` `Várõrség`…
#     原 GCE 版的 `[A-Za-z]` 会把 `Portée` 切成 `Port`+`ée` ⇒ `Port`→港口，误译）
src = src.replace('TOKEN = re.compile(r"[A-Za-z][A-Za-z\\-\'.]*")',
                  'TOKEN = re.compile(r"[A-Za-z\\u00c0-\\u024f][A-Za-z\\u00c0-\\u024f\\-\'.]*")')
assert "u00c0-\\u024f" in src

# ①-c 型号标记行整行保留（donor 实证：GCE 含口径/型号标记 115 行改动 0）
anchor3 = 'TOKEN = re.compile('
src = src.replace(anchor3, '''MARK = re.compile(
    r"(?i)\\b(obr|wz|vz|zr|md|mle|mod|mk|typ|cal|nom)\\.?\\s*[\\dIA]"
    r"|\\bM\\.?\\s*\\d|\\by\\.\\s*\\d{2,4}|\\bL/\\d|\\bC/\\d|\\b\\d{2}/\\d{2}\\b")

PART = re.compile(
    r"(?<![A-Za-z\\u00c0-\\u024f])(de|da|di|du|des|del|\\u00e0|au|zu|zum|zur|w|na|van|der|von|of|the|et|a)"
    r"(?![A-Za-z\\u00c0-\\u024f])")


''' + anchor3, 1)

src = src.replace("    if not changed:\n        return s, \"保留原文\"",
                  "    if not changed:\n        return s, \"保留原文\"\n"
                  "    if fn == \"equip.txt\":\n"
                  "        _res = \"\".join(out) + s[last:]\n"
                  "        if MARK.search(s):\n"
                  "            return s, \"型号保留\"\n"
                  "        if PART.search(s) and HAN.search(_res) and LAT.search(_res):\n"
                  "            return s, \"虚词回退\"", 1)
assert "虚词回退" in src

with io.open(os.path.join(HERE, "gen_root_zh.py"), "w", encoding="utf-8", newline="") as f:
    f.write(src)
print("已写 work\\kaiser\\gen_root_zh.py（%d B）" % len(src.encode("utf-8")))
