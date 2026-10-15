# -*- coding: utf-8 -*-
r"""
把 L7(exe 硬编码宽字符串)译文原地写回 PGForever.exe。

铁律:
  1. 只改 .rdata/.text/.data 数据区的字符串字节, 不动代码/指针/资源结构
  2. 写前校验该偏移处字节 == 原文 UTF-16LE, 不符即跳过(防错位)
  3. 译文字符数 <= 原文字符数, 不足补 0x0000 作为终止符
  4. 文件大小恒定不变
"""
import hashlib
import json
import os
import shutil
import struct
import sys

EXE = r'D:\PGForever1.021\PGForever.exe'
TERMS = r'D:\DSH\军事游戏汉化\pgforever\work\exe\translations.json'
RAW = r'D:\DSH\军事游戏汉化\pgforever\work\exe\strings-raw.json'
BAK = r'D:\DSH\军事游戏汉化\pgforever\backup\PGForever.before-L7.exe'

# 绝对不许碰的: 命令协议 / 文件名 / 内部键
BLACKLIST = {
    'purchase %d %d %d', 'place %d %d', 'unplace %d %d %d', 'disembark %d %d %d',
    'replace %d', 'load pg', 'load pg "%[^"]" %d', 'load pg %d %d', 'move %d %d',
    'attack %d %d %d', 'rename "%[^"]"', 'cheat "%[^"]"', 'endturn %d',
    'setopt %d %d %d %d %d %d %d', 'campaign %d %d %d', 'prestige %d %d',
    'reserve %d %d %d %d %d "%[^"]"', 'outcome "%[^"]" %d %d "%[^"]"',
    'select reserve', 'select reserve %d', 'select %d %d %d', 'upgrade %d %d',
    'endscn %d', 'prestige %d', 'core %d', 'aux %d', 'sea %d', 'air %d',
    'exp %d', 'str %d', 'ent %d', 'fuel %d', 'ammo %d', 'turns %d',
    'weather %d', 'ground %d', 'set ', 'add ',
    'fog of war', 'all eqp', 'no zoc', 'uber units', 'turbo units', 'force retreat',
    '<tr>', '<div>', '<span style="color: #FF0000">', '<table style="width: 100%%">',
    'PG Forever', ' GAME%03d.SCN.', '# Created by PG Forever, ',
    'open "%s" type mpegvideo alias %s', ' repeat', 'play %s%s',
    'setaudio %s volume to %u', 'stop %s', 'seek %s to start',
    'Accept-Encoding:gzip, deflate', 'Ss%s', 'Component Categories',
}


def main():
    raw = open(EXE, 'rb').read()
    orig_len = len(raw)
    print('exe %d 字节, md5=%s' % (orig_len, hashlib.md5(raw).hexdigest()))

    items = json.load(open(RAW, encoding='utf-8'))
    terms = json.load(open(TERMS, encoding='utf-8'))['terms']

    # 建立 文本 -> [offset]
    by_text = {}
    for it in items:
        by_text.setdefault(it['text'], []).append(it)

    ok, skip_nofind, skip_too_long, skip_black = [], [], [], []
    out = bytearray(raw)

    for en, zh in terms.items():
        if en in BLACKLIST:
            skip_black.append(en)
            continue
        hits = by_text.get(en)
        if not hits:
            skip_nofind.append(en)
            continue

        en_b = en.encode('utf-16-le')
        zh_b = zh.encode('utf-16-le')
        if len(zh_b) > len(en_b):
            skip_too_long.append((en, len(en), len(zh)))
            continue
        # 补零到原长度
        slot = zh_b + b'\x00' * (len(en_b) - len(zh_b))

        for it in hits:
            off = it['offset']
            cur = bytes(out[off:off + len(en_b)])
            if cur != en_b:
                skip_too_long.append((en + ' @0x%X' % off, '字节不匹配', ''))
                continue
            out[off:off + len(slot)] = slot
            ok.append((off, en, zh))

    print()
    print('✔ 已替换 %d 处' % len(ok))
    if skip_nofind:
        print('  ! 未找到偏移 %d 条: %s' % (len(skip_nofind), skip_nofind[:5]))
    if skip_too_long:
        print('  ! 长度或校验不符 %d 条:' % len(skip_too_long))
        for x in skip_too_long[:10]:
            print('      %s  (原%d / 译%r)' % (x[0], x[1], x[2]))
    if skip_black:
        print('  - 黑名单跳过 %d 条' % len(skip_black))

    if '--dry' in sys.argv:
        print('--dry 未写入')
        return

    if len(ok) == 0:
        print('没有任何替换, 中止写入')
        return

    shutil.copy2(EXE, BAK)
    print('已备份 -> %s' % os.path.basename(BAK))

    res = bytes(out)
    assert len(res) == orig_len, '大小变了!'
    open(EXE, 'wb').write(res)

    chk = open(EXE, 'rb').read()
    print('写入完成: %d 字节(不变=%s), md5=%s' % (len(chk), len(chk) == orig_len, hashlib.md5(chk).hexdigest()))
    print()
    print('抽样校验:')
    for off, en, zh in ok[:6]:
        got = chk[off:off + len(en) * 2].decode('utf-16-le').rstrip('\x00')
        print('  0x%X  %-28s -> %s' % (off, en, got))


if __name__ == '__main__':
    main()
