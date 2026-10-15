# -*- coding: utf-8 -*-
import io, sys, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
n = struct.unpack_from('<H', raw, 0)[0]
body = raw[2:]

# 完整名称 = key[3] + name_field[17]，其中 name_field 是"NUL 之前"的部分
names = []
for i in range(n):
    k  = body[i*20+17:i*20+20]
    nm = body[i*20:i*20+17]
    nul = nm.find(b'\x00')
    if nul >= 0: nm = nm[:nul]
    else: nm = nm.rstrip(b' ')
    full = k + nm
    try: d = full.decode('utf-8')
    except UnicodeDecodeError: d = full.decode('latin1')
    names.append(d)

nonempty = [x for x in names if x.strip()]
print('总记录', n, ' 非空名称', len(nonempty))
# 去重
uq = sorted(set(nonempty))
print('去重后', len(uq))
# 最长
print('最长名称:', max(uq, key=len), max(len(x) for x in uq), 'B')
print('--- 前 20 通用地形 (0..13) ---')
for i in range(14): print(' ', names[i])
open('cyber_names.txt','w',encoding='utf-8').write('\n'.join(nonempty))
print('已导出 cyber_names.txt')
# 检查是否有已有译表命中
import importlib, glob, os
tbl = {}
for f in sorted(glob.glob('place_*.py')):
    if os.path.basename(f) in ('place_tools.py','place_mojibake.py'): continue
    ns = {}
    exec(open(f,encoding='utf-8').read(), ns)
    for k,v in ns.items():
        if k.isupper() and isinstance(v, dict): tbl.update(v)
hit = sum(1 for x in uq if x in tbl)
print('★ 与现有译表重合:', hit, '/', len(uq))
miss = [x for x in uq if x not in tbl]
print('未覆盖:', len(miss))
open('cyber_miss.txt','w',encoding='utf-8').write('\n'.join(miss))
for x in miss[:40]: print('   ', repr(x))
