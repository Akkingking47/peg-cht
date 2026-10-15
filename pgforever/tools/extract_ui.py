# -*- coding: utf-8 -*-
r"""
UI 层文本提取 v2
- 源：backup\origin\Default\UI（原文备份，绝不用已被 POC 改动的现网文件）
- 分类 kind:
    text   需翻译的界面文案
    keep   保留原文（人名/公司名/文件路径/单字母键位/组合键/HTML 实体/纯数字）
- 输出 work\ui\strings.json，并打印短串上下文供人工复核（防止误替换）
"""
import json
import os
import re

SRC_DIR = r'D:\DSH\军事游戏汉化\pgforever\backup\origin\Default\UI'
OUT = r'D:\DSH\军事游戏汉化\pgforever\work\ui\strings.json'

# 保留原文的判定规则
RE_KEY = re.compile(r'^(Esc|Tab|Enter|Space|Ctrl\+.*|Alt\+.*|Shift\+.*|[A-Z]|F\d+)$')
RE_ENTITY = re.compile(r'^(&nbsp;|&#\d+;|&amp;)+$')
RE_NUM = re.compile(r'^[\s\d\(\)\-\.c©:/]+$', re.I)
RE_PATH = re.compile(r'^[A-Za-z0-9_\-\\/\.]+\.(png|bmp|css|htm|wav|mp3|cur|ico|jpg|gif)$', re.I)
RE_CAMEL = re.compile(r'^[A-Za-z]+(_?[A-Z][a-z]+)+$')
RE_CSSVAL = re.compile(r'^(none|auto|default|center|left|right|top|bottom|hidden|visible|transparent|expand|screen|no-repeat|contrast-screen|min-intrinsic|100%|h-flow|v-flow|scroll|radio|checkbox|select|hslider|mpegvideo|OK|ok)$', re.I)

# 人名 / 公司名（保留原文）
KEEP_NAMES = {
    'Alexander Shargin', 'Terra Informatica Software, Inc.', 'Strategic Simulations Inc.',
    'Kresimir Cuturic', 'Luis Guzman', 'Dean Skallerud', 'Eric Peterson', 'Pepa Drobny',
    'Julian Simko', 'Allied General Workshop', 'Radovan Nesic', 'Robert Mary',
    'Fred Chlanda', 'Charles Tyson', 'Larry Widing',
}
# 样例数据（装备名/单位名，非界面文案）
KEEP_SAMPLE = {'Wehr Inf', 'Opel 6700'}


def classify(s):
    if s in KEEP_NAMES or s in KEEP_SAMPLE:
        return 'keep'
    if RE_KEY.match(s) or RE_ENTITY.match(s) or RE_PATH.match(s) or RE_CAMEL.match(s):
        return 'keep'
    if RE_CSSVAL.match(s):
        return 'keep'
    if RE_NUM.match(s):
        return 'keep'
    return 'text'


records = []
files = sorted(f for f in os.listdir(SRC_DIR) if f.lower().endswith(('.htm', '.html')))
print('扫描源: %d 个 htm（来自 backup/origin）' % len(files))

for fn in files:
    txt = open(os.path.join(SRC_DIR, fn), 'rb').read().decode('utf-8', 'replace').lstrip('\ufeff')
    clean = re.sub(r'<style[^>]*>.*?</style>', lambda m: '\n' * m.group(0).count('\n'), txt, flags=re.S | re.I)
    clean = re.sub(r'<!--.*?-->', lambda m: '\n' * m.group(0).count('\n'), clean, flags=re.S)
    for ln, line in enumerate(clean.split('\n'), 1):
        for m in re.finditer(r'\b(title|alt|placeholder|label)\s*=\s*"([^"]+)"', line, re.I):
            val = m.group(2).strip()
            if val and re.search(r'[A-Za-z]', val):
                records.append({'file': fn, 'line': ln, 'en': val, 'kind': classify(val)})
        seg_line = re.sub(r'<[^>]+>', '\x00', line)
        for seg in seg_line.split('\x00'):
            seg = seg.strip()
            if not seg or not re.search(r'[A-Za-z]', seg) or len(seg) > 200:
                continue
            records.append({'file': fn, 'line': ln, 'en': seg, 'kind': classify(seg)})

merged = {}
for r in records:
    key = (r['file'], r['en'])
    if key in merged:
        merged[key]['lines'].append(r['line'])
    else:
        merged[key] = {'file': r['file'], 'en': r['en'], 'kind': r['kind'], 'lines': [r['line']]}

items = sorted(merged.values(), key=lambda x: (x['file'], x['lines'][0]))
for i, it in enumerate(items):
    it['id'] = i
    it['zh'] = ''
    it['lines'] = sorted(set(it['lines']))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(items, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

need = [it for it in items if it['kind'] == 'text']
keep = [it for it in items if it['kind'] == 'keep']
print('总计 %d 条：需翻译 %d 条，保留原文 %d 条' % (len(items), len(need), len(keep)))
print('-> %s' % OUT)

print()
print('=== 保留原文的条目（核对是否误判）===')
for it in keep:
    print('  %-18s %-32r' % (it['file'], it['en']))

print()
print('=== 短串（<=6 字符）需人工确认上下文 ===')
for it in need:
    if len(it['en']) <= 6:
        fp = os.path.join(SRC_DIR, it['file'])
        t = open(fp, 'rb').read().decode('utf-8', 'replace').lstrip('\ufeff')
        cl = re.sub(r'<style[^>]*>.*?</style>', lambda m: '\n' * m.group(0).count('\n'), t, flags=re.S | re.I)
        lines = cl.split('\n')
        for L in it['lines'][:2]:
            print('  %-16s L%-4d %-8r  |  %s' % (it['file'], L, it['en'], lines[L-1].strip()[:108]))
