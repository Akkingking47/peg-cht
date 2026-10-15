# -*- coding: utf-8 -*-
import io, json, collections
m = json.load(io.open('_xscn-crossmap.json', encoding='utf-8'))
rows = [l.rstrip('\n').split('\t') for l in io.open('bk-xscn-full.tsv', encoding='utf-8')][1:]
tot = len(rows); hit = 0; hitfreq = 0; allfreq = 0
miss = []
for src, freq, groups, ex in rows:
    f = int(freq); allfreq += f
    key = src.strip()
    if key in m:
        hit += 1; hitfreq += f
    else:
        miss.append((src, f, ex))
print('唯一串 %d  命中 %d (%.1f%%)' % (tot, hit, 100.0*hit/tot))
print('实例数 %d  命中 %d (%.1f%%)' % (allfreq, hitfreq, 100.0*hitfreq/allfreq))
print('未命中唯一 %d / 实例 %d' % (len(miss), sum(x[1] for x in miss)))
miss.sort(key=lambda x: -x[1])
with io.open('_xscn-todo.tsv','w',encoding='utf-8',newline='') as f:
    f.write('src\tfreq\texample\r\n')
    for s,fr,ex in miss:
        f.write('%s\t%d\t%s\r\n' % (s,fr,ex))
print('--- 未命中 TOP 40 ---')
for s,fr,ex in miss[:40]:
    print('%6d  %-55s %s' % (fr, s[:55], ex))
