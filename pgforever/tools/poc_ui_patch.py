# -*- coding: utf-8 -*-
"""
PGForever UI 汉化 POC：把主菜单可见文本改为中文，用于验证渲染与编码。
从 backup/origin 读取原文件，写出到游戏目录；原文件始终保留在 backup。
"""
import os
import shutil

SRC = r'D:\DSH\军事游戏汉化\pgforever\backup\origin\Default\UI\menu.htm'
DST = r'D:\PGForever1.021\Default\UI\menu.htm'

raw = open(SRC, 'rb').read()
orig = raw.decode('utf-8')

# (英文原文, 中文译文) —— 只改动可见标签，%% 转义与标签结构一律保留
RULES = [
    ('>Campaign<', '>战役<'),
    ('>Scenario<', '>场景<'),
    ('>Load Game<', '>载入存档<'),
    ('>Replay Game<', '>回放录像<'),
    ('>Join Online Game<', '>联机对战<'),
    ('>START!<', '>开始!<'),
    ('>Exit<', '>退出<'),
]

text = orig
applied = 0
for en, zh in RULES:
    n = text.count(en)
    if n == 0:
        print('[WARN] 未找到: %s' % en)
        continue
    text = text.replace(en, zh)
    applied += n
    print('替换 %-24s -> %-10s x%d' % (en, zh, n))

assert applied > 0, '没有任何替换，中止'

# 校验：%% 转义数量必须完全一致（防止误伤 printf 格式）
assert orig.count('%%') == text.count('%%'), '%% 转义数量变化，中止'
print('%% 转义校验通过 (%d 处)' % orig.count('%%'))

mode = os.environ.get('POC_ENC', 'utf8')
if mode == 'utf8':
    out = text.encode('utf-8')                      # 无 BOM
    tag = 'UTF-8 无 BOM'
elif mode == 'utf8bom':
    out = b'\xef\xbb\xbf' + text.encode('utf-8')     # 带 BOM
    tag = 'UTF-8 with BOM'
elif mode == 'gbk':
    out = text.encode('gbk')
    tag = 'GBK'
print('写出编码: %s, 字节数 %d (原文 %d)' % (tag, len(out), len(raw)))

with open(DST, 'wb') as f:
    f.write(out)
print('已写入: %s' % DST)
