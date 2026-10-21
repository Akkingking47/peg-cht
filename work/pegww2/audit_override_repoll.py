#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""反向污染复核（**只读**）：既有 per-file 覆盖里「原文行0 本来就是名字、却被覆盖」的行。

背景：`ZS_kanw_m.txt` 行0 原文 `Kaniow-Kanev, crossing the Dniepr` **本来就是它的真名**，
却被上一轮用「说明文件行0」覆盖成 `库尔斯克(Kursk) (ZS#05)，1943 年 7 月 5 日`（那是 ZS_krsk
的名）。本工具用**地图锚定**做判据，把同类风险一次性筛出来：

  ① 地图来源：每个场景 `.SCN` 字节里引用的 `*.MAP`（结构性强证据：它**确实**用这张图）
  ② 地图词表：所有用同一张图的场景，其 `_m.txt` / `.TXT` 行1起的地名标签（英/中成对收集）
  ③ 判定：`原文名(en)` 与 `现译名(zh)` 谁命中地图词表更多
       zh 命中 ≥ en ⇒ ✅ 覆盖合理（或本就与自有材料一致）
       en 命中 >  zh ⇒ ⚠️ 疑似改错（覆盖把名字改离了该图）
       两者皆 0    ⇒ ？无法判定（交人工/实机）

产出：`pegww2/research/_反向污染-复核.tsv`
用法: python audit_override_repoll.py
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2\SCENARIO"
BK = r"d:\DSH\军事游戏汉化\pegww2\testbed\backup\SCENARIO"
OVFP = os.path.join(WS, "pegww2", "research", "_scn-file-overrides.tsv")
OUT = os.path.join(WS, "pegww2", "research", "_反向污染-复核.tsv")

SUFFIX = re.compile(r"(?i)(_m|_u|_i|_l|_bv|_tv|_v)?(\.txt|\.TXT)$")
JUNK = re.compile(r"(?i)^(dummy|=====|消息来自|loading scen|n/?a|-+)$")


def index(root):
    return {n.lower(): n for n in os.listdir(root) if os.path.isfile(os.path.join(root, n))}


G, B = index(GAME), index(BK)


def lines(i, r, n, enc):
    real = i.get(n.lower())
    if not real:
        return []
    try:
        return io.open(os.path.join(r, real), encoding=enc, errors="replace").read().splitlines()
    except Exception:
        return []


def l0(i, r, n, enc):
    ls = lines(i, r, n, enc)
    return ls[0].strip() if ls else ""


def scn_maps(stem):
    real = G.get((stem + ".scn").lower())
    if not real:
        return set()
    try:
        b = io.open(os.path.join(GAME, real), "rb").read()
    except Exception:
        return set()
    return {t.decode("latin1").upper()[:-4] for t in re.findall(rb"[ -~]{4,}", b)
            if t.lower().endswith(b".map")}


def stem_of(fn):
    return SUFFIX.sub("", fn).strip()


def label_ok(s):
    s = s.strip()
    if len(s) < 3 or len(s) > 20 or JUNK.match(s):
        return False
    if re.search(r"[。！？，;:：]", s):
        return False
    return bool(re.search(r"[A-Za-z\u4e00-\u9fff]", s))


