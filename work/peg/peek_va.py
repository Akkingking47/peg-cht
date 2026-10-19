# -*- coding: utf-8 -*-
"""peek_va.py <hexva> [<hexva>...] [--exe <path>] -- dump words/dwords at a VA from the on-disk EXE."""
import sys
import pefile

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
import os
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────

args = list(sys.argv[1:])
EXE = os.path.join(GAME, "PeG030.exe")
if "--exe" in args:
    i = args.index("--exe")
    EXE = args[i + 1]
    del args[i:i + 2]
pe = pefile.PE(EXE, fast_load=True)
print("# %s" % EXE)
base = pe.OPTIONAL_HEADER.ImageBase
def raw(va, n):
    for s in pe.sections:
        va0 = base + s.VirtualAddress
        vs = max(s.Misc_VirtualSize, s.SizeOfRawData)
        if va0 <= va < va0 + vs:
            d = s.get_data()
            off = va - va0
            chunk = d[off:off+n] if off < len(d) else b""
            if len(chunk) < n:
                chunk += b"\x00" * (n - len(chunk))
            return chunk
    return b"\x00" * n
for a in args:
    va = int(a, 16)
    n = 32
    b = raw(va, n)
    words = " ".join("%04x" % int.from_bytes(b[i:i+2], "little") for i in range(0, n, 2))
    dws = " ".join("%08x" % int.from_bytes(b[i:i+4], "little") for i in range(0, n, 4))
    print("0x%06x  words: %s" % (va, words))
    print("           dwords: %s" % dws)
