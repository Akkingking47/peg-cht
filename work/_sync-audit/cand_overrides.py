#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""只读：列出「同一个英文键、地图名栏却出现 ≥2 种中文」的场景级清单，并标注每场景的预设视角。

用途：为 `glossary\\layers\\scn-place-override.tsv`（按场景定点覆盖）提供**人工裁决的输入**。
输出：`work\\_sync-audit\\cand-mdup.tsv`（en | 键类别 | 场景词干 | 现译名 | 阵营 | 来源 | 文件）
"""
import collections
import io
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
sys.path.insert(0, os.path.join(WS, "work", "glossary"))
import faction_place_audit as F  # noqa: E402

OUT = os.path.join(WS, "work", "_sync-audit", "cand-mdup.tsv")

print("载入场景（备份英文 + 成品中文）…")
data = F.load_scenarios()
pin = F.load_pin()
side, origin, voice = F.resolve_sides(data, pin)
print(f"  场景文件 {len(data)} · 判定视角 {len(side)}")

def body_lines(txt):
    """`_m.txt` 的**首行是场景标题**（`西线-09 德绍 PeG:WW2`）⇒ 两侧都跳过首行（与审计器 skip_title 一致）。"""
    ls = [s.strip() for s in txt.split("\n") if s.strip()]
    return ls[1:] if len(ls) >= 2 else ls


def is_place_key(k):
    """只要像地名的键：不含句末标点、词数 ≤ 4、不含全角句读。"""
    k = k.strip()
    if not k or len(k) > 28:
        return False
    if any(ch in k for ch in ".!?;,\u3002\uff01\uff1f\uff1b\uff0c\u2014\u2018\u2019"):
        return False
    return len(k.split()) <= 4


# (stem, en) -> {译名: [文件…]}
pairs = collections.defaultdict(lambda: collections.defaultdict(list))
for fn, (en, zh) in data.items():
    if not fn.lower().endswith("_m.txt"):
        continue
    st = F.stem_of(fn)
    for a, b in zip(body_lines(en), body_lines(zh)):
        if not a or not b or a == b or not is_place_key(a):
            continue
        pairs[(st, a)][b].append(fn)

# 同一英文键跨场景多值（⭐ 必须按 en 聚合，不能按 (stem,en)：M-DUP 的定义就是「不同场景取不同值」）
by_en = collections.defaultdict(list)
for (st, en), vals in pairs.items():
    by_en[en].append((st, vals))
by_en = {en: items for en, items in by_en.items()
         if len({zh for _st, vs in items for zh in vs}) >= 2}

print(f"地图名栏「同键多值」的英文键：{len(by_en)} 个")
rows = []
for en, items in sorted(by_en.items()):
    for st, vals in sorted(items):
        for zh, fns in sorted(vals.items()):
            f0 = fns[0]
            rows.append((en, st, zh, side.get(f0, "?"), origin.get(f0, "?"), f0))

with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write("# 同键多值清单（只读产出，供人工裁决 → scn-place-override.tsv）\n")
    f.write("en\t场景词干\t现译名\t阵营\t视角来源\t文件\n")
    for r in rows:
        f.write("\t".join(r) + "\n")
print(f"→ 写出 {len(rows)} 行：{OUT}")

print("\n=== 按英文键 × 阵营（该阵营现在用的值）")
for en, items in sorted(by_en.items()):
    per = collections.defaultdict(collections.Counter)
    for st, vals in items:
        for zh, fns in vals.items():
            per[side.get(fns[0], "?")][zh] += len(fns)
    txt = " ｜ ".join(f"{fac}: " + " / ".join(f"{zh}×{n}" for zh, n in c.most_common())
                     for fac, c in sorted(per.items()))
    print(f"  {en:24s} {txt}")
