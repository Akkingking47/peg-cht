# -*- coding: utf-8 -*-
"""part-03.tsv 交付前自检（POLICY.md 第 82-86 行要求）。"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'chunks', 'chunk-03.tsv')
DST = os.path.join(HERE, 'part-03.tsv')

CRLF = b'\x0d\x0a'
ok = True


def chk(cond, msg):
    global ok
    print(('PASS  ' if cond else 'FAIL  ') + msg)
    if not cond:
        ok = False


sb = open(SRC, 'rb').read()
ob = open(DST, 'rb').read()

chk(not ob.startswith(b'\xef\xbb\xbf'), '无 BOM')
chk(ob.count(b'\x0d\x0a') == 400, 'CRLF 数 = 400')
chk(ob.count(b'\x0a') == 400, 'LF 总数 = 400（无孤立 LF）')
chk(ob.count(b'\x09') == 400, 'TAB 总数 = 400（每行恰好 1 个）')

s = sb.decode('utf-8').split('\x0d\x0a')
o = ob.decode('utf-8').split('\x0d\x0a')
chk(s[-1] == '', '输入以 CRLF 结尾')
chk(o[-1] == '', '输出以 CRLF 结尾')
sl, ol = s[:-1], o[:-1]
chk(len(sl) == 400, '输入 400 行')
chk(len(ol) == 400, '输出 400 行')
chk(len(ol) == len(sl), '行数一致')

chk(all(l.count('\t') == 1 for l in ol), '每行恰好 1 个 TAB')
chk(all(ol[i].split('\t', 1)[0] == sl[i] for i in range(400)),
    '第一列逐字节等于输入原文')

for c in '/[]()':
    bad = [i + 1 for i in range(400)
           if ol[i].split('\t', 1)[1].count(c) != sl[i].count(c)]
    chk(not bad, "'%s' 数量逐行一致%s" % (c, '' if not bad else ' -> 行 %s' % bad))

chk(all(ol[i].split('\t', 1)[1].strip() != '' for i in range(400)), '无空译文')
chk(all(l != '' for l in ol), '无空行')
chk(not ol[0].startswith('#'), '无表头')

# 空段/尾随空格等结构性提示
ws = [i + 1 for i in range(400) if sl[i] != sl[i].strip()]
print()
print('提示：原文含首尾空格的条目 ->', ws if ws else '无')
print()
print('ALL PASS' if ok else 'HAS FAILURE')
