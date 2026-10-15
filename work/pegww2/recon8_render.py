#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 阶段0.7c：渲染指定 s16 条目（原生 RLE 布局）为 PNG，供判读烘焙文字。

用法: python recon8_render.py STARTSCR.S16 STAGE.S16 HEX.S16 ...
      可用 NAME:idx 指定某个 icon（默认 0）
"""
import os
import struct
import sys
import zlib

GAME = r"D:\Program Files\PeG-WW2"
DAT = os.path.join(GAME, "WW2GEN.dat")
EV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evidence")
os.makedirs(EV, exist_ok=True)


def write_png(path, w, h, px):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        row = px[y * w:(y + 1) * w]
        for r, g, b in row:
            raw += bytes((r, g, b))
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
                + chunk(b"IEND", b""))


def rle_decode(data, npix):
    out = []
    i, n = 0, len(data)
    while len(out) < npix and i + 2 < n:
        c = data[i]
        col = struct.unpack_from("<H", data, i + 1)[0]
        i += 3
        out.extend([col] * c)
    return out[:npix]


def rgb565(c):
    r, g, b = (c >> 11) & 0x1F, (c >> 5) & 0x3F, c & 0x1F
    return (r << 3 | r >> 2, g << 2 | g >> 4, b << 3 | b >> 2)


def main():
    want = sys.argv[1:] or ["STARTSCR.S16", "STAGE.S16", "HEX.S16"]
    with open(DAT, "rb") as f:
        n, dirend = struct.unpack("<II", f.read(8))
        d = f.read(dirend - 8)
    ents = {}
    off = 0
    while off + 17 <= len(d):
        nm = d[off:off + 13].rstrip(b"\0").decode("latin1")
        (o,) = struct.unpack_from("<I", d, off + 13)
        ents[nm.upper()] = o
        off += 17
    sz = os.path.getsize(DAT)
    with open(DAT, "rb") as f:
        for spec in want:
            name, _, idxs = spec.partition(":")
            idx = int(idxs) if idxs else 0
            o = ents.get(name.upper())
            if o is None:
                print(f"{name}: 未找到")
                continue
            f.seek(o)
            (nicon,) = struct.unpack("<I", f.read(4))
            recs = []
            raw = f.read(nicon * 40)
            for i in range(nicon):
                recs.append(struct.unpack_from("<10I", raw, i * 40))
            w, h, sx, sy, fw, fh, starts, nbytes, comp, load = recs[idx]
            print(f"{name}[{idx}] nIcons={nicon} w={w} h={h} fullW={fw} fullH={fh} "
                  f"starts={starts:#x} nbytes={nbytes} comp={comp} load={load:#x}")
            f.seek(o + starts)
            blob = f.read(nbytes if nbytes else (fw * fh * 3))
            px = rle_decode(blob, fw * fh)
            if len(px) < fw * fh:
                print(f"   警告: 只解出 {len(px)}/{fw * fh} 像素（blob={len(blob)}）")
            rgb = [rgb565(c) for c in px] + [(0, 0, 0)] * max(0, fw * fh - len(px))
            out = os.path.join(EV, f"{name.split('.')[0]}-i{idx}-{fw}x{fh}.png")
            write_png(out, fw, fh, rgb[:fw * fh])
            print(f"   -> {os.path.basename(out)}")


if __name__ == "__main__":
    main()
