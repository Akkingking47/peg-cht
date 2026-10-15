# -*- coding: utf-8 -*-
import io, sys, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
body = raw[2:]
n = 1721

# ★ 正确解码：整条记录 20 字节 = 变长名称 + NUL 填充 + 3 字节排序键
#   名称 = 记录开头到第一个 NUL（若 NUL 位置 <= 17）
#   但若前 17 字节无 NUL，则该 17 字节是"名称续片"，key 单独 3 字节
#   两种情况：
#     (a) rec[0:17] 含 NUL  -> name = rec[:nul]，key = rec[17:20]（名称独立完整）
#     (b) rec[0:17] 无 NUL  -> name 片段 = rec[0:17]，key = rec[17:20]（续片）
def name_at(i):
    rec = body[i*20:i*20+20]
    k = rec[17:20].split(b'\x00')[0]
    nm = rec[0:17]
    nul = nm.find(b'\x00')
    if nul >= 0:
        nm2 = nm[:nul]
        # (a) 完整名称就在 name 域
        full = nm2
        # 但若 name 域以空格开头（未排序的自定义名），前缀是空格
    else:
        nm2 = nm.rstrip(b' ')
        full = k + nm2
    try: return full.decode('utf-8')
    except: return full.decode('latin1')

names = [name_at(i) for i in range(n)]
print('--- 0..20 ---')
for i in range(21): print('%4d %r' % (i, names[i]))
print('--- 76..96 ---')
for i in range(76, 97): print('%4d %r' % (i, names[i]))
print('--- 1110..1130 ---')
for i in range(1110, 1131): print('%4d %r' % (i, names[i]))
