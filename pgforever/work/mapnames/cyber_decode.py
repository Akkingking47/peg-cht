# -*- coding: utf-8 -*-
"""Cyber General / MAPNAMES.STR 专用解码器（"格式 C"）

★ 结构：头部 2 字节小端计数 N；其后 N × 20 字节定长记录。
   记录 = name_field(17B) + sortkey(3B)
   四种记录类型（按 name_field 与 key 的内容判别）：

   [plain   ] name_field 内含 NUL   → 名称 = name_field[:NUL]
                                    （地形名/未排序的自定义短名）
   [key     ] name_field 无 NUL 且有尾空格填充，key = 名称前 3 字节
                                    → 名称 = key + name_field.rstrip(' ')
                                    这是文件的主体（1621/1721），按字母序排好的地名索引
   [spill   ] name_field 无 NUL 且无尾空格（恰好 17B 全满），key 是名称的第 18-20 字节
                                    → 名称 = name_field + key 中去掉尾部空格的部分
                                    仅长名（18-20B）会出现
   [empty   ] 全 NUL

★ 汉化写回策略：所有中文名 ≤17B（5 汉字 = 15B）→ 一律写成 plain 形式
   （名称 + NUL 补满 20B），引擎按 name_field[:NUL] 读取，安全且已被记录 77/1717 实证。
"""
import struct

REC = 20
KEY_LEN = 3
NAME_LIMIT = 17          # key 之后名字域上限（格式 C 主体）
ABS_LIMIT = 19           # plain 形式可用上限（NUL 终止），即 ≤6 汉字
SAFE_LIMIT = 15          # 5 汉字，跨格式最稳

def zb(s): return len(s.encode('utf-8'))

def decode_all(raw):
    """→ [(idx, name, kind)]"""
    n = struct.unpack_from('<H', raw, 0)[0]
    body = raw[2:]
    out = []
    for i in range(n):
        rec = body[i * REC:(i + 1) * REC]
        if len(rec) < REC:
            break
        nf, key = rec[:17], rec[17:20]
        nf_nul = nf.find(b'\x00')
        if nf_nul >= 0:
            nm, kind = nf[:nf_nul], 'plain'
        elif nf.endswith(b' ') or nf.rstrip(b' ') != nf:
            # 有尾空格 → key 型（key = 名称前 3 字节）
            k = key.split(b'\x00')[0].rstrip(b' ')
            nm, kind = (k + nf.rstrip(b' ')), 'key'
        else:
            # 填满无空格 → spill（key 区续写名称）
            k = key.split(b'\x00')[0].rstrip(b' ')
            nm, kind = (nf + k), 'spill'
        if not nf.strip() and not key.strip():
            nm, kind = b'', 'empty'
        try:
            s = nm.decode('utf-8')
        except UnicodeDecodeError:
            s = nm.decode('latin1')
        out.append((i, s, kind))
    return out

def names_only(raw):
    return [s for _, s, _ in decode_all(raw)]

def encode_name(zh):
    """中文名 → 20 字节 plain 记录（名称 + NUL 补满）"""
    b = zh.encode('utf-8')
    assert len(b) <= ABS_LIMIT, 'too long: %s (%dB)' % (zh, len(b))
    return b + b'\x00' * (REC - len(b))

def build(names):
    out = bytearray(struct.pack('<H', len(names)))
    for s in names:
        out += encode_name(s)
    return bytes(out)
