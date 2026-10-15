# -*- coding: utf-8 -*-
"""audit_place_mistag.py — 查词库里「部队/人名」被错标成 PLACE 的条目。只读。

起因（用户 m01642）：`赫尔曼·戈林师` 是**人名师**，不是地名；但词库 EFILE_OLGWW2 侧把它
标成了 cat=PLACE，导致我的分类器把 `第1团/HG师 ⇄ 第1团/赫尔曼·戈林师` 误判为地名分叉。
本脚本量化这类误标：中文以部队/司令部后缀结尾，却标成 PLACE。
"""
import io
import os
import re
from collections import Counter, defaultdict

W = r"D:\DSH\军事游戏汉化"
GL = os.path.join(W, "glossary")
LAYERS = [os.path.join(GL, "layers", f) for f in
          ("common-glossary.tsv", "scope-glossary.tsv", "series-glossary.tsv")]

UNIT_TAIL = ("师", "军", "团", "旅", "大队", "联队", "兵团", "司令部", "集团军", "纵队",
             "营", "连", "排", "中队", "舰队", "航空队", "警备队", "卫队")
PERSONY = re.compile(r"(赫尔曼|戈林|盖尔|隆美尔|曼施坦因|古德里安|莫德尔|保卢斯|龙德施泰特|"
                     r"凯塞林|邓尼茨|希姆莱|戈培尔|斯大林|列宁|朱可夫|罗斯福|巴顿|蒙哥马利)")
# ⭐ 人名来源的地名**必须豁免**（用户 m01642 明确提醒）：
#    列宁格勒/斯大林格勒/加里宁格勒/基洛夫格勒… 是地名，不是人名部队
PERSON_PLACE = re.compile(r"(列宁|斯大林|基洛夫|伏罗希洛夫|加里宁|古比雪夫|莫洛托夫|高尔基|"
                          r"伏龙芝|捷尔任斯基|日丹诺夫|恩格斯)(格勒|斯克|诺夫卡|诺|卡|市|州|区|堡|城)")
CITY_TAIL_GUARD = ("大连", "新连")


def main():
    tot = Counter()
    by_scope = defaultdict(Counter)
    samples = defaultdict(list)
    for p in LAYERS:
        if not os.path.isfile(p):
            continue
        for i, l in enumerate(io.open(p, encoding="utf-8-sig")):
            if i < 2 or l.startswith("#"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) < 4:
                continue
            en, zh, ct, sc = c[0].strip(), c[1].strip(), c[2].strip(), c[3].strip()
            if ct != "PLACE":
                continue
            tot["PLACE 总条目"] += 1
            if PERSON_PLACE.search(zh) or zh in CITY_TAIL_GUARD:
                tot["人名来源地名(豁免)"] += 1
                continue
            tail = [t for t in UNIT_TAIL if zh.endswith(t)]
            py = PERSONY.search(zh)
            if tail or py:
                why = []
                if tail:
                    why.append("部队后缀:" + ",".join(tail))
                if py:
                    why.append("人名:%s" % py.group(1))
                key = "+".join(why)
                tot[key.split(":")[0]] += 1
                by_scope[sc][key] += 1
                if len(samples[key]) < 8:
                    samples[key].append((os.path.basename(p), en, zh, sc))

    print("=== PLACE 误标扫描 ===")
    print("  PLACE 总条目（三层表去重前）: %d" % tot["PLACE 总条目"])
    for k in ("部队后缀", "人名"):
        print("  %s 疑似误标: %d" % (k, tot[k]))
    print()
    print("-- 按 scope --")
    for sc in sorted(by_scope, key=lambda s: -sum(by_scope[s].values())):
        n = sum(by_scope[sc].values())
        print("   %-18s %5d   %s" % (sc, n, dict(by_scope[sc])))
    print()
    print("-- 样本 --")
    for k in sorted(samples, key=lambda x: -len(samples[x])):
        print("  [%s]" % k)
        for src, en, zh, sc in samples[k][:6]:
            print("     %-20s en=%-34s zh=%-20s scope=%s" % (src, en[:34], zh[:20], sc))
    print()
    print("-- 人名来源的地名（应当**保留**为 PLACE 的对照样本）--")
    for p in LAYERS[:1]:
        if not os.path.isfile(p):
            continue
        for i, l in enumerate(io.open(p, encoding="utf-8-sig")):
            if i < 2 or l.startswith("#"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) < 4 or c[2].strip() != "PLACE":
                continue
            if re.search(r"(?i)leningrad|stalingrad|kalinin|kuibyshev|gorky|molotov|kirov|frunze", c[0]):
                print("     en=%-26s zh=%-16s scope=%s" % (c[0].strip()[:26], c[1].strip()[:16], c[3].strip()))


if __name__ == "__main__":
    main()
