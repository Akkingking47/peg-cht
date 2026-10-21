import struct

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
import os
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────

EXE = os.path.join(GAME, "PeG030.exe")
data = open(EXE,'rb').read()
VA, RAW = 0x8E000, 0x8B800      # .data
def off(va): return RAW + (va - (0x400000 + VA))
base = 0x4A0200
print("table @0x4A0200, 24 bytes/entry (hex dump):")
for i in range(6):
    o = off(base + i*24)
    row = data[o:o+24]
    print("  [%d] %s   bytes: %s" % (i, row.hex(' '), list(row)))
print()
i = 0
o = off(base + i*24)
print("entry0 fields (word@+0, byte@+2, byte@+6, byte@+0xb):",
      struct.unpack_from('<H', data, o)[0], data[o+2], data[o+6], data[o+0xb])
print()
print("cellW(byte@+2 +1) per entry:", [data[off(base+i*24)+2]+1 for i in range(6)])
print("cellH?(byte@+6 +1) per entry:", [data[off(base+i*24)+6]+1 for i in range(6)])
print("byte@+0xb per entry:", [data[off(base+i*24)+0xb] for i in range(6)])
