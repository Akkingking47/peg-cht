# -*- coding: utf-8 -*-
r"""统一总词库构建器 —— 把三层词典 + 译名库 + 词级通名 合并成单一权威真源。

分层（各层都由「原文↔部署件」配对器产出，全量、无中间产物依赖）：
  `_xscn_dict.tsv`    .xscn 层  →  build_dict.py
  `_root_dict.tsv`    根级四件套 →  build_root_dict.py
  `_prose_dict.tsv`   场景散文   →  build_prose_dict.py
  `standard-glossary.tsv`  译名库（人工维护真源）

产出：
  `master-glossary.tsv`  整串精确匹配：src \t dst \t layer \t n
  `master-words.tsv`     词级通名：token \t 中文
  `master-conflicts.tsv` 同 src 多译法（只报告不自动择一）
  `master-stat.txt`

用法（每完成一个 efile）：
  python build_dict.py && python build_root_dict.py && python build_prose_dict.py && python build_master.py
"""
import collections
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GLOSS = os.path.join(ROOT, "glossary", "standard-glossary.tsv")

SERIES = {
    "xscn":     os.path.join(HERE, "_xscn_dict.tsv"),
    "root":     os.path.join(HERE, "_root_dict.tsv"),
    "prose":    os.path.join(HERE, "_prose_dict.tsv"),
    "glossary": GLOSS,
}
# 词级通名（token → 中文）：kaiser 的 root-words + xscn-words + extra1-7
WORD_SOURCES = [os.path.join(ROOT, "work", "kaiser", "root-words.tsv"),
                os.path.join(ROOT, "work", "kaiser", "xscn-words.tsv")] + \
               [os.path.join(ROOT, "work", "kaiser", "xscn-words-extra%d.tsv" % i) for i in range(1, 8)]

# 短 src 过滤：纯数字/符号/括号、长度<2 的键不作精确匹配（编号槽位会误伤）
_NOISE = re.compile(r"^[\d\.\-\/\s\[\],\(\)\'\"\+]+$")


def _keepable(s):
    s = s.strip()
    return len(s) >= 2 and not _NOISE.match(s)


def read_dict(path, src_col=0, dst_col=1):
    d = {}
    if not os.path.exists(path):
        return d
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) > max(src_col, dst_col) and c[src_col] and c[dst_col]:
                d.setdefault(c[src_col].strip(), c[dst_col].strip())
    return d


def main():
    pairs = collections.defaultdict(lambda: collections.Counter())
    layer_of = {}
    for layer, path in SERIES.items():
        d = read_dict(path)
        for s, t in d.items():
            if s == t or not _keepable(s):
                continue
            pairs[s][t] += 1
            if s not in layer_of:
                layer_of[s] = layer
        print("layer=%-9s %6d 条" % (layer, len(d)))

    words = {}
    for p in WORD_SOURCES:
        for s, t in read_dict(p).items():
            if s != t and _keepable(s) and len(s) >= 2:
                words.setdefault(s, t)

    uniq = len(pairs)
    conflict = {k: v for k, v in pairs.items() if len(v) > 1}
    by_layer = collections.Counter(layer_of.values())

    # 冲突裁定表（resolve_master.py 产出）—— 归一多译法冲突为单一权威译法
    resolve = {}
    rp = os.path.join(HERE, "master-resolve.tsv")
    if os.path.exists(rp):
        resolve = read_dict(rp, 0, 1)

    with io.open(os.path.join(HERE, "master-glossary.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tdst\tlayer\tn\n")
        for s in sorted(pairs):
            if s in resolve:
                # 已裁定：只写权威译法，其余变体不再进词库
                f.write("%s\t%s\t%s\t%d\n" % (s, resolve[s], layer_of.get(s, "?"),
                                              sum(pairs[s].values())))
            else:
                for t, n in sorted(pairs[s].items(), key=lambda kv: -kv[1]):
                    f.write("%s\t%s\t%s\t%d\n" % (s, t, layer_of.get(s, "?"), n))
    with io.open(os.path.join(HERE, "master-words.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tdst\n")
        for s in sorted(words):
            f.write("%s\t%s\n" % (s, words[s]))
    with io.open(os.path.join(HERE, "master-conflicts.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tvariants\n")
        for s in sorted(conflict, key=lambda k: -sum(conflict[k].values())):
            f.write("%s\t%s\n" % (s, " | ".join("%s(%d)" % (d, n) for d, n in
                                                sorted(conflict[s].items(), key=lambda kv: -kv[1]))))
    with io.open(os.path.join(HERE, "master-stat.txt"), "w", encoding="utf-8", newline="\n") as f:
        for layer, n in by_layer.most_common():
            f.write("%s\t%d\n" % (layer, n))
        f.write("TOTAL\t%d\n冲突\t%d\n词级\t%d\n" % (uniq, len(conflict), len(words)))

    print("\n=== 统一总词库 === 整串 %d 条 / 词级 %d 条 / 冲突 %d (%.2f%%)" %
          (uniq, len(words), len(conflict), 100.0 * len(conflict) / max(1, uniq)))
    for layer, n in by_layer.most_common():
        print("   %-9s %6d" % (layer, n))
    print("\n冲突样例（前 18）:")
    for s in sorted(conflict, key=lambda k: -sum(conflict[k].values()))[:18]:
        print("   %-40s %s" % (s[:40], " | ".join("%s(%d)" % (d, n) for d, n in
                                                  sorted(conflict[s].items(), key=lambda kv: -kv[1]))[:70]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
