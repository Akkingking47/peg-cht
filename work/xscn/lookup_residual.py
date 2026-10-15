# -*- coding: utf-8 -*-
r"""给 `residual.tsv` 的每条残槽找「既有译法」候选，剩下的才是真正要人译的。

候选来源（优先级从高到低，取第一个命中）：
  1. work\comww2\label-keep-zh.tsv      COMWW2 label 层 09-30 已定译（.xscn 侧当时漏回填）
  2. glossary\standard-glossary.tsv     译名真源（en 列）
  3. work\xscn\master-glossary.tsv      统一总词库（跨 efile 交付件实证）
  4. work\xscn\master-resolve.tsv       冲突裁定表
  5. work\xscn\_xscn_dict.tsv           跨 efile .xscn 词典（键含首尾空白 ⇒ 两侧 strip）
  6. work\xscn\_root_dict.tsv           根级四件套词典（键含空白 ⇒ strip）
  7. work\xscn\master-words.tsv         词级通名（整串即为一词时才用）

用法: python lookup_residual.py --efile COMWW2
输出: work\<efile-lower>\residual-cand.tsv   src freq dst source
      未命中的 dst 留空 ⇒ 交人工/LLM。
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def rd_tsv(path, k=0, v=1, strip_key=True, minlen=2):
    d = {}
    if not os.path.exists(path):
        return d
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) > max(k, v) and c[k].strip():
                key = c[k].strip() if strip_key else c[k]
                if len(key) >= minlen and c[v].strip():
                    d.setdefault(key, c[v].strip())
    return d


def main():
    if "--efile" not in sys.argv:
        print(__doc__)
        return 2
    tag = sys.argv[sys.argv.index("--efile") + 1].strip().replace("EFILE_", "").replace("efile_", "")
    wd = os.path.join(ROOT, "work", tag.lower())
    src = os.path.join(wd, "residual.tsv")
    if not os.path.exists(src):
        print("!! 先跑 list_residual.py: %s 不存在" % src)
        return 2
    # 源优先级：先查「同 efile 既有交付」（label-keep），再查译名真源，最后跨 efile 词典
    SRC = [
        ("label-keep", os.path.join(ROOT, "work", "comww2", "label-keep-zh.tsv")),
        ("glossary", os.path.join(ROOT, "glossary", "standard-glossary.tsv")),
        ("master", os.path.join(HERE, "master-glossary.tsv")),
        ("resolve", os.path.join(HERE, "master-resolve.tsv")),
        ("xscn-dict", os.path.join(HERE, "_xscn_dict.tsv")),
        ("root-dict", os.path.join(HERE, "_root_dict.tsv")),
        ("words", os.path.join(HERE, "master-words.tsv")),
    ]
    dicts = [(n, rd_tsv(p)) for n, p in SRC]

    rows = []
    with io.open(src, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            key, freq = c[0], c[1] if len(c) > 1 else ""
            dst = ""
            who = ""
            for name, d in dicts:
                if key in d:
                    dst, who = d[key], name
                    break
            rows.append((key, freq, dst, who))

    hit = sum(1 for r in rows if r[2])
    outp = os.path.join(wd, "residual-cand.tsv")
    with io.open(outp, "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tfreq\tdst\tsource\n")
        for key, freq, dst, who in rows:
            f.write("%s\t%s\t%s\t%s\n" % (key, freq, dst, who))
    print("%s: 残槽唯一 %d；既有译法命中 %d，**仍需人译 %d**" % (tag, len(rows), hit, len(rows) - hit))
    from collections import Counter
    print("   命中来源分布: %s" % dict(Counter(r[3] for r in rows if r[2])))
    print("   未命中（前 60）:")
    for r in [r for r in rows if not r[2]][:60]:
        print("      %-46s x%s" % (r[0][:46], r[1]))
    print("已写 %s" % outp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
