# -*- coding: utf-8 -*-
"""find_mem.py <hexva> [maxhits] [--ctx N] -- linear-scan .text (skipping bad bytes) for instructions
that reference an absolute address (memory operand or immediate)."""
import re, sys
import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, Cs
EXE = r"D:\Program Files\PeG\PeG030.exe"
WRITERS = ("mov","add","sub","or","and","xor","inc","dec","not","neg")

def decode_all(md, data, va0):
    off = 0
    n = len(data)
    skipped = 0
    while off < n:
        one = list(md.disasm(data[off:off+16], va0 + off, count=1))
        if not one:
            off += 1
            skipped += 1
            continue
        ins = one[0]
        yield ins
        off += ins.size
    sys.stderr.write("bad bytes skipped: %d\n" % skipped)

def main():
    args = sys.argv[1:]
    target = int(args[0], 16)
    ctx = 0
    maxhits = 40
    if "--ctx" in args:
        ctx = int(args[args.index("--ctx")+1])
    rest = [a for a in args[1:] if not a.startswith("--") and a != str(ctx)]
    if rest:
        maxhits = int(rest[0])
    pat = re.compile(r"0x0*%x\b" % target, re.I)
    pe = pefile.PE(EXE, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    hits = 0
    for s in pe.sections:
        if not (s.Characteristics & 0x20000000):
            continue
        data = s.get_data()
        va0 = base + s.VirtualAddress
        pend = 0
        for ins in decode_all(md, data, va0):
            if pend > 0:
                print("            | 0x%-8x %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
                pend -= 1
                continue
            if pat.search(ins.op_str):
                tag = ""
                if re.match(r"^(byte|word|dword|qword) ptr \[0x", ins.op_str) and ins.mnemonic in WRITERS:
                    tag = "   <== WRITE"
                print("0x%-8x %-8s %-42s%s" % (ins.address, ins.mnemonic, ins.op_str, tag))
                hits += 1
                pend = ctx
                if hits >= maxhits:
                    print("-- stopped at maxhits")
                    return 0
    print("-- total %d" % hits)
    return 0

if __name__ == "__main__":
    sys.exit(main())
