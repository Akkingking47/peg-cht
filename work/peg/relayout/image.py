# -*- coding: utf-8 -*-
"""只读 PE 小工具：把 VA 映射到母本 exe 的文件偏移，并按 VA 读原始字节。

母本：D:\\Program Files\\PeG\\PeG030.exe（一字节不改，只读）。
节表实测：.text va=0x1000 vsize=0x8A136 raw=0x400 / .rdata va=0x8C000 vsize=0x1017 raw=0x8A600
          .data va=0x8E000 vsize=0x21BF3C raw=0x8B800 / .idata va=0x2AA000 / .rsrc va=0x2AC000
镜像基址 0x400000。
"""
from __future__ import annotations

import os
import struct

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


IMAGE_BASE = 0x400000
MOTHER = os.path.join(GAME, "PeG030.exe")

_cache = {}


class Section:
    __slots__ = ("name", "va", "vsize", "raw", "rawsize")

    def __init__(self, name, va, vsize, raw, rawsize):
        self.name = name
        self.va = va
        self.vsize = vsize
        self.raw = raw
        self.rawsize = rawsize

    @property
    def end_va(self):
        return IMAGE_BASE + self.va + max(self.vsize, self.rawsize)

    def __repr__(self):
        return "<%s va=%#x vsize=%#x raw=%#x>" % (self.name, IMAGE_BASE + self.va, self.vsize, self.raw)


def sections(path: str = MOTHER):
    if path in _cache:
        return _cache[path]
    data = open(path, "rb").read()
    e = struct.unpack_from("<I", data, 0x3C)[0]
    n = struct.unpack_from("<H", data, e + 6)[0]
    opt = struct.unpack_from("<H", data, e + 20)[0]
    off = e + 24 + opt
    out = []
    for i in range(n):
        o = off + i * 40
        name = data[o:o + 8].rstrip(b"\x00").decode("latin1")
        vsize, va, rawsize, raw = struct.unpack_from("<IIII", data, o + 8)
        out.append(Section(name, va, vsize, raw, rawsize))
    _cache[path] = (data, out)
    return _cache[path]


def image(path: str = MOTHER):
    data, secs = sections(path)
    return data, secs


def va_to_off(va: int, path: str = MOTHER) -> int:
    data, secs = sections(path)
    rva = va - IMAGE_BASE
    for s in secs:
        if s.va <= rva < s.va + max(s.vsize, s.rawsize):
            return s.raw + (rva - s.va)
    raise KeyError("VA %#x 不在任何节里" % va)


def section_of(va: int, path: str = MOTHER) -> str:
    data, secs = sections(path)
    rva = va - IMAGE_BASE
    for s in secs:
        if s.va <= rva < s.va + max(s.vsize, s.rawsize):
            return s.name
    raise KeyError("VA %#x 不在任何节里" % va)


def read_va(va: int, size: int, path: str = MOTHER) -> bytes:
    """读 VA 处的 size 字节。落在节的文件区外（BSS）时抛 KeyError。"""
    data, _ = sections(path)
    off = va_to_off(va, path)
    b = data[off:off + size]
    if len(b) != size:
        raise KeyError("VA %#x 处不够 %d 字节" % (va, size))
    return b


def is_data_va(va: int) -> bool:
    try:
        return section_of(va) in (".data", ".rdata")
    except KeyError:
        return False


if __name__ == "__main__":
    data, secs = sections()
    for s in secs:
        print(s)
    print("0x4A96E8 -> %s off=%#x" % (section_of(0x4A96E8), va_to_off(0x4A96E8)))
    print("前 15 字节:", read_va(0x4A96E8, 15).hex(" "))
