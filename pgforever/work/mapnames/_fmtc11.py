# -*- coding: utf-8 -*-
import io, sys, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
n = struct.unpack_from('<H', raw, 0)[0]
body = raw[2:]

# ★ 解密：key(3B 排序键) + name_field(17B) = 完整名称
for i in range(96, 125):
    k  = body[i*20+17:i*20+20]
    nm = body[i*20:i*20+17].rstrip(b'\x00 ')
    full = k + nm
    try: d = full.decode('utf-8')
    except: d = full.decode('latin1')
    print('%5d %s' % (i, d))
