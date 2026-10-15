# -*- coding: utf-8 -*-
import io, re, collections, random
rows = [l.rstrip('\n').split('\t') for l in io.open('_xscn-todo.tsv', encoding='utf-8')][1:]
srcs = [(r[0].strip(), int(r[1]), r[2]) for r in rows]
random.seed(7)
print('=== 随机样本 120 ===')
for t,f,ex in random.sample(srcs, 120):
    print('%5d  %s' % (f, t))
print()
# 有多少含数字
withd = [x for x in srcs if re.search(r'\d', x[0])]
print('含数字 %d / %d' % (len(withd), len(srcs)))
print('=== 含数字样本 60 ===')
for t,f,ex in random.sample(withd, 60):
    print('%5d  %s' % (f, t))
