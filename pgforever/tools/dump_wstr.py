# -*- coding: utf-8 -*-
"""转储 exe 指定文件偏移附近的宽字符串，用于核对硬编码 UI 文案。"""
import sys

path = r'D:\PGForever1.021\PGForever.exe'
d = open(path, 'rb').read()

starts = [int(x, 16) for x in sys.argv[1:]] or [0x8baa0]
for st in starts:
    print('=== 0x%X 附近 ===' % st)
    lo = max(0, st - 0x80)
    hi = min(len(d), st + 0x180)
    i = lo
    while i < hi - 1:
        # 找一个宽串起点：低字节可打印 ASCII，高字节 0
        if 32 <= d[i] < 0x7f and d[i + 1] == 0:
            j = i
            while j + 1 < len(d) and d[j + 1] == 0 and 32 <= d[j] < 0x7f:
                j += 2
            s = d[i:j].decode('utf-16-le')
            if len(s) >= 3:
                print('  +0x%06X  %r' % (i, s))
            i = j
        else:
            i += 1
