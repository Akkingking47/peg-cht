# -*- coding: utf-8 -*-
import io, re, collections
rows = [l.rstrip('\n').split('\t') for l in io.open('_xscn-todo.tsv', encoding='utf-8')][1:]
srcs = [(r[0].strip(), int(r[1])) for r in rows]
TOK = re.compile(r"[A-Za-z\u0080-\u00ff][A-Za-z0-9\u0080-\u00ff\.'\-]*|\d+")
cnt = collections.Counter(); doc = collections.Counter()
for s,f in srcs:
    seen = set()
    for t in TOK.findall(s):
        cnt[t] += f
        if t not in seen:
            doc[t] += 1; seen.add(t)
print('总 token 种类 %d' % len(cnt))
print('%-16s %8s %8s' % ('token','实例','唯一串'))
for t,c in cnt.most_common(200):
    print('%-16s %8d %8d' % (t, c, doc[t]))
with io.open('_tokens.tsv','w',encoding='utf-8',newline='') as fo:
    fo.write('token\tfreq\tdocs\r\n')
    for t,c in cnt.most_common():
        fo.write('%s\t%d\t%d\r\n' % (t,c,doc[t]))
