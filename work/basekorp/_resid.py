# -*- coding: utf-8 -*-
import io, re, collections
rows=[l.rstrip('\n').split('\t') for l in io.open('_det-out.tsv',encoding='utf-8')][1:]
out=[]
for src,zh,f,ex,rs in rows:
    clean = not any(c.isalpha() and ord(c)<128 for c in re.sub(r'\[[^\]]*\]','',zh))
    if not clean:
        out.append((src,zh,int(f),rs))
print('残留下发 LLM：唯一 %d  实例 %d' % (len(out), sum(x[2] for x in out)))
c=collections.Counter()
for _,_,f,_ in out:
    c[1 if f==1 else (2 if f<=3 else (4 if f<=10 else 11))]+=1
print('频次分布：f=1:%d  f2-3:%d  f4-10:%d  f>10:%d' % (c[1],c[2],c[4],c[11]))
# 纯单词（地名/专名）
single=[x for x in out if re.fullmatch(r"[A-Z][A-Za-z'’\-]*(\s[A-Z][A-Za-z'’\-]*)*", x[0])]
print('其中「纯专名串」%d' % len(single))
out.sort(key=lambda x:-x[2])
with io.open('_llm-src.tsv','w',encoding='utf-8',newline='') as f:
    f.write('src\tdraft\tfreq\tresid\r\n')
    for s,zh,fr,rs in out:
        f.write('%s\t%s\t%d\t%s\r\n' % (s,zh,fr,rs))
print('-> _llm-src.tsv')
for s,zh,fr,rs in out[:15]:
    print('  %3d  %-38s -> %-34s | %s' % (fr, s[:38], zh[:34], rs[:30]))
