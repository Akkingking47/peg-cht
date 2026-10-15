# -*- coding: utf-8 -*-
import io, re, collections
rows = [l.rstrip('\n').split('\t') for l in io.open('_xscn-todo.tsv', encoding='utf-8')][1:]
srcs = [(r[0].strip(), int(r[1])) for r in rows]
SUF = re.compile(r'(?<=[0-9])([A-Za-z][A-Za-z\.]*)')
c = collections.Counter(); doc = collections.Counter()
for s,f in srcs:
    seen=set()
    for m in SUF.findall(s):
        c[m]+=f
        if m not in seen: doc[m]+=1; seen.add(m)
print('后缀种类 %d' % len(c))
print('%-14s %7s %7s' % ('suffix','实例','唯一'))
for k,v in c.most_common(150):
    print('%-14s %7d %7d' % (k, v, doc[k]))
with io.open('_suffix.tsv','w',encoding='utf-8',newline='') as f:
    f.write('suffix\tfreq\tdocs\r\n')
    for k,v in c.most_common():
        f.write('%s\t%d\t%d\r\n' % (k,v,doc[k]))
