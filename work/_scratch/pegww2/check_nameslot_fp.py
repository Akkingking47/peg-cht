#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""排查 v2 判据的**假阳性**（把「标题+日期」误判成简报 ⇒ 可能已被错误替换）。

改进判据：先把日期模式抹掉，再判句子特征。
"""
import os
import re

WS = r"D:\DSH\军事游戏汉化"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
MAP = os.path.join(WS, "pegww2", "research", "ww2-scn-map.tsv")

DATE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2}(st|nd|rd|th)?,?\s*\d{4}\b|\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{1,2}(st|nd|rd|th)\b", re.I)
ABBR = re.compile(r"\b(St|Mr|Mrs|Dr|No|Pt|Gen|Col|Maj|Capt|Lt|Sgt|Cpl|Pvt|Co|Div|Rgt|Bn|Sec|WW|vs|etc)\.\s")
OPENERS = re.compile(r"(?i)^(herr\b|comrade\b|message from|congratulations|kongru|superb|excellent|good work|good job|well\b|you (have|managed|know)|it is your|if your|in this directory|of course|all right|these poles)")


def is_briefing(s):
    core = ABBR.sub(r"\1 ", DATE.sub(" ", s))
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
    for i, l in enumerate(open(MAP, encoding="utf-8-sig")):
        if i < 4 or not l.strip():
            continue
        f = l.rstrip("\n").split("\t")
        if len(f) >= 3 and f[1].strip():
            mp[f[0]] = f[1]
    # 读 v2 报告里判定可修的那些 stem
    rep = os.path.join(WS, "pegww2", "research", "_m-namefix-v2.tsv")
    stems = []
    if os.path.isfile(rep):
        for i, l in enumerate(open(rep, encoding="utf-8")):
            if i < 2:
                continue
            f = l.rstrip("\n").split("\t")
            if len(f) >= 7:
                stems.append(f[0])
    print(f"v2 报告里的 stem 共 {len(stems)}")
    fake = []
    for st in sorted(set(stems)):
        p = os.path.join(BK, st + "_m.txt")
        if not os.path.isfile(p):
            continue
        line0 = re.split(r"\r\n|\r|\n", open(p, "rb").read().decode("latin-1"))[0].strip()
        if not line0:
            continue
        if is_briefing(line0):
            continue                      # 仍判为简报 ⇒ 不是假阳性
        fake.append((st, line0, mp.get(line0, "(未在真源)")))
    print()
    print(f"⚠️ 用「抹掉日期后」的判据复检 ⇒ **假阳性 {len(fake)} 条**（这些行的原名可能是合法的，需还原）")
    for st, l0, cur in fake:
        print(f"  {st:14s} 备份行0 = {l0[:58]!r}")
        print(f"  {'':14s} 真源现值 = {cur[:58]!r}")


if __name__ == "__main__":
    main()
