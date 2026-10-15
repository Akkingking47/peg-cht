# -*- coding: utf-8 -*-
import io, sys, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
n = struct.unpack_from('<H', raw, 0)[0]
body = raw[2:]          # 34420 字节 = 1721 * 20

# ★ 关键推断：这是"20 字节定长记录 + 名称可跨记录连续（无 NUL 截断）"，
#   即记录边界处名称被直接切断、续写下一条。
#   末尾 3 字节排序键只出现在"名称较短、记录未填满"的情况。
# 验证：把 body 按 20 字节切，检查每个 20B 块的第 18..20 字节是否恰为排序键

# 用另一角度：读取"记录 i"的名称 = body[i*20:i*20+20] 去掉 NUL 及后续
# 但对跨记录名称，应拼接。检查是否有记录以非 NUL/非空格结尾且下一记录以字母开头
raw20 = [body[i*20:(i+1)*20] for i in range(n)]
cont = 0
for i in range(n-1):
    a, b = raw20[i], raw20[i+1]
    if a[19:20] not in (b'\x00', b' ') and a[0:1].isalpha():
        cont += 1
print('疑似跨记录续写数:', cont)

# 打印 96..99 的 20B 块，验证是否 "ington...Arl" 形式 = 名称跨记录
for i in [95,96,97,98]:
    print(i, repr(raw20[i]))
