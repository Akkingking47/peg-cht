# -*- coding: utf-8 -*-
# read-only: sweep .data for rect-like word tuples (x1,y1,x2,y2) that are 800x600-era
# and NOT patched in v10b. Focus on panel-sized rects.
import sys
sys.path.insert(0, r'D:\DSH\军事游戏汉化\work\peg')
import hint_pe as H
A = H.load(H.SRC); B = H.load(H.PORT)

DATA_VA = 0x48E000
DATA_FO = H.va_to_fo(DATA_VA)
DATA_LEN = 0x21400

hits = []
d = A[DATA_FO:DATA_FO+DATA_LEN]
db = B[DATA_FO:DATA_FO+DATA_LEN]
for o in range(0, DATA_LEN - 8, 2):
    x1 = int.from_bytes(d[o:o+2], 'little'); y1 = int.from_bytes(d[o+2:o+4], 'little')
    x2 = int.from_bytes(d[o+4:o+6], 'little'); y2 = int.from_bytes(d[o+6:o+8], 'little')
    if not (0 <= x1 < x2 <= 800 and 0 <= y1 < y2 <= 600):
        continue
    w = x2 - x1; h = y2 - y1
    if w < 150 or h < 120:
        continue
    if x1 < 5 or y1 < 5:
        continue
    same = d[o:o+8] == db[o:o+8]
    hits.append((DATA_VA + o, x1, y1, x2, y2, w, h, same))

# collapse near-duplicate overlapping hits (same tuple reported at multiple starts)
seen = set()
out = []
for va, x1, y1, x2, y2, w, h, same in hits:
    key = (x1, y1, x2, y2)
    if key in seen:
        continue
    seen.add(key)
    out.append((va, x1, y1, x2, y2, w, h, same))

print('unique panel-ish rects in .data: %d' % len(out))
for va, x1, y1, x2, y2, w, h, same in out:
    print('  0x%X  (%4d,%4d)-(%4d,%4d)  %4dx%4d  %s' % (va, x1, y1, x2, y2, w, h, 'SAME(未补)' if same else 'DIFF(已补)'))
