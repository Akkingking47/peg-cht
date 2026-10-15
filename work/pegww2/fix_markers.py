#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 场景层：**统一括号类型标记的译法**（跨片一致性修正）。

背景：括号标记是 MOD 作者在地图名后加的**显示用**注记（如 `Calais (PORT)`），
      引擎只把整行当地图格名绘制，**没有按括号关键字解析的证据**（前作无先例）。
      ⇒ 定案：**括号里的标记也翻译**（中文界面里不该留英文词）。
      但保留标记的**括号形状**，且 `(#NN)`/`(RTB#NN)`/坐标 `(NN,NN)` 等**编号标记仍原样**。

用法: python fix_markers.py <fill文件> [<输出文件>]
产出：只含需修正行的两列 fill（原文 / 修正译文），交给 apply_value_fill.py 覆盖。
"""
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")

# 括号标记对照（仅「显示用类型标记」；编号类不动）
MARKERS = [
    ("(impassible)", "（不可通行）"),
    ("(impassable)", "（不可通行）"),
    ("(PORT)", "（港口）"),
    ("(OCEAN)", "（海洋）"),
    ("(SEA)", "（海域）"),
    ("(LAKE)", "（湖泊）"),
    ("(RIVER)", "（河流）"),
]

# 正则类修正（跨片一致性：同一表达必须同一译法）
REGEX_RULES = [
    # `: Redux` / `:  Redux` ⇒ 统一作「：重制版」（第 2 片已如此译，第 4 片误留原文）
    (r":\s+Redux\b", "：重制版"),
    # `(Part N)` 是显示标记（含可译词），按括号标记规则译出；编号保留
    (r"\(\s*Part\s*(\d+)\s*\)", r"（第\1部分）"),
    (r"\[\s*Part\s*(\d+)\s*\]", r"[第\1部分]"),
    # 军级航空部队统一写「航空军」（第 1 片写「航空野战军」、第 2 片按口径写「航空军」⇒ 统一）
    (r"航空野战军", "航空军"),
]


def main():
    src = os.path.join(RES, sys.argv[1])
    out = os.path.join(RES, sys.argv[2] if len(sys.argv) > 2 else "_scn-fill-markerfix.tsv")
    fixed = []
    with open(src, encoding="utf-8") as f:
        for i, line in enumerate(f):
            s = line.rstrip("\n")
            if not s.strip() or s.startswith("#"):
                continue
            f2 = s.split("\t")
            if len(f2) < 2 or f2[0] in ("原文",):
                continue
            orig, zh = f2[0], f2[1]
            if not zh.strip():
                continue
            nz = zh
            for a, b in MARKERS:
                nz = nz.replace(a, b)
            for pat, rep in REGEX_RULES:
                nz = re.sub(pat, rep, nz)
            if nz != zh:
                fixed.append((orig, nz))
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 括号类型标记统一修正（fix_markers.py 生成）\n原文\t译文\n")
        for a, b in fixed:
            f.write(f"{a}\t{b}\n")
    print(f"  {os.path.basename(src)} ⇒ 需修正 {len(fixed)} 行 → {os.path.basename(out)}")
    for a, b in fixed[:12]:
        print(f"     {a[:40]:42s} → {b[:40]}")


if __name__ == "__main__":
    main()
