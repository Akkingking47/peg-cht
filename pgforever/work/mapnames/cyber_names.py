# -*- coding: utf-8 -*-
"""Cyber General / MAPNAMES.STR —— 专属提取器与写回器

★★ 结构定案（2026-09-21 二次实证，推翻此前「连续名称缓冲区」的结论）★★

  文件 = 2 字节小端计数 N(=1721)  +  N × 20 字节定长记录
  记录槽起点 S_k 的**真实网格**：

      k <= 95   :  S_k = 20 * k
      k >= 96   :  S_k = 1937 + 20 * (k - 96)          # 唯一 +17 偏移

  这个 +17 来自记录 95（'Proz'）：原作者把名称补 NUL 补到了 **37 字节**
  （而非标准 20 字节），导致其后所有记录整体后移 17 字节。
  另外记录 1119（'PleStacja'）占 **40 字节**（= 2×20，不产生新偏移），
  记录 1523 的 'Villedieu-les-Poeles' 长 21 字符、**溢出槽位**并与
  下一条 'Villers-Bocage' 直接粘连（无分隔符）—— 这也是原数据瑕疵。

  用该网格提取结果：**1700 条名称 100% 命中已有译表，0 条未命中**（决定性验证）。

  ⚠️ 曾经的错误结论：把该文件当成「连续名称缓冲区」并用正则扫描。
  正则能扫出名称，但**无法定位写回位置**，且会把「跨槽粘连」的张冠李戴。
  正确做法是按 20B 定长槽 + 上述网格逐槽处理。

★ 写回：名称 ≤19 字节（6 汉字 = 18B 安全）；槽内左对齐、空格补满 20B。
  恒长替换，文件大小不变。
"""

import struct

REC = 20
MAX_BYTES = 19           # 留 1B 余量 → 6 汉字
MAX_HANZI = 6

# ── 记录网格：偏移断点（记录号 → 该记录起额外的字节数） ──────────────
# key = 记录号 k，断点含义：k > PIVOT 时起点额外 +EXTRA
PIVOTS = ((95, 17), (1119, 20), (1523, 20))


def rec_start(k):
    """第 k 条记录的槽起点（相对于 body，即 raw[2:] 的偏移）"""
    o = REC * k
    for p, extra in PIVOTS:
        if k > p:
            o += extra
    return o


def slot_len(k):
    """第 k 条记录实际占用的槽长（绝大多数 20，个别 37/40）"""
    import bisect
    a = rec_start(k)
    b = rec_start(k + 1)
    return b - a


def zb(s):
    return len(s.encode('utf-8'))


def read_name(body, k):
    """读取第 k 条记录的名称（bytes）"""
    o = rec_start(k)
    blk = bytes(body[o:o + REC])
    return blk.split(b'\x00')[0].rstrip(b' ')


def body_of(raw):
    """raw（含 2 字节头）→ (N, body)"""
    n = struct.unpack_from('<H', raw, 0)[0]
    return n, raw[2:]


def extract(raw):
    """→ 名称列表（str，文件顺序，记录 0 起，不含空槽）"""
    out = []
    n, body = body_of(raw)
    for k in range(n):
        nm = read_name(body, k)
        if not nm:
            out.append(None)
            continue
        try:
            out.append(nm.decode('utf-8'))
        except UnicodeDecodeError:
            out.append(nm.decode('latin1'))
    return out


def extract_custom(raw, first=14):
    """→ 记录 14 起的名称（str，跳过空槽）"""
    out = []
    for i, nm in enumerate(extract(raw)):
        if i < first or not nm:
            continue
        out.append(nm)
    return out


def slots(raw, first=14):
    """→ [(k, offset_abs, name_str)]，供写回使用（offset 为整文件绝对偏移）"""
    out = []
    n, body = body_of(raw)
    for k in range(first, n):
        nm = read_name(body, k)
        if not nm:
            continue
        try:
            s = nm.decode('utf-8')
        except UnicodeDecodeError:
            s = nm.decode('latin1')
        out.append((k, 2 + rec_start(k), s))
    return out


def encode_slot(zh, slot_length=REC):
    """中文名 → 槽字节（左对齐 + 空格补满）"""
    b = zh.encode('utf-8')
    assert len(b) <= MAX_BYTES, 'too long: %s (%dB > %dB)' % (zh, len(b), MAX_BYTES)
    if slot_length <= len(b):
        raise ValueError('slot %d 放不下 %d 字节' % (slot_length, len(b)))
    return b + b' ' * (slot_length - len(b))


def fits(zh):
    return zb(zh) <= MAX_BYTES
