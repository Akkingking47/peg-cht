# -*- coding: utf-8 -*-
import io, re, collections
rows = [l.rstrip('\n').split('\t') for l in io.open('_xscn-todo.tsv', encoding='utf-8')][1:]
srcs = [(r[0].strip(), int(r[1])) for r in rows]
VAL = {'I':1,'V':5,'X':10,'L':50,'C':100,'D':500,'M':1000}
def rom_ok(s):
    if not s or any(c not in VAL for c in s): return False
    n = len(s); tot = 0
    for i,c in enumerate(s):
        v = VAL[c]
        nxt = VAL[s[i+1]] if i+1 < n else 0
        tot += -v if v < nxt else v
    # 标准形式校验（减法只能一次且合法）
    return str(tot) and tot > 0 and __import__('re').fullmatch(r'M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})', s) is not None
import re as _re
def rom_ok(s):
    return _re.fullmatch(r'M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})', s) is not None
CAND = _re.compile(r'\b[IVXLCDM]{1,7}\b')
ROMRE = _re.compile(r'\b(?:M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3}))\b')
def mask(s):
    s = CAND.sub(lambda m: '@R' if rom_ok(m.group(0)) else m.group(0), s)
    s = _re.sub(r'\d+', '@N', s)
    return s
pat = collections.defaultdict(list)
for s,f in srcs:
    pat[mask(s)].append((s,f))
print('唯一 %d -> 掩码后模式 %d  (压缩 %.2fx)' % (len(srcs), len(pat), len(srcs)/len(pat)))
top = sorted(pat.items(), key=lambda kv: -len(kv[1]))
for p, mem in top[:45]:
    print('%5d  %-34s  eg: %s' % (len(mem), p[:34], mem[0][0]))
with io.open('_patterns.tsv','w',encoding='utf-8',newline='') as f:
    f.write('pattern\tcount\ttotfreq\texamples\r\n')
    for p, mem in sorted(pat.items(), key=lambda kv:(-len(kv[1]), kv[0])):
        ex = ' | '.join(m[0] for m in mem[:6])
        f.write('%s\t%d\t%d\t%s\r\n' % (p, len(mem), sum(m[1] for m in mem), ex))
