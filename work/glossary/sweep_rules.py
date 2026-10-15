# -*- coding: utf-8 -*-
"""梳理：新裁定是否贯通到所有层
 ① 番号齐步译（.scn 已做）是否也落到 UI/EQP/DOCS 层
 ② DOCS 层（check_glossary.py 报 0 条规则 ⇒ 未被术语校验覆盖）
 ③ 禁用/作废词
"""
import io, os, re, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
WS = r'D:\DSH\军事游戏汉化'

ABBR = re.compile(r'\b(\d{1,3}(?:st|nd|rd|th))\s+'
                  r'(GIR|PIR|AB|AIR|Armd|Cav|Inf|Bde|Div|Para|SS|Pz|Gd|Mot|Mech|Rgt|Bn|Kav|Ski|Mtn|Mar|Eng|Sig|Recon|TD|AT)\b')
RULE = [('声望', '威望'), ('海军攻击', '对海杀伤'), ('空中出击', '空中任务'),
        ('前进观测官', '炮兵观测/前沿观测'), ('光荣胜利', '辉煌胜利'), ('国力', '威望')]


def scan(name, path, is_table):
    if not os.path.exists(path):
        print('  (缺) %s' % path)
        return
    ab = []
    ru = []
    for i, l in enumerate(io.open(path, encoding='utf-8', errors='replace')):
        if is_table:
            if l.startswith('#') or not l.strip():
                continue
            c = l.rstrip('\n').split('\t')
            zh = c[2] if len(c) > 2 else ''
            s = zh
        else:
            s = l.rstrip('\n')
        for m in ABBR.finditer(s):
            ab.append((i + 1, m.group(0)))
        for bad, good in RULE:
            if bad in s:
                ru.append((i + 1, bad, good, s.strip()[:80]))
    print('  %-34s 番号缩写残留 %-4d 旧译法 %d' % (name, len(ab), len(ru)))
    for x in ab[:6]:
        print('        行%-6s %s' % (x[0], x[1]))
    for x in ru[:6]:
        print('        行%-6s %s→%s   %s' % x)


print('=== ① 场景真源/成品 ===')
scan('ww2-scn-map.tsv', os.path.join(WS, 'pegww2', 'research', 'ww2-scn-map.tsv'), True)
print('=== ② UI / EQP / TIPS 层 ===')
for f in ('WW2Gui-map.tsv', 'WW2Misc-map.tsv', 'WW2Tips-map.tsv', 'ww2-eqp-map.tsv'):
    scan(f, os.path.join(WS, 'pegww2', 'research', f), True)
print('=== ③ 前作 PEG 层 ===')
scan('peg/research/gui030-zh.tsv', os.path.join(WS, 'peg', 'research', 'gui030-zh.tsv'), True)
print('=== ④ DOCS 层（73 成品）===')
dd = os.path.join(WS, 'pegww2', 'docs-zh')
tot_ab, tot_ru, files = 0, 0, 0
hits = collections.Counter()
for f in sorted(os.listdir(dd)):
    if not f.lower().endswith('.md'):
        continue
    files += 1
    p = os.path.join(dd, f)
    t = io.open(p, encoding='utf-8', errors='replace').read()
    a = ABBR.findall(t)
    r = [(b, g) for b, g in RULE if b in t]
    tot_ab += len(a)
    tot_ru += len(r)
    if a or r:
        print('  %-42s 番号 %-3d 旧译 %d' % (f, len(a), len(r)))
        for x in a[:4]:
            print('        ', ' '.join(x))
        for b, g in r[:4]:
            print('         %s→%s' % (b, g))
print('  DOCS 合计：%d 文件 · 番号残留 %d · 旧译法 %d' % (files, tot_ab, tot_ru))
