# -*- coding: utf-8 -*-
import io, sys, os
sys.stdout.reconfigure(encoding='utf-8')
SRC = r'D:\OpenPG2\EFILE_BASEKORP\SCENARIO'
for fn in ['dragrom.txt', 'mussoak.txt', 'rcampdfr.txt']:
    t = open(os.path.join(SRC, fn), 'rb').read().decode('cp1252')
    print('=== ' + fn)
    for i, l in enumerate(t.split('\r\n')[:10], 1):
        print('%2d len=%-4d %r' % (i, len(l), l))
