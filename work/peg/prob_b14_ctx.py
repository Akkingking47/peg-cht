# -*- coding: utf-8 -*-
# read-only: print short context around each UNPATCHED 0x320/0x258/0x31f/0x257 site,
# with containing-function guess (scan back for 55 8B EC) and callers of that function.
import sys, re

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
import os
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────

sys.path.insert(0, os.path.join(WS, "work", "peg"))
import hint_pe as H

SRC = H.SRC
PORT = H.PORT
A = H.load(SRC); B = H.load(PORT)

SITES = [0x405C1F,0x408835,0x414529,0x414649,0x414668,0x4146E8,0x417703,0x42041E,
         0x45E741,0x46B2AB,0x46CF45,0x4700DD,0x4888F9,0x491118,
         0x40E743,0x414533,0x467299,0x46795E,0x46CF4E,0x4700E4,0x49111C]

def funcstart(va, limit=0x600):
    best = None
    x = va - 3
    while x >= va - limit:
        fo = H.va_to_fo(x)
        if fo is None:
            x -= 1; continue
        if A[fo] == 0x55 and A[fo+1] == 0x8B and A[fo+2] == 0xEC:
            best = x
        x -= 1
    return best

import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False

def dis1(va):
    fo = H.va_to_fo(va)
    if fo is None: return None
    it = next(md.disasm(A[fo:fo+15], va, count=1), None)
    return it

def disasm_range(lo, hi, maxn=60):
    out = []
    va = lo
    n = 0
    while va < hi and n < maxn:
        fo = H.va_to_fo(va)
        if fo is None: break
        it = next(md.disasm(A[fo:fo+15], va, count=1), None)
        if it is None:
            va += 1; continue
        out.append((va, it.mnemonic+' '+it.op_str))
        va += it.size; n += 1
    return out

# callers map: find 'call rel32' targets
CALLERS = {}
i = 0
TEXT_FO = H.va_to_fo(0x401000)
end = TEXT_FO + 0x8A136
while i < end - 5:
    if A[i] == 0xE8:
        rel = int.from_bytes(A[i+1:i+5], 'little', signed=True)
        tgt = H.fo_to_va(i) + 5 + rel
        CALLERS.setdefault(tgt, []).append(H.fo_to_va(i))
        i += 5
    else:
        i += 1

for s in SITES:
    fs = funcstart(s)
    print('=' * 70)
    print('SITE imm@0x%X  src=%s' % (s, A[s:s+4].hex()), ' B=%s' % B[s:s+4].hex(), 'SAME' if A[s:s+4]==B[s:s+4] else 'DIFF')
    it = dis1(s-2) if True else None
    # print 3 insns before through 3 after
    lo = s - 24
    seq = disasm_range(lo, s+18, 40)
    for va, t in seq:
        mark = '  <== imm site' if s-4 <= va <= s+4 else ''
        print('  0x%X  %s%s' % (va, t, mark))
    print('  func_start_guess=0x%X  callers_of_that=%s' % (fs or 0, [hex(c) for c in CALLERS.get(fs, [])][:8]))
