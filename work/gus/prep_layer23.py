# -*- coding: utf-8 -*-
"""
阶段 4 · 层 2/3 准备：
1. 把 EFILE_GUS\\SCENARIO\\*.txt 按后缀分类（标签表 vs 散文）。
2. 散文（i/bv/tv/v/l/loss/__flow）按 25 个文件一批切成 batch 清单。
3. 标签表留给层 2：用层 1 的同一张 .xscn 表逐行查。
"""
import os, re, sys, collections

G = r"D:\OpenGeneral\EFILE_GUS\SCENARIO"
W = r"D:\DSH\军事游戏汉化\work\gus"
BATCH = os.path.join(W, "batch-txt")
PER = 25

# 散文后缀（相对「主名」的尾部标记）
PROSE_SUF = re.compile(r"(?:__flow|loss|bv|tv|i|v|l|PL)$", re.I)


def classify(name):
    base = os.path.splitext(name)[0]
    # 主名 = 去掉战役序号里的场景号后剩下的部分？这里用后缀表判
    # 例：G27_STA03i 的主名是 G27_STA03 -> 后缀 i
    m = re.match(r"^(.*?)(__flow|_?loss|bv|tv|i|v|l)$", base, re.I)
    if m and m.group(2):
        return "prose", m.group(2).lower()
    return "label", ""


def main():
    os.makedirs(BATCH, exist_ok=True)
    files = sorted(f for f in os.listdir(G) if f.lower().endswith(".txt"))
    kinds = collections.Counter(); sufs = collections.Counter()
    labels = []; prose = []
    for f in files:
        k, s = classify(f)
        kinds[k] += 1
        if k == "prose":
            sufs[s] += 1; prose.append(f)
        else:
            labels.append(f)

    print("SCENARIO\\*.txt 共 %d 个" % len(files))
    print("  标签表(层 2，查 .xscn 表) %d 个" % len(labels))
    print("  散文  (层 3，交 LLM)     %d 个" % len(prose))
    print("  散文后缀分布: %s" % dict(sufs.most_common()))

    # 散文按战役分组排序，让同一批语境连续
    prose.sort()
    n = 0
    for i in range(0, len(prose), PER):
        chunk = prose[i:i + PER]
        n += 1
        with open(os.path.join(BATCH, "txt-%03d.txt" % n), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(chunk) + "\n")
    print("\n散文批次 %d 个（每批 %d 个文件）-> %s" % (n, PER, BATCH))

    with open(os.path.join(W, "txt-labels.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(labels) + "\n")
    print("层 2 清单 %d 条 -> %s" % (len(labels), os.path.join(W, "txt-labels.txt")))

    # 体积
    tot = 0; ptot = 0
    for f in labels: tot += os.path.getsize(os.path.join(G, f))
    for f in prose: ptot += os.path.getsize(os.path.join(G, f))
    print("\n标签表体积 %.1f KB / 散文体积 %.1f KB" % (tot/1024, ptot/1024))
    if prose:
        print("散文首批样例: %s" % ", ".join(prose[:5]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
