# -*- coding: utf-8 -*-
# read-only: dump candidate UI layout tables + nearby strings, compare SRC vs PORT.
import sys

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
import os
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────

sys.path.insert(0, os.path.join(WS, "work", "peg"))
import hint_pe as H
A = H.load(H.SRC); B = H.load(H.PORT)

def rd(buf, va, n):
    fo = H.va_to_fo(va)
    return buf[fo:fo+n] if fo is not None else b''

def s(buf, va):
    fo = H.va_to_fo(va)
    if fo is None: return '<no-file>'
    e = buf.find(b'\x00', fo, fo+200)
    try:
        return buf[fo:e].decode('cp936', 'replace')
    except Exception:
        return repr(buf[fo:e])

for va in (0x48F614, 0x48F624, 0x4A42EC, 0x48F310, 0x4AF5B8, 0x4A96E8, 0x4CCE30, 0x69CF30, 0x4AF320, 0x69ED30):
    print('STR 0x%X = %r' % (va, s(A, va)[:90]))

print('--- table 0x4A96E8 stride 0xF, 24 records (SRC | PORT) ---')
for k in range(24):
    va = 0x4A96E8 + k * 0xF
    a = rd(A, va, 0xF); b = rd(B, va, 0xF)
    wa = [int.from_bytes(a[i:i+2], 'little') for i in range(0, 14, 2)]
    wb = [int.from_bytes(b[i:i+2], 'little') for i in range(0, 14, 2)]
    print(' 0x%X %s %s  %s' % (va, ' '.join('%5d' % v for v in wa), '|', ' '.join('%5d' % v for v in wb)))

print('--- table 0x48F310 stride 0x24, 12 records ---')
for k in range(12):
    va = 0x48F310 + k * 0x24
    a = rd(A, va, 0x24); b = rd(B, va, 0x24)
    print(' 0x%X %s  |DIFF| %s' % (va, a[:18].hex(), 'YES' if a != b else 'no'))

print('--- 0x4A42EC raw (SRC) ---')
print(rd(A, 0x4A42E0, 0x40).hex())
print('--- 0x498D30 raw (SRC) ---')
print(rd(A, 0x498D30, 0x28).hex())
print('--- 0x498D30 raw (PORT) ---')
print(rd(B, 0x498D30, 0x28).hex())
