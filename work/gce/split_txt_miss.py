# -*- coding: utf-8 -*-
r"""把 `txt-miss.tsv`（未覆盖行）切成 N 份供子代理并行翻译。

**按文件分组**切分：同一场景文件的西语段与英译段会落在同一份里，
子代理能同时看到两段、用词自然一致（人/地名/编制名不会两边打架）。

用法: python split_txt_miss.py [N=8]
产出: _txt_todo_partNN.txt   格式 `  频次|原文`（与 `.xscn` 批次同格式）
      _txt_todo_parts.tsv    分块索引
"""
import io
import os
import sys
import collections

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SC = r"D:\OpenPG2\EFILE_GCE\SCENARIO"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 8


def read_miss():
    out = []
    with io.open(os.path.join(HERE, "txt-miss.tsv"), encoding="utf-8", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2:
                out.append((c[0], int(c[1])))
    return out


def main():
    miss = read_miss()
    order = {}                      # src -> (文件序, 行序)
    fi = 0
    for fn in sorted(f for f in os.listdir(SC) if f.lower().endswith(".txt")):
        fi += 1
        raw = open(os.path.join(SC, fn), "rb").read().decode("cp1252", "replace")
        for li, l in enumerate(raw.replace("\r\n", "\n").split("\n")):
            if l.strip() and l not in order:
                order[l] = (fi, li)
    # 按（文件序, 行序）排；未在原文出现的（理论上不会有）排最后
    miss.sort(key=lambda x: order.get(x[0], (999, 0)))
    total = sum(len(s) for s, _ in miss)
    print("待译唯一 %d 条 / %d 字符" % (len(miss), total))

    # 均衡切分（同文件尽量不跨块）
    target = total / N
    parts = []
    cur = []
    cur_ch = 0
    cur_file = None
    for s, n in miss:
        f = order.get(s, (999, 0))[0]
        if cur and cur_ch >= target and f != cur_file:
            parts.append(cur); cur = []; cur_ch = 0
        cur.append((s, n)); cur_ch += len(s); cur_file = f
    if cur:
        parts.append(cur)

    idx = []
    for i, p in enumerate(parts, 1):
        tag = "%02d" % i
        with io.open(os.path.join(HERE, "_txt_todo_part%s.txt" % tag), "w",
                     encoding="utf-8", newline="\n") as fh:
            for s, n in p:
                fh.write("   %d|%s\n" % (n, s))
        idx.append((tag, len(p), sum(len(s) for s, _ in p)))
        print("  part%s: %3d 条 / %6d 字符" % (tag, len(p), idx[-1][2]))
    with io.open(os.path.join(HERE, "_txt_todo_parts.tsv"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write("part\tn\tnchars\n")
        for tag, n, c in idx:
            fh.write("%s\t%d\t%d\n" % (tag, n, c))
    print("共 %d 块" % len(parts))


if __name__ == "__main__":
    main()
