# -*- coding: utf-8 -*-
"""xr.py — 交叉引用工具
  xr.py call <target_va>            # 列出所有 call target 的站点
  xr.py dword <data_va>             # 列出所有出现在 .text 里的 dword 引用
  xr.py push <imm>                  # 列出所有 push imm32 == imm 的站点
  xr.py near <va> <radius>          # 列出该 VA 附近的反汇编
  xr.py diff <va> <len>             # SRC vs PORT 逐字节 diff
"""
import struct
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

b = H.load(H.SRC)
p = H.load(H.PORT)
fo = H.va_to_fo(H.TEXT_VA)
blob = b[fo:fo + H.TEXT_SIZE]
pblob = p[fo:fo + H.TEXT_SIZE]

cmd = sys.argv[1]


def callers(tgt):
    for off in range(len(blob) - 5):
        if blob[off] == 0xE8:
            rel = struct.unpack_from("<i", blob, off + 1)[0]
            if H.TEXT_VA + off + 5 + rel == tgt:
                yield H.TEXT_VA + off


def jmps(tgt):
    for off in range(len(blob) - 5):
        if blob[off] == 0xE9:
            rel = struct.unpack_from("<i", blob, off + 1)[0]
            if H.TEXT_VA + off + 5 + rel == tgt:
                yield H.TEXT_VA + off


if cmd == "call":
    t = int(sys.argv[2], 16)
    print("callers of 0x%06X:" % t)
    for a in callers(t):
        print("  0x%06X" % a)
    print("jmp to 0x%06X:" % t)
    for a in jmps(t):
        print("  0x%06X" % a)

elif cmd == "dword":
    t = int(sys.argv[2], 16)
    nd = struct.pack("<I", t)
    i = -1
    n = 0
    while True:
        i = blob.find(nd, i + 1)
        if i < 0:
            break
        n += 1
        print("  .text 0x%06X   ctx %s" % (H.TEXT_VA + i, blob[max(0, i - 10):i + 4].hex(" ")))
    print("  total .text hits: %d" % n)

elif cmd == "push":
    t = int(sys.argv[2], 16)
    nd = struct.pack("<I", t)
    i = -1
    while True:
        i = blob.find(b"\x68" + nd, i + 1)
        if i < 0:
            break
        print("  push 0x%X at 0x%06X" % (t, H.TEXT_VA + i))

elif cmd == "near":
    va = int(sys.argv[2], 16)
    r = int(sys.argv[3], 16)
    for i in H.dis_all(va, va + r, b):
        print("0x%06X  %-26s %s %s" % (i.address, H.blob(b, i.address, i.size).hex(" "), i.mnemonic, i.op_str))

elif cmd == "diff":
    va = int(sys.argv[2], 16)
    ln = int(sys.argv[3], 16)
    o = H.va_to_fo(va)
    same = True
    for k in range(ln):
        x = b[o + k]
        y = p[o + k]
        if x != y:
            same = False
            print("  0x%06X  SRC %02x  PORT %02x" % (va + k, x, y))
    if same:
        print("  [%d bytes identical]" % ln)

elif cmd == "find":
    # find decoded instructions whose op_str contains the regex
    import re
    rx = re.compile(sys.argv[2])
    for i in H.dis_all(H.TEXT_VA, H.TEXT_VA + H.TEXT_SIZE, b):
        t = i.mnemonic + " " + i.op_str
        if rx.search(t):
            print("0x%06X  %-26s %s" % (i.address, H.blob(b, i.address, i.size).hex(" "), t))
