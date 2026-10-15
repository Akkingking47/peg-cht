# -*- coding: utf-8 -*-
import io, re
rows = [l.rstrip('\n').split('\t') for l in io.open('_tokens.tsv', encoding='utf-8')][1:]
out = []
for tok, freq, docs in rows:
    freq=int(freq); docs=int(docs)
    if re.fullmatch(r'\d+', tok): continue          # 纯数字 -> 结构规则处理
    if tok.lower() in ('th','st','nd','rd'): continue # 序数后缀
    if docs < 2: continue
    out.append((tok, freq, docs))
print('待定 token %d' % len(out))
with io.open('_tok-todo.tsv','w',encoding='utf-8',newline='') as f:
    f.write('token\tfreq\tdocs\r\n')
    for t,fr,d in out:
        f.write('%s\t%d\t%d\r\n' % (t,fr,d))
print('覆盖实例 %d' % sum(x[1] for x in out))
