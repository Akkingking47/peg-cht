# -*- coding: utf-8 -*-
import io, sys, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
n = struct.unpack_from('<H', raw, 0)[0]
ca=cb=cc=0
runs = []
cur = None; cnt = 0
for i in range(14, n):
    rec = raw[2+i*20:2+i*20+20]
    if b'\x00' in rec: t='A'
    elif rec[17:20]==b'   ': t='B'
    else: t='?'
    if t=='A': ca+=1
    elif t=='B': cb+=1
    else: cc+=1
    if t!=cur:
        if cur is not None: runs.append((cur,start,i-1,cnt))
        cur=t; start=i; cnt=0
    cnt+=1
runs.append((cur,start,n-1,cnt))
print('总 A=',ca,' B=',cb,' 其他=',cc)
print('--- 记录类型分段 ---')
for t,a,b,c in runs[:40]:
    print('%s  %5d..%-5d  n=%d' % (t,a,b,c))
