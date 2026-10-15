# -*- coding: utf-8 -*-
"""梳理：ui5 槽位规则对现有译文的合规情况（含短名覆盖）"""
import io, os, re, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

WS = r'D:\DSH\军事游戏汉化'
LAY = os.path.join(WS, 'glossary', 'layers')
CJK = re.compile(r'[\u4e00-\u9fff]')


def hanzi(s):
    return len(CJK.findall(s))


def load(p):
    rows = []
    for i, l in enumerate(io.open(p, encoding='utf-8')):
        if l.startswith('#') or not l.strip():
            continue
        rows.append(l.rstrip('\n').split('\t'))
    return rows


sg = load(os.path.join(LAY, 'scope-glossary.tsv'))
hdr = None
for i, l in enumerate(io.open(os.path.join(LAY, 'scope-glossary.tsv'), encoding='utf-8')):
    if l.startswith('en\t'):
        hdr = l.rstrip('\n').split('\t')
        break
ix = {k: i for i, k in enumerate(hdr)}
print('scope-glossary 列:', hdr)

sh = load(os.path.join(LAY, 'short-glossary.tsv'))
sh_slot = collections.defaultdict(list)
for c in sh:
    if len(c) >= 6:
        sh_slot[(c[5], c[0])].append((c[1], c[2]))

ui5 = [r for r in sg if len(r) > ix['slot'] and r[ix['slot']] == 'ui5']
print('ui5 行数:', len(ui5))
over = [r for r in ui5 if hanzi(r[ix['zh']]) > 5]
print('超 5 汉字:', len(over))
cov = [r for r in over if (('ui5', r[ix['en']]) in sh_slot)]
unc = [r for r in over if (('ui5', r[ix['en']]) not in sh_slot)]
print('已有短名:', len(cov), ' 仍缺短名:', len(unc))
print()
print('--- 仍缺短名的 ui5 超长条目（按汉字数降序）---')
for r in sorted(unc, key=lambda r: -hanzi(r[ix['zh']])):
    print('%2d  %-42s %-26s %s' % (hanzi(r[ix['zh']]), r[ix['en']][:42], r[ix['zh']][:26], r[ix['scope']][:30]))
print()
print('--- 已有短名但短名仍超 5 汉字（短名本身不合规）---')
bad = 0
for k, v in sh_slot.items():
    if k[0] != 'ui5':
        continue
    for long_, short in v:
        if hanzi(short) > 5:
            bad += 1
            print('%2d  %-30s %s' % (hanzi(short), long_[:30], short))
print('  不合规短名:', bad)

out = os.path.join(WS, 'pegww2', 'research', 'evidence', 'ui5-todo.txt')
os.makedirs(os.path.dirname(out), exist_ok=True)
with io.open(out, 'w', encoding='utf-8') as f:
    f.write('# ui5 槽位梳理：超 5 汉字且无短名的 UI 短标签（%d 条）\n' % len(unc))
    f.write('汉字数\t原文\t现译文\t范围\n')
    for r in sorted(unc, key=lambda r: -hanzi(r[ix['zh']])):
        f.write('%d\t%s\t%s\t%s\n' % (hanzi(r[ix['zh']]), r[ix['en']], r[ix['zh']], r[ix['scope']]))
print('\n清单 →', out)
