# -*- coding: utf-8 -*-
"""把 bridge-mismatch.tsv 的 1399 处不一致分类，区分「仅风格差异」与「核心译名不同」。

分类：
  S_SUF   —— 去掉末尾「类别词」（河/运河/森林/城堡/路…）后核心相同 ⇒ 纯风格
  S_SUB   —— 一方是另一方的子串（含序列） ⇒ 纯风格
  N_VAR   —— 字符重合高（去掉类别词后仍有少量差异，如 蔚松/蔚城） ⇒ 疑似笔误
  E_DIS   —— 重合低（译法根本不同，如 库姆维/金渭、翁泽利弗劳韦弗尔/瓦弗圣母） ⇒ 重点
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# 末尾类别词（长优先）
SUF = ["运河", "公路", "大道", "铁路", "森林", "沼泽", "丘陵", "高地", "半岛", "海峡", "防线",
       "地区", "机场", "车站", "港口", "渠道", "河口", "城堡", "碉堡", "要塞", "水库",
       "河", "江", "湖", "山", "岛", "湾", "港", "城", "镇", "村", "庄", "堡", "桥", "街",
       "路", "道", "林", "营", "场", "区", "口", "峰", "岭", "关", "浦", "川", "潭", "原", "洲"]
# 前缀方位/连接词
PRE = ["通往", "至", "北", "南", "东", "西", "新", "旧", "上", "下", "内", "外", "大", "小", "老"]


def strip_suf(s):
    for _ in range(3):
        for t in SUF:
            if len(s) > len(t) and s.endswith(t):
                s = s[:-len(t)]
                break
        else:
            break
    return s


def strip_pre(s):
    for _ in range(3):
        for t in PRE:
            if len(s) > len(t) and s.startswith(t):
                s = s[len(t):]
                break
        else:
            break
    return s


def lcs_len(a, b):
    """两串最长公共子序列长度（字符级）。"""
    if len(a) > len(b):
        a, b = b, a
    prev = [0] * (len(a) + 1)
    for cb in b:
        cur = [0]
        for x in range(1, len(a) + 1):
            if a[x - 1] == cb:
                cur.append(prev[x - 1] + 1)
            else:
                cur.append(max(cur[-1], prev[x]))
        prev = cur
    return prev[-1]


def classify(sc, want):
    if sc == want:
        return "OK", 1.0
    a, b = strip_suf(sc), strip_suf(want)
    if a == b or strip_pre(a) == strip_pre(b):
        return "S_SUF", 1.0
    if sc in want or want in sc:
        return "S_SUB", 1.0
    l = lcs_len(sc, want)
    r = l / float(max(len(sc), len(want)))
    if r >= 0.75:
        return "N_VAR", r
    return "E_DIS", r


def main():
    p = os.path.join(HERE, "out", "bridge-mismatch.tsv")
    rows = []
    for ln in io.open(p, encoding="utf-8").read().splitlines():
        c = ln.split("\t")
        if len(c) == 5:
            rows.append(c)
    cats = {}
    for n, i, se, sc, want in rows:
        c, r = classify(sc, want)
        cats.setdefault(c, []).append((n, int(i), se, sc, want, r))

    print("总不一致: %d 处 / %d 个文件" % (len(rows), len(set(r[0] for r in rows))))
    print()
    order = ["S_SUF", "S_SUB", "N_VAR", "E_DIS"]
    desc = {"S_SUF": "仅末尾类别词差异（河/运河/森林/路…）——纯风格",
            "S_SUB": "一方为另一方子串（含方位前缀）——纯风格",
            "N_VAR": "核心译名近似（少数字不同，如 蔚松/蔚城）——疑似笔误",
            "E_DIS": "译法根本不同（如 库姆维/金渭）——重点"}
    for c in order:
        v = cats.get(c, [])
        fl = sorted(set(x[0] for x in v))
        print("%-6s %5d 处 / %3d 文件   %s" % (c, len(v), len(fl), desc[c]))
    print()

    for c in ("N_VAR", "E_DIS"):
        v = cats.get(c, [])
        print("=" * 100)
        print("%s —— 全部 %d 处" % (c, len(v)))
        print("=" * 100)
        print("%-18s %-4s %-26s %-20s %s" % ("file", "i", "orig英文", "现有中文", "权威中文"))
        for n, i, se, sc, want, r in sorted(v, key=lambda x: (x[0], x[1])):
            print("%-18s %-4d %-26s %-20s %s" % (n, i, se[:26], sc[:20], want))
        print()

    # 按场景前缀汇总
    print("=" * 100)
    print("按文件汇总：N_VAR + E_DIS 处数 top 40")
    print("=" * 100)
    agg = {}
    for c in ("N_VAR", "E_DIS"):
        for n, i, se, sc, want, r in cats.get(c, []):
            agg[n] = agg.get(n, 0) + 1
    for n, k in sorted(agg.items(), key=lambda x: -x[1])[:40]:
        print("  %-22s %d" % (n, k))


if __name__ == "__main__":
    main()
