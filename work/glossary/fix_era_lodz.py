#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**年代维度 · 首个真发现落地** + 补齐 Königsberg 1946 规则。

发现：`lah_it_gran_i.txt`（**1945-02**，德方视角）行4 写「华沙(Warsaw)、**罗兹**(Lodz)与克拉科夫(Krakow)已经陷落」
  ⇒ 德方 1940-04 起已把 Łódź 改称 **Litzmannstadt**（利茨曼施塔特）⇒ 该行应用**利茨曼施塔特(Lodz)**
  ⇒ 这是**阵营维度永远抓不到**的错（同阵营、跨年代改名），**年代维度**首战即抓到 ✓

用法: python fix_era_lodz.py [--apply]
"""
import io
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
OVF = os.path.join(WS, "pegww2", "research", "_scn-file-overrides.tsv")
PLACES = os.path.join(WS, "glossary", "layers", "faction-places.tsv")
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
GAME = r"D:\Program Files\PeG-WW2\SCENARIO"
CBK = os.path.join(WS, "backup", "before-era-fix")
FN, IDX, OLD, NEW = "lah_it_gran_i.txt", 3, "罗兹", "利茨曼施塔特"


def main():
    apply_ = "--apply" in sys.argv
    zh = io.open(os.path.join(GAME, FN), encoding="gbk", errors="replace").read().split("\n")
    cur = zh[IDX]
    if OLD not in cur:
        print("   ⚠️ 未见「%s」" % OLD)
        return 1
    new = cur.replace(OLD, NEW)
    print("=== ① 年代改正：%s 行%d ===" % (FN, IDX + 1))
    print("   旧: …%s…" % cur[max(0, cur.find(OLD) - 40):cur.find(OLD) + 20])
    print("   新: …%s…" % new[max(0, new.find(NEW) - 40):new.find(NEW) + 20])
    print("\n=== ② 补齐 Königsberg 苏方 1946 规则（使跨名检测生效）===")
    pl = io.open(PLACES, encoding="utf-8").read().split("\n")
    has = any(l.startswith("Koenigsberg\t苏") and ">=1946" in l for l in pl)
    print("   已存在：%s" % has)
    if not apply_:
        print("\n（dry-run；加 --apply）")
        return 0
    os.makedirs(CBK, exist_ok=True)
    for p in (OVF, PLACES):
        b = os.path.join(CBK, os.path.basename(p))
        if not os.path.isfile(b):
            shutil.copy2(p, b)
    # ① 覆盖表
    t = io.open(OVF, encoding="utf-8").read()
    en = io.open(os.path.join(BK, FN), encoding="cp1252", errors="replace").read().split("\n")[IDX]
    out, done = [], False
    for l in t.split("\n"):
        c = l.split("\t")
        if len(c) >= 3 and c[1] == FN and c[2] == str(IDX):
            l = "\t".join(("SCENARIO", FN, str(IDX), en.rstrip("\r\n"), new, "年代改正：1945-02 德方应称利茨曼施塔特"))
            done = True
        out.append(l)
    if not done:
        if not out[-1].endswith("\n"):
            out[-1] += "\n"
        out.append("\t".join(("SCENARIO", FN, str(IDX), en.rstrip("\r\n"), new,
                              "年代改正：1945-02 德方应称利茨曼施塔特")))
    io.open(OVF, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print("   ✅ 覆盖表已写")
    # ② 登记表补行
    if not has:
        add = "Koenigsberg\t苏\tКалининград\t加里宁格勒\tKaliningrad\t>=1946 → 加里宁格勒\t1946 年改名（1945 年攻占时仍称 Кёнигсберг）"
        pl = [l for l in pl if l.strip() != ""] + [add, ""]
        io.open(PLACES, "w", encoding="utf-8", newline="\n").write("\n".join(pl))
        print("   ✅ 登记表已补 Königsberg/苏 >=1946 行")
    return 0


if __name__ == "__main__":
    sys.exit(main())
