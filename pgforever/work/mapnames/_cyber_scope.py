# -*- coding: utf-8 -*-
import io, sys, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
body = raw[2:]
n = 1721

def name_at(i):
    k = body[i*20+17:i*20+20].split(b'\x00')[0]
    nm = body[i*20:i*20+17]
    nul = nm.find(b'\x00')
    nm2 = nm[:nul] if nul>=0 else nm.rstrip(b' ')
    full = k+nm2
    try: return full.decode('utf-8')
    except: return full.decode('latin1')

tbl = {}
for f in sorted(glob.glob('place_*.py')):
    if os.path.basename(f) in ('place_tools.py','place_mojibake.py'): continue
    ns={}; exec(open(f,encoding='utf-8').read(), ns)
    for k,v in ns.items():
        if k.isupper() and isinstance(v,dict): tbl.update(v)

names = [name_at(i) for i in range(n)]
# 统计（排除前 14 通用地形）
body_names = names[14:]
uq = sorted(set(x for x in body_names if x.strip()))
print('Cyber General 名称总数(14+) =', len(body_names), ' 去重 =', len(uq))
hit = [x for x in uq if x in tbl]
miss = [x for x in uq if x not in tbl]
print('译表命中 =', len(hit), ' 未覆盖 =', len(miss))
open('cyber_scope.txt','w',encoding='utf-8').write('\n'.join(miss))
print('--- 未覆盖前 50 ---')
for x in miss[:50]: print('   ', repr(x))
