# -*- coding: utf-8 -*-
"""_find_map_sites.py — 找地图面尺寸(0x780=1920)与地图面地址引用（只读，不改任何文件）。

输出：
  1) .text 中所有 dword 0x00000780 出现点，带前 6 字节（判定是指令立即数还是数据）
  2) 0x655574 / 0x622A10（两块 1920x1920 地图面指针）的 push/mov 引用点
用法: python work\\peg\\_find_map_sites.py [--exe D:\\Program Files\\PeG\\PeG030.exe]
"""
import argparse
import os
import struct

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_EXE = os.path.join(GAME, "PeG030.exe")
IMAGE_BASE = 0x400000


def parse_sections(data):
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, e_lfanew + 6)[0]
    opt_size = struct.unpack_from("<H", data, e_lfanew + 20)[0]
    sec0 = e_lfanew + 24 + opt_size
    secs = []
    for i in range(nsec):
        off = sec0 + i * 40
        name = data[off:off + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, va, rawsize, raw = struct.unpack_from("<IIII", data, off + 8)
        secs.append(dict(name=name, va=va, vsize=vsize, raw=raw, rawsize=rawsize))
    return secs


def off_to_va(secs, off):
    for s in secs:
        if s["raw"] <= off < s["raw"] + s["rawsize"]:
            return IMAGE_BASE + s["va"] + (off - s["raw"]), s["name"]
    return None, None


def scan(data, secs, pat, label, ctx=6):
    out = []
    start = 0
    while True:
        i = data.find(pat, start)
        if i < 0:
            break
        va, sec = off_to_va(secs, i)
        if va is not None:
            pre = data[max(0, i - ctx):i].hex(" ")
            out.append((va, sec, pre))
        start = i + 1
    print("== %s : %d 处 ==" % (label, len(out)))
    for va, sec, pre in out:
        print("  0x%08X  [%s]  前置: %s" % (va, sec, pre))
    print()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default=DEFAULT_EXE)
    a = ap.parse_args()
    with open(a.exe, "rb") as f:
        data = f.read()
    secs = parse_sections(data)
    print("exe: %s  (%d 字节)" % (a.exe, len(data)))
    for s in secs:
        print("  节 %-8s va=0x%X raw=0x%X rawsize=0x%X vsize=0x%X"
              % (s["name"], s["va"], s["raw"], s["rawsize"], s["vsize"]))
    print()
    scan(data, secs, b"\x80\x07\x00\x00", "dword 0x780 (=1920)")
    scan(data, secs, b"\x74\x55\x65\x00", "0x655574 (地图面 A)")
    scan(data, secs, b"\x10\x2a\x62\x00", "0x622A10 (地图面 B)")


if __name__ == "__main__":
    main()
