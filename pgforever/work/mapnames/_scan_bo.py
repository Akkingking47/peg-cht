# -*- coding: utf-8 -*-
import sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import place_tools as T
bad = {}
for p in T.find_mapnames():
    raw = open(p,'rb').read()
    n = struct.unpack_from('<H', raw, 0)[0]
    fmt = T.detect_format(raw, n)
    for i in range(14, n):
        off = 2 + i*20
        if off+20 > len(raw): break
        blk = raw[off:off+20]
        if fmt == 'A':
            nm = blk.split(b'\x00')[0]
        else:
            nm = blk[:17].rstrip(b' ')
        try:
            nm.decode('utf-8')
        except UnicodeDecodeError:
            bad[nm] = bad.get(nm, 0) + 1
print('非UTF-8名称数:', len(bad))
for v, c in sorted(bad.items(), key=lambda x:-x[1]):
    print(c, v.hex(' '), repr(v))
