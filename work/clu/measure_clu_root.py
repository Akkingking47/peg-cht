# -*- coding: utf-8 -*-
r"""量测 EFILE_Clu 根级大表（names.txt / equip97.txt）的既有译法覆盖率，并切出待译块。

来源优先级（与 `gen_root_zh.py` 一致）：
  1. `work\xscn\_root_dict.tsv`    跨 efile「原文↔TEXT-ZH」全量配对词典
  2. `work\xscn\master-glossary.tsv` / `master-resolve.tsv`  统一总词库
  3. `glossary\standard-glossary.tsv`  译名真源
  4. `work\xscn\master-words.tsv`  词级通名（整串全部 token 命中才用）

输出：work\clu\root-cov.tsv（file line src dst source）+ work\clu\root-miss-<file>.txt（单列待译）
"""
import collections
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
WX = r"D:\DSH\军事游戏汉化\work\xscn"
GLOSS = r"D:\DSH\军事游戏汉化\glossary\standard-glossary.tsv"
EFILE = r"D:\OpenPG2\EFILE_Clu"
TOK = re.compile(r"(?<![A-Za-z0-9\u00c0-\u024f])[A-Za-z\u00c0-\u024f][A-Za-z\u00c0-\u024f'\.\-]*")


def rd(path, k=0, v=1):
    d = {}
    if not os.path.exists(path):
        return d
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) > max(k, v) and c[k].strip() and c[v].strip():
                d.setdefault(c[k].strip(), c[v].strip())
    return d


def main():
    srcs = [("root-dict", rd(os.path.join(WX, "_root_dict.tsv"))),
            ("master", rd(os.path.join(WX, "master-glossary.tsv"))),
            ("resolve", rd(os.path.join(WX, "master-resolve.tsv"))),
            ("glossary", rd(GLOSS))]
    words = rd(os.path.join(WX, "master-words.tsv"))
    cov = io.open(os.path.join(HERE, "root-cov.tsv"), "w", encoding="utf-8", newline="\n")
    cov.write("file\tline\tsrc\tdst\tsource\n")
    for name in ("names.txt", "equip97.txt"):
        p = os.path.join(EFILE, name)
        raw = open(p, "rb").read()
        nl = "\r\n" if raw.count(b"\r\n") else "\n"
        lines = raw.decode("cp1252").split(nl)
        miss = collections.Counter()
        stat = collections.Counter()
        for i, l in enumerate(lines, 1):
            s = l.strip()
            if not s or s.startswith("*"):
                continue
            dst, who = "", ""
            for nm, d in srcs:
                if s in d and d[s] != s:
                    dst, who = d[s], nm
                    break
            if not dst:
                toks = TOK.findall(s)
                if toks and all(t in words for t in toks) and not re.search(r"\d", s):
                    rest = s
                    for t in toks:
                        rest = rest.replace(t, "", 1)
                    if not rest.strip(" \t-/.,'()[]:"):
                        dst, who = "".join(words[t] for t in toks), "words"
            cov.write("%s\t%d\t%s\t%s\t%s\n" % (name, i, s, dst, who))
            stat[who or "未覆盖"] += 1
            if not dst:
                miss[s] += 1
        cov.flush()
        mp = os.path.join(HERE, "root-miss-%s.txt" % name.split(".")[0])
        with io.open(mp, "w", encoding="utf-8", newline="\n") as f:
            for k, n in miss.most_common():
                f.write(k + "\n")
        print("%-14s 非空行 %d  命中 %s" % (name, sum(stat.values()), dict(stat)))
        print("            未覆盖唯一 %d -> %s" % (len(miss), mp))
        print("            样例:", [k for k, _ in miss.most_common(8)])
    cov.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
