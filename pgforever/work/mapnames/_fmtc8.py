# -*- coding: utf-8 -*-
import io, sys, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
n = struct.unpack_from('<H', raw, 0)[0]
body = raw[2:]

# 解码：名称域 = 记录[0:17]；排序键 = 记录[17:20]
# 名称流 = 依次拼接各记录的前 17 字节
namebuf = b''.join(body[i*20:i*20+17] for i in range(n))
keys    = [body[i*20+17:i*20+20] for i in range(n)]

# 名称之间用 NUL 分隔；空的是延续片段
parts = namebuf.split(b'\x00')
print('切片', len(parts), '非空', len([x for x in parts if x]))

# 逐条解读：连续的非空片段接在一起构成完整名称
# 但真正的划分是：每条记录的"排序键"指示该记录是否是一个名称的开头？
print('--- 记录 90..110 逐条 ---')
for i in range(90, 111):
    nm = body[i*20:i*20+17]
    k  = body[i*20+17:i*20+20]
    try: d=nm.rstrip(b'\x00').decode('utf-8')
    except: d=nm.rstrip(b'\x00').decode('latin1')
    print('%5d %-20s | key=%r' % (i, d, k.decode('latin1')))
