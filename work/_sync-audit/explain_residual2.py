# -*- coding: utf-8 -*-
"""给「残留未译」分桶（只读）：160 条 A未译残留按成因归类，并汇总另两份残留表。"""
import csv
import io
import os
import re
import collections

WS = r"D:\DSH\军事游戏汉化"
REV = os.path.join(WS, "glossary", "glossary-authority-review.tsv")
RES = os.path.join(WS, "glossary", "glossary-residual.tsv")
TODO = os.path.join(WS, "pegww2", "research", "_未译清单.tsv")

UNITWORDS = re.compile(
    r"(?i)\b(corps|forces|army|division|divisionen|brigade|regiment|battalion|squadron|"
    r"habforce|group|detachment|company|platoon|troop|battery|regt|bn|abteilung|kampfgruppe|"
    r"african|position|verfugungs|verfügungs)\b")
META = re.compile(r"(?i)(https?://|version|creator|designer|\bmap:\s|revised|modified|"
                  r"\d{1,2}/\d{4}|\d{4}\s*$)")

with io.open(REV, encoding="utf-8-sig", newline="") as f:
    a = [r for r in csv.DictReader(f, delimiter="\t") if r["kind"] == "A未译残留"]

buckets = collections.OrderedDict([
    ("① not used 弃用条目", []),
    ("② 具名装备保留英文", []),
    ("③ 番号/编制单位名", []),
    ("④ 署名·版本·URL 元数据", []),
    ("⑤ 散文层(TEXT/TITLE)里夹英文", []),
    ("⑥ 其它", []),
])
for r in a:
    en, zh, cat = r["en"], r["zh"], r["cat"]
    if "(未使用)" in zh or "not used" in en.lower():
        buckets["① not used 弃用条目"].append(r)
    elif META.search(en):
        buckets["④ 署名·版本·URL 元数据"].append(r)
    elif UNITWORDS.search(en) and cat in ("UNIT", "PLACE"):
        buckets["③ 番号/编制单位名"].append(r)
    elif cat in ("TEXT", "TITLE", "TERM"):
        buckets["⑤ 散文层(TEXT/TITLE)里夹英文"].append(r)
    elif cat == "EQUIP":
        buckets["② 具名装备保留英文"].append(r)
    else:
        buckets["⑥ 其它"].append(r)

print("A未译残留 共 %d 条" % len(a))
for k, v in buckets.items():
    print("  %-26s %3d" % (k, len(v)))
print()
for k, v in buckets.items():
    if not v:
        continue
    print("### %s（%d）" % (k, len(v)))
    for r in v[:18]:
        print("   [%-6s %-18s] %-44s => %s" % (r["cat"], r["scope"], r["en"][:44], r["zh"][:34]))
    if len(v) > 18:
        print("   …… 另 %d 条" % (len(v) - 18))
    print()


def summar(path, cols, label, hint=10):
    print("### %s" % label)
    if not os.path.exists(path):
        print("   （不存在）\n")
        return
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        rd = list(csv.DictReader(f, delimiter="\t"))
    print("   数据行 %d · 列 %s" % (len(rd), list(rd[0].keys()) if rd else "?"))
    for r in rd[:hint]:
        print("   " + " | ".join((r.get(c) or "")[:34] for c in cols))
    if len(rd) > hint:
        print("   …… 另 %d 行" % (len(rd) - hint))
    print()


summar(RES, ["en", "zh", "scope", "note"], "glossary/glossary-residual.tsv")
summar(TODO, ["文件", "行号", "原文"], "pegww2/research/_未译清单.tsv")
