# -*- coding: utf-8 -*-
import io, sys, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
n = struct.unpack_from('<H', raw, 0)[0]
body = raw[2:]

# ★ 真实结构：记录 i = name_field(17B) + sortkey(3B)
#   完整名称流 = 顺序拼接所有 name_field；片段之间无 NUL 的是同一名称的续写
namebuf = b''.join(body[i*20:i*20+17] for i in range(n))
parts = namebuf.split(b'\x00')

# 现在把非空片段按"是否被 NUL 分隔"归组
# 但更准：真实名称边界 = 排序键变化处？不，排序键是每记录一个（对应一个地名）
# 观察：记录 96..110 每个都有独立排序键 Arl, Arm, Arn... 且名称片段递增
# 说明这是"排序后的名称索引表"：每记录对应『一条索引项』，名称被截断成 17B + 续写

# 换个思路：直接从 96 起把 17B 域拼起来，看能否还原出完整名称序列
seg = namebuf[96*17:]
print(repr(seg[:300]))
