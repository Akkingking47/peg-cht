#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 阶段0.2b/0.3：补丁落点逐字节核验 + 文本 stem 扫描 + 文本层普查。

补丁落点一律用【文件偏移 FO】表述（避免 VA/FO 混用事故）。
PeG 参照原版: D:\\Program Files\\PeG\\PeG030.exe.orig-backup
"""
import os
import re
import struct
import sys
from collections import Counter, defaultdict

GAME = r"D:\Program Files\PeG-WW2"
ORIG = r"D:\Program Files\PeG\PeG030.exe.orig-backup"
PATCHED = r"D:\Program Files\PeG\PeG030.exe"

# (名称, FO, 长度)  —— 全部为【文件偏移】
SITES = [
    ("iCharSet(push imm)", 0x70CE3, 2),          # 6a 00 -> 6a 86
    ("_pctype 0x81-0xFE", 0xA938A, 256 - 2),     # 128 words 区（0x81..0xFE -> 0x8040）
    ("__mbcodepage", 0xA948C, 4),                # 1 -> 936
    ("date_LCID", 0x7BE86, 5),                   # A1 48 91 49 00 -> B8 04 08 00 00
    ("lineterm#1_start", 0xA938A, 8),
    ("labeldrop#2", 0x6F31C, 2),                 # 7c 08 -> eb 00
]


def rd(p):
    with open(p, "rb") as f:
        return f.read()


def scan_stems(data):
    """大小写不敏感的子串扫描：找出该 exe 引用的文本文件 stem。"""
    low = data.lower()
    pats = {
        "gui030": b"gui030", "gui031": b"gui031", "gui97": b"gui97", "gui98": b"gui98",
        "equip30": b"equip30", "equip31": b"equip31", "equip97": b"equip97", "equip98": b"equip98",
        "misc030": b"misc030", "misc98": b"misc98", "name030": b"name030",
        "tips030": b"tips030", "tips97": b"tips97", "tips98": b"tips98",
        "ww2gui": b"ww2gui", "ww2misc": b"ww2misc", "ww2name": b"ww2name",
        "ww2tips": b"ww2tips", "ww2-eqp": b"ww2-eqp", "ww2gen": b"ww2gen",
        "peoples": b"peoples", "ww2": b"ww2",
    }
    return {k: low.count(v) for k, v in pats.items() if low.count(v)}


def all_strings(data, minlen=4):
    return set(m.group(0) for m in re.finditer(rb"[\x20-\x7e]{%d,}" % minlen, data))


def pe_sections(data):
    e = struct.unpack_from("<I", data, 0x3C)[0]
    coff = e + 4
    nsec = struct.unpack_from("<H", data, coff + 2)[0]
    optsz = struct.unpack_from("<H", data, coff + 16)[0]
    ib = struct.unpack_from("<I", data, coff + 20 + 28)[0]
    sec = coff + 20 + optsz
    out = []
    for i in range(nsec):
        o = sec + i * 40
        name = data[o:o + 8].rstrip(b"\0").decode("latin1")
        vs, va, rs, ra = struct.unpack_from("<IIII", data, o + 8)
        out.append((name, va, vs, ra, rs))
    return ib, out


def main():
    orig = rd(ORIG)
    patched = rd(PATCHED)
    print("=" * 96)
    print("A. 参照原版 PeG030.exe.orig-backup 的落点字节（FO 制）")
    print("=" * 96)
    for name, fo, n in SITES:
        print(f"  {name:22s} FO={fo:#08x} len={n:<4d} {orig[fo:fo + n].hex(' ')}")
    print()
    print("  —— 与已打补丁版 PeG030.exe 的差异 FO ——")
    diffs = [i for i in range(min(len(orig), len(patched))) if orig[i] != patched[i]]
    print(f"  总差异字节数 = {len(diffs)}")
    print(f"  首尾 = {diffs[0]:#x} .. {diffs[-1]:#x}" if diffs else "")

    # 归纳连续区段
    segs = []
    for i in diffs:
        if segs and i == segs[-1][1] + 1:
            segs[-1][1] = i
        else:
            segs.append([i, i])
    for a, b in segs:
        print(f"    段 {a:#08x}..{b:#08x}  ({b - a + 1} B)  orig={orig[a:b + 1].hex(' ')[:60]}  patched={patched[a:b + 1].hex(' ')[:60]}")

    print()
    print("=" * 96)
    print("B. PeG-WW2 各 exe：落点是否 = 原版（⇒ 补丁可否 1:1 套用）")
    print("=" * 96)
    exes = []
    for root, dirs, files in os.walk(GAME):
        for f in files:
            if f.lower().endswith(".exe"):
                exes.append(os.path.join(root, f))
    for p in sorted(exes):
        try:
            d = rd(p)
        except Exception as e:
            print(f"{os.path.basename(p)}: 读失败 {e}")
            continue
        if len(d) != len(orig) or d[:2] != b"MZ":
            continue
        same = sum(1 for i in range(len(d)) if d[i] != orig[i])
        nd = sum(1 for i in range(len(d)) if d[i] != patched[i])
        sites_ok = all(d[fo:fo + n] == orig[fo:fo + n] for _, fo, n in SITES)
        stems = scan_stems(d)
        print(f"\n{os.path.basename(p)}  (与原版差异 {same} B / 与补丁版差异 {nd} B)")
        print(f"   落点==原版? {'✅ 是' if sites_ok else '❌ 否'}")
        print(f"   stem: {stems}")
        strs = all_strings(d)
        cand = sorted(s for s in strs if re.search(rb"(?i)(gui|equip|misc|name|tips|ww2|peoples|\.eqp|\.txt|\.dat)", s) and len(s) < 40)
        print(f"   相关串({len(cand)}): {[c.decode('latin1') for c in cand][:24]}")

    print()
    print("=" * 96)
    print("C. 根级文本文件（待汉化主表）")
    print("=" * 96)
    for f in sorted(os.listdir(GAME)):
        fp = os.path.join(GAME, f)
        if not os.path.isfile(fp):
            continue
        if not re.search(r"(?i)\.(txt|eqp|aux|int|dat|ply|scn|s16)$", f):
            continue
        b = rd(fp)
        hi = sum(1 for x in b if x > 127)
        crlf, lf, cr = b.count(b"\r\n"), b.count(b"\n"), b.count(b"\r")
        n = len(re.split(rb"\r\n|\r|\n", b))
        bom = b[:3] == b"\xef\xbb\xbf"
        print(f"  {f:20s} {len(b):>10,d} B  hi={hi:<7d}({hi / max(1, len(b)) * 100:.2f}%)  行={n:<6d} CRLF={crlf:<6d} 裸LF={lf - crlf:<5d} 裸CR={cr - crlf:<4d} BOM={bom}")


if __name__ == "__main__":
    main()
