# -*- coding: utf-8 -*-
import io, os, sys, struct
sys.path.insert(0, '.')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import place_tools as T

for p in T.find_mapnames():
    raw = open(p, 'rb').read()
    n = struct.unpack_from('<H', raw, 0)[0]
    if T.detect_format(raw, n) != 'B':
        continue
    print('FORMAT B FILE:', p, 'N =', n, 'size =', len(raw))
    # 格式 B: 名称 + 空格补到 17 字节 + 3 字节排序键
    names = []
    for i in range(n):
        off = 2 + i * 20
        if off + 20 > len(raw): break
        rec = raw[off:off+20]
        nm = rec[:17].rstrip(b' ')
        try:
            s = nm.decode('utf-8')
        except UnicodeDecodeError:
            s = nm.decode('latin1')
        names.append((i, s, rec[17:20]))
    print('records:', len(names))
    for i, s, tail in names[:25]:
        print('%5d  %-20s tail=%s' % (i, repr(s), tail.hex()))
