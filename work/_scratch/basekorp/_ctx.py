# -*- coding: utf-8 -*-
import io, re, sys
rows = [l.rstrip('\n').split('\t') for l in io.open('_xscn-todo.tsv', encoding='utf-8')][1:]
srcs = [(r[0].strip(), int(r[1])) for r in rows]
for tok in sys.argv[1:]:
    hits = [(s,f) for s,f in srcs if re.search(r'(?<![A-Za-z0-9])%s(?![A-Za-z0-9])' % re.escape(tok), s)]
    hits.sort(key=lambda x: -x[1])
    print('### %s  唯一 %d  实例 %d' % (tok, len(hits), sum(f for _,f in hits)))
    for s,f in hits[:14]: print('   %4d  %s' % (f, s))
    print()
