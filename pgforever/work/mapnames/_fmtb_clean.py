# -*- coding: utf-8 -*-
import io, sys, struct, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
n = struct.unpack_from('<H', raw, 0)[0]
body = raw[2:]

# ★ 修正解码：
#   key = body[i*20+17 : i*20+20]，取到 NUL 为止
#   name = body[i*20 : i*20+17]，取到 NUL 为止
#   若 name 域全 NUL 且以空格起（如 '   Aegean Sea'），说明该记录的"名称"实际从 name 域开头算
#   真实顺序： name_field(17B) 在前? 还是 key 在前?
# 实测 96: name_field='ington', key='Arl' -> 完整 = Arl+ington ✓
# 实测 110: name_field='sburg', key='Aug' -> Augsburg ✓
# 但 118: name_field='ues River', key='Bab' -> Babues River ?
#   Babylon 附近的河应叫 "Babylon"? 不，可能是 'Babylon'... 
# 检查: 119 key=Bac name='yak' -> Bacyak ? 应是 'Bac yak'? 实际地名 'Bacs' 'Bacau'?
# ▶ 重新审视：也许 name_field 才是"完整名称"，key 是"排序键"，两者独立！
for i in range(96, 130):
    nm = body[i*20:i*20+17]
    k  = body[i*20+17:i*20+20]
    print('%5d name=%-20r key=%-6r' % (i, nm.decode('latin1'), k.decode('latin1')))
