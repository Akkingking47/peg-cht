#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""只读：按「预设扮演势力」核对**成品里已落地的地名写法**，找出与势力/年代不符的处。

判据（用户裁定 m01055-④ / m01214-③）：
  同一个地名该用哪种写法，取决于**该场景预设扮演哪方势力**（+ 年代）。
  真源 = `glossary\\layers\\faction-places.tsv`（`地名ID | 阵营 | 该方称法 | 中文译名 | 英文/其它写法 | 时期 | 依据`）。

报告：每个「场景词干 / 表格英文键 / 现译名 / 该场景阵营 / 应当写法 / 文件 / 行号」，
     可直接改写成 `glossary\\layers\\scn-place-override.tsv` 的行。
"""
import collections
import io
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
sys.path.insert(0, os.path.join(WS, "work", "glossary"))
import faction_place_audit as F  # noqa: E402

REG = os.path.join(WS, "glossary", "layers", "faction-places.tsv")
OUT = os.path.join(WS, "work", "_sync-audit", "faction-place-mismatch.tsv")


def load_reg():
    """{地名ID: {阵营: 中文}} · {英文写法小写: 地名ID}"""
    per, en2id = collections.defaultdict(dict), {}
    with io.open(REG, encoding="utf-8-sig") as f:
        for ln in f:
            s = ln.rstrip("\r\n")
            if not s.strip() or s.startswith("#"):
                continue
            c = s.split("\t")
            if len(c) < 4 or c[0].strip() == "地名ID":
                continue
            pid, fac, zh, alts = c[0].strip(), c[1].strip(), c[3].strip(), c[4].strip()
            per[pid][fac] = zh
            en2id[pid.lower()] = pid
            for a in alts.split("|"):
                a = a.strip()
                if a:
                    en2id[a.lower()] = pid
    return per, en2id


per, en2id = load_reg()
print(f"历史称法登记：{len(per)} 个地名 ID · {len(en2id)} 个英文写法")

data = F.load_scenarios()
pin = F.load_pin()
side, origin, voice = F.resolve_sides(data, pin)
print(f"场景 {len(data)} · 判定视角 {len(side)}")

rows = []
for fn in sorted(data):
    en_txt, zh_txt = data[fn]
    fac = side.get(fn)
    st = F.stem_of(fn)
    for i, (a, b) in enumerate(zip(en_txt.split("\n"), zh_txt.split("\n"))):
        a, b = a.strip(), b.strip()
        if not a or not b or a == b:
            continue
        pid = en2id.get(a.lower())
        if not pid:
            # 英文行可能带装饰（`Lodz (#3)`）⇒ 剥尾部括号/编号再试
            import re
            pid = en2id.get(re.sub(r"\s*[\(\[].*?[\)\]]\s*$|\s*#\d+\s*$", "", a).strip().lower())
        if not pid:
            continue
        names = per[pid]
        mine = set(v for f2, v in names.items() if f2 == fac) if fac else set()
        if not mine:
            continue          # 该阵营在登记表里没有名字 ⇒ 无法判对错（否则 96 条里绝大多数是这种噪声）
        if any(b == v for v in mine):
            continue          # 已经是本阵营的写法之一（含年代/变体分叉，如 Lodz 德方 利茨曼施塔特｜罗兹）
        others = {f2: v for f2, v in names.items() if f2 != fac and v not in mine}
        if b in others.values():
            want = sorted(mine)
            rows.append((st, pid, a, b, fac or "?", " / ".join(want),
                         origin.get(fn, "?"), fn, str(i + 1)))

print(f"\n⚠️ 与「预设势力」不符的处：{len(rows)}")
with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write("# 按势力核对地名写法的差异（只读产出 → 人工裁决 → scn-place-override.tsv）\n")
    f.write("场景词干\t地名ID\t表格英文键\t现译名\t场景阵营\t该阵营应当写法\t视角来源\t文件\t行号\n")
    for r in rows:
        f.write("\t".join(r) + "\n")
print(f"→ {OUT}\n")
for r in rows:
    print(f"  {r[0]:14s} {r[1]:12s} {r[3]:12s} 阵营={r[4]:3s} 应={r[5] or '（该阵营未登记）':12s} "
          f"{r[7]}:{r[8]}  [{r[6]}]")
