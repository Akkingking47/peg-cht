# -*- coding: utf-8 -*-
"""
阶段 4 · 层 1 准备：
1. 用规则表（rule_proto/rule_proto2 的 397 条 token + 序数/罗马数字规则）对 30,703 条待译串
   生成「提示译文」（hint）——注意：规则表逐 token 拼接会出词序问题（如
   `1 "Warszawska" Dywizja Pancerna` -> `1 "华沙" 师 装甲`），**因此 hint 只作 LLM 的参考，
   不作为最终译文直接落盘**。
2. 把待译串切成 batch/*.tsv，每批 1,000 条，供子代理定译。
3. 另外两条不走 LLM：不含拉丁字母的 1,389 条（原样保留）、已实装词典命中的 822 条（复用）。
"""
import os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rule_proto as R
import rule_proto2 as R2

R.TOK.update(R2.BATCH2)

W = r"D:\DSH\军事游戏汉化\work\gus"
FULL = r"D:\DSH\_s4_gus_full.tsv"
MISS = r"D:\DSH\_s4_miss.txt"
BATCH = os.path.join(W, "batch")
PER = 1000


def main():
    os.makedirs(BATCH, exist_ok=True)
    rows = [l.rstrip("\n").split("\t") for l in open(FULL, encoding="utf-8") if l.strip()][1:]
    freq = {}; grp = {}; exa = {}
    for r in rows:
        if not r or not r[0].strip():
            continue
        s = r[0].strip()
        freq[s] = int(r[1]) if len(r) > 1 and r[1].strip().isdigit() else 0
        grp[s] = r[2] if len(r) > 2 else ""
        exa[s] = r[3] if len(r) > 3 else ""

    miss = [x for x in open(MISS, encoding="utf-8").read().split("\n") if x]
    # 已实装词典
    have = {}
    for p in (r"D:\DSH\军事游戏汉化\work\gus_zx\xscn-map.tsv",
              r"D:\DSH\军事游戏汉化\work\alberich\xscn-map.tsv"):
        if os.path.exists(p):
            for ln in open(p, encoding="utf-8"):
                c = ln.rstrip("\n").split("\t")
                if len(c) >= 2 and c[0].strip():
                    have[c[0].strip()] = c[1].strip()

    # 按频次降序排列，让同一批里的串语义相近
    miss.sort(key=lambda s: (-freq.get(s, 0), s))

    hint = {}
    stat = collections.Counter()
    for s in miss:
        out, m = R.translate(s)
        hint[s] = out
        stat["hint_clean" if not m else ("hint_partial" if len(m) <= 2 else "hint_weak")] += 1

    with open(os.path.join(W, "xscn_hint.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tfreq\tgroups\texample\thint\n")
        for s in miss:
            f.write("%s\t%d\t%s\t%s\t%s\n" % (s, freq.get(s, 0), grp.get(s, ""), exa.get(s, ""),
                                              hint[s] if not R.translate(s)[1] else ""))

    # 切批
    n = 0
    for i in range(0, len(miss), PER):
        chunk = miss[i:i + PER]
        n += 1
        with open(os.path.join(BATCH, "batch-%02d.tsv" % n), "w", encoding="utf-8", newline="\n") as f:
            f.write("src\tfreq\tgroups\texample\thint\t dst\n")
            for s in chunk:
                h = hint[s] if not R.translate(s)[1] else ""
                f.write("%s\t%d\t%s\t%s\t%s\t\n" % (s, freq.get(s, 0), grp.get(s, ""), exa.get(s, ""), h))

    print("待译串 %d 条" % len(miss))
    print("  hint 全 token 命中(可用提示) %d / 部分 %d / 太弱 %d"
          % (stat["hint_clean"], stat["hint_partial"], stat["hint_weak"]))
    print("  不含拉丁字母(原样保留) %d" % sum(1 for s in rows if s and s[0].strip() and not re.search(r"[A-Za-z]", s[0])))
    print("  已实装词典命中 %d" % sum(1 for s in miss if s in have))
    print("批次 %d 个（每批 %d 条）-> %s" % (n, PER, BATCH))
    print("提示表 -> %s" % os.path.join(W, "xscn_hint.tsv"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
