# -*- coding: utf-8 -*-
"""核验污染条目是否已真正命中 COMWW2 文件（备份原文 vs 现状 逐条配对）。"""
import io
import os
import re
import sys
import struct
import collections

sys.stdout.reconfigure(encoding="utf-8")
BK = r"D:\DSH\军事游戏汉化\backup\ORIGINAL-EFILE_COMWW2\SCENARIO"
CUR = r"D:\OpenPG2\EFILE_COMWW2\SCENARIO"


def parse_entries(data):
    """返回 [(gi, idx, off, L, raw)]，与 xscn.py 同构：跳过 <N:...> 头与一层计数头。"""
    out = []
    st = data.find(b"<N:")
    if st < 0:
        return out
    e = data.index(b">", st)
    off = e + 1
    tl = int.from_bytes(data[off:off + 2], "little")
    off += 2 + tl
    gi = 0
    while off + 2 <= len(data):
        cnt = int.from_bytes(data[off:off + 2], "little")
        off += 2
        if cnt == 0:
            gi += 1
            if off >= len(data):
                break
            continue
        n = 0
        while n < cnt:
            if off + 2 > len(data):
                break
            L = int.from_bytes(data[off:off + 2], "little")
            off += 2
            if L > len(data) - off:
                break
            out.append((gi, n, off, L, data[off:off + L]))
            off += L
            n += 1
        gi += 1
    return out


def gbk(b):
    try:
        return b.decode("gbk")
    except UnicodeDecodeError:
        return b.decode("gbk", "replace")


def main():
    pol = []
    with io.open("_pollution_cand.tsv", encoding="utf-8") as f:
        for i, ln in enumerate(f):
            if i == 0 or not ln.strip():
                continue
            c = ln.rstrip("\r\n").split("\t")
            if len(c) >= 3:
                pol.append((c[0], c[1], c[2]))
    pset = {s for s, _, _ in pol}
    print("污染候选 %d 条" % len(pol))

    files = sorted(f for f in os.listdir(BK) if f.lower().endswith(".xscn"))
    hit_files = collections.defaultdict(list)     # src -> [(file, gi, idx)]
    changed = collections.Counter()               # src -> 实际被改写次数
    nonsrc = 0
    for f in files:
        a = open(os.path.join(BK, f), "rb").read()
        b = open(os.path.join(CUR, f), "rb").read()
        ea, eb = parse_entries(a), parse_entries(b)
        if len(ea) != len(eb):
            print("  !! 条目数不等 %s: %d vs %d" % (f, len(ea), len(eb)))
            nonsrc += 1
            continue
        for (ga, ia, oa, la, ra), (gb_, ib, ob, lb, rb) in zip(ea, eb):
            sa = gbk(ra)
            sb = gbk(rb)
            if sa in pset and sa != sb:
                hit_files[sa].append((f, ga, ia, sb))
            if sa != sb and sa in pset:
                changed[sa] += 1

    print("\n=== 污染条目中『确实命中了原文』的 ===")
    tot = 0
    for s, v in sorted(hit_files.items(), key=lambda x: -len(x[1])):
        print("  %-32s 命中 %d 实例；例: %s 组%d #%d -> %s"
              % (s[:32], len(v), v[0][0], v[0][1], v[0][2], v[0][3][:30]))
        tot += len(v)
    print("合计命中实例 %d" % tot)

    print("\n=== 未命中的污染候选（应只是映射表垃圾，无害） ===")
    nomiss = [s for s, _, _ in pol if s not in hit_files]
    print("  %d 条: %s" % (len(nomiss), ", ".join(nomiss[:40])))

    with io.open("_pollution_hits.tsv", "w", encoding="utf-8", newline="") as f:
        f.write("src\tdst_used\tfile\tgi\tidx\n")
        for s, v in sorted(hit_files.items()):
            for fh, gi, ia, sb in v:
                f.write("%s\t%s\t%s\t%d\t%d\n" % (s, sb, fh, gi, ia))


if __name__ == "__main__":
    main()
