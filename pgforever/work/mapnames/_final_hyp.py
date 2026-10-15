# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
raw=open(r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str','rb').read()
body=raw[2:]
n=1721
# ★ 最终假设：key(3B) 是**本记录**的排序键 = 名称前 3 字母
#   但 111 key='Auw' != 'Aug' -> 说明它其实是"下一名称的前3字母"？
#   112 nf=全空格 key='Ave'，113 nf='snes' key='Ave' => 'Avesnes'
#   所以 112 是**空名条目**（nf 全空），其 key 指向 113 的名称前缀? 不
# 检验 111 后一条 112: nf='                 ' key='Ave'
# 若 112 是"空名占位"，113 名称='Ave'+'snes'='Avesnes'
# 111 名称应='Aug'+'ustow Forest'='Augustow Forest'（key 存 Aug）
# 实测 key='Auw' → 疑似该文件写入时 off-by-one，第 3 字节取到了下一名的第 1 字母
# ★ 决定性检验：key[0:2] + nf 是不是真实地名？
recs=[]
for i in range(n):
    rec=body[i*20:i*20+20]
    nf=rec[:17]; key=rec[17:20]
    nf_nul=nf.find(b'\x00')
    if nf_nul>=0:
        nm=nf[:nf_nul]
    else:
        nm=(key[:2]+nf.rstrip(b' '))
    try: s=nm.decode('utf-8')
    except: s=nm.decode('latin1')
    recs.append((i,s))
# 用 2 字节 key 拼接，检查有多少成为已知真实地名（与译表比对）
import glob,os
tbl={}
for f in sorted(glob.glob('place_*.py')):
    if os.path.basename(f) in ('place_tools.py','place_mojibake.py'): continue
    ns={}; exec(open(f,encoding='utf-8').read(),ns)
    for k,v in ns.items():
        if k.isupper() and isinstance(v,dict): tbl.update(v)

# 方案X: key(3) + nf
raw3=open(r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str','rb').read()
import cyber_decode as C
a=[s for _,s,_ in C.decode_all(raw3)]
hitA=sum(1 for s in set(a[14:]) if s in tbl)
# 方案Y: key[:2] + nf
b=[]
for i in range(n):
    rec=body[i*20:i*20+20]; nf=rec[:17]; key=rec[17:20]
    if nf.find(b'\x00')>=0: nm=nf[:nf.find(b'\x00')]
    else: nm=key[:2]+nf.rstrip(b' ')
    try: b.append(nm.decode('utf-8'))
    except: b.append(nm.decode('latin1'))
hitB=sum(1 for s in set(b[14:]) if s in tbl)
print('方案A key(3)+nf  命中', hitA)
print('方案B key[:2]+nf 命中', hitB)
