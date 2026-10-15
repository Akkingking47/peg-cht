# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
n = 1721
namebytes = bytearray()
for i in range(n):
    namebytes += raw[2+i*20 : 2+i*20+17]

# 名称流用 NUL 切分，看是否得到连续合理名称
parts = bytes(namebytes).split(b'\x00')
names = [x for x in parts if x]
print('切片数 =', len(parts), ' 非空 =', len(names))
for i, s in enumerate(names[:40]):
    try: d = s.decode('utf-8')
    except: d = s.decode('latin1')
    print('%4d %-30s' % (i, d))
