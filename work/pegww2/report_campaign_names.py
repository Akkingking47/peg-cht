#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「战役内场景名 vs 说明名」的差集分类，给出处置建议（**只读**）。

读 `pegww2/research/_战役-场景与地图核准.tsv`，对每行「名栏≠说明名」判：
  同源    同一地点的不同写法/译法（剥括注、去助词后仍互含） ⇒ 不改
  改说明名 说明名能落到该场实际地图的同图场景集里，而名栏落不进去 ⇒ 名栏疑借自别处，按说明名改
  留名栏  名栏能落到同图场景集 ⇒ 名栏与地图相符 ⇒ 保留
  待判    两者都落不进 / 都落得进 ⇒ 交人工

产出：`pegww2/research/_战役-名栏与说明不符-20261019.tsv`
用法: python report_campaign_names.py
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2\SCENARIO"
RES = os.path.join(WS, "pegww2", "research")
SRC = os.path.join(RES, "_战役-场景与地图核准.tsv")
OUT = os.path.join(RES, "_战役-名栏与说明不符-20261019.tsv")

PREFIX = re.compile(r"^[\u4e00-\u9fff]{2,4}\s*-\s*\d+\s+")
DROP = re.compile(r"(?i)peg\s*:\s*ww2|\buk\b")
CJKWORD = re.compile(r"[\u4e00-\u9fff]{2,}")


def index(root):
    return {n.lower(): n for n in os.listdir(root) if os.path.isfile(os.path.join(root, n))}


IDX = index(GAME)


def rd(name, k=0):
    real = IDX.get(name.lower())
    if not real:
        return None
    try:
        ls = io.open(os.path.join(GAME, real), encoding="gbk", errors="replace").read().splitlines()
    except Exception:
        return None
    return ls[k].rstrip("\r\n") if len(ls) > k else None


def maptok(stem):
    real = IDX.get((stem + ".scn").lower())
    if not real:
        return ""
    try:
        b = io.open(os.path.join(GAME, real), "rb").read()
    except Exception:
        return ""
    return ",".join(m.decode("latin1")[:-4].upper() for m in
                    sorted({t for t in re.findall(rb"[ -~]{4,}", b) if t.lower().endswith(b".map")})[:3])


def cjk(s):
    return "".join(re.findall(r"[\u4e00-\u9fff]", s or ""))


def key(s):
    if not s:
        return ""
    s = PREFIX.sub("", s.strip())
    s = DROP.sub("", s)
    s = re.sub(r"\([^)]*\)|（[^）]*）", "", s)          # 去括注
    s = re.sub(r"[\s:：·\-—,，.。/\\]", "", s)
    s = re.sub(r"(行动|战役|攻势|之战|防线|的|和|与)$", "", s)
    return s.lower()


def same(a, b):
    """同源：去括注与助词后互含，或共享 ≥2 连续汉字。"""
    ka, kb = key(a), key(b)
    if not ka or not kb:
        return False
    ca, cb = cjk(ka), cjk(kb)
    if not ca or not cb:
        return False
    if ca in cb or cb in ca:
        return True
    for n in range(min(len(ca), len(cb)), 1, -1):
        for i in range(len(ca) - n + 1):
            if ca[i:i + n] in cb:
                return True
    return False


def overlap(name, peer_list):
    """name 与同图场景名集的「同源」命中数。"""
    return sum(1 for p in peer_list if same(name, p))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    # 全库：场景 → 名栏 / 地图
    stems = {}
    for fn in sorted(n for n in IDX if n.lower().endswith("_m.txt")):
        st = re.sub(r"(?i)_m\.txt$", "", IDX[fn])
        stems[st.lower()] = st
    name_of = {k: (rd(st + "_m.txt", 0) or "") for k, st in stems.items()}
    map_of = {k: maptok(st) for k, st in stems.items()}
    bymap = {}
    for k, mp in map_of.items():
        for one in mp.split(","):
            if one:
                bymap.setdefault(one, []).append(k)
    name2maps = {}
    for k, n in name_of.items():
        if n:
            name2maps.setdefault(key(n), set()).add(map_of[k])

    rows = []
    for l in io.open(SRC, encoding="utf-8"):
        if not l.strip() or l.startswith("#"):
            continue
        c = l.rstrip("\n").split("\t")
        if c[0] == "战役":
            continue
        camp, cf, idx, stem, M, I, Iraw, ifile, MP, peers_s, lname, lmap, seq, flags = c
        if "名栏≠说明名" not in flags:
            continue
        peers = [name_of.get(p.strip().lower(), "") for p in peers_s.split("|") if p.strip()]
        peers = [p for p in peers if p]
        if same(M, I):
            verdict, adv = "同源·不改", ""
        else:
            i_hit, m_hit = overlap(I, peers), overlap(M, peers)
            m_borrow = len(name2maps.get(key(M), set()) - {MP}) > 0
            i_borrow = len(name2maps.get(key(I), set()) - {MP}) > 0
            if i_hit > m_hit:
                verdict, adv = "名栏疑借用·改按说明名", I
            elif m_hit > i_hit:
                verdict, adv = "名栏合图·保留", ""
            elif m_borrow and not i_borrow:
                verdict, adv = "名栏疑借用·改按说明名", I
            elif i_borrow and not m_borrow:
                verdict, adv = "说明疑借用·保留", ""
            else:
                verdict, adv = "待判", ""
        rows.append([camp, cf, idx, stem, M, I, Iraw, MP, peers_s, verdict, adv])

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 战役内「名栏(_m.txt 行0) vs 说明名(_i.txt 名字行)」反差分类（只读产出）\n")
        f.write("# 判据：说明名/名栏 谁能落到『该场实际地图的同图场景名集』；同源=同地点不同写法\n")
        f.write("战役\t战役文件\t场次\t场景\t名栏\t说明名\t说明名原文行\t地图\t同图场景名\t判定\t建议\n")
        for r in rows:
            f.write("\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in r) + "\n")

    from collections import Counter
    cnt = Counter(r[9] for r in rows)
    print("反差行 %d" % len(rows))
    for k, v in cnt.most_common():
        print("  %-22s %d" % (k, v))
    print("→ %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
