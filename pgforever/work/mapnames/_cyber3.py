# -*- coding: utf-8 -*-
import io, sys, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
body = raw[2:]
n = 1721

# ★ 最终模型：
#   记录 = name_field(17B) + key(3B)
#   ● 主条目：key 之前 3 字母（不是空格/NUL）且 name_field 以该 key 之后的续片开始
#     → 完整名 = key + name_field（到 NUL 或 17B 满）
#   ● name_field 以 NUL 开头 → 空名
#   ● name_field 全部无 NUL 且很长 → 名称恰好 20B? 最长 20B，key 占 3B 所以 name_field 最多 17B ✓
#   ● 特殊：name_field 以空格开头 → 该记录名称内嵌在 20B 里（未排序项），key 区也是名称一部分
def name_at(i):
    rec = body[i*20:i*20+20]
    # 先看整条 20B 里第一个 NUL
    nul_all = rec.find(b'\x00')
    if nul_all >= 0:
        # NUL 前的部分即完整名称（可能含 key 区）
        cand = rec[:nul_all]
        # 但若 name_field 无 NUL 且 key 有 NUL? 不可能，nul_all 是最早的
        # 若 nul_all <= 17，名称就是 cand
        if nul_all <= 17:
            # 可能名称以空格开头（未排序项），cand 就是名称
            return cand
        # nul_all == 20 或 17<nul<20 -> 名称跨了 key 边界，说明是 key+namefield
    k = rec[17:20].split(b'\x00')[0]
    nm = rec[0:17].rstrip(b' ')
    return k + nm

names = [name_at(i) for i in range(n)]
# 检查已知问题点
for i in [14,15,22,75,76,77,1119,1120,1121,1716,1717,1718,1719,1720]:
    try: d = names[i].decode('utf-8')
    except: d = names[i].decode('latin1')
    print('%5d %r' % (i, d))
print()
print('总数', n, ' 非空', sum(1 for x in names if x.strip()))
