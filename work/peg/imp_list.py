# -*- coding: utf-8 -*-
"""List imports (name + IAT VA) for chosen DLLs; optionally find call sites.

usage: python imp_list.py [exe] [dll-substr]
Then:  python imp_list.py --calls [exe] <iat_va_hex>
"""
import sys

import pefile

EXE = r"D:\Program Files\PeG\PeG030.exe"
filt = ""

args = [a for a in sys.argv[1:]]
if args and not args[0].startswith("-") and args[0].lower().endswith(".exe"):
    EXE = args.pop(0)
if args and not args[0].startswith("-") and not args[0].startswith("0x"):
    filt = args.pop(0).lower()

pe = pefile.PE(EXE, fast_load=True)
pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])

if args and args[0] == "--calls":
    iat = int(args[1], 16)
    base = pe.OPTIONAL_HEADER.ImageBase
    pat = iat.to_bytes(4, "little")
    for s in pe.sections:
        d = s.get_data()
        va = base + s.VirtualAddress
        i = 0
        while True:
            i = d.find(pat, i)
            if i < 0:
                break
            print("  xref 0x%08x  rel 0x%08x" % (va + i, i))
            i += 1
    sys.exit(0)

for entry in pe.DIRECTORY_ENTRY_IMPORT:
    dll = entry.dll.decode("ascii", "replace")
    if filt and filt not in dll.lower():
        continue
    print("=== %s ===" % dll)
    for imp in entry.imports:
        nm = imp.name.decode("ascii", "replace") if imp.name else "(ord %d)" % imp.ordinal
        print("  %-34s IAT 0x%08x" % (nm, imp.address))
