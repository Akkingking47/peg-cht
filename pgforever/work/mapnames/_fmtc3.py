# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
n = 1721

# 关键：直接从字节 2+76*20 起，把整段当作连续名称流（不做 20B 切分）
off = 2 + 76*20
seg = raw[off:off+400]
print('从记录76起的原始连续字节:')
print(repr(seg))
