# -*- coding: utf-8 -*-
"""独立校验 part-02.tsv（不依赖生成脚本）。"""
import io, os, sys
sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'chunks', 'chunk-02.tsv')
DST = os.path.join(HERE, 'part-02.tsv')

src = io.open(SRC, 'rb').read()
dst = io.open(DST, 'rb').read()

ok = True
def chk(name, cond, extra=''):
    global ok
    print(('  OK  ' if cond else ' FAIL ') + name + ('  ' + extra if extra else ''))
    if not cond:
        ok = False

# 1. 编码 / 行尾
chk('UTF-8 无 BOM', dst[:3] != b'\xef\xbb\xbf')
chk('CRLF 行尾 400', dst.count(b'\r\n') == 400, 'got %d' % dst.count(b'\r\n'))
chk('无裸 LF', dst.count(b'\n') == dst.count(b'\r\n'))
chk('结尾换行', dst.endswith(b'\r\n'))
dst.decode('utf-8')  # 非法字节会抛异常
chk('可解码为 UTF-8', True)

srows = src.decode('utf-8').split('\r\n')
drows = dst.decode('utf-8').split('\r\n')
if srows and srows[-1] == '':
    srows.pop()
if drows and drows[-1] == '':
    drows.pop()

# 2. 行数
chk('行数一致 400', len(srows) == len(drows) == 400,
    'src=%d dst=%d' % (len(srows), len(drows)))

# 3. 每行恰好 1 个 TAB，且第 1 列逐字节等于原文
tab_bad = [i for i, r in enumerate(drows, 1) if r.count('\t') != 1]
chk('每行恰好 1 个 TAB', not tab_bad, str(tab_bad[:10]))
mism = [i for i, (s, d) in enumerate(zip(srows, drows), 1)
        if d.split('\t')[0] != s]
chk('第 1 列 == 原文', not mism, str(mism[:10]))

# 4. 分隔符数量一致
sep_bad = []
for i, (s, d) in enumerate(zip(srows, drows), 1):
    t = d.split('\t')[1]
    for ch in '/[]()':
        if t.count(ch) != s.count(ch):
            sep_bad.append((i, ch, s, t))
chk('分隔符 /[]() 数量一致', not sep_bad)
for b in sep_bad[:10]:
    print('       ', b)

# 5. 无空行 / 无表头
chk('无空行', all(r.strip() for r in drows))
chk('无 TAB 表头行', drows[0].split('\t')[0] != 'src')

print()
print('结论:', '全部通过' if ok else '存在问题')
sys.exit(0 if ok else 1)
