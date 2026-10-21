# -*- coding: utf-8 -*-
"""只读：把 exe 里的"界面布局记录表"按字节 dump 出来，用来反推字段语义。

用法：C:\\Python314\\python.exe _dump_layout_table.py [VA] [count]
默认 dump 0x4A96E8 起的 24 条（记录长度 15 字节）。
输出：stdout 精简表 + work\\peg\\out\\layout-table-dump.txt 全量。
"""
import os
import struct
import sys

EXE = r"D:\Program Files\PeG\PeG030.exe"
OUT = r"D:\DSH\军事游戏汉化\work\peg\out\layout-table-dump.txt"
BASE = 0x400000


def sections(data):
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, e_lfanew + 6)[0]
    opt_size = struct.unpack_from("<H", data, e_lfanew + 20)[0]
    base = e_lfanew + 24 + opt_size
    out = []
    for i in range(nsec):
        off = base + i * 40
        name = data[off:off + 8].rstrip(b"\x00").decode("latin1")
        vsize, va, rawsize, raw = struct.unpack_from("<IIII", data, off + 8)
        out.append({"name": name, "va": va, "vsize": vsize, "raw": raw, "rawsize": rawsize})
    return out


def va_to_off(secs, va):
    rva = va - BASE
    for s in secs:
        if s["va"] <= rva < s["va"] + max(s["vsize"], s["rawsize"]):
            return s["raw"] + (rva - s["va"]), s["name"]
    raise KeyError("VA %#x 不在任何节里" % va)


def main(argv):
    va = int(argv[1], 0) if len(argv) > 1 else 0x4A96E8
    count = int(argv[2]) if len(argv) > 2 else 24
    rec = int(argv[3]) if len(argv) > 3 else 15
    data = open(EXE, "rb").read()
    secs = sections(data)
    print("节表：", ", ".join("%s va=%#x vsize=%#x raw=%#x" % (s["name"], s["va"], s["vsize"], s["raw"]) for s in secs))
    off, sec = va_to_off(secs, va)
    print("表 VA %#x 在 %s，文件偏移 %#x，记录长度 %d，dump %d 条" % (va, sec, off, rec, count))
    lines = []
    lines.append("VA      idx  bytes                                    | i8@0 i8@1 i16@2 i16@4 i16@6 i16@8 i16@10 i16@12 i8@14")
    for i in range(count):
        o = off + i * rec
        raw = data[o:o + rec]
        if len(raw) < rec:
            break
        i16 = [struct.unpack_from("<h", raw, k)[0] if k + 2 <= rec else None for k in range(0, rec, 2)]
        line = "%06X  %3d  %-40s | %5d %5d %6d %6d %6d %6d %7d %7d %5d" % (
            va + i * rec, i, raw.hex(" "),
            struct.unpack_from("<b", raw, 0)[0], struct.unpack_from("<b", raw, 1)[0],
            i16[1], i16[2], i16[3], i16[4], i16[5], i16[6],
            struct.unpack_from("<b", raw, 14)[0])
        lines.append(line)
    text = "\n".join(lines)
    print(text)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    # 全量：dump 到 0x4AF400 为止
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("VA %#x 记录长度 %d\n" % (va, rec))
        fh.write(text + "\n")
        end_va = 0x4AF400
        n = max(0, (end_va - va) // rec)
        fh.write("\n=== 全量 %d 条 ===\n" % n)
        for i in range(n):
            o = off + i * rec
            raw = data[o:o + rec]
            if len(raw) < rec:
                break
            fh.write("%06X  %s\n" % (va + i * rec, raw.hex(" ")))
    print("\n全量 -> %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
