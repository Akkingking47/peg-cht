#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 阶段0.3c：真实工作量测算（唯一串 / 可译串 / 既有词库覆盖率）。

要点：行数 ≠ 工作量。判据取「非空唯一串」与「含字母的可译串」。
覆盖率用既有资产实测：glossary/standard-glossary.tsv + peg/research/ui-glossary.tsv
                        + work/xscn/master-glossary.tsv
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recon3-out")
os.makedirs(OUT, exist_ok=True)
_REPORT = os.path.join(OUT, "recon5-workload.txt")
_sink = io.StringIO()


class _Tee:
    def __init__(self, *s):
        self.s = s

    def write(self, x):
        for t in self.s:
            t.write(x)
        return len(x)

    def flush(self):
        for t in self.s:
            t.flush()


sys.stdout = _Tee(sys.stdout, _sink)


def rd(p):
    with open(p, "rb") as f:
        return f.read()


def lines_of(p):
    b = rd(p)
    return [x.decode("cp1252", "replace") for x in re.split(rb"\r\n|\r|\n", b)]


def classify(name):
    n = name.lower()
    if n.endswith("_m.txt"):
        return "m.txt 地图格名"
    if n.endswith("_u.txt"):
        return "u.txt 部队名"
    if n.endswith("_i.txt"):
        return "i.txt 战役内简报"
    if n.endswith("_bv.txt"):
        return "bv.txt 大胜评述"
    if n.endswith("_tv.txt"):
        return "tv.txt 战术胜评述"
    if n.endswith("_l.txt"):
        return "l.txt 败报"
    if n.endswith("_v.txt"):
        return "v.txt 胜报"
    if n.endswith(".log"):
        return "log 评述"
    if n.endswith(".tx"):
        return "tx 评述(冗余扩展名)"
    if n.endswith(".t"):
        return "t 评述(断扩展名)"
    if n.endswith(".txt"):
        return "txt 场景简报"
    if n.endswith(".ply"):
        return "ply 描述框"
    return "其他"


def load_gloss():
    """既有词库：英文 -> 中文（取第一列/第二列）"""
    g = {}
    files = [
        os.path.join(WS, "glossary", "standard-glossary.tsv"),
        os.path.join(WS, "peg", "research", "ui-glossary.tsv"),
        os.path.join(WS, "work", "xscn", "master-glossary.tsv"),
        os.path.join(WS, "work", "xscn", "master-words.tsv"),
    ]
    for f in files:
        if not os.path.isfile(f):
            continue
        n = 0
        for enc in ("utf-8-sig", "gbk"):
            try:
                with open(f, encoding=enc) as fh:
                    for line in fh:
                        parts = line.rstrip("\n").split("\t")
                        if len(parts) < 2:
                            continue
                        en, zh = parts[0].strip(), parts[1].strip()
                        if not en or not zh or en == zh:
                            continue
                        if re.fullmatch(r"[A-Za-z][A-Za-z0-9 '\-\./&,()]{0,60}", en):
                            g.setdefault(en.lower(), zh)
                            n += 1
                break
            except UnicodeDecodeError:
                continue
        print(f"   词库 {os.path.relpath(f, WS)}: +{n} 条")
    return g


def has_letters(s):
    return bool(re.search(r"[A-Za-z]", s))


def main():
    print("=" * 94)
    print("A. 场景层逐类工作量（非空唯一串 / 可译串）")
    print("=" * 94)
    scn = os.path.join(GAME, "SCENARIO")
    usr = os.path.join(GAME, "USERSCEN")
    buckets = defaultdict(lambda: {"files": 0, "lines": 0, "nonempty": 0, "uniq": set(),
                                   "uniq_trans": set(), "bytes": 0, "maxlen": 0})
    for d, tag in ((scn, "SCENARIO"), (usr, "USERSCEN")):
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            p = os.path.join(d, f)
            if not os.path.isfile(p):
                continue
            if not re.search(r"(?i)\.(txt|ply|tx|t|log)$", f):
                continue
            k = f"{tag}/{classify(f)}"
            ls = lines_of(p)
            b = buckets[k]
            b["files"] += 1
            b["bytes"] += os.path.getsize(p)
            b["lines"] += len(ls)
            for s in ls:
                s = s.strip()
                if not s:
                    continue
                b["nonempty"] += 1
                b["uniq"].add(s)
                b["maxlen"] = max(b["maxlen"], len(s))
                if has_letters(s):
                    b["uniq_trans"].add(s)
    tot_files = tot_nonempty = tot_u = tot_ut = 0
    for k, b in sorted(buckets.items()):
        print(f"  {k:28s} 文件={b['files']:<5d} 行={b['lines']:<7d} 非空={b['nonempty']:<7d} "
              f"唯一={len(b['uniq']):<7d} 可译唯一={len(b['uniq_trans']):<7d} 最长={b['maxlen']:<5d} {b['bytes'] / 1024:,.0f} KB")
        tot_files += b["files"]
        tot_nonempty += b["nonempty"]
        tot_u += len(b["uniq"])
        tot_ut += len(b["uniq_trans"])
    print(f"  {'合计':28s} 文件={tot_files:<5d} 非空={tot_nonempty:<7d} 唯一={tot_u:<7d} 可译唯一={tot_ut:<7d}")

    print()
    print("=" * 94)
    print("B. 根级 5 文本 + mod 清单文件")
    print("=" * 94)
    for f in ["WW2Gui.txt", "WW2Misc.txt", "WW2NAME.TXT", "WW2Tips.TXT", "ww2-eqp.txt", "WW2gen.txt"]:
        p = os.path.join(GAME, f)
        if not os.path.isfile(p):
            continue
        ls = lines_of(p)
        ne = [x.strip() for x in ls if x.strip()]
        uq = set(ne)
        print(f"  {f:16s} 行={len(ls):<7d} 非空={len(ne):<7d} 唯一={len(uq):<7d} 可译唯一={len([x for x in uq if has_letters(x)]):<7d}")

    print()
    print("=" * 94)
    print("C. 既有词库覆盖率（对「场景层可译唯一串」）")
    print("=" * 94)
    g = load_gloss()
    print(f"   词库合计 {len(g):,} 条（键为小写原文）")
    alluniq = set()
    for b in buckets.values():
        alluniq |= b["uniq_trans"]
    exact = sum(1 for s in alluniq if s.lower() in g)
    print(f"   场景层可译唯一串 {len(alluniq):,}；整串精确命中 {exact:,}（{exact / max(1, len(alluniq)) * 100:.1f}%）")
    # 分词命中率（乐观上界）
    tok = Counter()
    for s in list(alluniq)[:60000]:
        for w in re.findall(r"[A-Za-z][A-Za-z'\-]{2,}", s):
            tok[w.lower()] += 1
    hit = sum(c for w, c in tok.items() if w in g)
    tot = sum(tok.values())
    print(f"   词级命中（上界）：{hit:,}/{tot:,} 词次 = {hit / max(1, tot) * 100:.1f}%")


if __name__ == "__main__":
    main()
    with open(_REPORT, "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
    print(f"\n[report] {_REPORT}")
