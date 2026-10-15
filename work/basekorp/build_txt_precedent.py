# -*- coding: utf-8 -*-
"""抽取「场景散文 .txt」行级 EN→ZH 先例库（跨已交付 efile）。

为什么能这么干：散文层的交付形态是「原文留 SCENARIO\\、中文放 TEXT-ZH\\SCENARIO\\」。
但 OLGWW2 / OPENPG 当年是**原地覆盖**的（原文侧已被中文顶掉）⇒ 必须回备份取原文侧。

| efile   | 原文侧（cp1252）                              | 中文侧（gbk）                        |
|---------|-----------------------------------------------|--------------------------------------|
| OLGWW2  | backup\\ORIGINAL-EFILE_OLGWW2\\SCENARIO\\*.txt | EFILE_OLGWW2\\SCENARIO\\*.txt        |
| OPENPG  | backup\\ORIGINAL-EFILE_OPENPG\\SCENARIO\\*.txt | EFILE_OPENPG\\SCENARIO\\*.txt        |
| AG      | backup\\ORIGINAL-EFILE_AG\\SCENARIO\\*.txt     | EFILE_AG\\TEXT-ZH\\SCENARIO\\*.txt   |
| ATOMIC  | EFILE_ATOMIC\\SCENARIO\\*.txt                  | EFILE_ATOMIC\\TEXT-ZH\\SCENARIO\\*.txt |
| AO      | EFILE_AO\\SCENARIO\\*.txt                      | EFILE_AO\\TEXT-ZH\\SCENARIO\\*.txt   |

对齐方式：**按行号一一对应**（空行同步跳过）。行数不等的文件整份丢弃（宁缺勿错）。
输出：
  work/basekorp/txt-precedent.tsv       src \t dst \t 计数 \t 来源
  work/basekorp/txt-precedent-conflicts.tsv   同一 src 多种译法
"""
import os
import io
import re
import sys
import collections

GAME = r"D:\OpenPG2"
ROOT = r"D:\DSH\军事游戏汉化"
HERE = os.path.join(ROOT, "work", "basekorp")
BK = os.path.join(ROOT, "backup")

SOURCES = [
    ("OLGWW2", os.path.join(BK, "ORIGINAL-EFILE_OLGWW2", "SCENARIO"),
     os.path.join(GAME, "EFILE_OLGWW2", "SCENARIO")),
    ("OPENPG", os.path.join(BK, "ORIGINAL-EFILE_OPENPG", "SCENARIO"),
     os.path.join(GAME, "EFILE_OPENPG", "SCENARIO")),
    ("AG", os.path.join(BK, "ORIGINAL-EFILE_AG", "SCENARIO"),
     os.path.join(GAME, "EFILE_AG", "TEXT-ZH", "SCENARIO")),
    ("ATOMIC", os.path.join(GAME, "EFILE_ATOMIC", "SCENARIO"),
     os.path.join(GAME, "EFILE_ATOMIC", "TEXT-ZH", "SCENARIO")),
    ("AO", os.path.join(GAME, "EFILE_AO", "SCENARIO"),
     os.path.join(GAME, "EFILE_AO", "TEXT-ZH", "SCENARIO")),
]

HAN = re.compile(r"[\u4e00-\u9fff]")
ALPHA = re.compile(r"[A-Za-z]")


def dec(b, enc):
    try:
        return b.decode(enc)
    except UnicodeDecodeError:
        return None


def main():
    pairs = collections.defaultdict(collections.Counter)   # src -> Counter(dst)
    origin = {}                                            # src -> set(efile)
    nfile = nskip = npair = 0
    for tag, odir, zdir in SOURCES:
        if not os.path.isdir(odir) or not os.path.isdir(zdir):
            print("  ⚠️ 跳过 %s（目录缺失）" % tag)
            continue
        ofiles = sorted(f for f in os.listdir(odir) if f.lower().endswith(".txt"))
        hit = 0
        for f in ofiles:
            pz = os.path.join(zdir, f)
            if not os.path.exists(pz):
                continue
            so = dec(open(os.path.join(odir, f), "rb").read(), "cp1252")
            sz = dec(open(pz, "rb").read(), "gbk")
            if so is None or sz is None:
                nskip += 1
                continue
            lo, lz = so.split("\r\n"), sz.split("\r\n")
            if len(lo) != len(lz):
                nskip += 1
                continue
            nfile += 1
            hit += 1
            for a, b in zip(lo, lz):
                if not a.strip() or not ALPHA.search(a):
                    continue
                if not HAN.search(b):
                    continue
                pairs[a][b] += 1
                origin.setdefault(a, set()).add(tag)
                npair += 1
        print("  %-7s 对齐文件 %4d / 可用 %4d" % (tag, hit, len(ofiles)))

    # 冲突：同一 src 多种 dst
    conf = []
    out = []
    for src, c in pairs.items():
        if len(c) > 1:
            conf.append((src, c))
        dst = c.most_common(1)[0][0]
        out.append((src, dst, sum(c.values()), ",".join(sorted(origin[src]))))
    out.sort(key=lambda r: -r[2])

    with io.open(os.path.join(HERE, "txt-precedent.tsv"), "w",
                 encoding="utf-8", newline="\r\n") as fh:
        fh.write("src\tdst\tcount\tsrc_efile\n")
        for s, d, n, o in out:
            fh.write("%s\t%s\t%d\t%s\r\n" % (s, d, n, o))
    with io.open(os.path.join(HERE, "txt-precedent-conflicts.tsv"), "w",
                 encoding="utf-8", newline="\r\n") as fh:
        fh.write("src\tdst\tcount\n")
        for src, c in sorted(conf, key=lambda x: -sum(x[1].values())):
            for d, n in c.most_common():
                fh.write("%s\t%s\t%d\r\n" % (src, d, n))
    print("先例 %d 条（实例 %d）/ 对齐文件 %d / 跳过 %d" % (len(out), npair, nfile, nskip))
    print("冲突 src %d 个 -> txt-precedent-conflicts.tsv" % len(conf))


if __name__ == "__main__":
    main()
