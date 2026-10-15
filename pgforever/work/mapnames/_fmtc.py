# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
n = 1721

# 假设：17 字节名称域 + 3 字节排序键；名称域若被填满则溢出到下一记录
# 且排序键放在"名称结束"后的位置 -> 说明排序键是独立的 3 字节数组覆盖在 20 字节记录上
# 试拆分：每个 20B 记录 = 前 17B 属于名称流，后 3B 属于排序键流
namebytes = bytearray()
keys = []
for i in range(n):
    rec = raw[2+i*20:2+i*20+20]
    namebytes += rec[:17]
    keys.append(rec[17:20])

# 从 76*17 位置开始看名称流
off = 76*17
print('名称流 @76:', repr(bytes(namebytes[off:off+120])))
print('名称流 @0 :', repr(bytes(namebytes[0:120])))
print('排序键 @76:', [bytes(k) for k in keys[76:86]])
