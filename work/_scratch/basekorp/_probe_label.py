# -*- coding: utf-8 -*-
import io, sys, os
sys.stdout.reconfigure(encoding='utf-8')
SRC = r'D:\OpenPG2\EFILE_BASEKORP\SCENARIO'
for fn in ['gaw29_i.txt', 'cm3moscw.txt', 'boak.txt']:
    t = open(os.path.join(SRC, fn), 'rb').read().decode('cp1252', errors='replace')
    print('===== ' + fn)
    for l in t.split('\r\n')[:8]:
        print('   |' + repr(l[:130]))
print()
b = open(os.path.join(SRC, 'btobruk.txt'), 'rb').read()
i = b.find(b'King')
print('King bytes:', b[i:i + 14])
b2 = open(os.path.join(SRC, '10airwar_i.txt'), 'rb').read()
print('10airwar_i src:', b2[:90])
print()
for s in ['\u00af', '\u2019', '\u201c', '\u2026', '\u00b7']:
    try:
        print(repr(s), 'gbk ok', s.encode('gbk'))
    except Exception as e:
        print(repr(s), 'GBK FAIL', e)
