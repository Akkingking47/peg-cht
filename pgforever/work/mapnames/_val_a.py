# -*- coding: utf-8 -*-
import sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
import place_tools as T
import place_A as A
import place_mojibake as M

names = {}
for p in T.find_mapnames():
    raw = open(p,'rb').read()
    n = struct.unpack_from('<H', raw, 0)[0]
    fmt = T.detect_format(raw, n)
    if fmt == 'B':
        continue                      # ★ B 格式文件单独处理，不混入 A 段
    for i in range(14, n):
        off = 2 + i*20
        if off+20 > len(raw): break
        nm = raw[off:off+20].split(b'\x00')[0]
        try: s = nm.decode('utf-8')
        except UnicodeDecodeError: continue
        if s: names[s] = names.get(s, 0) + 1

seg = sorted(k for k in names if k[:1].upper() == 'A')
tbl = dict(A.PLACE_A)
over = [(k, v, T.zb(v)) for k, v in tbl.items() if not T.fits(v)]
nocn = [(k, v) for k, v in tbl.items() if not T.has_cn(v)]
missing = sorted(set(seg) - set(tbl) - set(M.MOJIBAKE.keys()))
extra = sorted(set(tbl) - set(seg))
print('A段实际 %d 条，译表 %d 条' % (len(seg), len(tbl)))
print('超长 %d' % len(over))
print('无中文 %d: %s' % (len(nocn), nocn))
print('未覆盖 %d:' % len(missing))
for m in missing: print('   ', repr(m))
print('译表多余(源中不存在) %d:' % len(extra))
for e in extra[:20]: print('   ', repr(e))
