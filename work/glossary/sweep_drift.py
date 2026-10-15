# -*- coding: utf-8 -*-
"""梳理：C 桶待收敛 + 本作范围内的跨层漂移，逐条摊开"""
import io, os, sys, collections, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
LAY = r'D:\DSH\军事游戏汉化\glossary\layers'
MINE = re.compile(r'PEGWW2|PEG_BASE|PEG_UI|WW2')


def rows(f):
    out = []
    for i, l in enumerate(io.open(os.path.join(LAY, f), encoding='utf-8')):
        if i == 0 or l.startswith('#') or not l.strip():
            continue
        out.append(l.rstrip('\n').split('\t'))
    return out


print('#' * 12, 'C 桶：同家族待收敛（逐 scope 摊开）')
for f in rows('converge-list.tsv'):
    if f[0] != 'C同家族待收敛':
        continue
    print('\n◆ %s' % f[1])
    print('   各译法: %s' % f[2])
    print('   scopes: %s' % f[3])
    print('   理由  : %s' % (f[4] if len(f) > 4 else ''))

print('\n' + '#' * 12, '本作范围（PEGWW2_*/PEG_*/WW2*）内的漂移')
n = 0
for f in rows('common-drift.tsv'):
    if len(f) < 4:
        continue
    en, cat, grade, spans = f[0], f[1], f[2], f[3]
    parts = [p.strip() for p in spans.split('｜')]
    mine = [p for p in parts if MINE.search(p)]
    if len(mine) < 2:
        continue
    n += 1
    print('%2d ◆ %-24s [%s/%s]' % (n, en[:24], cat, grade))
    for p in parts:
        mark = '  ★' if MINE.search(p) else '   '
        print('    %s %s' % (mark, p[:110]))
print('\n  本作范围内漂移 %d 条' % n)
