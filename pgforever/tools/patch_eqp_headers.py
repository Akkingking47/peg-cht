# -*- coding: utf-8 -*-
r"""
P6：装备表列头模板汉化（exe 硬编码）

背景
    属性面板里的 `Target Type`、`Close Defense` 等标签并不来自 htm，而是 exe 在
    0x8BA80 处保存的一行 **TAB 分隔的列头模板**（33 个字段，共 750 字节），
    渲染时按位置拼字段。因此只汉化 htm 不够，必须同时改这里。

约束（与 P3 同铁律）
    * 译文 UTF-16 字符数 <= 原文字符数；不足用 **半角空格** 补齐，
      保持每个字段的字节长度与 TAB 位置完全不变 → 文件大小恒定 753664。
    * 只做等长就地替换，不改指针。

偏移依赖：0x8BA80 / 750 字节（原始 exe）
"""
import os
import shutil
import sys

EXE = r'D:\PGForever1.021\PGForever.exe'
BAK = r'D:\DSH\军事游戏汉化\pgforever\backup\PGForever.before-L7b-headers.exe'
OFF = 0x8BA80
NBYTES = 750

# 字段索引 -> 中文（按上一步解析出的 33 字段顺序）
TR = {
    0: '# ID',
    1: '名称',
    2: '类别',
    3: '软攻',
    4: '硬攻',
    5: '空攻',
    6: '海攻',
    7: '地防',
    8: '空防',
    9: '抵近防御',
    10: '移动方式',
    11: '先手',
    12: '射程',
    13: '侦察',
    14: '目标类型',
    15: '移动',
    16: '最大燃料',
    17: '最大弹药',
    18: '造价',
    19: '图标',
    20: '动画',
    21: '月份',
    22: '年份',
    23: '上一年',
    24: '轰炸机特技',
    25: '无视工事',
    26: '可带建制运输',
    27: '可带海上运输',
    28: '可带空中运输',
    29: '可空降',
    30: '可架桥',
    31: '喷气',
    32: '国旗',
}


def parse_header(data, off, nbytes):
    """按 TAB/CRLF 切分固定字节块，返回 [(字段原文, 起始偏移, 字节长度), ...]。"""
    fields = []
    i = off
    end = off + nbytes
    start = i
    buf = []
    while i < end:
        ch = data[i] | (data[i + 1] << 8)
        if ch in (9, 0x0D, 0x0A, 0):
            fields.append((''.join(buf), start, i - start))
            buf = []
            i += 2
            if ch == 0x0D and i < end and (data[i] | (data[i + 1] << 8)) == 0x0A:
                i += 2
            start = i
            if ch == 0:
                break
            continue
        buf.append(chr(ch))
        i += 2
    return fields


def main():
    data = bytearray(open(EXE, 'rb').read())
    size0 = len(data)
    fields = parse_header(bytes(data), OFF, NBYTES)
    print('解析到 %d 个字段' % len(fields))

    if len(fields) != 33:
        print('!! 字段数异常，中止（预期 33，实得 %d）' % len(fields))
        return 1

    # 备份
    if not os.path.exists(BAK):
        shutil.copy2(EXE, BAK)
        print('已备份 ->', BAK)

    changed = 0
    for idx, (orig, off, blen) in enumerate(fields):
        zh = TR.get(idx, orig)
        n = blen // 2          # 可用 UTF-16 字符数（不含 TAB）
        if len(zh) > n:
            print('  [跳过] 字段%d %r -> %r 超长 (%d > %d)' % (idx, orig, zh, len(zh), n))
            continue
        raw = zh + ' ' * (n - len(zh))       # 空格补齐，保持字节长度
        assert len(raw.encode('utf-16-le')) == blen
        data[off:off + blen] = raw.encode('utf-16-le')
        if zh != orig:
            changed += 1
            print('  %2d  %-26r -> %-14r (占 %d 字符)' % (idx, orig, zh, n))

    assert len(data) == size0, '文件大小变化！'
    open(EXE, 'wb').write(bytes(data))
    print('\n共修改 %d 个字段，文件大小 %d 字节（未变）' % (changed, len(data)))
    return 0


sys.exit(main())
