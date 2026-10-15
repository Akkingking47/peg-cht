# -*- coding: utf-8 -*-
r"""实验：修改 pg.pgcam 的 Entry 描述，验证截断是否与文本长度/累积有关。
用法: python exp_cam_len.py <mode>
  short  —— 所有 Entry 描述改为极短（5 字）
  only4  —— 只把第 4 条(1943 West)改短，其余保持
  long4  —— 把第 4 条改为超长中文
"""
import os
import re
import shutil
import subprocess
import sys
import time

SRC = r'D:\PGForever1.021\PG\Scenario\pg.pgcam'
BAK = r'D:\DSH\军事游戏汉化\pgforever\backup\origin\PG\Scenario\pg.pgcam'
SAFE = r'D:\DSH\军事游戏汉化\pgforever\work\pg\pgcam.deployed.bak'


def read_lines():
    raw = open(SRC, 'rb').read()
    return raw, raw.decode('utf-16').split('\r\n')


def write_lines(lines):
    body = '\r\n'.join(lines).encode('utf-16-le')
    open(SRC, 'wb').write(b'\xff\xfe' + body)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'short'

    # 首次运行：把当前"已部署译文"另存为基线
    if not os.path.exists(SAFE):
        shutil.copy2(SRC, SAFE)
        print('已保存部署基线 -> %s' % os.path.basename(SAFE))
    shutil.copy2(SAFE, SRC)

    raw, lines = read_lines()
    # Entry 行特征：>=6 列，第4、5列为数字，第2列为内部键（无 .pgscn）
    n = 0
    for i, l in enumerate(lines):
        c = l.split('\t')
        if len(c) >= 6 and c[3].strip().isdigit() and c[4].strip().isdigit() and '.pgscn' not in c[1]:
            n += 1
            if mode == 'short':
                c[2] = '短描述%d' % n
            elif mode == 'only4' and n == 4:
                c[2] = '短描述4'
            elif mode == 'long4' and n == 4:
                c[2] = '这是一段特意写得非常长的中文描述用于测试渲染缓冲区到底能容纳多少字符以及出现截断时的具体表现形态' * 1
            lines[i] = '\t'.join(c)
    write_lines(lines)
    print('模式=%s 已改写 %d 条 Entry 描述' % (mode, n))
    for l in lines[12:17]:
        print('   ', l[:110])


if __name__ == '__main__':
    main()
