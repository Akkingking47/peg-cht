# -*- coding: utf-8 -*-
"""probe_keep_source.py — 「keep 桶」（词库值 == 英文原文）在 PeG-WW2 成品里
到底是哪条链路给的中文。只读。

链路（work\\pegww2\\gen_scn.py）：
  ① per-file 覆盖表 pegww2\\research\\_scn-file-overrides.tsv（子目录|文件|行号0based|期望原文|译文）—— 优先
  ② 整串映射表 pegww2\\research\\ww2-scn-map.tsv（原文|译文|来源）—— 整行精确匹配
  ③ 都没有 => 原样保留英文

输出 work\\_sync-audit\\keep-source.tsv（键|命中数|来源|样例）与终端汇总。
"""
import io
import os
import re
from collections import defaultdict

W = r"D:\DSH\军事游戏汉化"
BK = os.path.join(W, "pegww2", "testbed", "backup")
GAME = r"D:\Program Files\PeG-WW2"
RES = os.path.join(W, "pegww2", "research")
OVF = os.path.join(RES, "_scn-file-overrides.tsv")
MAP = os.path.join(RES, "ww2-scn-map.tsv")
OUT = os.path.join(W, "work", "_sync-audit", "keep-source.tsv")
LIBF = [
    os.path.join(W, "glossary", "standard-glossary.tsv"),
    os.path.join(W, "glossary", "layers", "common-glossary.tsv"),
    os.path.join(W, "glossary", "layers", "scope-glossary.tsv"),
]
MAPSUF = re.compile(r"(?i)_m\.txt$")


def strip_deco(s):
    return re.sub(r"\s*\([^)]*\)\s*$", "", s).strip()


def load_lib():
    """{归一英文键: {译名}} —— 只收 scope 以 PEG 开头的条目。"""
    lib = defaultdict(set)
    for p in LIBF:
        for ln in io.open(p, encoding="utf-8-sig", errors="replace"):
            c = ln.rstrip("\r\n").split("\t")
            if len(c) < 4:
                continue
            en, zh, scope = c[0].strip(), c[1].strip(), c[3].strip()
            if not scope.upper().startswith("PEG"):
                continue
            lib[en.lower()].add(zh)
    return lib


def load_ovf():
    ov = {}
    for i, ln in enumerate(io.open(OVF, encoding="utf-8-sig", errors="replace")):
        if i < 2:
            continue
        c = ln.rstrip("\r\n").split("\t")
        if len(c) < 5:
            continue
        try:
            idx = int(c[2])
        except ValueError:
            continue
        ov[(c[0].strip().upper(), c[1].strip().lower(), idx)] = (c[3], c[4])
    return ov


def load_map():
    m = {}
    for i, ln in enumerate(io.open(MAP, encoding="utf-8-sig", errors="replace")):
        if i < 4:
            continue
        c = ln.rstrip("\r\n").split("\t")
        if len(c) < 3:
            continue
        m[c[0]] = (c[1], c[2])
    return m


def read_lines(path, enc):
    if not os.path.exists(path):
        return None
    raw = io.open(path, "rb").read()
    return re.split(r"\r\n|\r|\n", raw.decode(enc, "replace"))


def is_name_line(s):
    t = s.strip()
    if not t or len(t) > 60:
        return False
    if not re.search(r"[A-Za-z]", t):
        return False
    if re.search(r"[.!?;]\s*$", t):
        return False
    return True


def main():
    lib = load_lib()
    keep = {k for k, v in lib.items() if v and all(strip_deco(z).lower() == k for z in v)}
    ovf = load_ovf()
    m = load_map()
    print("词库 PEG* 键 %d · keep 桶 %d · 覆盖表 %d 行 · 映射表 %d 行" % (len(lib), len(keep), len(ovf), len(m)))

    per_key = defaultdict(lambda: defaultdict(int))
    sample = defaultdict(dict)
    for sub in ("SCENARIO", "USERSCEN"):
        bdir = os.path.join(BK, sub)
        gdir = os.path.join(GAME, sub)
        if not os.path.isdir(bdir):
            continue
        for fn in sorted(os.listdir(bdir)):
            if not MAPSUF.search(fn):
                continue
            bl = read_lines(os.path.join(bdir, fn), "cp1252")
            gl = read_lines(os.path.join(gdir, fn), "gbk")
            if not bl or not gl:
                continue
            for i, (b, g) in enumerate(zip(bl, gl)):
                en = b.strip()
                if not is_name_line(en):
                    continue
                k = en.lower()
                if k not in keep:
                    continue
                zh = g.strip()
                o = ovf.get((sub.upper(), fn.lower(), i))
                if o and o[0].strip() == en:
                    src = "per-file覆盖表"
                elif zh == en:
                    src = "未译(原样英文)"
                elif k in m and m[k][0].strip() != en:
                    src = "整串映射表"
                else:
                    src = "其它来源"
                per_key[k][src] += 1
                if src not in sample[k]:
                    sample[k][src] = "%s L%d %s -> %s" % (fn, i, en, zh)

    OUTDIR = os.path.dirname(OUT)
    if not os.path.isdir(OUTDIR):
        os.makedirs(OUTDIR)
    tally = defaultdict(int)
    rows = []
    for k in sorted(per_key):
        for src, n in per_key[k].items():
            tally[src] += n
        main_src = max(per_key[k].items(), key=lambda kv: kv[1])[0]
        rows.append((k, main_src, sum(per_key[k].values()), " | ".join(
            "%s=%d" % (s, n) for s, n in sorted(per_key[k].items())), sample[k].get(main_src, "")))
    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write("键\t主要来源\t出现次数\t来源分布\t样例\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")

    print("\n== 按来源汇总（按处计）")
    for s, n in sorted(tally.items(), key=lambda kv: -kv[1]):
        print("  %-16s %d" % (s, n))
    print("\n== 按来源分组的键数")
    grp = defaultdict(list)
    for k, src, n, dist, ex in rows:
        grp[src].append((k, n, dist, ex))
    for src in sorted(grp, key=lambda s: -len(grp[s])):
        items = grp[src]
        print("  %-16s %d 键" % (src, len(items)))
        for k, n, dist, ex in items[:12]:
            print("      %-28s x%-3d %s | %s" % (k, n, dist, ex))
        if len(items) > 12:
            print("      ... 另 %d 键见 %s" % (len(items) - 12, OUT))
    print("\n明细 -> %s" % OUT)


if __name__ == "__main__":
    main()
