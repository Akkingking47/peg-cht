# -*- coding: utf-8 -*-
"""定名前的现状勘查：对 residual-names-todo.tsv 的每条，列出
每次出现的**文件实际内容**（.xscn 槽 / .txt 行）与词库 occ 记录值。只读。

判定：含汉字+拉丁 → 「中文夹英文」；无汉字 → 「纯英文未译」。
"""
import collections
import io
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
sys.path.insert(0, os.path.join(WS, "work", "efile-nashornpbem"))
from apply_residual import parse  # noqa

TODO = os.path.join(WS, "work", "_sync-audit", "residual-names-todo.tsv")
OCC = os.path.join(WS, "glossary", "glossary-occ.tsv")
GAME = r"D:\OpenPG2"
CJK = lambda s: any("\u4e00" <= c <= "\u9fff" for c in s)


def read_tsv(p):
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        L = f.read().replace("\r\n", "\n").split("\n")
    head = L[0].split("\t")
    out = []
    for ln in L[1:]:
        if not ln.strip():
            continue
        c = ln.split("\t")
        out.append({head[k]: (c[k] if k < len(c) else "") for k in range(len(head))})
    return out


todo = read_tsv(TODO)
want = set(r["en"] for r in todo)

occ = collections.defaultdict(list)
for r in read_tsv(OCC):
    if r["en"] in want:
        occ[r["en"]].append(r)

cache = {}


def slot(efile, fn, g, idx):
    key = (efile, fn)
    if key not in cache:
        p = os.path.join(GAME, efile, "SCENARIO", fn)
        if not os.path.exists(p):
            cache[key] = None
        else:
            data, items, meta = parse(p)
            t = {}
            if items:
                for gi, k, off, L in items:
                    t[(gi, k)] = data[off + 2:off + 2 + L]
            if meta and meta[0] is not None:
                t[(-1, 0)] = data[meta[0] + 2:meta[0] + 2 + meta[1]]
            cache[key] = t
    t = cache[key]
    if not t:
        return None
    b = t.get((g, idx))
    if b is None:
        return None
    try:
        return b.decode("gbk")
    except Exception:
        return repr(b)


def txtline(efile, rel, ln):
    p = os.path.join(GAME, efile, rel)
    if not os.path.exists(p):
        return None
    raw = open(p, "rb").read().decode("gbk", "replace").split("\n")
    return raw[ln - 1] if 0 < ln <= len(raw) else None


stat = collections.Counter()
rows = []
for r in todo:
    en = r["en"]
    kinds = []
    sample = ""
    for o in occ[en]:
        efile, src, loc = o["scope"], o["src"], o["loc"]
        if src == "xscn":
            m = loc.split(":")
            fn, gid = m[0].split("/", 1)[1], m[1]
            g, idx = gid[1:].split("#")
            cur = slot(efile, fn, int(g), int(idx))
        elif src == "txt":
            fn, ln = loc.rsplit(":", 1)
            cur = txtline(efile, fn, int(ln))
        else:
            cur = o["zh"]
        cur = "" if cur is None else cur.strip()
        k = ("中文夹英文" if (CJK(cur) and any(c.isalpha() and ord(c) < 128 for c in cur))
             else "纯英文未译" if not CJK(cur) else "已全中文")
        kinds.append(k)
        if not sample:
            sample = cur
    c = collections.Counter(kinds)
    stat.update(c)
    rows.append((en, r["当前库译文"], len(occ[en]), " ".join("%s×%d" % kv for kv in sorted(c.items())), sample))

with io.open(os.path.join(WS, "work", "_sync-audit", "residual-state.tsv"), "w",
             encoding="utf-8", newline="\n") as f:
    f.write("en\t当前库译文\t出现数\t实际状态\t样例\n")
    for en, zh, n, st, s in rows:
        f.write("\t".join((en, zh, str(n), st, s)) + "\n")

print("== 出现处状态合计 ==")
for k, v in stat.most_common():
    print("   %-10s %d" % (k, v))
print()
print("== 按条（95）状态分布 ==")
c2 = collections.Counter(r[3] for r in rows)
for k, v in c2.most_common():
    print("   %-40s %d" % (k, v))
print()
print("== 纯英文未译样例（前 25）==")
n = 0
for en, zh, cnt, st, s in rows:
    if "纯英文" in st:
        print("   %-46s | %s" % (en[:46], s[:60]))
        n += 1
        if n >= 25:
            break
