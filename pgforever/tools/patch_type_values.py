# -*- coding: utf-8 -*-
r"""
P6b：目标类型 / 移动方式 取值串汉化（exe 硬编码，NUL 终止宽串）

属性面板的 `Target Type` 显示值（Soft/Hard/Air/Naval）与 `Movement Type` 显示值
（Leg/Wheel/Track/Half-trk/Towed/All-Trn/Amtrac）都在 0x80200~0x802C0 这一小块。

约束：译文 UTF-16 字符数 <= 原文；不足补 0x0000；文件大小恒定。
"""
import os
import shutil
import sys

EXE = r'D:\PGForever1.021\PGForever.exe'
BAK = r'D:\DSH\军事游戏汉化\pgforever\backup\PGForever.before-L7b-types.exe'

# 原文 -> 中文
TR = {
    'Amtrac':   '两栖车',
    'All-Trn':  '全地形',
    'Towed':    '牵引',
    'Leg':      '徒步',
    'Wheel':    '轮式',
    'Half-trk': '半履带',
    'Track':    '履带',
    'Naval':    '海上',
    'Air':      '空中',
    'Hard':     '硬目标',
    'Soft':     '软目标',
}


def main():
    data = bytearray(open(EXE, 'rb').read())
    size0 = len(data)
    if not os.path.exists(BAK):
        shutil.copy2(EXE, BAK)
        print('已备份 ->', BAK)

    changed = 0
    for en, zh in TR.items():
        raw = en.encode('utf-16-le') + b'\x00\x00'
        idx = data.find(raw)
        if idx < 0:
            print('  [未找到] %r' % en)
            continue
        avail = len(en)                      # 可用字符数
        if len(zh) > avail:
            print('  [跳过] %r -> %r 超长 (%d > %d)' % (en, zh, len(zh), avail))
            continue
        out = zh + '\x00' * (avail - len(zh))
        data[idx:idx + len(en) * 2] = out.encode('utf-16-le')
        changed += 1
        print('  %-9r -> %-6r @0x%X (占 %d 字符)' % (en, zh, idx, avail))

    assert len(data) == size0, '文件大小变化！'
    open(EXE, 'wb').write(bytes(data))
    print('\n共修改 %d 处，文件大小 %d 字节（未变）' % (changed, len(data)))
    return 0


sys.exit(main())
