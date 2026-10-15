# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
body = raw[2:]

# 查看问题记录的原始 20B
for i in [21,22,23,75,76,77,1715,1716,1717,1718,1719,1720]:
    rec = body[i*20:i*20+20]
    print('%5d %r' % (i, rec))
