# -*- coding: utf-8 -*-
"""part-04.tsv 交付自检（POLICY.md §交付前自检）。"""
import io, sys

ROOT = 'D:/DSH/军事游戏汉化'
SRC = ROOT + '/work/atomic/chunks/chunk-04.tsv'
DST = ROOT + '/work/atomic/zh/part-04.tsv'


def lines(p):
    return io.open(p, encoding='utf-8', newline='').read().replace('\r\n', '\n').split('\n')


s = lines(SRC)
if s and s[-1] == '':
    s = s[:-1]

raw = io.open(DST, 'rb').read()
txt = raw.decode('utf-8')
d = txt.replace('\r\n', '\n').split('\n')
if d and d[-1] == '':
    d = d[:-1]

ok = True

# 1. 行数
print('[1] 输入 %d 行 / 输出 %d 行 -> %s' % (len(s), len(d), 'PASS' if len(s) == len(d) else 'FAIL'))
ok &= len(s) == len(d)

# 2. 每行恰好 1 个 TAB，且 TAB 前 == 原文
bad_tab = [i for i, l in enumerate(d) if l.count('\t') != 1]
bad_src = [i for i, (a, b) in enumerate(zip(s, d)) if b.split('\t')[0] != a]
print('[2] TAB 数异常行 %d / 原文字节不一致行 %d -> %s'
      % (len(bad_tab), len(bad_src), 'PASS' if not bad_tab and not bad_src else 'FAIL'))
ok &= not bad_tab and not bad_src

# 3. 括号/分隔符计数一致
#    `/ [ ] ( ) ,` 属结构符，必须逐字保留；
#    `'`（西里尔软音号/阿拉伯语 ain）与 `-`（法德正字法连字符）属正字法符号，
#    中文音译后自然消失，不计入本项（既有片同样处理，如 Bel'bek River → 别利别克河）。
SYM = ['/', '[', ']', '(', ')', ',']
diff = []
soft = 0
for i, (a, b) in enumerate(zip(s, d)):
    z = b.split('\t')[1] if '\t' in b else ''
    if a.count("'") != z.count("'"):
        soft += 1
    for c in SYM:
        if a.count(c) != z.count(c):
            diff.append((i + 1, c, a, z))
            break
print('[3] 结构符(/ [ ] ( ) ,)计数不一致行 %d -> %s ；软音号/撇号自然消减行 %d（预期内）'
      % (len(diff), 'PASS' if not diff else 'FAIL', soft))
for x in diff[:10]:
    print('    ', x)
ok &= not diff

# 4. 编码 / 空行 / 表头
print('[4] BOM=%s  CRLF=%d  LF=%d  尾=CRLF:%s  空行=%d'
      % (raw[:3] == b'\xef\xbb\xbf', raw.count(b'\r\n'), raw.count(b'\n'),
         raw.endswith(b'\r\n'), sum(1 for l in d if l.strip() == '')))
ok &= raw[:3] != b'\xef\xbb\xbf' and raw.count(b'\r\n') == len(d) and raw.endswith(b'\r\n')

# 5. 与既有 25 片译名冲突检查（同一原文不同译法）
import glob
prior = {}
for p in sorted(glob.glob(ROOT + '/work/xscn/zh/part-*.tsv')):
    for l in io.open(p, encoding='utf-8', newline=''):
        f = l.rstrip('\r\n').split('\t')
        if len(f) == 2 and f[0] not in prior:
            prior[f[0]] = f[1]
conf = [(a.split('\t')[0], a.split('\t')[1], prior[a.split('\t')[0]])
        for a in d if a.split('\t')[0] in prior and prior[a.split('\t')[0]] != a.split('\t')[1]]
print('[5] 与既有片译名冲突 %d -> %s' % (len(conf), 'PASS' if not conf else 'FAIL'))
for c in conf[:10]:
    print('    ', c)
ok &= not conf

# 6. 未译残留（译文中仍含拉丁字母的条目，逐个列出以便人工确认）
import re
res = [a for a in d if re.search(r'[A-Za-z]{3,}', a.split('\t')[1])]
print('[6] 译文中含拉丁字母的条目 %d 条（下面逐条列出）' % len(res))
for r in res:
    print('    ', r)

print('\n总检: %s' % ('PASS' if ok else 'FAIL'))
sys.exit(0 if ok else 1)
