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
e = struct.unpack_from('<I', data, 0x3C)[0]
nsec = struct.unpack_from('<H', data, e+6)[0]
optsz = struct.unpack_from('<H', data, e+20)[0]
sec0 = e+24+optsz
secs = []
for i in range(nsec):
    o = sec0+i*40
    nm = data[o:o+8].rstrip(b'\0').decode('ascii','replace')
    vsz, va, rsz, raw = struct.unpack_from('<IIII', data, o+8)
    secs.append((nm, va, raw, rsz))
def va_of(off):
    for nm, va, raw, rsz in secs:
        if raw <= off < raw+rsz:
            return 0x400000+va+(off-raw), nm
    return None, None
for pat, label in ((b"\x42\x2d\x62\x00","0x622d42"), (b"\x44\x2d\x62\x00","0x622d44")):
    print("== %s ==" % label)
    st = 0
    n = 0
    while True:
        i = data.find(pat, st)
        if i < 0: break
        va, sec = va_of(i)
        if va:
            print("  0x%08X [%s] pre: %s" % (va, sec, data[max(0,i-10):i].hex(' ')))
            n += 1
        st = i+1
    print("  total", n)
