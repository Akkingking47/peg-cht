# -*- coding: utf-8 -*-
import io, re, collections
rows = [l.rstrip('\n').split('\t') for l in io.open('_xscn-todo.tsv', encoding='utf-8')][1:]
srcs = [(r[0], int(r[1]), r[2]) for r in rows]
NUM = re.compile(r'^[\d/\-\.\s]+$')
ABBR = re.compile(r'^[A-Za-z][A-Za-z0-9\.\-/]{0,5}$')
cls = collections.Counter(); freq = collections.Counter()
samples = collections.defaultdict(list)
for s, f, ex in srcs:
    t = s.strip()
    if not t:                      k='空'
    elif NUM.match(t):             k='纯数字/编号'
    elif ABBR.match(t):            k='短缩写(<=6)'
    elif len(t) <= 3:              k='其它<=3'
    else:                          k='待译正文'
    cls[k] += 1; freq[k] += f
    if len(samples[k]) < 25: samples[k].append((t, f))
print('%-14s %8s %8s' % ('类别','唯一','实例'))
for k in ['待译正文','短缩写(<=6)','纯数字/编号','其它<=3','空']:
    print('%-14s %8d %8d' % (k, cls[k], freq[k]))
print()
for k in ['短缩写(<=6)','待译正文']:
    print('=== %s 样本 ===' % k)
    for t,f in samples[k]: print('  %5d  %s' % (f,t))
