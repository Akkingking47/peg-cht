# -*- coding: utf-8 -*-
"""量化 OLGWW2 .xscn 组1 番号串里的「编制单位名截断」问题。
对照 backup\ORIGINAL-EFILE_OLGWW2\SCENARIO 与生效目录，按 (gi,idx) 逐条对齐。
输出：glossary/xscn-division-trunc.tsv
"""
import os, sys, io, glob, collections, re

sys.path.insert(0, r'D:\DSH\军事游戏汉化\work\efile-nashornpbem')
from apply_residual import parse

OR = r'D:\DSH\军事游戏汉化\backup\ORIGINAL-EFILE_OLGWW2\SCENARIO'
NN = r'D:\OpenPG2\EFILE_OLGWW2\SCENARIO'

# 原文里表示「师」的缩写/词
DIV_TOK = re.compile(r'(?:^|/)\s*\d+\s*(?:Pz|Div|Division|Inf|Infantry|Mot|Mtn|Air|Cav)\b', re.I)

def g1(path):
    d, items, meta = parse(path)
    if not items:
        return {}
    out = {}
    for gi, idx, off, ln in items:
        if gi >= 1:
            out[(gi, idx)] = d[off + 2:off + 2 + ln]
    return out

tally = collections.Counter()
rows = []
for po in sorted(glob.glob(os.path.join(OR, '*.xscn'))):
    fn = os.path.basename(po)
    pn = os.path.join(NN, fn)
    if not os.path.exists(pn):
        continue
    o = g1(po); n = g1(pn)
    for key in sorted(set(o) & set(n)):
        ot = o[key].decode('cp1252', 'replace')
        nt = n[key].decode('gbk', 'replace')
        for seg_o, seg_n in zip(ot.split('/'), nt.split('/')):
            seg_o = seg_o.strip(); seg_n = seg_n.strip()
            if not seg_n:
                continue
            if not re.match(r'^第\d', seg_n):
                continue
            has_shi = '师' in seg_n
            # 原文这一段像「师」级吗
            looks_div = bool(re.match(r'^\d+\s*(?:Pz|Div|Inf|Mot|Mtn|Air|Cav)\b', seg_o, re.I))
            tally[(looks_div, has_shi)] += 1
            rows.append((fn, key[0], key[1], seg_o, seg_n, looks_div, has_shi))

print('原文像「师」/  译文含「师」  计数：')
for k in sorted(tally, key=lambda x: (-x[0], x[1])):
    print('   looks_div=%-5s has_shi=%-5s  %d' % (k[0], k[1], tally[k]))
print()
susp = [r for r in rows if r[5] and not r[6]]
print('原文像师、译文缺「师」的条目 %d 条，去重样例：' % len(susp))
seen = set()
for fn, g, i, so, sn, _, _ in susp:
    if sn in seen:
        continue
    seen.add(sn)
    if len(seen) <= 40:
        print('   %-14s g%d#%-4d  ORIG %-26s -> NOW %s' % (fn, g, i, so, sn))

with io.open(r'D:\DSH\军事游戏汉化\glossary\xscn-division-trunc.tsv', 'w',
             encoding='utf-8-sig', newline='') as f:
    f.write('file\tgroup\tidx\torig_seg\tnow_seg\tlooks_div\thas_shi\n')
    for r in rows:
        f.write('%s\t%d\t%d\t%s\t%s\t%s\t%s\n' % r)
print('\n明细 -> glossary/xscn-division-trunc.tsv（%d 行）' % len(rows))
