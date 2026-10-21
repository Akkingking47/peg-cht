# -*- coding: utf-8 -*-
"""prob0_sechdr.py — 打印真实节表。"""
import struct

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
import os
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────

D = os.path.join(GAME, "PeG030.exe")
d = open(D, "rb").read()
e = struct.unpack_from("<I", d, 0x3C)[0]
nsec = struct.unpack_from("<H", d, e + 6)[0]
optsz = struct.unpack_from("<H", d, e + 20)[0]
print("e_lfanew=0x%X nsec=%d optsz=0x%X filesize=%d (0x%X)" % (e, nsec, optsz, len(d), len(d)))
sec0 = e + 24 + optsz
for i in range(nsec):
    o = sec0 + i * 40
    name = d[o:o + 8].rstrip(b"\0").decode()
    vsize, va, rawsize, raw = struct.unpack_from("<IIII", d, o + 8)
    print("%-8s VA=0x%08X vsize=0x%-6X raw=0x%-6X rawsize=0x%-6X  VAend=0x%08X rawend=0x%08X"
          % (name, 0x400000 + va, vsize, raw, rawsize, 0x400000 + va + vsize, raw + rawsize))
