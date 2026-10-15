#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交叉核对：`_m.txt` 名栏（列表显示名） vs `@11329` 说明文件第 0 行（游戏内实际身份）。

判据（用户实测得出）：**进入游戏后加载的是说明文件/简报** ⇒ 它才是这个场景的真实身份。
    `sedan-R_m.txt` 名栏 = 'Avalanche'，但它的 `sedan-R.scn` map=Sedan.MAP、说明 `S-R.TXT`=色当
    ⇒ 名栏张冠李戴（MOD 数据错）。

做法：不一致时**以说明文件为准**，把名栏按 per-file 覆盖改为说明文件第 0 行的译法。
产出：research/_scn-file-overrides.tsv（追加）+ 打印清单
"""
import os
import re

WS = r"D:\DSH\军事游戏汉化"
G = r"D:\Program Files\PeG-WW2"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
MAP = os.path.join(WS, "pegww2", "research", "ww2-scn-map.tsv")
OVF = os.path.join(WS, "pegww2", "research", "_scn-file-overrides.tsv")
REPORT = os.path.join(WS, "pegww2", "research", "_name-crosscheck.tsv")


def fld(b, o, n=20):
    return b[o:o + n].split(b"\x00")[0].decode("latin-1")


def norm(s):
    s = re.sub(r"(?i)\s*(pe?g\s*:?\s*ww2|:?\s*redux|重制版?|修改版)\s*$", "", s.strip())
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]", "", s.lower())


def main():
    mp = {}
    for i, l in enumerate(open(MAP, encoding="utf-8-sig")):
        if i < 4 or not l.strip():
            continue
        f = l.rstrip("\n").split("\t")
        if len(f) >= 3 and f[1].strip():
            mp[f[0]] = f[1]
    hits = []
    for fn in sorted(os.listdir(BK)):
        if not fn.lower().endswith("_m.txt"):
            continue
        stem = fn[:-6]
        mline = re.split(r"\r\n|\r|\n", open(os.path.join(BK, fn), "rb").read().decode("latin-1"))[0].strip()
        scn = None
        for cs in (stem + ".scn", stem.lower() + ".scn", stem + ".SCN"):
            p = os.path.join(G, "SCENARIO", cs)
            if os.path.isfile(p):
                scn = p
                break
        if not scn or not mline:
            continue
        b = open(scn, "rb").read()
        if len(b) < 11350:
            continue
        intro, flag = fld(b, 11329), b[11349]
        dfirst = ""
        for dd, ex in ((os.path.join(G, "USERSCEN"), ".ply"), (os.path.join(G, "SCENARIO"), ".TXT")) if flag \
                else ((os.path.join(G, "SCENARIO"), ".TXT"), (os.path.join(G, "USERSCEN"), ".ply")):
            for nm in (intro + ex, intro + ex.lower()):
                q = os.path.join(dd, nm)
                if os.path.isfile(q):
                    t = open(q, "rb").read().decode("gbk", "replace")
                    ls = [x for x in re.split(r"\r\n|\r|\n", t) if x.strip()]
                    if ls:
                        dfirst = ls[0].strip()
                    break
            if dfirst:
                break
        if not dfirst or not mline:
            continue
        if norm(mline) and norm(dfirst) and norm(mline) != norm(dfirst):
            hits.append((stem, mline, dfirst))
    # 追加 per-file 覆盖（以说明文件第 0 行为准）
    add = []
    for stem, mline, dfirst in hits:
        zh = mp.get(dfirst) or mp.get(mline)
        if zh:
            add.append(("SCENARIO", stem + "_m.txt", 0, mline, zh))
    lines = []
    if os.path.isfile(OVF):
        lines = [l.rstrip("\n") for l in open(OVF, encoding="utf-8") if l.strip()]
    have = {(c.split("\t")[1] if len(c.split("\t")) > 1 else "") for c in lines}
    with open(OVF, "w", encoding="utf-8", newline="\n") as f:
        for l in lines:
            f.write(l + "\n")
        for sub, fn, idx, orig, zh in add:
            if fn in have:
                continue
            f.write(f"{sub}\t{fn}\t{idx}\t{orig}\t{zh}\n")
    with open(REPORT, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 名栏 vs 说明文件 交叉核对（不一致项）\n场景\t名栏原文\t说明文件第0行\t拟改为\n")
        for stem, mline, dfirst in hits:
            f.write(f"{stem}\t{mline}\t{dfirst}\t{mp.get(dfirst, '(无译法)')}\n")
    print(f"名单栏与说明文件**不一致** {len(hits)} 个 → {os.path.relpath(REPORT, WS)}")
    print(f"  其中 {len(add)} 条已追加到 per-file 覆盖表")
    for stem, mline, dfirst in hits[:24]:
        print(f"  {stem:16s} 名栏={mline[:26]!r:30s} 说明文件={dfirst[:26]!r}")


if __name__ == "__main__":
    main()
