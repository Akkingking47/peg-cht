#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 阶段0.3b：.scn 结构反查（不得沿用 PeG 偏移，必须本作实测）。

输出：6 个样本的 ASCII 串+偏移；全库 @0 / @4 / 文件名引用偏移直方图。
"""
import io
import os
import re
import struct
import sys
from collections import Counter, defaultdict

GAME = r"D:\Program Files\PeG-WW2"
SCN = os.path.join(GAME, "SCENARIO")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recon3-out")
os.makedirs(OUT, exist_ok=True)
_REPORT = os.path.join(OUT, "recon4-scn.txt")
_sink = io.StringIO()


class _Tee:
    def __init__(self, *s):
        self.s = s

    def write(self, x):
        for t in self.s:
            t.write(x)
        return len(x)

    def flush(self):
        for t in self.s:
            t.flush()


sys.stdout = _Tee(sys.stdout, _sink)


def rd(p):
    with open(p, "rb") as f:
        return f.read()


def strings_with_off(d, minlen=4):
    out = []
    for m in re.finditer(rb"[\x20-\x7e]{%d,}" % minlen, d):
        out.append((m.start(), m.group(0).decode("latin1")))
    return out


def main():
    files = sorted(f for f in os.listdir(SCN) if f.lower().endswith(".scn"))
    print(f"SCENARIO 下 .scn 共 {len(files)} 个\n")

    print("=" * 92)
    print("A. 样本 .scn：ASCII 串与偏移（判字段布局）")
    print("=" * 92)
    for f in files[:6]:
        p = os.path.join(SCN, f)
        d = rd(p)
        print(f"\n### {f}   {len(d):,} B   @0={d[0]}  @4(u16)={struct.unpack_from('<H', d, 4)[0]}  @4(u32)={struct.unpack_from('<I', d, 4)[0]}")
        for off, s in strings_with_off(d, 4):
            print(f"    @{off:<8d} {s[:100]!r}")

    print()
    print("=" * 92)
    print("B. 全库 .scn：字段直方图")
    print("=" * 92)
    c0 = Counter()
    c4 = Counter()
    ref_kind = Counter()
    ref_off = defaultdict(Counter)
    sizes = []
    extname_off = Counter()
    for f in files:
        d = rd(os.path.join(SCN, f))
        sizes.append(len(d))
        c0[d[0]] += 1
        if len(d) >= 6:
            c4[struct.unpack_from("<H", d, 4)[0]] += 1
        for off, s in strings_with_off(d, 4):
            low = s.lower()
            if low.endswith(".map"):
                ref_kind["map"] += 1
                ref_off["map"][off] += 1
            elif low.endswith(".txt") or low.endswith(".ply"):
                ref_kind["txt"] += 1
                ref_off["txt"][off] += 1
            elif low.endswith(".scn"):
                ref_kind[".scn"] += 1
            elif low.endswith(".cam"):
                ref_kind[".cam"] += 1
    print(f"  .scn 字节数: min={min(sizes):,} max={max(sizes):,} 中位={sorted(sizes)[len(sizes) // 2]:,}")
    print(f"  @0 分布: {dict(c0.most_common(10))}")
    print(f"  @4(u16) 分布 top12: {c4.most_common(12)}")
    print(f"  文件名引用计数: {dict(ref_kind)}")
    for k, v in ref_off.items():
        print(f"   {k} 引用偏移 top8: {v.most_common(8)}")

    print()
    print("=" * 92)
    print("C. 交叉核对：@4 值 vs `<场景>_m.txt` 行数")
    print("=" * 92)
    stems = {f[:-4]: f for f in os.listdir(SCN) if f.lower().endswith(".scn")}
    lowmap = {k.lower(): v for k, v in stems.items()}
    hits = 0
    mismatch = []
    for f in files:
        stem = f[:-4]
        m = os.path.join(SCN, stem + "_m.txt")
        if not os.path.isfile(m):
            continue
        d = rd(os.path.join(SCN, f))
        if len(d) < 6:
            continue
        idx = struct.unpack_from("<H", d, 4)[0]
        lines = re.split(rb"\r\n|\r|\n", rd(m))
        if idx < len(lines):
            hits += 1
        else:
            mismatch.append((f, idx, len(lines)))
    print(f"  @4(u16) 落在 _m.txt 行范围内的: {hits} 个; 越界: {len(mismatch)} 个")
    for f, i, n in mismatch[:10]:
        print(f"    越界 {f}: idx={i} 行数={n}")


if __name__ == "__main__":
    main()
    with open(_REPORT, "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
    print(f"\n[report] {_REPORT}")
