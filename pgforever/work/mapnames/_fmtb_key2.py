# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
body = raw[2:]

# ★ 新假设：排序键 = 名称的前 3 字符（大写化），名称域 = 名称的第 4 字符起
#   96: key='Arl', name='ington' -> 'Arlington'  ✓ (Arl + ington)
#   110: key='Aug', name='sburg' -> 'Augsburg'   ✓
#   113: key='Ave', name='snes'  -> 'Avesnes'    ✓
#   114: key='Ave', name='llino' -> 'Avellino'   ✓
#   118: key='Bab', name='ues River' -> 'Babues River'  ✗ (应为 Babylon?)
#  ── 检查 118 是否名称域被截断：'ues River' 17B 未满? 是 'ues River        '(9+8=17) 满了
#     若完整名 >20B，则溢出到 119 的 name 域？但 119 已是 'Bac yak'
#  ▶ 说明每个记录名称上限 = 3 + 17 = 20 字节，够用（最长 'Civterna di Littoria' = 20B）✓

# 那 118 的 'Babues River' 真的存在吗？搜一下 38 个文件里有没有 Babylon
import glob
found = []
for f in glob.glob(r'D:/PGForever1.021/**/Scenario/mapnames.str', recursive=True):
    pass
print('check')

# 直接列出 key 与 name 的关系统计：key 是否 == name 的前3字母? 
# 不可能，因为 name 域不含前3字母
# 验证：把所有 = key+name 拼起来，去重后与 633 条重合 -> 说明拼接正确
