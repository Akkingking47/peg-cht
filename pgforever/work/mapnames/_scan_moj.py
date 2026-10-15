# -*- coding: utf-8 -*-
import sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import place_tools as T
seen = {}
for p in T.find_mapnames():
    raw = open(p,'rb').read()
    n = struct.unpack_from('<H', raw, 0)[0]
    fmt = T.detect_format(raw, n)
    for i in range(14, n):
        off = 2 + i*20
        if off+20 > len(raw): break
        blk = raw[off:off+20]
        nm = blk.split(b'\x00')[0] if fmt=='A' else blk[:17].rstrip(b' ')
        try: nm.decode('utf-8')
        except UnicodeDecodeError:
            seen.setdefault(nm, set()).add(p.split('\\')[-2])
for v, c in sorted(seen.items()):
    print(repr(v), sorted(c))
