# -*- coding: utf-8 -*-
"""vtcalls.py <off> [<off> ...]
Find every `call dword ptr [reg + off]` (vtable method call) in .text and print
the call VA with the few instructions leading up to it.

DirectDraw vtable slots (IDirectDraw):
  0x10 CreateClipper  0x14 CreatePalette  0x18 CreateSurface  0x1C DuplicateSurface
  0x20 EnumDisplayModes 0x2C GetCaps  0x30 GetDisplayMode  0x38 GetGDISurface
  0x40 GetScanLine    0x4C RestoreDisplayMode  0x50 SetCooperativeLevel
  0x54 SetDisplayMode 0x58 WaitForVerticalBlank
IDirectDrawSurface:
  0x14 Blt  0x18 BltBatch  0x1C BltFast  0x2C Flip  0x30 GetAttachedSurface
  0x40 GetColorKey  0x44 GetDC  0x54 GetPixelFormat  0x58 GetSurfaceDesc
  0x60 IsLost  0x64 Lock  0x68 ReleaseDC  0x6C Restore  0x70 SetClipper
  0x74 SetColorKey  0x78 SetOverlayPosition  0x7C SetPalette  0x80 Unlock
"""
import sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Program Files\PeG\PeG030.exe"
pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
va0, data = None, None
for s in pe.sections:
    if s.Name.rstrip(b"\x00") == b".text":
        va0 = base + s.VirtualAddress
        data = s.get_data()
if data is None:
    sys.exit("no .text")

want = set(int(a, 16) for a in sys.argv[1:]) or {0x18}
md = Cs(CS_ARCH_X86, CS_MODE_32)
hits = {}
for i in range(len(data) - 3):
    if data[i] != 0xFF:
        continue
    m = data[i + 1]
    if 0x50 <= m <= 0x57:
        off, disp = data[i + 2], 8
    elif 0x90 <= m <= 0x97:
        off, disp = int.from_bytes(data[i + 2:i + 6], "little"), 32
    else:
        continue
    if off in want:
        hits.setdefault(off, []).append((va0 + i, disp))

for off in sorted(hits):
    sites = hits[off]
    print("=== +0x%02x : %d site(s)" % (off, len(sites)))
    for a, disp in sorted(sites):
        st = a - 18
        ins = list(md.disasm(data[st - va0:a - va0 + 6], st))
        txt = " | ".join("%s %s" % (x.mnemonic, x.op_str) for x in ins[-4:])
        print("  0x%06x (disp%d)  %s" % (a, disp, txt))
