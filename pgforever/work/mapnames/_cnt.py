# -*- coding: utf-8 -*-
import sys, io, collections
import place_tools as T
sys.path.insert(0,'.')
sys.path.insert(0, r'D:/DSH/军事游戏汉化/pgforever/work/mapnames')
import check_place as C
names = C.load_source_names()
seg = collections.Counter()
for k in names:
    if T.has_cn(k): continue
    seg[k[:1].upper()] += 1
out = []
done = set('ABCD')
tot = 0
for s in sorted(seg):
    mark = '[x]' if s in done else '[ ]'
    out.append('%s %s : %d' % (mark, s, seg[s]))
    if s not in done: tot += seg[s]
out.append('未完成段合计 %d 条（去重后）' % tot)
sys.stderr.write('\n'.join(out) + '\n')
