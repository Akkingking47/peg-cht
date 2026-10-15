# -*- coding: utf-8 -*-
import sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import place_tools as T
for p in T.find_mapnames():
    raw = open(p,'rb').read()
    n = struct.unpack_from('<H', raw, 0)[0]
    sp = nul = other = 0
    for i in range(14, n):
        off = 2 + i*20
        if off+20 > len(raw): break
        blk = raw[off:off+20]
        if blk[-1] == 0 and blk[-2] == 0: nul += 1
        if b'  ' in blk[:17]: sp += 1
    g = p.replace(r'D:/PGForever1.021','').split('\\')[1]
    print('%-34s N=%-5d nul=%-5d sp=%-5d -> %s' % (g[:34], n, nul, sp, 'B' if sp>nul else 'A'))
