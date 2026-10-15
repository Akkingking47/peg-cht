# -*- coding: utf-8 -*-
"""列出「残留未译」里可定名的候选（③ 番号/编制单位名 ＋ ⑥ 其它外语番号），并给出出现位置。只读。

输出 work/_sync-audit/residual-names-todo.tsv：en | 当前库译文 | 残留英文 | 出现次数 | 出现位置(前4) | 范围
"""
import csv
import io
import os
import re
import collections

WS = r"D:\DSH\军事游戏汉化"
REV = os.path.join(WS, "glossary", "glossary-authority-review.tsv")
OCC = os.path.join(WS, "glossary", "glossary-occ.tsv")
OUT = os.path.join(WS, "work", "_sync-audit", "residual-names-todo.tsv")

UNITWORDS = re.compile(
    r"(?i)\b(corps|forces|army|division|brigade|regiment|battalion|squadron|habforce|group|"
    r"detachment|company|platoon|troop|battery|regt|bn|abteilung|kampfgruppe|african|position|"
    r"verfugungs|verfügungs)\b")
META = re.compile(r"(?i)(https?://|version|creator|designer|\bmap:\s|revised|modified|\d{1,2}/\d{4}|\d{4}\s*$)")


def rows_of(path):
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


rev = [r for r in rows_of(REV) if r["kind"] == "A未译残留"]

# 出现位置索引
occ = collections.defaultdict(list)
for r in rows_of(OCC):
    occ[r["en"]].append("%s@%s" % (r["src"], r["loc"]))

todo = []
for r in rev:
    en, zh, cat = r["en"], r["zh"], r["cat"]
    if "(未使用)" in zh or "not used" in en.lower():
        continue
    if META.search(en):
        continue
    if UNITWORDS.search(en) and cat in ("UNIT", "PLACE"):
        todo.append((en, zh, r["note"], cat, "③番号/编制"))
    elif cat in ("TEXT", "TITLE", "TERM"):
        continue
    elif cat == "EQUIP":
        continue
    else:
        todo.append((en, zh, r["note"], cat, "⑥外语番号/其它"))

with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write("范围\tcat\ten\t当前库译文\t残留英文\t出现次数\t出现位置(前4)\n")
    for en, zh, note, cat, scope in sorted(todo, key=lambda x: (x[4], -len(occ.get(x[0], [])))):
        locs = occ.get(en, [])
        f.write("\t".join((scope, cat, en, zh, note, str(len(locs)), " ".join(locs[:4]))) + "\n")

print("候选 %d 条（③ %d · ⑥ %d）"
      % (len(todo), sum(1 for t in todo if t[4].startswith("③")),
         sum(1 for t in todo if t[4].startswith("⑥"))))
print("出现次数合计 %d" % sum(len(occ.get(t[0], [])) for t in todo))
print()
print("-- 出现最多的 30 条 --")
for en, zh, note, cat, scope in sorted(todo, key=lambda x: -len(occ.get(x[0], [])))[:30]:
    locs = occ.get(en, [])
    print("   %-42s => %-30s 残留=%-22s 出现%3d  %s"
          % (en[:42], zh[:30], note[:22], len(locs), locs[0] if locs else ""))
print()
print("写出 -> %s" % OUT)
