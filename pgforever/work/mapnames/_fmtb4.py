# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()

# 直接从 76 开始看原始字节，每 20 字节一条
for i in [75,76,77,95,96,97,98,99,100]:
    rec = raw[2+i*20:2+i*20+20]
    print('%5d %s' % (i, repr(rec)))

print('--- 96..1119 区域每 100 条抽样 ---')
for i in range(96, 1200, 100):
    rec = raw[2+i*20:2+i*20+20]
    print('%5d %s' % (i, repr(rec)))
