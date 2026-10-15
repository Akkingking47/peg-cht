# -*- coding: utf-8 -*-
import io, sys, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
body = raw[2:]
n = 1721

# 解码 = key[3] + namefield[17]
def dec(i):
    k  = body[i*20+17:i*20+20]
    nm = body[i*20:i*20+17]
    nul = nm.find(b'\x00')
    if nul >= 0: nm = nm[:nul]
    else: nm = nm.rstrip(b' ')
    kn = k.split(b'\x00')[0]
    return (kn + nm)

# 载入已有译表
tbl = {}
for f in sorted(glob.glob('place_*.py')):
    if os.path.basename(f) in ('place_tools.py','place_mojibake.py'): continue
    ns={}; exec(open(f,encoding='utf-8').read(), ns)
    for k,v in ns.items():
        if k.isupper() and isinstance(v,dict): tbl.update(v)

# 决定性测试：若拼接正确，则 key 前3字母应等于 完整名的前3字母（大写）
ok=bad=0
badlist=[]
for i in range(14, n):
    k = body[i*20+17:i*20+20].split(b'\x00')[0]
    nm = body[i*20:i*20+17]
    nul = nm.find(b'\x00')
    nm2 = nm[:nul] if nul>=0 else nm.rstrip(b' ')
    full = (k+nm2)
    try: f=full.decode('utf-8')
    except: f=full.decode('latin1')
    kk=k.decode('latin1')
    if not f.strip(): continue
    if f[:3].upper()==kk.upper(): ok+=1
    else:
        bad+=1
        if len(badlist)<25: badlist.append((i,kk,f))
print('key==前3字母:', ok, '  不等:', bad)
for i,kk,f in badlist: print('  %5d key=%-5s full=%r' % (i,kk,f[:40]))
