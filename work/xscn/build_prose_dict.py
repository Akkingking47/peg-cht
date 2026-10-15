# -*- coding: utf-8 -*-
r"""场景散文（SCENARIO\*.txt / USERSCEN\*.ply/.txt）跨 efile 词典构建器。

原理同 build_dict.py：原文（就地，未动）↔ TEXT-ZH 部署件**逐行配对**，得到全量 src→dst。

产出 `_prose_dict.tsv`：src \t dst \t efiles \t n
用法: python build_prose_dict.py
"""
import collections
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\OpenPG2"
HERE = os.path.dirname(os.path.abspath(__file__))
EFS = ["EFILE_AG", "EFILE_AO", "EFILE_ATOMIC", "EFILE_BASEKORP",
       "EFILE_COMWW2", "EFILE_GCE", "EFILE_KAISER",
       "EFILE_NASHORNPBEM", "EFILE_OLGWW2", "EFILE_OPENPG", "EFILE_PzLIGA"]


def read_lines(path, cp1252=True):
    if not os.path.exists(path):
        return None
    raw = open(path, "rb").read()
    if raw[:3] == b"\xef\xbb\xbf":
        raw = raw[3:]
    return raw.decode("cp1252" if cp1252 else "gbk", "replace").replace("\r\n", "\n").replace("\r", "\n").split("\n")


def main():
    pairs = collections.defaultdict(lambda: collections.Counter())
    stat = []
    for ef in EFS:
        ndir = os.path.join(ROOT, ef, "SCENARIO")
        zdir = os.path.join(ROOT, ef, "TEXT-ZH", "SCENARIO")
        udir = os.path.join(ROOT, ef, "USERSCEN")
        uzdir = os.path.join(ROOT, ef, "TEXT-ZH", "USERSCEN")
        if not os.path.isdir(zdir):
            stat.append((ef, "无 TEXT-ZH", 0, 0))
            continue
        nf = npair = 0
        # SCENARIO/*.txt
        for fn in sorted(os.listdir(ndir)):
            if not fn.lower().endswith(".txt"):
                continue
            a = read_lines(os.path.join(ndir, fn))
            b = read_lines(os.path.join(zdir, fn), cp1252=False)
            if a is None or b is None or len(a) != len(b):
                continue
            nf += 1
            for x, y in zip(a, b):
                x, y = x.rstrip(), y.rstrip()
                if not x or x == y:
                    continue
                pairs[x][y] += 1
                npair += 1
        # USERSCEN/*.ply + *.txt
        if os.path.isdir(udir):
            for fn in sorted(os.listdir(udir)):
                if not (fn.lower().endswith(".ply") or fn.lower().endswith(".txt")):
                    continue
                a = read_lines(os.path.join(udir, fn))
                b = read_lines(os.path.join(uzdir, fn), cp1252=False)
                if a is None or b is None or len(a) != len(b):
                    continue
                nf += 1
                for x, y in zip(a, b):
                    x, y = x.rstrip(), y.rstrip()
                    if not x or x == y:
                        continue
                    pairs[x][y] += 1
                    npair += 1
        stat.append((ef, "OK", nf, npair))

    print("%-20s %-6s %6s %7s" % ("efile", "状态", "文件", "真译文对"))
    for s in stat:
        print("%-20s %-6s %6d %7d" % s)

    uniq = len(pairs)
    conflict = {k: v for k, v in pairs.items() if len(v) > 1}
    print("\n散文词典唯一 src %d ；多译法冲突 %d (%.1f%%)" %
          (uniq, len(conflict), 100.0 * len(conflict) / max(1, uniq)))

    with io.open(os.path.join(HERE, "_prose_dict.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tdst\tefiles\tn\n")
        for s in sorted(pairs):
            for d, n in sorted(pairs[s].items(), key=lambda kv: (-kv[1], kv[0])):
                f.write("%s\t%s\t%d\t%d\n" % (s, d, n, sum(pairs[s].values())))
    print("已写 _prose_dict.tsv")
    print("冲突样例（前 10）:")
    for s in sorted(conflict, key=lambda k: -sum(conflict[k].values()))[:10]:
        print("   %-40s %s" % (s[:40], " | ".join("%s(%d)" % (d, n) for d, n in
                                                  sorted(conflict[s].items(), key=lambda kv: -kv[1]))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
