# -*- coding: utf-8 -*-
"""show_bytes.py —— 按 VA 打印 PE 文件字节（可多个区间）

用途：写补丁站点表前，先亲眼确认「立即数到底落在哪个偏移」，
避免像 0x41C4D4（指令地址）与 0x41C4D7（imm32 地址）那样差 3 字节。

用法：
    python show_bytes.py <exe> 0x41C4D4:32 0x44C5C0:32
    python show_bytes.py                      # 默认对 v4 产物看下表里的候选点

节表按本工程实测硬编（ImageBase 0x400000）：
    .text  VA 0x401000  raw 0x400    size 0x8A200
    .rdata VA 0x48C000  raw 0x8A600  size 0x1200
    .data  VA 0x48E000  raw 0x8B800  size 0x21400
    .idata VA 0x6AA000  raw 0xACC00
    .rsrc  VA 0x6AC000  raw 0xAE200
"""
import sys
import os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = 0x400000
SECS = [
    ("".join(chr(b) for b in n), va, raw, size)
    for n, va, raw, size in [
        (b".text", 0x401000, 0x400, 0x8A200),
        (b".rdata", 0x48C000, 0x8A600, 0x1200),
        (b".data", 0x48E000, 0x8B800, 0x21400),
        (b".idata", 0x6AA000, 0xACC00, 0x5E00),
        (b".rsrc", 0x6AC000, 0xAE200, 0x5600),
    ]
]

V4 = r"D:\Program Files\PeG-1\PeG030res.exe"

# 默认要看的候选点（VA:长度）——v5 变体要动的立即数附近
DEFAULT = [
    "0x41C4C8:40",   # 面板矩形 22/571/799/180 与 left=right-180+1
    "0x44C5B8:48",   # 屏幕边框 570/796 + call 0x4235E5
    "0x44C724:40",   # 视口裁剪组 1：mov eax,0x320 / mov [0x663388],0x320
    "0x44C770:40",   # 视口裁剪组 1：600
    "0x44C860:40",   # 视口裁剪组 2：800
    "0x44C8A8:48",   # 视口裁剪组 2：600
    "0x44CC60:40",   # 视口裁剪组 3：800
    "0x44CCA0:48",   # 视口裁剪组 3：600
]


def va_to_fo(va):
    for name, sva, raw, size in SECS:
        if sva <= va < sva + size:
            return raw + (va - sva), name
    return None, None


def main():
    args = sys.argv[1:]
    if args and args[0].lower().endswith(".exe"):
        path = args[0]
        specs = args[1:]
    else:
        path = V4
        specs = args or DEFAULT
    data = open(path, "rb").read()
    print("EXE : %s" % path)
    print("SIZE: %d bytes" % len(data))
    if not specs:
        specs = DEFAULT
    for spec in specs:
        va_s, _, len_s = spec.partition(":")
        va = int(va_s, 16)
        ln = int(len_s) if len_s else 16
        fo, sec = va_to_fo(va)
        if fo is None:
            print("\nVA %#x  ->  不在已知节内" % va)
            continue
        raw = data[fo:fo + ln]
        print("\nVA %#010x  FO %#08x  %s  len=%d" % (va, fo, sec, len(raw)))
        for off in range(0, len(raw), 16):
            chunk = raw[off:off + 16]
            hexs = " ".join("%02X" % b for b in chunk)
            txt = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            print("  %#010x  %-47s  %s" % (va + off, hexs, txt))


if __name__ == "__main__":
    main()
