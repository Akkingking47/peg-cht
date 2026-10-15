#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""名栏修复 v2：改用**内容判据**（v1 的「行0 > 120 字符」漏掉了较短的简报：如 saturn-R、s001 等）。

判据：`_m.txt` 第 0 行若像「句子/简报」而非「场景名」即命中：
  · 长度 > 45，或
  · 句末标点后跟大写（一句接一句），或
  · 以句末标点结尾且长度 > 20，或
  · 以简报常见开头词起句（Herr/Comrade/Message/Well/You/The/Congratulations/Kongratulieren/Victory/Superb/Excellent/Good）
产出：research/_m-namefix-v2.tsv（stem / 行0 / 判据 / 候选名 / 候选名译文 / 来源）
"""
import os
import re

WS = r"D:\DSH\军事游戏汉化"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
MAP = os.path.join(WS, "pegww2", "research", "ww2-scn-map.tsv")
OUT = os.path.join(WS, "pegww2", "research", "_m-namefix-v2.tsv")
GAME_SCN = r"D:\Program Files\PeG-WW2\SCENARIO"

OPENERS = re.compile(r"(?i)^(herr\b|comrade\b|message from|congratulations|kongru|superb|excellent|good work|good job|well\b|you (have|managed|know)|it is your|if your|in this directory|of course|all right|these poles)")
# 常见缩写里的句点不算句子结束（否则 `St. Come du Mont` 会被误判成两句）
ABBR = re.compile(r"\b(St|Mr|Mrs|Dr|No|Pt|Gen|Col|Maj|Capt|Lt|Sgt|Cpl|Pvt|Co|Div|Rgt|Bn|Sec|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec|WW|vs|etc)\.\s")


def looks_like_briefing(s):
    """判据已收窄（v1 版把 `The Battle for Berlin` / `St. Quentin` 这类正常名误判 ⇒ 已排除）"""
    core = ABBR.sub(r"\1 ", s)          # 先把缩写句点抹掉再判句末
    if OPENERS.match(s):
        return "简报开头词"
    if core.count(", ") >= 1 and len(s) > 30:
        return "含逗号长句"
    if len(re.findall(r"[.!?](\s|$)", core)) >= 2 and len(s) > 25:
        return "多句"
    if len(s) > 60:
        return "长(>60)"
    return ""


def main():
    mp = {}
    with open(MAP, encoding="utf-8-sig") as f:
        for i, l in enumerate(f):
            if i < 4 or not l.strip():
                continue
            f2 = l.rstrip("\n").split("\t")
            if len(f2) >= 3 and f2[1].strip():
                mp[f2[0]] = f2[1]
    rows = []
    for fn in sorted(os.listdir(BK)):
        if not fn.lower().endswith("_m.txt"):
            continue
        st = fn[:-6]
        t = open(os.path.join(BK, fn), "rb").read().decode("latin-1")
        ls = re.split(r"\r\n|\r|\n", t)
        line0 = ls[0].strip() if ls else ""
        if not line0:
            continue
        why = looks_like_briefing(line0)
        if not why:
            continue
        # 候选名（MOD 自己写在 <stem>.TXT / _u.txt 里的短名）
        cand, src = "", ""
        for suf, tag in ((".TXT", ".TXT"), (".txt", ".txt"), ("_u.txt", "_u")):
            p = os.path.join(BK, st + suf)
            if os.path.isfile(p):
                first = re.split(r"\r\n|\r|\n", open(p, "rb").read().decode("latin-1"))[0].strip()
                if first and not looks_like_briefing(first) and first.lower() != "dummy":
                    cand, src = first, tag
                    break
        has_scn = any(os.path.isfile(os.path.join(GAME_SCN, st + s)) for s in (".scn", ".SCN"))
        rows.append((st, line0, why, cand, mp.get(cand, ""), src, "有.scn" if has_scn else "无.scn"))
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 名栏修复 v2（内容判据）\n")
        f.write("stem\t行0\t判据\t候选名\t候选名译文\t来源\t是否可显示\n")
        for r in rows:
            f.write("\t".join(x.replace("\t", " ") for x in r) + "\n")
    print(f"内容判据命中 {len(rows)} 条（v1 只查了「>120 字符」）")
    print(f"{'stem':18s} {'判据':10s} {'可显示':8s} 行0 / 候选名")
    print("-" * 100)
    for st, l0, why, cand, zh, src, vis in rows:
        print(f"{st:18s} {why:10s} {vis:8s} {l0[:44]!r}")
        if cand:
            print(f"{'':38s} ⇒ 候选 {cand[:30]!r} → {zh}")


if __name__ == "__main__":
    main()
