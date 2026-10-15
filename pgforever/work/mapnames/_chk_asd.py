# -*- coding: utf-8 -*-
import sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
import place_tools as T
for p in T.find_mapnames():
    raw = open(p,'rb').read()
    n = struct.unpack_from('<H', raw, 0)[0]
    if T.detect_format(raw, n) == 'B': continue
    for i in range(14, n):
        off = 2 + i*20
        if off+20 > len(raw): break
        nm = raw[off:off+20].split(b'\x00')[0]
        try: s = nm.decode('utf-8')
        except UnicodeDecodeError: continue
        if s.strip() in ('a', 'asd', 'Empty', 'Lake', '??', '???', '1', '9', '888888'):
            print('%-40s rec=%-5d %r' % (p.replace(r'D:/PGForever1.021','')[:40], i, s))
