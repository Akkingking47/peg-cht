# -*- coding: utf-8 -*-
"""跨批次一致性检测：同一英文 token，有的条目保留原文、有的译中文 => 冲突。"""
import io, re, collections
rows=[l.rstrip('\n').split('\t') for l in io.open('bk-xscn-map.tsv',encoding='utf-8-sig')][1:]
TOK=re.compile(r'(?<![A-Za-z0-9])([A-Za-z][A-Za-z\.]{1,9})(?![A-Za-z0-9])')
keep=collections.Counter(); drop=collections.Counter(); ex=collections.defaultdict(list)
for s,d,n in rows:
    seen=set()
    for t in TOK.findall(s):
        if t in seen: continue
        seen.add(t)
        if re.search(r'(?<![A-Za-z0-9])%s(?![A-Za-z0-9])'%re.escape(t), d):
            keep[t]+=1
        else:
            drop[t]+=1
            if len(ex[t])<4: ex[t].append((s,d))
cand=[]
for t in set(list(keep)+list(drop)):
    k,d2=keep[t],drop[t]; tot=k+d2
    if tot<8: continue
    r=min(k,d2)/tot
    if r>=0.20: cand.append((tot,r,k,d2,t))
cand.sort(key=lambda x:-x[0]*x[1])
print('%-14s %6s %6s %6s  %s' % ('token','总','保留','已译','例'))
for tot,r,k,d2,t in cand[:35]:
    print('%-14s %6d %6d %6d  %.0f%%' % (t,tot,k,d2,100*r))
    for s,dd in ex[t][:2]: print('        %-34s -> %s' % (s[:34], dd[:44]))
