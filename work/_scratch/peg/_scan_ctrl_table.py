# -*- coding: utf-8 -*-
"""只读：扫描"控件矩形表" 0x4A96E8（记录 15 字节）的边界与字段分布。

判定：一条记录的前 8 字节是 4 个 int16 矩形 (x0,y0,x1,y1)，
满足 0<=x0<x1<=800 且 0<=y0<y1<=600 视为"像控件"。
连续 12 条不像就认为表结束。结果写 work\\peg\\out\\ctrl-table-scan.txt。
"""
import os
import struct
import sys

EXE = r"D:\Program Files\PeG\PeG030.exe"
OUT = r"D:\DSH\军事游戏汉化\work\peg\out\ctrl-table-scan.txt"
BASE = 0x400000
TABLE = 0x4A96E8
REC = 15
LIMIT = 0x4AF400  # .data 里真实数据的上界


def sections(data):
    e = struct.unpack_from("<I", data, 0x3C)[0]
    n = struct.unpack_from("<H", data, e + 6)[0]
    opt = struct.unpack_from("<H", data, e + 20)[0]
    off = e + 24 + opt
    out = []
    for i in range(n):
        o = off + i * 40
        name = data[o:o + 8].rstrip(b"\x00").decode("latin1")
        vsize, va, rawsize, raw = struct.unpack_from("<IIII", data, o + 8)
        out.append((name, va, vsize, raw, rawsize))
    return out


def va_to_off(secs, va):
    rva = va - BASE
    for name, sva, vsize, raw, rawsize in secs:
        if sva <= rva < sva + max(vsize, rawsize):
            return raw + (rva - sva)
    raise KeyError(hex(va))


def main():
    data = open(EXE, "rb").read()
    secs = sections(data)
    off = va_to_off(secs, TABLE)
    good, bad_run = [], 0
    tail_hist = {}
    i = 0
    max_recs = (LIMIT - TABLE) // REC
    while i < max_recs:
        raw = data[off + i * REC: off + (i + 1) * REC]
        if len(raw) < REC:
            break
        x0, y0, x1, y1 = struct.unpack_from("<hhhh", raw, 0)
        ok = 0 <= x0 < x1 <= 800 and 0 <= y0 < y1 <= 600
        if ok:
            bad_run = 0
            good.append((TABLE + i * REC, i, x0, y0, x1, y1, raw[8:].hex(" ")))
            key = raw[10:12].hex()
            tail_hist[key] = tail_hist.get(key, 0) + 1
        else:
            bad_run += 1
            if bad_run >= 12 and good:
                break
        i += 1
    end_va = TABLE + (i - bad_run) * REC
    xs = [g[2] for g in good] + [g[4] for g in good]
    ys = [g[3] for g in good] + [g[5] for g in good]
    lines = []
    lines.append("控件矩形表 VA %#x 记录 %d 字节" % (TABLE, REC))
    lines.append("像控件的记录 %d 条，扫描 %d 条后判定结束；表结束约在 VA %#x（未对齐含义：最后一条像控件的记录结束于 %#x）"
                 % (len(good), i, TABLE + i * REC, TABLE + len(good) * REC))
    lines.append("x 范围 [%d, %d]（设计空间 800）；y 范围 [%d, %d]（设计空间 600）" % (min(xs), max(xs), min(ys), max(ys)))
    lines.append("")
    lines.append("VA      idx   x0    y0    x1    y1   | 尾部 7 字节")
    for va, idx, x0, y0, x1, y1, tail in good:
        lines.append("%06X  %4d  %4d  %4d  %4d  %4d  | %s" % (va, idx, x0, y0, x1, y1, tail))
    lines.append("")
    lines.append("尾部 +10..+11 的取值分布（可能是 type/flags）：")
    for k, v in sorted(tail_hist.items(), key=lambda kv: -kv[1]):
        lines.append("  bytes %s : %d 条" % (k, v))
    text = "\n".join(lines)
    print("\n".join(lines[:6]))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    print("\n全部 %d 条 -> %s" % (len(good), OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
