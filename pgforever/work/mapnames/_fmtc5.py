# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
n = 1721

# 假设：这是"格式 C" = NUL 分隔的连续名称流，名称可超过 20 字节
# 头部 2 字节计数 N=1721。记录数不等于 1721 ？验证总切片数。
body = raw[2:]
parts = body.split(b'\x00')
names = [x for x in parts if x.strip()]
print('N(头)=', n, ' 实际名称数(非空切片)=', len(names))
print('总切片(含空)=', len(parts))

# 那么 34420 = ? 若名称数应=1721，则说明有大量空切片
empt = len(parts) - len(names)
print('空切片数=', empt)
# 1721 名称 + 1721 NUL 终止 = ？
print('若每名 NUL 终止，最小字节= sum(len)+1721 =', sum(len(x) for x in names)+len(names))
print('实际主体=', len(body))
