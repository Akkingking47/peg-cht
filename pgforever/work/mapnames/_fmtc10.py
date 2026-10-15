# -*- coding: utf-8 -*-
import io, sys, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
n = struct.unpack_from('<H', raw, 0)[0]
body = raw[2:]

# 记录 96 起：名称域=前17B，排序键=后3B
# 片段 'ington' + key 'Arl'  => 后续片段拼成 'Arlington'？
# 96:'ington' 97:'on' ... 不对。
# 试试：显示 96..115 的名称域与键，看键是否= 该名称的前3字母
for i in range(96, 120):
    nm = body[i*20:i*20+17].rstrip(b'\x00 ')
    k  = body[i*20+17:i*20+20]
    print('%5d name=%-18r key=%-6r' % (i, nm.decode('latin1'), k.decode('latin1')))
