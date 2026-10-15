# -*- coding: utf-8 -*-
import io, sys, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:/PGForever1.021/Cyber General\Scenario\mapnames.str'
raw = open(p,'rb').read()
n = struct.unpack_from('<H', raw, 0)[0]
body = raw[2:]

# ★ 最终假设：记录 = [名称域(变长,NUL或名称填满)][排序键(3字节)]
#   名称域从记录起点开始；名称长度 L；若 L <= 17 则有 NUL 填充到 17，然后 3 字节排序键
#   若 L > 17，名称溢出到下一记录（下一记录的名称域被占用）
# 验证：把 body 当作"名称流 + 排序键流"交错，但排序键流偏移随名称长度浮动
# 直接手工解码：
def decode(body, n):
    out = []
    pos = 0
    for i in range(n):
        rec_start = i*20
        rec = body[rec_start:rec_start+20]
        # 找名称：从 rec 起点取到第一个 NUL 或取满 20
        nul = rec.find(b'\x00')
        if nul >= 0:
            nm = rec[:nul]
            key = rec[17:20] if nul <= 17 else rec[nul+1:nul+4]
            out.append((i, nm, rec[17:20], 'short'))
        else:
            # 名称占满 20 字节 -> 需要看接下来
            out.append((i, rec, rec[17:20], 'long?'))
    return out

r = decode(body, n)
print('--- 96..103 ---')
for i, nm, key, t in r[96:104]:
    print('%5d %-24s key=%s %s' % (i, repr(nm), key.hex() if key else '-', t))
