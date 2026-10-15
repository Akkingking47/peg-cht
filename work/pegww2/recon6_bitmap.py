#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 阶段0.7：位图文字排查（WW2GEN.dat / MAP\\*.s16 内是否有烘焙文字）。

格式（沿用 PeG 实测结论）：
  WW2GEN.dat : u32 nEntry + u32 dirEnd + nEntry×(13B 名 + u32 偏移)
  .s16       : u32 nIcons + nIcons×40B {w,h,startX,startY,fullW,fullH,starts,nbytes,comp,loadAddr}
               图形数据 RLE = (u8 重复次数 + u16 RGB565 颜色)
输出 PNG 到 evidence/，供人工/模型看图判定。
"""
import io
import os
import re
import struct
import sys
import zlib
from collections import Counter

GAME = r"D:\Program Files\PeG-WW2"
HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.join(HERE, "evidence")
os.makedirs(EV, exist_ok=True)
_REPORT = os.path.join(EV, "recon6-bitmap.txt")
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


def write_png(path, w, h, pixels):
    """pixels: list of (r,g,b) 行优先"""
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            r, g, b = pixels[y * w + x]
            raw += bytes((r, g, b))
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def rle_decode(data, npix):
    """RLE: u8 count + u16 color。返回 RGB565 列表。"""
    out = []
    i = 0
    n = len(data)
    while len(out) < npix and i + 2 < n:
        c = data[i]
        col = struct.unpack_from("<H", data, i + 1)[0]
        i += 3
        out.extend([col] * c)
    return out[:npix]


def rgb565(c):
    r = (c >> 11) & 0x1F
    g = (c >> 5) & 0x3F
    b = c & 0x1F
    return (r << 3 | r >> 2, g << 2 | g >> 4, b << 3 | b >> 2)


def parse_s16(buf, want=0):
    (n,) = struct.unpack_from("<I", buf, 0)
    idx = []
    off = 4
    for i in range(n):
        if off + 40 > len(buf):
            break
        vals = struct.unpack_from("<10I", buf, off)
        idx.append(vals)
        off += 40
    if want >= len(idx):
        return None
    w, h, sx, sy, fw, fh, starts, nbytes, comp, load = idx[want]
    blob = buf[starts:starts + nbytes]
    return {"n": n, "idx": idx, "w": w, "h": h, "fw": fw, "fh": fh,
            "nbytes": nbytes, "comp": comp, "blob": blob, "wanted": want}


def dump_dat():
    p = os.path.join(GAME, "WW2GEN.dat")
    with open(p, "rb") as f:
        head = f.read(8)
        n, dirend = struct.unpack("<II", head)
        print(f"WW2GEN.dat: nEntry={n:,} dirEnd={dirend:,} size={os.path.getsize(p):,}")
        d = f.read(dirend - 8)
    ents = []
    off = 0
    while off + 17 <= len(d) and len(ents) < n:
        name = d[off:off + 13].rstrip(b"\0").decode("latin1")
        (o,) = struct.unpack_from("<I", d, off + 13)
        ents.append((name, o))
        off += 17
    print(f"  解析条目 {len(ents):,}（首条 {ents[0] if ents else None}）")
    return p, ents


def main():
    dat, ents = dump_dat()
    names = [e[0] for e in ents]
    print(f"  扩展名分布: {dict(Counter(os.path.splitext(x)[1].lower() for x in names).most_common(6))}")

    for want in ["ST030.S16", "HEX.S16", "MAINBAR.S16", "SCENDESC.S16", "STRING.S16"]:
        hit = [i for i, e in enumerate(ents) if e[0].upper() == want]
        print(f"  {want}: {'找到 idx=' + str(hit) if hit else '未找到'}")

    print()
    print("=" * 88)
    print("A. 渲染候选画面（找烘焙文字）")
    print("=" * 88)
    targets = []
    for want in ["ST030.S16", "HEX.S16", "SCENDESC.S16"]:
        for i, e in enumerate(ents):
            if e[0].upper() == want:
                targets.append((want, e[1]))
                break
    with open(dat, "rb") as f:
        for nm, off in targets:
            f.seek(off)
            hdr = f.read(4)
            (nicon,) = struct.unpack("<I", hdr)
            rest = f.read(nicon * 40 + 4)
            recs = []
            for i in range(nicon):
                recs.append(struct.unpack_from("<10I", rest, i * 40))
                if i == 0:
                    first_starts = recs[0][6]
            # 取全部数据
            f.seek(off)
            blob = f.read(4 + nicon * 40 + (first_starts - (4 + nicon * 40)) + 0)
            # 简化：一次性读足够大
            f.seek(off)
            data = f.read(4 + nicon * 40 + 8_000_000)
            print(f"\n{nm}: nIcons={nicon}  各 icon 尺寸前 6 个: {[(r[0], r[1]) for r in recs[:6]]}")
            base = 4 + nicon * 40
            for i in range(min(3, nicon)):
                w, h, sx, sy, fw, fh, starts, nbytes, comp, load = recs[i]
                if starts + nbytes > len(data):
                    print(f"   icon[{i}] 数据越界 starts={starts} nbytes={nbytes}")
                    continue
                px = rle_decode(data[starts:starts + nbytes], fw * fh)
                if not px:
                    print(f"   icon[{i}] 解码为空")
                    continue
                rgb = [rgb565(c) for c in px]
                out = os.path.join(EV, f"{nm.split('.')[0]}-icon{i}-{fw}x{fh}.png")
                write_png(out, fw, fh, rgb)
                print(f"   icon[{i}] {fw}x{fh} 解码像素={len(px)} 消耗字节≈{len(px) and nbytes} -> {os.path.basename(out)}")

    print()
    print("=" * 88)
    print("B. MAP\\*.s16 抽查（地形图是否含烘焙文字）")
    print("=" * 88)
    mp = os.path.join(GAME, "MAP")
    for nm in ["MAP0000.s16", "MAP0001.s16"]:
        p = os.path.join(mp, nm)
        if not os.path.isfile(p):
            print(f"  {nm} 缺")
            continue
        with open(p, "rb") as f:
            (n,) = struct.unpack("<I", f.read(4))
            recs = [struct.unpack_from("<10I", f.read(40), 0) for _ in range(n)]
            f.seek(0)
            data = f.read()
        w, h, sx, sy, fw, fh, starts, nbytes, comp, load = recs[0]
        px = rle_decode(data[starts:starts + nbytes], fw * fh)
        rgb = [rgb565(c) for c in px]
        out = os.path.join(EV, f"{nm.split('.')[0]}-{fw}x{fh}.png")
        write_png(out, fw, fh, rgb)
        print(f"  {nm}: nIcons={n} icon0={fw}x{fh} 解码={len(px)} -> {os.path.basename(out)}")


if __name__ == "__main__":
    main()
    with open(_REPORT, "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
    print(f"\n[report] {_REPORT}")
