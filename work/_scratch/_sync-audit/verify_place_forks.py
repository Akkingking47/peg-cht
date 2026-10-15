# -*- coding: utf-8 -*-
"""verify_place_forks.py — 对 A 类地名分叉逐条取原始登记 + 核对真实地名。只读。

1) 打印 faction-places.tsv 里每个实体的**全部登记行**（阵营 / 该方称法 / 中文译名 / 英文写法 / 时期 / 依据）
2) 打印词库里该实体的所有 (en, zh, cat, scope)，看类别标得对不对
3) 打印证据表里每条的实际两值 + 文件 + 该场景阵营（走 faction_place_audit.resolve_sides）
4) 特别核查用户点名的「人名师」：赫尔曼·戈林师 被标成什么类别
"""
import io
import os
import re
import sys
from collections import defaultdict

W = r"D:\DSH\军事游戏汉化"
GL = os.path.join(W, "glossary")
sys.path.insert(0, os.path.join(W, "work", "glossary"))

LAYERS = [os.path.join(GL, "layers", f) for f in
          ("common-glossary.tsv", "scope-glossary.tsv", "series-glossary.tsv")]
FP = os.path.join(GL, "layers", "faction-places.tsv")
EVID = os.path.join(GL, "evidence", "ingest-scn-ovr.tsv")

FORKS = ["Cernauti", "Chernovice", "Chisinau", "Kattowitz", "Lodz", "Posen", "Ternopil'",
         "赫尔曼·戈林师", "Hermann", "Goering", "Göring"]


def layer_rows():
    rows = []
    for p in LAYERS:
        if not os.path.isfile(p):
            continue
        for i, l in enumerate(io.open(p, encoding="utf-8-sig")):
            if i < 2 or l.startswith("#"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 4:
                rows.append((os.path.basename(p), c[0].strip(), c[1].strip(), c[2].strip(), c[3].strip()))
    return rows


def main():
    print("=" * 78)
    print("① faction-places.tsv 原始登记行")
    print("=" * 78)
    fp = defaultdict(list)
    for l in io.open(FP, encoding="utf-8-sig"):
        if l.startswith("#"):
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) < 7:
            continue
        fp[c[0].strip()].append(c)
    for e in ("Cernauti", "Chernovice", "Chisinau", "Kattowitz", "Lodz", "Posen", "Ternopil'"):
        hit = [k for k in fp if k.lower() == e.lower() or e.lower() in k.lower()]
        for k in sorted(set(hit)):
            print("  [%s]" % k)
            for c in fp[k]:
                print("     阵营=%-3s 该方称法=%-22s 中文=%-12s 英文/其它=%-22s 时期=%-14s 依据=%s"
                      % (c[1], c[2], c[3], c[4], c[5] if len(c) > 5 else "", c[6] if len(c) > 6 else ""))

    print()
    print("=" * 78)
    print("② 「赫尔曼·戈林师」在词库里的类别（用户点名：这是人名师，不是地名）")
    print("=" * 78)
    lr = layer_rows()
    for src, en, zh, ct, sc in lr:
        if "赫尔曼" in zh or "戈林" in zh or re.search(r"(?i)goering|göring|hermann", en):
            print("  %-22s en=%-40s zh=%-16s cat=%-8s scope=%s" % (src, en[:40], zh, ct, sc))
    for src, en, zh, ct, sc in lr:
        if "HG师" in zh or zh == "HG" or re.search(r"(?i)^HG", en):
            print("  %-22s en=%-40s zh=%-16s cat=%-8s scope=%s" % (src, en[:40], zh, ct, sc))

    print()
    print("=" * 78)
    print("③ A 类证据行的两值 + 场景阵营")
    print("=" * 78)
    try:
        import faction_place_audit as F
        data = F.load_scenarios()
        pin = F.load_pin()
        side, origin, voice = F.resolve_sides(data, pin)
    except Exception as ex:
        side, origin = {}, {}
        print("  （resolve_sides 不可用：%r）" % (ex,))

    def stem_of(fn):
        b = os.path.basename(fn)
        return re.sub(r"(?i)(?:_(i|m|u|l|bv|tv|v)$|(?<=[0-9])(i|m|u|l|bv|tv|v)$)", "", b)

    want = ("Cernauti", "Chernovice", "Chisinau", "Kattowitz", "Lodz", "Posen", "Ternopil", "HG D")
    for i, l in enumerate(io.open(EVID, encoding="utf-8")):
        if i < 4:
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) < 4:
            continue
        en, ozh, f, why = c[0].strip(), c[1].strip(), c[2].strip(), c[3].strip()
        if not any(w.lower() in en.lower() for w in want):
            continue
        mzh = why.split(":", 1)[1].strip() if why.startswith("映射表另有中文") else why
        st = stem_of(f)
        s = side.get(f, "(未判定)")
        o = origin.get(f, "")
        print("  %-30s 映射=%-22s 覆盖=%-22s 场景阵营=%-3s(%s) %s"
              % (en[:30], mzh[:22], ozh[:22], s, o, f))


if __name__ == "__main__":
    main()
