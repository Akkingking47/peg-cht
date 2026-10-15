# -*- coding: utf-8 -*-
"""导出 OLGWW2 全部「未含汉字」的 .xscn 条目，按分类落盘为 TSV（唯一真源）。

分类 category 取值：
  TITLE   未译场景标题        —— 硬漏译
  PLACE   组0 未译地名        —— 硬漏译
  UNIT_W  组>=1 含真实单词番号 —— 硬漏译
  BRACKET 整串方括号标记       —— 政策保留（军级符号）
  ABBR    缩写式番号           —— 口径待定
  SHIP    船名前缀             —— 政策保留
  ACRO    全大写/含数字型号     —— 政策保留

输出列：file \t group \t idx \t category \t src \t dst
dst 列留空，供人工/批量填写译文。src==dst 表示「保持原文」（政策保留项）。
"""
import os
import re
import io
from collections import Counter

D = r"D:/OpenPG2/EFILE_OLGWW2/SCENARIO"
OUT = r"D:/DSH/军事游戏汉化/work/efile-nashornpbem/olgww2-residual.tsv"

SHIP = re.compile(r"^(HMS|USS|IJN|RMS|SMS|MV|SS|HMCS|HMAS|ORP|ARA|KM|RN|HMIS|HNLMS)\b")
ACRO = re.compile(r"^[A-Z0-9][A-Z0-9 /\-\.',&\+\(\)]*$")
BRACKET_ONLY = re.compile(r"^[\s\-/]*(?:\[[^\]]*\][\s\-/]*)+$")
ROMAN_TOK = re.compile(r"^\[?[IVXLCDM]+\]?$")
WORD = re.compile(r"[A-Za-z]{6,}")


def parse(path):
    f = open(path, "rb").read()
    st = f.find(b"<N:")
    if st < 0:
        return None
    off = f.index(b">", st) + 1
    title = b""
    if off + 2 <= len(f):
        L = f[off] | (f[off + 1] << 8)
        if 0 < L and off + 2 + L <= len(f):
            title = f[off + 2:off + 2 + L]
            off += 2 + L
    items, groups = [], []
    gi = 0
    while off + 2 <= len(f):
        cnt = f[off] | (f[off + 1] << 8)
        if cnt <= 0 or cnt > 4000:
            break
        off += 2
        bad = False
        for k in range(cnt):
            if off + 2 > len(f):
                bad = True
                break
            L = f[off] | (f[off + 1] << 8)
            if L <= 0 or off + 2 + L > len(f):
                bad = True
                break
            items.append((gi, k, f[off + 2:off + 2 + L]))
            off += 2 + L
        if bad:
            break
        groups.append(cnt)
        gi += 1
        if gi > 64:
            break
    return dict(title=title, groups=groups, items=items)


def cjk(raw):
    try:
        s = raw.decode("gbk")
    except Exception:
        return False
    return any("\u4e00" <= c <= "\u9fff" for c in s)


def classify_unit(s):
    toks = [t for t in re.split(r"[\s/]+", s) if t]
    if BRACKET_ONLY.match(s):
        return "BRACKET"
    if any(len(re.sub(r"[^A-Za-z]", "", t)) >= 6 for t in toks):
        return "UNIT_W"
    return "ABBR"


rows = []
stat = Counter()

files = sorted(f for f in os.listdir(D) if f.lower().endswith(".xscn"))
for fn in files:
    x = parse(os.path.join(D, fn))
    if x is None:
        stat["unparsed"] += 1
        continue
    # 标题
    if x["title"] and not cjk(x["title"]):
        try:
            t = x["title"].decode("ascii")
            if t.strip() and not SHIP.match(t) and not ACRO.match(t):
                rows.append((fn, -1, 0, "TITLE", t))
                stat["TITLE"] += 1
        except Exception:
            pass
    for g, i, raw in x["items"]:
        if cjk(raw):
            continue
        try:
            s = raw.decode("ascii")
        except Exception:
            stat["non-ascii-non-cjk"] += 1
            continue
        if len(s.strip()) < 3:
            stat["too-short"] += 1
            continue
        if SHIP.match(s):
            rows.append((fn, g, i, "SHIP", s))
            stat["SHIP"] += 1
        elif ACRO.match(s):
            rows.append((fn, g, i, "ACRO", s))
            stat["ACRO"] += 1
        elif g == 0:
            rows.append((fn, g, i, "PLACE", s))
            stat["PLACE"] += 1
        else:
            c = classify_unit(s)
            rows.append((fn, g, i, c, s))
            stat[c] += 1

with io.open(OUT, "w", encoding="utf-8", newline="") as f:
    f.write("file\tgroup\tidx\tcategory\tsrc\tdst\n")
    for fn, g, i, c, s in rows:
        f.write("%s\t%d\t%d\t%s\t%s\t\n" % (fn, g, i, c, s))

print("输出:", OUT)
print("总条目(未含汉字):", len(rows))
for k in ("TITLE", "PLACE", "UNIT_W", "ABBR", "BRACKET", "SHIP", "ACRO"):
    print("  %-8s %4d" % (k, stat[k]))
hard = stat["TITLE"] + stat["PLACE"] + stat["UNIT_W"]
print("  硬漏译合计(TITLE+PLACE+UNIT_W) =", hard)
print("  其它:", dict((k, v) for k, v in stat.items() if k in ("too-short", "non-ascii-non-cjk", "unparsed")))
per = Counter(r[0] for r in rows)
print("  涉及文件数:", len(per))
