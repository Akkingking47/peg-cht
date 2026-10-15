# -*- coding: utf-8 -*-
"""把 prose 层剩余待译清单切成 N 份，供子代理并行翻译。

用法:
    python split_prose_rest.py            # 默认切 10 份
    python split_prose_rest.py --parts 5

输入:  `_prose_authority.txt`（715 条真源，顺序权威）+ `prose-zh.tsv`（已译键集）
产出:  `_prose_rest_part01.txt` …（每行 `NNN|原文`，NNN = 真源序号，制表符显示为 ` ⟦T⟧ `）
       `_prose_rest_parts.tsv`（part<TAB>条数<TAB>字符<TAB>N 起<TAB>N 止）
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
AUTH = os.path.join(HERE, "_prose_authority.txt")
ZH = os.path.join(HERE, "prose-zh.tsv")
TABMARK = " \u27e6T\u27e7 "


def read_first_col(path):
    s = set()
    if not os.path.exists(path):
        return s
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if c and c[0]:
                s.add(c[0])
    return s


def main():
    parts = int(sys.argv[sys.argv.index("--parts") + 1]) if "--parts" in sys.argv else 10
    auth = [x for x in io.open(AUTH, encoding="utf-8", newline="").read()
            .replace("\r\n", "\n").split("\n") if x.strip()]
    done = read_first_col(ZH)
    rest = [(i + 1, s) for i, s in enumerate(auth) if s not in done]
    print("剩余 %d 条 / 真源 %d 条 / 切 %d 份" % (len(rest), len(auth), parts))

    base = len(rest) // parts
    rem = len(rest) % parts
    idx = 0
    meta = []
    for p in range(1, parts + 1):
        n = base + (1 if p <= rem else 0)
        chunk = rest[idx:idx + n]
        idx += n
        if not chunk:
            continue
        fn = os.path.join(HERE, "_prose_rest_part%02d.txt" % p)
        with io.open(fn, "w", encoding="utf-8", newline="") as f:
            for no, s in chunk:
                f.write("%4d|%s\n" % (no, s.replace("\t", TABMARK)))
        meta.append((p, len(chunk), sum(len(s) for _, s in chunk), chunk[0][0], chunk[-1][0]))
        print("  part%02d: %d 条 / %d 字符 / N %d..%d -> %s"
              % (p, len(chunk), sum(len(s) for _, s in chunk), chunk[0][0], chunk[-1][0], os.path.basename(fn)))
    with io.open(os.path.join(HERE, "_prose_rest_parts.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("part\tn\tchars\tfrom\tto\n")
        for m in meta:
            f.write("part%02d\t%d\t%d\t%d\t%d\n" % m)
    assert idx == len(rest)


if __name__ == "__main__":
    main()
