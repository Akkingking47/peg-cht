# -*- coding: utf-8 -*-
import io, re, collections, sys
rows=[l.rstrip('\n').split('\t') for l in io.open('bk-xscn-map.tsv',encoding='utf-8-sig')][1:]
print('映射 %d 条' % len(rows))
bad=[]
for s,d,n in rows:
    try: d.encode('gbk')
    except Exception as e: bad.append((s,d,str(e)[:60]))
print('GBK 不可编码 %d 条' % len(bad))
for s,d,e in bad[:15]: print('   %-32s -> %-32s  %s' % (s[:32],d[:32],e))
# 可疑产物
sus = [(s,d) for s,d,n in rows if re.search(r'第0(?!\d)', d) or d.count('第')>4 or '锟' in d or '�' in d]
print('可疑「第0」/异常 %d 条' % len(sus))
for s,d in sus[:10]: print('   %-34s -> %s' % (s[:34], d[:50]))
# 空译文
empty=[s for s,d,n in rows if not d.strip()]
print('空译文 %d 条' % len(empty))
for s in empty[:8]: print('   %r' % s)
# 与 src 完全相同（未译）
same=[(s,d) for s,d,n in rows if d.strip()==s.strip()]
print('译文==原文 %d 条' % len(same))
# 残留英文（非方括号）
res=[(s,d) for s,d,n in rows if re.search(r'[A-Za-z]{2,}', re.sub(r'\[[^\]]*\]','',d))]
print('仍含英文词 %d 条 (%.1f%%)' % (len(res), 100.0*len(res)/len(rows)))
import random; random.seed(5)
for s,d in random.sample(res, 15): print('   %-36s -> %s' % (s[:36], d[:46]))
