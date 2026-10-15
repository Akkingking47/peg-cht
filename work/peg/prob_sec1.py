# -*- coding: utf-8 -*-
# read-only: inspect the three candidate clusters for the secondary-UI problems.
import sys
sys.path.insert(0, r'D:\DSH\军事游戏汉化\work\peg')
import hint_pe as H
import capstone

A = H.load(H.SRC); B = H.load(H.PORT)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

def dis(lo, hi):
    va = lo
    while va < hi:
        fo = H.va_to_fo(va)
        if fo is None: break
        it = next(md.disasm(A[fo:fo+16], va, count=1), None)
        if it is None:
            va += 1; continue
        print('  0x%X  %-24s %s' % (va, A[fo:fo+it.size].hex(), it.mnemonic + ' ' + it.op_str))
        va += it.size

# build call map
CALLERS = {}
i = 0
end = H.va_to_fo(0x401000) + H.va_to_fo(0x48A136) - H.va_to_fo(0x401000)
end = H.va_to_fo(0x401000) + 0x8A136
i = H.va_to_fo(0x401000)
while i < end - 5:
    if A[i] == 0xE8:
        rel = int.from_bytes(A[i+1:i+5], 'little', signed=True)
        CALLERS.setdefault(H.fo_to_va(i) + 5 + rel, []).append(H.fo_to_va(i))
        i += 5
    else:
        i += 1

for t in (0x41407A, 0x414132, 0x413512, 0x4136AA, 0x46C97B, 0x46FB54, 0x4700C6, 0x414500):
    print('CALLERS 0x%X -> %s' % (t, [hex(c) for c in CALLERS.get(t, [])]))

print('--- 0x414520..0x4146A0 (stride-800 pixel writer) ---')
dis(0x414520, 0x4146A0)
print('--- 0x4146C0..0x414720 ---')
dis(0x4146C0, 0x414720)
print('--- 0x41407A..0x414160 (func head) ---')
dis(0x41407A, 0x414160)
print('--- 0x414132..0x4141C0 (func head 2) ---')
dis(0x414132, 0x4141C0)
print('--- 0x46CEF0..0x46CF80 ---')
dis(0x46CEF0, 0x46CF80)
print('--- 0x4700C6..0x470115 ---')
dis(0x4700C6, 0x470115)
