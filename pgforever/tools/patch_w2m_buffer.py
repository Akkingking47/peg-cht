# -*- coding: utf-8 -*-
r"""修复 PG Forever 的 UTF-8 缓冲区溢出 bug。

根因:
  WideCharToMultiByte(CP_UTF8, ...) 在 VA 0x46D64A (文件偏移 0x6CA4A) 处被调用，
  其 cbMultiByte 参数由 `sar eax,1` 算出 —— 即"宽字符数 N"。
  但 UTF-8 下一个汉字需要 3 字节，缓冲区按 N 声明就是差 3 倍 → 截断 + 越界读
  (表现为最后一条文本损坏、HTML 标签 `body>` 泄漏、汉字末位变异)。

补丁:
  文件偏移 0x6CA3E:  D1 F8 (sar eax,1)  ->  D1 E0 (shl eax,1)
  eax 原值 = end-start = 2N (UTF-16 字节差)
    sar eax,1 => N          (原: 不够)
    shl eax,1 => 4N         (新: 纯中文最多 3N, 安全)
  等长 2 字节替换, 文件大小与所有偏移均不变。
"""
import hashlib
import os
import shutil
import sys

EXE = r'D:\PGForever1.021\PGForever.exe'
SITE = 0x6CA3E
OLD = b'\xd1\xf8'          # sar eax,1
NEW = b'\xd1\xe0'          # shl eax,1
BAKDIR = r'D:\DSH\军事游戏汉化\pgforever\backup'


def main():
    raw = open(EXE, 'rb').read()
    print('exe 大小 %d, md5=%s' % (len(raw), hashlib.md5(raw).hexdigest()))

    cur = raw[SITE:SITE + 2]
    if cur == NEW:
        print('已经打过补丁，跳过')
        return
    if cur != OLD:
        print('!! 预期字节 %s，实际 %s，中止' % (OLD.hex(' '), cur.hex(' ')))
        sys.exit(1)

    # 校验上下文，确保改的是那个调用点
    ctx = raw[SITE:SITE + 14]
    print('上下文: %s' % ctx.hex(' '))
    # 期望: d1 f8 50 8b c1 50 56 68 e9 fd 00 00 ff 15
    assert raw[SITE + 12:SITE + 14] == b'\xff\x15', '后随指令不是 call [mem]'
    assert raw[SITE + 7:SITE + 12].hex(' ') == '68 e9 fd 00 00', 'CodePage 不是 65001'

    if '--dry' in sys.argv:
        print('--dry 模式，未写入')
        return

    bak = os.path.join(BAKDIR, 'PGForever.before-w2m-patch.exe')
    shutil.copy2(EXE, bak)
    print('已备份 -> %s' % bak)

    out = raw[:SITE] + NEW + raw[SITE + 2:]
    assert len(out) == len(raw)
    with open(EXE, 'wb') as f:
        f.write(out)

    chk = open(EXE, 'rb').read()
    print('已写入: 0x%X  %s -> %s' % (SITE, OLD.hex(' '), NEW.hex(' ')))
    print('大小 %d (不变: %s), md5=%s' % (len(chk), len(chk) == len(raw), hashlib.md5(chk).hexdigest()))


if __name__ == '__main__':
    main()
