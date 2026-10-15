# -*- coding: utf-8 -*-
import io, re, sys, collections
rows=[l.rstrip('\n').split('\t') for l in io.open('bk-xscn-map.tsv',encoding='utf-8-sig')][1:]
for tok in sys.argv[1:]:
    hits=[(s,d) for s,d,n in rows if re.search(r'(?<![\w])%s(?![\w])'%re.escape(tok), s)]
    kept=[x for x in hits if tok in x[1]]
    # 未保留的：看看换成了什么（取该 token 在 src 里的上下文窗口，在 dst 里找对应片段）
    print('### %s  共 %d；仍保留原文 %d；已译 %d' % (tok, len(hits), len(kept), len(hits)-len(kept)))
    seen=collections.Counter()
    for s,d in hits:
        m=re.search(r'(?<![\w])%s(?![\w])'%re.escape(tok), s)
        a=max(0,m.start()-6); b=min(len(s),m.end()+6)
        ctx_s=s[a:b]
        # 在 dst 里找与 ctx_s 左右锚点对应的片段
        la=s[a:m.start()]; ra=s[m.end():b]
        seen[ctx_s]+=1
    for s,d in hits[:10]:
        print('   %-38s -> %s' % (s[:38], d[:46]))
    print()
