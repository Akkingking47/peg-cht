# -*- coding: utf-8 -*-
import io, sys, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
n = struct.unpack_from('<H', raw, 0)[0]
print('N=',n,'size=',len(raw),'expect 2+20N=',2+20*n)

# 逐条判断：是 A 型（NUL终止）还是 B 型（17B名称+3B键）
ca=cb=0
for i in range(14, min(n,900)):
    rec = raw[2+i*20:2+i*20+20]
    if b'\x00' in rec: ca+=1
    elif rec[17:20]==b'   ': cb+=1
print('A型(含NUL)=',ca,' B型(空格尾)=',cb)

# 打印若干 A 型样例
print('--- A 型样例 ---')
k=0
for i in range(14, n):
    rec = raw[2+i*20:2+i*20+20]
    if b'\x00' in rec:
        print(i, repr(rec)); k+=1
        if k>=8: break

print('--- B 型样例 ---')
k=0
for i in range(14, n):
    rec = raw[2+i*20:2+i*20+20]
    if b'\x00' not in rec:
        print(i, repr(rec)); k+=1
        if k>=12: break
