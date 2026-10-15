# -*- coding: utf-8 -*-
r"""
新回合横幅汉化 (P5) —— 就地等长替换 exe 内的 UTF-16LE 常量。

背景:
  新回合横幅由 PGForever.exe 的 0x4074A0 函数构造:
      newturn.htm 模板
      → HTMLayoutVisitElements 按 id 找 <span id=Side/Date/Weather/>
      → SetElementInnerText16 注入文本
  注入的文本来自 exe 常量表, 改 newturn.htm 无效。

本补丁替换的常量 (全部在 .rdata, VA-file 差 = 0x400E00):
  阵营    0x482A08 'Axis'      0x482A14 'Allied'
  月份表  0x482774..0x48281C  December..January   (指针表 @0x482AF0 索引1..12)
  天气    0x48282C..0x482884  Frozen/Muddy/Dry/Snowing/Raining/Overcast/Clear

铁律: 译文字符数 <= 原文字符数; 不足补 0x0000; 写前校验偏移字节 == 原文; 文件大小恒定。
"""
import hashlib
import os
import shutil
import sys

EXE = r'D:\PGForever1.021\PGForever.exe'
BAK = r'D:\DSH\军事游戏汉化\pgforever\backup\PGForever.before-banner-P1P2P3P4.exe'
RDATA_DELTA = 0x400E00          # VA - file   (.rdata)

# (VA, 原文, 译文)
ITEMS = [
    # ---- 阵营 ----
    (0x482A08, 'Axis', '轴心'),
    (0x482A14, 'Allied', '盟军'),
    # ---- 日期格式串  %s=月  %d=日  19%d=年 ----
    (0x482B24, '%s %d, 19%d', '%s%d日, 19%d'),
    # ---- 月份 (指针表 @0x482AF0: idx1=January ... idx12=December) ----
    (0x48281C, 'January', '1月'),
    (0x482808, 'February', '2月'),
    (0x4827FC, 'March', '3月'),
    (0x4827F0, 'April', '4月'),
    (0x4827E8, 'May', '5月'),
    (0x4827DC, 'June', '6月'),
    (0x4827D0, 'July', '7月'),
    (0x4827C0, 'August', '8月'),
    (0x4827AC, 'September', '9月'),
    (0x48279C, 'October', '10月'),
    (0x482788, 'November', '11月'),
    (0x482774, 'December', '12月'),
    # ---- 天气 ----
    (0x48282C, 'Frozen', '冰冻'),
    (0x48283C, 'Muddy', '泥泞'),
    (0x482848, 'Dry', '干燥'),
    (0x482850, 'Snowing', '降雪'),
    (0x482860, 'Raining', '降雨'),
    (0x482870, 'Overcast', '阴天'),
    (0x482884, 'Clear', '晴朗'),
]


def run(apply=False):
    raw = open(EXE, 'rb').read()
    orig_len = len(raw)
    print('exe %d 字节  md5=%s' % (orig_len, hashlib.md5(raw).hexdigest()))
    print()

    out = bytearray(raw)
    ok, bad, already = [], [], []
    for va, en, zh in ITEMS:
        off = va - RDATA_DELTA
        en_b = en.encode('utf-16-le')
        zh_b = zh.encode('utf-16-le')
        cur = bytes(raw[off:off + len(en_b)])
        nxt = raw[off + len(en_b):off + len(en_b) + 2]
        if cur == zh_b + b'\x00' * (len(en_b) - len(zh_b)) and len(zh_b) <= len(en_b):
            already.append((va, en, zh))
            continue
        if cur != en_b or nxt != b'\x00\x00':
            bad.append((va, en, cur, nxt))
            continue
        if len(zh_b) > len(en_b):
            bad.append((va, en, '译文过长'.encode('utf-8'), b''))
            continue
        slot = zh_b + b'\x00' * (len(en_b) - len(zh_b))
        out[off:off + len(slot)] = slot
        ok.append((off, va, en, zh))

    for off, va, en, zh in ok:
        print('  OK  0x%06X (VA 0x%06X)  %-10s -> %-4s   %d/%d 字符'
              % (off, va, en, zh, len(zh), len(en)))
    for va, en, zh in already:
        print('  已译 VA 0x%06X  %-10s -> %s' % (va, en, zh))
    for va, en, cur, nxt in bad:
        print('  BAD VA 0x%06X  %-10s  实际=%r 终止符=%r' % (va, en, cur, nxt))

    print()
    print('可替换 %d / 已译 %d / 异常 %d / 共 %d'
          % (len(ok), len(already), len(bad), len(ITEMS)))
    if bad:
        print('有校验失败项, 中止')
        return
    if not ok:
        print('全部已应用, 无需写入')
        return
    if not apply:
        print('--dry (未写入)')
        return

    os.makedirs(os.path.dirname(BAK), exist_ok=True)
    if not os.path.exists(BAK):
        shutil.copy2(EXE, BAK)
        print('已备份 -> %s' % os.path.basename(BAK))
    else:
        print('备份已存在 -> %s' % os.path.basename(BAK))

    res = bytes(out)
    assert len(res) == orig_len, '文件大小变了!'
    open(EXE, 'wb').write(res)
    chk = open(EXE, 'rb').read()
    print('写入完成 %d 字节 (大小不变=%s) md5=%s'
          % (len(chk), len(chk) == orig_len, hashlib.md5(chk).hexdigest()))
    print()
    print('抽样校验:')
    for off, va, en, zh in ok[:6]:
        n = len(en)
        got = chk[off:off + n * 2].decode('utf-16-le').rstrip('\x00')
        print('  0x%06X  %-10s -> %r' % (off, en, got))


if __name__ == '__main__':
    run(apply='--apply' in sys.argv)
