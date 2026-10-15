# -*- coding: utf-8 -*-
"""imm_range.py <lo_hex> <hi_hex> [min_imm] [--exe path]
Print every instruction in [lo,hi) that carries a hex immediate >= min_imm.

Robust to a bad start offset: decodes one instruction at a time and advances a
single byte when decoding fails (marks the skipped bytes with '*').
"""
import re
import sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Program Files\PeG\PeG030.exe"
argv = sys.argv[1:]
if "--exe" in argv:
    i = argv.index("--exe")
    EXE = argv[i + 1]
    del argv[i:i + 2]
lo = int(argv[0], 16)
hi = int(argv[1], 16)
minimm = int(argv[2], 16) if len(argv) > 2 else 0x100

pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
for s in pe.sections:
    if s.Name.rstrip(b"\x00") == b".text":
        va0, data = base + s.VirtualAddress, s.get_data()
        break

md = Cs(CS_ARCH_X86, CS_MODE_32)
print("# %s  0x%x-0x%x  min imm 0x%x" % (EXE, lo, hi, minimm))
o = lo
skipped = 0
while o < hi:
    ins = list(md.disasm(data[o - va0:o - va0 + 15], o, count=1))
    if not ins:
        o += 1
        skipped += 1
        continue
    ins = ins[0]
    nums = [int(x, 16) for x in re.findall(r"0x([0-9a-f]+)", ins.op_str)]
    if any(x >= minimm for x in nums):
        mark = " *resync(%d)" % skipped if skipped else ""
        print("0x%06x  %-8s %s%s" % (ins.address, ins.mnemonic, ins.op_str, mark))
        skipped = 0
    o += ins.size
