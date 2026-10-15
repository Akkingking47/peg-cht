#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""关键安全性检验：同一段英文的两种译法，是否**出现在同一个成品文件里**？

数据源 = **已投放的游戏正文**（`SCENARIO` + `USERSCEN` 的 `.txt`），不是映射表——
这样「文件内并列」就是**玩家真能看到的不一致**。

判读：
  · 同一文件内并列两种写法 ⇒ 差异**不可能是**「按文件/槽位刻意截短」 ⇒ 可安全统一。
  · 两种写法**严格按文件分开** ⇒ 必须逐个查该文件的槽位约束，不可轻改。
"""
import io
import os
import re
import sys
from collections import defaultdict

GAME = r"D:\Program Files\PeG-WW2"
# 候选段（与 sweep_map_segments.py 的 61 组真冲突一致）
SEGS = """VIII|2 NZ|HG D|[SS Pz]|9 ID|1 Army Free|Das Reich|1 Arm|1 Br|9 Aust.|4 Bde|90 LD|
I Army|II Corps|1 SA|5 LD|4 Br|8 R|1 SA Div|12 R|2 Indian ID|V Army|2 African D|- [A Corps]|
7 R|1 African D|102 Trento|2 SA Div|4 Ind|4 Ind D.|4 Indian.|7 Arm D|StG1|132 Ariete|4 Ind D|
Carpathian Rifle Brigade|Polish|Raemcke Bde.|101 Trieste|164 LD|168 R|101Trieste|27 Brescia|
Saharian Grouping|17SS|185 Folgore|2 155 R|55 Savona|7 SG|DR [2SS]|Imperiali D|JG26 [JFF2] LF2|
JG51 [II] LF2|Trento D|2 90 R|7 Mot Bde|8 FR|GD [48]|Giov.Fasc D|LAH [2SS]|ZG1 [JFF2] LF2"""
SEGS = [s.strip() for s in SEGS.replace("\n", "").split("|") if s.strip()]


def load_map_segs():
    """一次读完映射表：en_seg → Counter(zh_seg)。"""
    idx = defaultdict(lambda: defaultdict(int))
    p = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "..", "..", "pegww2", "research", "ww2-scn-map.tsv"))
    for l in io.open(p, encoding="utf-8-sig"):
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
            if a and b:
                idx[a][b] += 1
    return idx


def read_files():
    files = {}
    for sub in ("SCENARIO", "USERSCEN"):
        d = os.path.join(GAME, sub)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if not fn.lower().endswith(".txt"):
                continue
            try:
                t = io.open(os.path.join(d, fn), encoding="gbk", errors="replace").read()
            except Exception:
                continue
            if not re.search(r"[\u4e00-\u9fff]", t):
                continue
            files[sub + "/" + fn] = [ln.split("/") for ln in t.replace("\r", "").split("\n")]
    return files


def main():
    if "--out" in sys.argv:
        fp = sys.argv[sys.argv.index("--out") + 1]
        sys.stdout = io.open(fp, "w", encoding="utf-8", newline="\n")
    files = read_files()
    IDX = load_map_segs()
    print("扫描成品文件 %d 个" % len(files))
    print("=" * 100)
    mixed_all, split_all = [], []
    for en in SEGS:
        vs = dict(IDX.get(en, {}))
        if len(vs) < 2:
            continue
        homes = defaultdict(set)
        for f, lines in files.items():
            segs = set(x.strip() for ln in lines for x in ln)
            for v in vs:
                if v in segs:
                    homes[v].add(f)
        mixed = set()
        for v, fs in homes.items():
            for w, gs in homes.items():
                if v < w:
                    mixed |= (fs & gs)
        tot = sum(len(s) for s in homes.values())
        print("%-28s 共%4d处 → %s" % (en[:28], tot,
              " ｜ ".join("%s×%d文件" % (v[:18], len(fs)) for v, fs in
                          sorted(homes.items(), key=lambda x: -len(x[1])))))
        if mixed:
            mixed_all.append(en)
            print("        ⭐同一成品文件内并列 %d 个：%s" % (len(mixed), "; ".join(sorted(mixed)[:5])))
        else:
            if all(len(fs) for fs in homes.values()):
                split_all.append(en)
                print("        （按文件严格分开，需查槽位）")
    print("=" * 100)
    print("⭐文件内并列（可安全统一）= %d 组：%s" % (len(mixed_all), " ｜ ".join(mixed_all)))
    print("⚠️按文件严格分开（需查槽位）= %d 组：%s" % (len(split_all), " ｜ ".join(split_all)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
