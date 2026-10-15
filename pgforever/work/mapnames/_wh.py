# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import place_tools as T
found = {}
for g in ['Tobruk','Sicily','Normandy','Stalingrad','Kursk','Aachen','Bulge','Anzio','Market Garden','Arnhem']:
    ...
# 直接全扫，找出所有含这些 mojibake 的文件全路径
targets = [b'Alca\xa4ices', b'Alca\xf1iz', b'Almu\xa4ecar', b'Besan\x87on',
           b'Fuentidue\xa4a', b'Logro\xa4o', b'Mora d\xb4Ebre', b'Pe\xa4arroya',
           b'Pe\xf1alver', b'Razdol\xefnoie', b'Santo\xa4a', b'Sig\xfcenza']
for p in T.find_mapnames():
    raw = open(p,'rb').read()
    hit = [t for t in targets if t in raw]
    if hit:
        print(p.replace(r'D:/PGForever1.021',''))
        for t in hit: print('    ', repr(t))
