# -*- coding: utf-8 -*-
import io, sys, os
sys.stdout.reconfigure(encoding='utf-8')
SRC = r'D:\OpenPG2\EFILE_BASEKORP\SCENARIO'
for fn in ['dragrom.txt', 'mussoak.txt', 'rcampdfr.txt']:
    t = open(os.path.join(SRC, fn), 'rb').read().decode('cp1252')
    ls = t.split('\r\n')
    print('=== %s (%d lines)' % (fn, len(ls)))
    for i, l in enumerate(ls, 1):
        if l.strip():
            print('%2d len=%-4d %s' % (i, len(l), l))
    print()
