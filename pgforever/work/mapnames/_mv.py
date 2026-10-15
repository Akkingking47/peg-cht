# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
import place_tools as T
import place_mojibake as M
for b, zh in M.MOJIBAKE.items():
    print('%2dB  %-18s %s' % (T.zb(zh), b.decode('latin1'), zh))
