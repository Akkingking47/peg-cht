# -*- coding: utf-8 -*-
"""只读文本资产清点：统计各层可翻译文本量（行数/字符数）。"""
import os, sys, glob, io, collections

def read(p):
    return open(p, 'rb').read()


def lines_crlf(b):
    return b.decode('latin1').split('\r\n')


def inv(root):
    print('#### %s' % root)
    out = collections.OrderedDict()

    # 1 场景 .scn/.scl
    for pat in ('*.scn', '*.scl', '*.SCN', '*.SCL'):
        fs = glob.glob(os.path.join(root, pat))
        if not fs:
            continue
        names = brief = auth = 0
        for f in fs:
            L = lines_crlf(read(f))
            if len(L) > 2:
                names += 1
                # 简报块：末尾连续非空文本行
                cnt = 0
                for l in reversed(L):
                    if not l.strip():
                        continue
                    if len(l) > 30 and l.count(' ') >= 3:
                        cnt += 1
                    else:
                        break
                brief += cnt
                auth += 1
        print('  %-6s 文件 %4d ｜ 场景名 %4d ｜ 作者/日期行 %4d ｜ 简报行合计 %5d'
              % (pat, len(fs), names, auth, brief))

    # 2 编成 .org / .oob
    for pat in ('*.org', '*.oob'):
        fs = glob.glob(os.path.join(root, pat))
        tot = 0
        chars = 0
        for f in fs:
            for l in lines_crlf(read(f)):
                if len(l) > 12:
                    tot += 1
                    chars += len(l)
        print('  %-6s 文件 %4d ｜ 含名称行 %5d ｜ 字符 %8d' % (pat, len(fs), tot, chars))

    # 3 外部文本
    for pat in ('*.txt', '*.TXT', '*.dat', '*.DAT'):
        fs = glob.glob(os.path.join(root, pat))
        tot = chars = 0
        for f in fs:
            b = read(f)
            try:
                s = b.decode('latin1')
            except Exception:
                continue
            ls = s.split('\r\n')
            tot += len(ls)
            chars += len(s)
        if fs:
            print('  %-6s 文件 %4d ｜ 行 %6d ｜ 字符 %9d' % (pat, len(fs), tot, chars))

    # 4 单位图形
    for pat in ('*.bit', '*.BIT'):
        fs = glob.glob(os.path.join(root, pat))
        if fs:
            print('  %-6s 文件 %4d（图形，含字者需目视抽查）' % (pat, len(fs)))
    for pat in ('*.bmp', '*.BMP'):
        fs = glob.glob(os.path.join(root, pat))
        if fs:
            print('  %-6s 文件 %4d' % (pat, len(fs)))


if __name__ == '__main__':
    for r in sys.argv[1:]:
        inv(r)
