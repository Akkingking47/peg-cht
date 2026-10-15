# -*- coding: utf-8 -*-
r"""
扫描全部 UI htm（Default + 各 game，源取 backup\origin），找出尚未纳入译表的可见文案。
输出：work\ui\missing.json 供补译。
"""
import json
import os
import re

B = r'D:\DSH\军事游戏汉化\pgforever\backup\origin'
TR = r'D:\DSH\军事游戏汉化\pgforever\work\ui\translations.json'
OUT = r'D:\DSH\军事游戏汉化\pgforever\work\ui\missing.json'

RE_KEY = re.compile(r'^(Esc|Tab|Enter|Space|Ctrl\+.*|Alt\+.*|Shift\+.*|[A-Z]|F\d+)$')
RE_ENTITY = re.compile(r'^(&nbsp;|&#\d+;|&amp;)+$')
RE_NUM = re.compile(r'^[\s\d\(\)\-\.c©:/]+$', re.I)
RE_PATH = re.compile(r'^[A-Za-z0-9_\-\\/\.]+\.(png|bmp|css|htm|wav|mp3|cur|ico|jpg|gif)$', re.I)
RE_CAMEL = re.compile(r'^[A-Za-z]+(_?[A-Z][a-z]+)+$')
RE_CSSVAL = re.compile(r'^(none|auto|default|center|left|right|top|bottom|hidden|visible|transparent|expand|screen|no-repeat|contrast-screen|min-intrinsic|100%|h-flow|v-flow|scroll|radio|checkbox|select|hslider|mpegvideo|OK|ok)$', re.I)
KEEP_NAMES = {'Alexander Shargin', 'Terra Informatica Software, Inc.', 'Strategic Simulations Inc.',
              'Kresimir Cuturic', 'Luis Guzman', 'Dean Skallerud', 'Eric Peterson', 'Pepa Drobny',
              'Julian Simko', 'Allied General Workshop', 'Radovan Nesic', 'Robert Mary',
              'Fred Chlanda', 'Charles Tyson', 'Larry Widing'}
KEEP_SAMPLE = {'Wehr Inf', 'Opel 6700'}

tr = json.load(open(TR, encoding='utf-8'))
GLOBAL = tr['global']
PER = tr['per_file']


def classify(s):
    if s in KEEP_NAMES or s in KEEP_SAMPLE:
        return 'keep'
    if RE_KEY.match(s) or RE_ENTITY.match(s) or RE_PATH.match(s) or RE_CAMEL.match(s) or RE_CSSVAL.match(s) or RE_NUM.match(s):
        return 'keep'
    return 'text'


targets = []
base = os.path.join(B, 'Default', 'UI')
targets.append(('Default', base))
for g in sorted(os.listdir(B)):
    gp = os.path.join(B, g, 'UI')
    if os.path.isdir(gp) and g != 'Default':
        targets.append((g, gp))

seen = {}
files_scanned = 0
for game, d in targets:
    for f in sorted(os.listdir(d)):
        if not f.lower().endswith('.htm'):
            continue
        files_scanned += 1
        txt = open(os.path.join(d, f), 'rb').read().decode('utf-8', 'replace').lstrip('\ufeff')
        clean = re.sub(r'<style[^>]*>.*?</style>', lambda m: '\n' * m.group(0).count('\n'), txt, flags=re.S | re.I)
        clean = re.sub(r'<!--.*?-->', lambda m: '\n' * m.group(0).count('\n'), clean, flags=re.S)
        for ln, line in enumerate(clean.split('\n'), 1):
            segs = []
            for m in re.finditer(r'\b(title|alt|placeholder|label)\s*=\s*"([^"]+)"', line, re.I):
                segs.append(m.group(2).strip())
            for s in re.sub(r'<[^>]+>', '\x00', line).split('\x00'):
                s = s.strip()
                if s and len(s) <= 200:
                    segs.append(s)
            for s in segs:
                if not re.search(r'[A-Za-z]', s):
                    continue
                if classify(s) != 'text':
                    continue
                key = (f, s)
                if key not in seen:
                    seen[key] = {'file': f, 'en': s, 'games': set(), 'lines': []}
                seen[key]['games'].add(game)
                seen[key]['lines'].append(ln)

missing = []
known = 0
for (f, s), v in sorted(seen.items()):
    if s in PER.get(f, {}) or s in GLOBAL:
        known += 1
        continue
    missing.append({'file': f, 'en': s, 'games': sorted(v['games'])[:6], 'n_games': len(v['games'])})

json.dump(missing, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('扫描 %d 个 htm（Default + 12 个 game UI）' % files_scanned)
print('去重后可见文案条目: %d，其中已译 %d，未译 %d' % (len(seen), known, len(missing)))
print('-> %s' % OUT)
print()
print('=== 未译条目（按出现文件分组）===')
cur = None
for m in sorted(missing, key=lambda x: (x['file'], x['en'])):
    if m['file'] != cur:
        cur = m['file']
        print()
        print('## %s' % cur)
    print('   %-46r  game数=%d %s' % (m['en'][:46], m['n_games'], m['games'][:4]))
