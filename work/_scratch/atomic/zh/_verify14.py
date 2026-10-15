# -*- coding: utf-8 -*-
"""part-14.tsv 交付前自检（严格按 work/xscn/POLICY.md 的检查清单）。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'chunks', 'chunk-14.tsv')
DST = os.path.join(HERE, 'part-14.tsv')

errs = []


def load(path):
    raw = open(path, 'rb').read()
    if raw.startswith(b'\xef\xbb\xbf'):
        errs.append('BOM found in %s' % os.path.basename(path))
    txt = raw.decode('utf-8')
    if not raw.endswith(b'\r\n'):
        errs.append('%s does not end with CRLF' % os.path.basename(path))
    # 检查 CRLF 纯净：不允许裸 LF
    if b'\n' in raw.replace(b'\r\n', b''):
        errs.append('%s has bare LF' % os.path.basename(path))
    if b'\r' in raw.replace(b'\r\n', b''):
        errs.append('%s has bare CR' % os.path.basename(path))
    lines = txt.split('\r\n')
    assert lines[-1] == ''
    return lines[:-1]


src = load(SRC)
dst = load(DST)

# 1) 行数一致
if len(src) != len(dst):
    errs.append('line count mismatch: src=%d dst=%d' % (len(src), len(dst)))

# 2) 每行恰好 1 个 TAB，且 TAB 前逐字节 == 原文
for i, (s, d) in enumerate(zip(src, dst), 1):
    if d.count('\t') != 1:
        errs.append('line %d: TAB count = %d' % (i, d.count('\t')))
        continue
    head, tail = d.split('\t')
    if head != s:
        errs.append('line %d: head != src\n  src=%r\n  got=%r' % (i, s, head))
    if head.encode('utf-8') != s.encode('utf-8'):
        errs.append('line %d: head bytes != src bytes' % i)
    if tail == '':
        errs.append('line %d: empty translation' % i)

# 3) 分隔符 / 括号数量一致
for ch in '/[]()':
    for i, (s, d) in enumerate(zip(src, dst), 1):
        if d.count('\t') != 1:
            continue
        z = d.split('\t', 1)[1]
        if s.count(ch) != z.count(ch):
            errs.append('line %d: %r count src=%d dst=%d\n  src=%r\n  dst=%r'
                        % (i, ch, s.count(ch), z.count(ch), s, z))

# 4) 无空行 / 无表头
for i, d in enumerate(dst, 1):
    if d.strip() == '':
        errs.append('line %d: blank line' % i)
    if d.count('\t') == 1 and d.split('\t')[1] in ('译文', 'translation'):
        errs.append('line %d: header detected' % i)

print('src lines : %d' % len(src))
print('dst lines : %d' % len(dst))
print('src bytes : %d' % os.path.getsize(SRC))
print('dst bytes : %d' % os.path.getsize(DST))
if errs:
    print('FAIL (%d issues)' % len(errs))
    for e in errs[:40]:
        print(' -', e)
    sys.exit(1)
print('SELF-CHECK PASSED')
