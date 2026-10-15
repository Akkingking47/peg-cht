#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 阶段0.3d：.scn 文本字段与标志位精查（11200..11360 区）。

要落实的字段：
  @11210 (20B) 地图名        @11230 (20B) ?        @11329 (20B) 简报名
  @11349 (1B)  PeG 的"位置标志"（0=Scenario+.TXT / 1=Userscen+.PLY）在本作是否同义
  @216  PeG 的 Player3 主国家（多人分档判据）
"""
import io
import os
import re
import struct
import sys
from collections import Counter

GAME = r"D:\Program Files\PeG-WW2"
SCN = os.path.join(GAME, "SCENARIO")
USR = os.path.join(GAME, "USERSCEN")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evidence")
os.makedirs(OUT, exist_ok=True)
_REPORT = os.path.join(OUT, "recon9-scnfields.txt")
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


def field(b, off, n=20):
    return b[off:off + n].split(b"\0")[0].decode("latin1")


def main():
    files = sorted(f for f in os.listdir(SCN) if f.lower().endswith(".scn"))
    print("=" * 96)
    print("A. 样本 11200..11360 区字段")
    print("=" * 96)
    for f in files[:8] + ["7Pzra7147.scn"]:
        p = os.path.join(SCN, f)
        if not os.path.isfile(p):
            continue
        b = rd(p)
        print(f"\n### {f}  ({len(b):,} B)")
        print(f"   @0={b[0]}  @4(u16)={struct.unpack_from('<H', b, 4)[0]}  @216={b[216] if len(b) > 216 else '-'}")
        print(f"   @11210 map  = {field(b, 11210)!r}")
        print(f"   @11230 n2   = {field(b, 11230)!r}   原始={b[11230:11250].hex(' ')}")
        print(f"   @11250 n3   = {field(b, 11250)!r}")
        print(f"   @11270 n4   = {field(b, 11270)!r}")
        print(f"   @11290 n5   = {field(b, 11290)!r}")
        print(f"   @11310 n6   = {field(b, 11310)!r}")
        print(f"   @11329 intro= {field(b, 11329)!r}")
        print(f"   @11349 flag = {b[11349] if len(b) > 11349 else '-'}")
        stem = f[:-4]
        ex = []
        for cand in [stem + ".txt", stem + "_i.txt", stem + ".ply", stem + "_m.txt",
                     stem + "_u.txt", stem + "_v.txt", stem + "_tv.txt", stem + "_bv.txt",
                     stem + "_l.txt"]:
            if os.path.isfile(os.path.join(SCN, cand)):
                ex.append(cand)
            elif os.path.isfile(os.path.join(USR, cand)):
                ex.append("user:" + cand)
        print(f"   同目录存在的伴侣文件: {ex}")

    print()
    print("=" * 96)
    print("B. 全库字段统计")
    print("=" * 96)
    c0, cflag, cn2 = Counter(), Counter(), Counter()
    has_i = has_txt = has_ply = 0
    for f in files:
        b = rd(os.path.join(SCN, f))
        c0[b[0]] += 1
        if len(b) > 11349:
            cflag[b[11349]] += 1
        cn2[field(b, 11230) or "(空)"] += 1
        stem = f[:-4]
        has_i += os.path.isfile(os.path.join(SCN, stem + "_i.txt"))
        has_txt += os.path.isfile(os.path.join(SCN, stem + ".txt"))
        has_ply += os.path.isfile(os.path.join(SCN, stem + ".ply"))
    print(f"  @0:      {dict(c0)}")
    print(f"  @11349:  {dict(cflag)}")
    print(f"  伴侣: _i.txt={has_i}  .txt={has_txt}  .ply={has_ply}   (共 {len(files)} 场景)")
    print(f"  @11230 非空值 top10: {[x for x in cn2.most_common(10)]}")

    print()
    print("=" * 96)
    print("C. @11230 字段与实体文件一致性核对")
    print("=" * 96)
    ok = bad = 0
    miss = []
    for f in files:
        b = rd(os.path.join(SCN, f))
        v = field(b, 11230)
        if not v:
            continue
        for cand in (v + ".txt", v + ".ply", v + ".TXT", v):
            for d in (SCN, USR):
                if os.path.isfile(os.path.join(d, cand)):
                    ok += 1
                    break
            else:
                continue
            break
        else:
            bad += 1
            miss.append((f, v))
    print(f"  非空且能对上实体文件: {ok}；对不上: {bad}")
    for f, v in miss[:12]:
        print(f"    {f}: @11230={v!r}")

    print()
    print("=" * 96)
    print("D. USERSCEN\\Third Reich.scn 同项（用户场景）")
    print("=" * 96)
    b = rd(os.path.join(USR, "Third Reich.scn"))
    print(f"   size={len(b):,} @0={b[0]} @4(u16)={struct.unpack_from('<H', b, 4)[0]} @216={b[216]}")
    for off in (11210, 11230, 11250, 11270, 11290, 11310, 11329):
        print(f"   @{off} = {field(b, off)!r}")
    print(f"   @11349 = {b[11349] if len(b) > 11349 else '-'}")


if __name__ == "__main__":
    main()
    with open(_REPORT, "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
    print(f"\n[report] {_REPORT}")
