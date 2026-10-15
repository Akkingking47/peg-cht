# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
n = 1721

# 验证：从记录 0 起，整段主体是连续 NUL 分隔的名称流
body = raw[2:]
parts = body.split(b'\x00')
names = [x for x in parts if x.strip()]
print('主体长度', len(body), ' NUL 切片', len(parts), ' 非空', len(names))

# 看名称是否全部可 UTF-8/latin1 解码 且 尾部是否残留排序键
print('--- 前 30 ---')
for i,s in enumerate(names[:30]):
    try: d=s.decode('utf-8')
    except: d=s.decode('latin1')
    print('%4d %r  len=%d' % (i, d[:60], len(s)))

print('--- 名称尾部残留检查（含 3 字符排序键的名称）---')
susp = 0
for s in names:
    if len(s) >= 20 and not s.endswith(b' '):
        susp += 1
print('长度>=20 且不以空格结尾的名称数:', susp)
