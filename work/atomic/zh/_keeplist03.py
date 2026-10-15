# -*- coding: utf-8 -*-
"""列出 part-03.tsv 中「译文 == 原文」的保留条目。"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'chunks', 'chunk-03.tsv')
DST = os.path.join(HERE, 'part-03.tsv')

sl = open(SRC, 'rb').read().decode('utf-8').split('\r\n')[:-1]
ol = open(DST, 'rb').read().decode('utf-8').split('\r\n')[:-1]

keep = [(i + 1, sl[i]) for i in range(400)
        if ol[i].split('\t', 1)[1] == sl[i]]
print('总行数: %d' % len(ol))
print('保留原文条数: %d' % len(keep))
for n, t in keep:
    print('  行%d: %s' % (n, t))
