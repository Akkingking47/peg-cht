# -*- coding: utf-8 -*-
"""梳理：C 桶 4 条的逐行明细（含用途/note，判定是真冲突还是用途分工）"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
LAY = r'D:\DSH\军事游戏汉化\glossary\layers'
KEYS = ['Air Transport', 'Naval Transport', 'AT', 'Air Defense', 'Entrenchment',
        'Fortification', 'Ranger', 'March', 'LUFT']


def load(f):
    hdr = None
    out = []
    for i, l in enumerate(io.open(os.path.join(LAY, f), encoding='utf-8')):
        if l.startswith('#'):
            if hdr is None:
                hdr = l.lstrip('# ').rstrip('\n').split('\t')
            continue
        if not l.strip():
            continue
        if hdr and l.split('\t')[0] in ('en', '层', '桶'):
            continue
        out.append(l.rstrip('\n').split('\t'))
    return hdr, out


for f in ('scope-glossary.tsv', 'common-glossary.tsv'):
    hdr, rows = load(f)
    print('=' * 16, f, '| 列:', hdr)
    for r in rows:
        if r[0] in KEYS:
            d = dict(zip(hdr, r))
            print('  %-16s | %-10s | %-30s | 用途=%-42s | status=%s | layer=%s | slot=%s'
                  % (d.get('en', '')[:16], d.get('zh', '')[:10], d.get('scope', '')[:30],
                     d.get('note', '')[:42], d.get('status', ''), d.get('layer', ''), d.get('slot', '')))
    print()

print('=' * 16, 'override.tsv 中这 4 条的登记')
hdr, rows = load('override.tsv')
print('  列:', hdr)
for r in rows:
    if r and r[0] in KEYS:
        print('  ', ' | '.join(x[:46] for x in r))
