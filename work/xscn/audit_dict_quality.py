# -*- coding: utf-8 -*-
"""全局 `.xscn` 词典（`_xscn_dict.tsv`）质量审计 —— 抓已交付 efile 的历史误译。

可疑判据（机械可判，不涉语义猜测）：
  D1 纯数字 src，dst 不是「第N…」形式          （如 `100 → 连`）
  D2 dst 是纯数字，而 src 含字母               （如 `StG 2/ L 2 → 1`）
  D3 「A/B」型 src 而 dst 不是「第X/第Y」形式   （前段/后段至少一段丢了）
  D4 dst 明显短于 src（<=1/3 且 src >= 8 字符）
  D5 dst 含控制符 / 只有空白
用法: python audit_dict_quality.py
"""
import io
import os
import re
import sys
import collections

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
DICT = os.path.join(HERE, "_xscn_dict.tsv")
HAN = re.compile(r"[\u4e00-\u9fff]")


def main():
    rows = []
    with io.open(DICT, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 4:
                rows.append((c[0], c[1], c[2], c[3]))
    print("词典 %d 条" % len(rows))

    buckets = collections.defaultdict(list)
    for s, d, ne, ni in rows:
        ds, ss = d.strip(), s.strip()
        if ds == ss:
            continue                                   # 恒等 = 口径保留
        if re.fullmatch(r"\d+", ss) and not re.match(r"第\d+", ds):
            buckets["D1 数字src但dst非第N"].append((s, d, ne, ni))
        elif re.fullmatch(r"\d+", ds) and re.search(r"[A-Za-z]", ss):
            buckets["D2 dst是纯数字"].append((s, d, ne, ni))
        elif "/" in ss and not re.search(r"第|/", ds):
            buckets["D3 斜杠型但dst无「第X/第Y」"].append((s, d, ne, ni))
        elif len(ss) >= 8 and len(ds) <= len(ss) / 3:
            buckets["D4 dst过短"].append((s, d, ne, ni))
        if not ds or any(ch in d for ch in "\t\r\n"):
            buckets["D5 空/控制符"].append((s, d, ne, ni))

    for k in sorted(buckets):
        arr = buckets[k]
        print("\n=== %s : %d 条 ===" % (k, len(arr)))
        byd = collections.defaultdict(list)
        for s, d, ne, ni in arr:
            byd[(s, d)].append(ne)
        for (s, d), nes in sorted(byd.items(), key=lambda x: -sum(int(n) for n in x[1]))[:40]:
            print("   %-36s -> %-30s  %s" % (s[:36], d[:30], ",".join(sorted(set(nes))[:3])))

    with io.open(os.path.join(HERE, "_dict_suspects.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("kind\tsrc\tdst\tefiles\tinstances\n")
        for k in sorted(buckets):
            for s, d, ne, ni in buckets[k]:
                f.write("%s\t%s\t%s\t%s\t%s\n" % (k, s, d, ne, ni))
    print("\n已写 _dict_suspects.tsv")


if __name__ == "__main__":
    main()
