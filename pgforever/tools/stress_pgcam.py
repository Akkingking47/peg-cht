# -*- coding: utf-8 -*-
r"""
压力测试：把 pg.pgcam 里第 1 条战役描述改成超长中文，验证不再截断。
用法：python stress_pgcam.py set    # 写入超长文本
      python stress_pgcam.py restore # 还原
"""
import os
import shutil
import subprocess
import sys
import time

CAM = r'D:\PGForever1.021\PG\Scenario\pg.pgcam'
BAK = r'D:\DSH\军事游戏汉化\pgforever\backup\pg.pgcam.stress.bak'

LONG = ('这是一段用于验证中文长文本是否被完整渲染的压力测试描述，'
        '它包含大量汉字与少量 ASCII 数字 1943，'
        '如果补丁正确，末尾的结束标记也应该完整显示出来，不应出现 body 之类的标签泄漏。')


def kill():
    subprocess.run(['taskkill', '/F', '/IM', 'PGForever.exe'], capture_output=True)
    time.sleep(0.8)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'set'
    if mode == 'set':
        if not os.path.exists(BAK):
            os.makedirs(os.path.dirname(BAK), exist_ok=True)
            kill(); shutil.copy2(CAM, BAK); print('备份 ->', BAK)
        d = open(CAM, 'rb').read().decode('utf-16le')
        lines = d.split('\r\n')
        cnt = 0
        for i, l in enumerate(lines):
            f = l.split('\t')
            if len(f) >= 3 and f[0][:2] == '19':
                f[2] = LONG
                lines[i] = '\t'.join(f)
                cnt += 1
        out = '\r\n'.join(lines).encode('utf-16le')
        kill()
        open(CAM, 'wb').write(out)
        print('已替换 %d 条描述为超长中文（%d 字，UTF-8 后约 %d 字节）'
              % (cnt, len(LONG), len(LONG.encode('utf-8'))))
        print('新文件大小 %d（原 %d）' % (len(out) + 0, len(open(BAK, 'rb').read())))
    elif mode == 'restore':
        if os.path.exists(BAK):
            kill(); shutil.copy2(BAK, CAM); print('已还原')
        else:
            print('无备份')
    else:
        print(__doc__)


main()
