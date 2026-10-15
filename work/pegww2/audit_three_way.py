#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2：场景「三方一致性」审计 v2（**只读**）—— 用**英文备份**做基准。

（v1 的错：关键词表是英文，却去比中文部署态 ⇒ 假阴性，只报 1 条。v2 修正。）

对每个进列表场景（.SCN@0==0）比对四方，全部取**英文原文**：
  a) `.SCN@11210` 地图名
  b) `<stem>_i.txt` 行0（`@11329` 指向；= 实际显示在描述框的名字行）
  c) `<stem>_m.txt` 行0（英文原版名栏）+ 行1..3（正文线索）
  d) `<stem>_u.txt` 行0（单位资料标题）

按地名/部队/行动代号把每方归到 西线/东线/北非/北欧/意大利；**四方跨战场 ⇒ ⚠️ 冲突**。
"""
import os
import re

WS = r"D:\DSH\军事游戏汉化"
G = r"D:\Program Files\PeG-WW2"
S = os.path.join(G, "SCENARIO")
U = os.path.join(G, "USERSCEN")
BKS = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
BKU = os.path.join(WS, "pegww2", "testbed", "backup", "USERSCEN")
RES = os.path.join(WS, "pegww2", "research")
OUT = os.path.join(RES, "_三方一致性审计.tsv")

THEATER = {
    "北非": ["gazala", "garamlah", "tobruk", "bardia", "sollum", "halfaya", "cyrenaica", "afrika",
             "rommel", "dak", "alamein", "benghazi", "tripoli", "malta", "herkules", "sidi",
             "mersa", "desert", "africa", "creta", "crete"],
    "意大利": ["salerno", "anzio", "cassino", "sicily", "etna", "volturno", "gustav", "shingle",
               "avalanche", "taranto", "messina", "naples", "monte cassino"],
    "东线": ["stalingrad", "kursk", "kharkov", "prokhorovka", "donets", "dnepr", "dniepr", "moscow",
             "leningrad", "kalinin", "rzhev", "vyazma", "kiev", "kishinev", "kanev", "novgorod",
             "viipuri", "volokolamsk", "seelow", "berlin", "soviet", "red army", "partisan",
             "romny", "klin", "ciechanow", "warsaw", "vistula", "oder", "konrad", "saturn"],
    "西线": ["carentan", "normandy", "caen", "st. lo", "st lo", "arracourt", "metz", "sedan",
             "dunkirk", "antwerp", "arnhem", "market garden", "bulge", "ardennes", "nordwind",
             "rhine", "ruhr", "101st airborne", "506th", "paratrooper", "glider", "carentan",
             "charnwood", "oden", "goodwood", "cobra", "hedgerows", "maldon", "canterbury"],
    "北欧": ["norway", "lillehammer", "iceland", "narvik", "oslo", "gjovik", "sealion"],
    "伊比利亚": ["madrid", "sevilla", "gibraltar", "spain", "spanish"],
    "芬兰": ["suomussalmi", "viipuri", "finnish", "finland"],
}


def fld(b, o, n=20):
    return b[o:o + n].split(b"\x00")[0].decode("latin-1")


def rd(p, enc="cp1252"):
    if not os.path.isfile(p):
        return None
    t = open(p, "rb").read()
    if p.lower().endswith(".ply"):
        t = t.split(b"\x00")[0]
    return re.split(r"\r\n|\r|\n", t.decode(enc, "replace"))


def find(back, game, stem, suffix):
    """在备份里找英文原文；备份缺则在游戏目录找（此时退回英文名栏/上下文判断）。"""
    for base in (back, game):
        for name in (stem + suffix, stem.upper() + suffix, stem.lower() + suffix):
            p = os.path.join(base, name)
            if os.path.isfile(p):
                return p
    return None


def cls(txt):
    t = (txt or "").lower()
    return "/".join(k for k, ws in THEATER.items() if any(w in t for w in ws)) or "?"


def main():
    rows = []
    for sub in ("SCENARIO", "USERSCEN"):
        gd = os.path.join(G, sub)
        bd = BKS if sub == "SCENARIO" else BKU
        for fn in sorted(os.listdir(gd)):
            if not fn.lower().endswith(".scn"):
                continue
            b = open(os.path.join(gd, fn), "rb").read()
            if len(b) < 11350 or b[0] != 0:
                continue
            stem = fn[:-4]
            mp = fld(b, 11210)
            intro = fld(b, 11329)
            pi = find(bd, gd, intro, ".txt") or find(bd, gd, intro, ".TXT")
            pm = find(bd, gd, stem, "_m.txt")
            pu = find(bd, gd, stem, "_u.txt")
            li = rd(pi) if pi else None
            lm = rd(pm) if pm else None
            lu = rd(pu) if pu else None
            i0 = li[0] if li else "(无 _i)"
            m0 = lm[0] if lm else "(无 _m)"
            u0 = lu[0] if lu else "(无 _u)"
            ctx = " ".join(x for x in ((lm[1] if lm and len(lm) > 1 else ""),
                                       (li[1] if li and len(li) > 1 else ""),
                                       (lu[1] if lu and len(lu) > 1 else "")) if x)
            t_mp, t_i, t_m, t_u = cls(mp), cls(i0), cls(m0 + " " + ctx), cls(u0)
            votes = {x for x in (t_mp, t_m, t_u) if x != "?"}
            verdict = "✅ 一致" if len(votes) <= 1 else "⚠️ 冲突"
            rows.append((stem, mp, t_mp, i0[:34], t_i, m0[:34], t_m, u0[:34], t_u, verdict))
    out = ["# 场景「三方一致性」审计 v2（只读 · 未改动）· 基准=英文备份",
           "# 列：stem | 地图 | 地图战场 | _i行0 | _i战场 | _m行0(英文名栏) | _m战场(含正文线索) | _u行0 | _u战场 | 判定",
           "# 冲突 = 地图/_m/_u 三方战场归类跨 >1 个战场 ⇒ MOD 原数据拼错位", ""]
    conf = []
    for r in rows:
        out.append("\t".join(r))
        if r[-1].startswith("⚠️"):
            conf.append(r)
    open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print("审计 %d 个进列表场景 ⇒ %s" % (len(rows), OUT))
    print("⚠️ 冲突 %d 个：\n" % len(conf))
    for r in conf:
        print("  %-16s 地图[%s]  _m[%s] %r" % (r[0], r[2], r[6], r[5]))
        print("  %-16s _u[%s] %r   _i[%s] %r" % ("", r[8], r[7], r[4], r[3]))


if __name__ == "__main__":
    main()