def main():
    stems = {}
    for fn in sorted(G):
        if fn.endswith("_m.txt"):
            st = stem_of(fn)
            stems[st.lower()] = st
    maps = {k: scn_maps(v) for k, v in stems.items()}

    # 地图词表（英/中成对）
    ven, vzh = {}, {}
    for k, st in stems.items():
        ms = maps.get(k) or set()
        if not ms:
            continue
        en = lines(B, BK, st + "_m.txt", "cp1252")[1:41] + lines(B, BK, st + ".TXT", "cp1252")[1:41]
        zh = lines(G, GAME, st + "_m.txt", "gbk")[1:41] + lines(G, GAME, st + ".TXT", "gbk")[1:41]
        for i in range(min(len(en), len(zh))):
            if label_ok(en[i]) and label_ok(zh[i]):
                for m in ms:
                    ven.setdefault(m, set()).add(en[i].strip().lower())
                    vzh.setdefault(m, set()).add(zh[i].strip())

    def hits(text, vocab):
        t = (text or "").lower()
        return sum(1 for v in vocab if len(v) >= 4 and v in t)

    # 忠实翻译判据：映射表里 en 的译法 == 现译名（剥组号前缀后）⇒ 覆盖只是把原名译出来，无风险
    MAPZ = {}
    mapp = os.path.join(WS, "pegww2", "research", "ww2-scn-map.tsv")
    if os.path.isfile(mapp):
        for ml in io.open(mapp, encoding="utf-8-sig"):
            f2 = ml.rstrip("\n").split("\t")
            if len(f2) >= 2 and f2[0].strip() and f2[0] not in MAPZ:
                MAPZ[f2[0]] = f2[1].strip()
    PRE = re.compile(r"^[\u4e00-\u9fff]{2,4}\s*-\s*\d+\s+")

    def zk(s):
        s = PRE.sub("", (s or "").strip())
        s = re.sub(r"(?i)peg\s*:\s*ww2|\buk\b", "", s)
        return re.sub(r"[\s:：·\-—()（）\[\]【】,，.。!！?？\"'’“”/\\]", "", s).lower()

    rows = []
    for l in io.open(OVFP, encoding="utf-8-sig"):
        c = l.rstrip("\n").split("\t")
        if len(c) < 5 or not c[2].strip().isdigit() or int(c[2]) != 0:
            continue
        en, zh, fn = c[3].strip(), c[4].strip(), c[1].strip()
        if not en or fn in ("文件", "期望原文"):
            continue
        if (re.search(r"[.!?]\s*$", en) and len(en.split()) > 2) or len(en.split()) > 8:
            continue                                    # 原文本身是句/长句 ⇒ 覆盖应属正确
        st = stem_of(fn)
        ms = maps.get(st.lower()) or set()
        vEn = set().union(*[ven.get(m, set()) for m in ms]) if ms else set()
        vZh = set().union(*[vzh.get(m, set()) for m in ms]) if ms else set()
        hEn, hZh = hits(en, vEn), hits(zh, vZh)
        cups = l0(G, GAME, st + ".TXT", "gbk") or l0(G, GAME, st + "_u.txt", "gbk")
        own = (cups.strip() and (cups.strip() in zh or zh in cups.strip())) or False
        faithful = bool(MAPZ.get(en)) and zk(MAPZ.get(en)) == zk(zh)
        if faithful:
            verdict = "✓ 忠实翻译"
        elif own:
            verdict = "✓ 与自有材料一致"
        elif hZh >= hEn and hZh > 0:
            verdict = "✓ 更贴地图"
        elif hEn > hZh:
            verdict = "⚠️ 疑似改错"
        else:
            verdict = "？无法判定"
        rows.append([verdict, st, fn, zh, en, ",".join(sorted(ms)) or "-",
                     "en命中%d/zh命中%d" % (hEn, hZh), cups or "-"])

    rows.sort(key=lambda r: ({"⚠️ 疑似改错": 0, "？无法判定": 1}.get(r[0], 2), r[1]))
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 反向污染复核（只读）：既有 per-file 覆盖里「原文行0 本是名字」的行\n")
        f.write("# 判据：该场景 .SCN 引用的 *.MAP → 该图同图场景的地名标签词表（英/中）；谁命中多谁更贴图\n")
        f.write("判定\t场景\t文件\t现译名\t原文行0\t地图\t命中\tself.TXT/_u 行0\n")
        for r in rows:
            f.write("\t".join(x.replace("\t", " ") for x in r) + "\n")

    print("复核 %d 行 → %s" % (len(rows), OUT))
    for k in ("⚠️ 疑似改错", "？无法判定", "✓ 更贴地图", "✓ 与自有材料一致"):
        print("  %-14s %d" % (k, sum(1 for r in rows if r[0] == k)))
    for r in rows:
        if r[0].startswith("⚠️"):
            print("   ⚠ %-14s 原文=%-44s 现=%s" % (r[1], r[4][:44], r[3][:30]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
