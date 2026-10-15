# -*- coding: utf-8 -*-
"""全仓扫描：定名规则表（naming.tsv）的 old 串还残留在哪些「中文侧」文本里。

目的：回答「把词库更新铺到 PeG 及 peg-ww2」时**到底哪些工程还有残留**。
只读。输出：
  - 控制台：按工程/根目录汇总（中文侧命中 / 英文侧命中）
  - work\\_sync-audit\\residue-all-hits.tsv：逐条命中

「中文侧」＝该行/该槽里既含汉字、又含规则 old 串（即“中文夹英文”的残留形态）。
「英文侧」＝只有 old 串、没有汉字（多为原文/映射表英文列/死镜像），**不是**本次对象。
"""
import io
import os
import re
import sys

sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\efile-nashornpbem")
from apply_residual import parse  # noqa: E402

WS = r"D:\DSH\军事游戏汉化"
NAMING = os.path.join(WS, "work", "_sync-audit", "naming.tsv")
OUT = os.path.join(WS, "work", "_sync-audit", "residue-all-hits.tsv")
CJK = re.compile(u"[\u4e00-\u9fff]")
TEXT_EXT = (".txt", ".tsv", ".md", ".csv", ".xml", ".ini", ".cfg", ".lst", ".json")
SKIP_DIR = ("backup", "_ref", ".git", "node_modules", "__pycache__", ".workbuddy",
            "OpenIcons", "Docs", "maps", "graphics", "sound", "music", "_scn-bak")


def load_rules():
    rows = []
    for i, ln in enumerate(io.open(NAMING, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")):
        if i == 0 or not ln.strip() or ln.startswith("#"):
            continue
        c = ln.split("\t")
        if len(c) < 3:
            continue
        rows.append((c[0], c[1], c[2]))
    return rows


def build_re(rules):
    olds = sorted({o for _k, o, _n in rules}, key=len, reverse=True)
    return re.compile("|".join(re.escape(o) for o in olds))


def scan_bytes(path, rex, hits, tag, enc=None):
    try:
        raw = open(path, "rb").read()
    except Exception as e:
        hits.append((tag, path, "-", "READFAIL", str(e)[:60]))
        return 0, 0
    if enc is None:
        if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
            enc = "utf-16"
        elif raw[:3] == b"\xef\xbb\xbf":
            enc = "utf-8-sig"
        else:
            enc = "utf-8"
    try:
        s = raw.decode(enc, "replace")
    except Exception:
        s = raw.decode("gbk", "replace")
    if not rex.search(s):
        return 0, 0
    zh = en = 0
    for n, ln in enumerate(s.replace("\r\n", "\n").split("\n"), 1):
        m = rex.search(ln)
        if not m:
            continue
        ws_ = sorted({x for x in rex.findall(ln)})
        if CJK.search(ln):
            zh += 1
            if zh <= 400:
                hits.append((tag, path, str(n), "中文侧", "/".join(ws_)[:80], ln.strip()[:160]))
        else:
            en += 1
    return zh, en


def scan_xscn(path, rex, hits, tag):
    data, items, meta = parse(path)
    if items is None:
        return 0, 0
    zh = en = 0
    todo = []
    if meta and meta[0] is not None:
        o, L = meta[0], meta[1]
        todo.append(("title", data[o + 2:o + 2 + L]))
    for gi, idx, off, L in items:
        todo.append(("g%d#%d" % (gi, idx), data[off + 2:off + 2 + L]))
    for loc, raw in todo:
        try:
            v = raw.decode("gbk")
        except Exception:
            continue
        m = rex.search(v)
        if not m:
            continue
        ws_ = sorted({x for x in rex.findall(v)})
        if CJK.search(v):
            zh += 1
            if zh <= 400:
                hits.append((tag, path, loc, "中文侧", "/".join(ws_)[:80], v.strip()[:160]))
        else:
            en += 1
    return zh, en


def scan_tree(base, rex, hits, tag, allow_xscn=True):
    zh = en = 0
    for dp, dns, fns in os.walk(base):
        dns[:] = [d for d in dns if d not in SKIP_DIR and not d.startswith("_scn-bak")]
        if any(p in dp for p in SKIP_DIR):
            continue
        for fn in fns:
            low = fn.lower()
            p = os.path.join(dp, fn)
            if low.endswith(".xscn"):
                if allow_xscn:
                    a, b = scan_xscn(p, rex, hits, tag)
                    zh += a
                    en += b
                continue
            if not low.endswith(TEXT_EXT):
                continue
            enc = "gbk" if "OpenPG2" in p else None
            a, b = scan_bytes(p, rex, hits, tag, enc)
            zh += a
            en += b
    return zh, en


def main():
    rules = load_rules()
    rex = build_re(rules)
    print("规则 old 串 %d 个 · old 行 %d" % (len({o for _k, o, _n in rules}), len(rules)))
    hits = []
    order = []
    pg = r"D:\OpenPG2"
    if os.path.isdir(pg):
        for d in sorted(os.listdir(pg)):
            p = os.path.join(pg, d)
            if not os.path.isdir(p) or not d.startswith("EFILE_"):
                continue
            order.append(("efile:" + d, p))
    for extra in (r"D:\Program Files\PeG",):
        if os.path.isdir(extra):
            order.append(("product:" + os.path.basename(extra), extra))
    order.append(("workspace", WS))
    tot = []
    for tag, base in order:
        zh, en = scan_tree(base, rex, hits, tag)
        tot.append((tag, zh, en))
        if zh or en:
            print("  %-26s 中文侧 %4d · 英文侧 %4d" % (tag, zh, en))
    print("\n=== 有中文侧命中的根 ===")
    for tag, zh, en in tot:
        if zh:
            print("  %-26s 中文侧 %4d" % (tag, zh))
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("根\t文件\t位置\t类别\t命中规则\t片段\n")
        for h in hits:
            f.write("\t".join(x.replace("\t", " ") for x in h) + "\n")
    print("\n明细: %s (%d 行)" % (OUT, len(hits)))


if __name__ == "__main__":
    main()
