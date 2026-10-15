#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""梳理 · **段级统一裁定单生成**（提议稿，需人工复核后才生效）。

原则（用户的规则）：
  1. 词库能判就按词库 —— 查**裸段**在词库里的规范译法；
  2. 前作 vs 本作冲突 → **本作层（PEGWW2_*）优先**（m00211 裁决「以本作界面层为准」）；
  3. 词库没有 → 取映射表内**多数**写法；
  4. 词库自身明显错译（如 South African 译成「非洲」）→ 标 ❓交人工。

来源文件：`glossary\\standard-glossary.tsv` + `glossary\\layers\\{common,series,scope}-glossary.tsv`
输出：`glossary\\layers\\seg-canon-proposal.tsv`
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

WS = r"D:\DSH\军事游戏汉化"
GL = os.path.join(WS, "glossary")
LAY = os.path.join(GL, "layers")
RES = os.path.join(WS, "pegww2", "research")
OUT = os.path.join(LAY, "seg-canon-proposal.tsv")
SKIP_SEG = re.compile(r"^\[?[0-9A-Za-z]{0,3}\]?$|^[-–—/]+$|^\[[IVXL]+\]$")
# 本作层前缀（优先）
MINE = ("PEGWW2", "PEG-WW2", "PEGWW2_SCN")

# 词库自身疑似错译 → 强制交人工（依据：番号/编制与史实不符）
SUSPECT = {
    "1 African D": "South African = 南非，词库作「第1非洲师」疑错（m01492 裁决：词库只是约束不是事实源）",
    "2 African D": "同 1 African D",
    "9 Aust.": "词库（前作层）作「9澳大利亚师」无「第」，本作场景层惯用「第9澳大利亚师」",
    "4 Ind": "词库（前作层）作「4印度师」无「第」",
    "4 Ind D.": "同上",
    "4 Ind D": "同上",
    "4 Indian.": "同上",
    "Das Reich": "词库本作层作「帝国师」，场景层多数作「达斯帝国师」——两者皆有据，需裁定",
    "GD [48]": "GD=Grossdeutschland「大德意志」，词库 PLACE 层未译",
    "7 SG": "词库作「第7支援群」，场景层作「第7SG」——Support Group 是否译出需裁定",
    "17SS": "词库作「党卫军第17师」，场景层作「第17党卫军」——语序需裁定",
    "- [A Corps]": "A Corps 疑 Australian Corps「澳军」，但取值为空说明原文即空/丢字，需看原件",
    "164 LD": "场景层有未译「164 LD」，词库规范为「第164轻装师」",
}


def load_bank():
    """en → [(zh, cat, scope, layer)]，按「本作层优先、条目数少优先」排序取用。"""
    d = defaultdict(list)
    for tag, p in (("std", os.path.join(GL, "standard-glossary.tsv")),
                   ("common", os.path.join(LAY, "common-glossary.tsv")),
                   ("series", os.path.join(LAY, "series-glossary.tsv")),
                   ("scope", os.path.join(LAY, "scope-glossary.tsv"))):
        if not os.path.isfile(p):
            continue
        for l in io.open(p, encoding="utf-8-sig"):
            c = l.rstrip("\r\n").split("\t")
            if len(c) < 4 or not c[0].strip() or c[0].strip() == "en":
                continue
            d[c[0].strip()].append((c[1].strip(), c[2] if len(c) > 2 else "",
                                    c[3] if len(c) > 3 else "", tag))
    return d


def load_map(table="ww2-scn-map"):
    """en_seg → Counter(zh_seg) + 整行示例"""
    seg = defaultdict(Counter)
    for l in io.open(os.path.join(RES, table + ".tsv"), encoding="utf-8-sig"):
        s = l.rstrip("\r\n")
        if not s or s.startswith("#"):
            continue
        c = s.split("\t")
        if len(c) < 2 or "/" not in c[0] or "/" not in c[1]:
            continue
        es = [x.strip() for x in c[0].split("/")]
        zs = [x.strip() for x in c[1].split("/")]
        if len(es) != len(zs):
            continue
        for a, b in zip(es, zs):
            if a and b and not SKIP_SEG.match(a):
                seg[a][b] += 1
    return seg


def main():
    bank = load_bank()
    seg = load_map()
    conf = {a: c for a, c in seg.items() if len(c) >= 2}
    rows = []
    for a, c in sorted(conf.items(), key=lambda x: (-sum(x[1].values()), x[0])):
        dist = " ｜ ".join("%s×%d" % (v, n) for v, n in c.most_common())
        top = c.most_common(1)[0][0]
        src, cand = "多数", top
        # 1) 词库裸段
        hits = bank.get(a, [])
        mine = [h for h in hits if any(h[2].upper().startswith(m) for m in MINE)]
        other = [h for h in hits if h not in mine]
        if mine:
            src, cand = "词库·本作层", mine[0][0]
        elif other:
            src, cand = "词库·前作层", other[0][0]
        # 2) 词库给出的写法若与多数不同，且多数在场景层出现更多 → 仍以词库为准，但标注
        note = ""
        if cand != top:
            note = "词库「%s」≠ 映射表多数「%s」" % (cand, top)
        if a in SUSPECT:
            src = "❓待裁定·" + src
            note = SUSPECT[a] + ("；" + note if note else "")
        rows.append((a, cand, src, dist, note))
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 段级统一裁定单（提议稿）\n")
        f.write("# 列：en_seg\t建议译法\t依据\t映射表现行分布\t备注\n")
        f.write("# 依据取值：词库·本作层 / 词库·前作层 / 多数 / ❓待裁定·*\n")
        f.write("# 复核后另存为 seg-canon.tsv 并去掉本注释头以外的 ❓。\n")
        for r in rows:
            f.write("\t".join(r) + "\n")
    n_q = sum(1 for r in rows if r[2].startswith("❓"))
    print("冲突段 %d 组 → %s" % (len(rows), OUT))
    print("  词库·本作层 %d · 词库·前作层 %d · 多数 %d · ❓待裁定 %d"
          % (sum(1 for r in rows if r[2] == "词库·本作层"),
             sum(1 for r in rows if r[2] == "词库·前作层"),
             sum(1 for r in rows if r[2] == "多数"), n_q))
    return 0


if __name__ == "__main__":
    sys.exit(main())
