"""一次性侦察：从既有词库挖「部队番号缩写 → 中文」的权威译法，供 PeG-WW2 番号翻译立据。

为什么不能自己造译法：词库里 PEGWW2_SCN / EFILE_OLGWW2 两个 scope 已经积累了同引擎
前作（OpenGen OLG-WW2）与本案的历史裁决（如 `RTR`→皇家坦克团、`Aufkl.-Abt.`→侦察营）。

用法：python unit_map_probe.py
"""
import collections
import io
import os
import re
import sys

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = [
    os.path.join(WS, "glossary", "standard-glossary.tsv"),
    os.path.join(WS, "glossary", "layers", "scope-glossary.tsv"),
]
TOKENS = ["SS", "GMech", "GT", "VK", "PJ", "RTR", "Abn", "RHA", "BEF", "FFV", "DAK",
          "GC", "GCC", "WDD", "RAA", "L1", "L3", "L4", "DF", "DR", "SA", "GM", "VH",
          "Belov", "Aufkl", "Recce", "Pavia", "zbV", "ID", "Pz", "Inf", "Lw", "Km"]
CJK = re.compile(r"[\u4e00-\u9fff]")
ROMAN = re.compile(r"(?i)^[IVXLCDM]+$")


def rows(path):
    if not os.path.isfile(path):
        return
    with io.open(path, encoding="utf-8-sig") as fh:
        for ln, raw in enumerate(fh, 1):
            s = raw.rstrip("\r\n")
            if not s.strip() or s.lstrip().startswith("#"):
                continue
            f = s.split("\t")
            if len(f) >= 2:
                yield os.path.basename(path), ln, f[0], f[1]


def main():
    hits = collections.defaultdict(collections.Counter)
    src_of = collections.defaultdict(set)
    for path in SRC:
        for base, ln, en, zh in rows(path):
            if not CJK.search(zh):
                continue
            for t in TOKENS:
                pat = re.compile(r"(?<![A-Za-z])%s(?![A-Za-z])" % re.escape(t), re.I)
                if pat.search(en):
                    key = (t, zh.strip())
                    hits[t][zh.strip()] += 1
                    src_of[key].add("%s:%d" % (base, ln))
    for t in TOKENS:
        c = hits.get(t)
        if not c:
            print("%-10s —— 词库无据" % t)
            continue
        print("%-10s 词库命中 %d 条译法：" % (t, sum(c.values())))
        for zh, n in c.most_common(4):
            eg = sorted(src_of[(t, zh)])[:1]
            print("     %4d× %-38s  ← %s" % (n, zh[:38], eg[0] if eg else ""))


if __name__ == "__main__":
    main()
