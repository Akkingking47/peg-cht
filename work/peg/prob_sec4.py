# -*- coding: utf-8 -*-
# read-only: verify every proposed patch site: instruction VA, imm file VA, old bytes (SRC),
# current bytes (PORT), decoded value, proposed value.
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
import capstone
A = H.load(H.SRC); B = H.load(H.PORT)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True

# (comment, instruction VA, expected old value, proposed new value)
SITES = [
    ('viewport setter A push bottom', 0x45A0F1, 571, 1052),
    ('viewport setter A push right',  0x45A0F6, 799, 1919),
    ('viewport setter B push bottom', 0x45A94A, 571, 1052),
    ('viewport setter B push right',  0x45A94F, 799, 1919),
    ('edge test x (pred)',            0x4567C2, 799, 1919),
    ('edge test y (pred)',            0x4567DC, 599, 1079),
    ('edge test x (pred2)',           0x4568E0, 799, 1919),
    ('edge test y (pred2)',           0x4568FA, 599, 1079),
    ('scroll dir x == right edge',    0x456982, 799, 1919),
    ('scroll dir y == bottom edge',   0x456A3D, 599, 1079),
    ('dead-store [0x4A42EC]',         0x45696D, 799, 1919),
    ('fullscreen rect helper bottom', 0x42E496, 599, 1079),
    ('fullscreen rect helper right',  0x42E49B, 799, 1919),
    ('text layout rect right',        0x4700DA, 800, 1920),
    ('text layout rect bottom',       0x4700E1, 600, 1080),
    ('tile bounds x',                 0x46CF42, 800, 1920),
    ('tile bounds y',                 0x46CF4B, 600, 1080),
    ('dialog right (w/2)',            0x43BCAB, 400, 960),
    ('dialog center basis',           0x43BCF7, 400, 960),
    ('hint box left',                 0x43BBCA, 100, 660),
    ('hint box top',                  0x43BBD1, 10, 250),
    ('hint box right',                0x43BBD8, 700, 1260),
    ('hint box bottom',               0x43BBDF, 590, 830),
]

def insn_at(buf, va):
    fo = H.va_to_fo(va)
    if fo is None: return None, None, None
    it = next(md.disasm(buf[fo:fo+16], va, count=1), None)
    return it, fo, buf

for cmt, va, old, new in SITES:
    it, fo, _ = insn_at(A, va)
    if it is None:
        print('%-32s 0x%X  <no insn>' % (cmt, va)); continue
    ops = it.operands
    imm = None
    for o in ops:
        if o.type == capstone.x86.X86_OP_IMM:
            imm = o.imm; break
    ioff = it.encoding.imm_offset
    isz = it.encoding.imm_size
    imm_va = va + ioff
    fo2 = H.va_to_fo(imm_va)
    a = A[fo2:fo2+isz]; b = B[fo2:fo2+isz]
    bnew = new.to_bytes(isz, 'little')
    print('%-32s insn=0x%-7X %-26s imm@0x%-7X size=%d old=%s(cur=%s) dec=%s  -> new=%s %s' % (
        cmt, va, it.mnemonic + ' ' + it.op_str, imm_va, isz, a.hex(), b.hex(), imm, bnew.hex(),
        'OK' if (a == b and imm == old) else ('ALREADY-PATCHED' if a != b else 'MISMATCH')))
print()
fo = H.va_to_fo(0x4A4DE0)
print('rect copy 0x4A4DE0 SRC ', A[fo:fo+24].hex())
print('rect copy 0x4A4DE0 PORT', B[fo:fo+24].hex())
