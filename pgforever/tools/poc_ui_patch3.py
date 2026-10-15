# -*- coding: utf-8 -*-
"""
PGForever UI 汉化 POC 第三轮：确定文件编码
上一轮已证明：HTML 数字实体（ASCII 字节）中文渲染完全正常 → 渲染层 OK，问题在文件编码。
本轮：全部标签用裸中文，文件写为 UTF-8 with BOM，看引擎是否按 BOM 识别。
（保留 tab1 为实体对照，万一 BOM 无效也能证明渲染无问题）
"""
import os
import sys

SRC = r'D:\DSH\军事游戏汉化\pgforever\backup\origin\Default\UI\menu.htm'
DST = r'D:\PGForever1.021\Default\UI\menu.htm'

text = open(SRC, 'rb').read().decode('utf-8')

RULES = [
    ('>Campaign<', '>&#25112;&#24441;<'),   # 实体对照
    ('>Scenario<', '>场景<'),
    ('>Load Game<', '>载入存档<'),
    ('>Replay Game<', '>回放录像<'),
    ('>Join Online Game<', '>联机对战<'),
    ('>START!<', '>开始!<'),
    ('>Exit<', '>退出<'),
]

out = text
for en, zh in RULES:
    n = out.count(en)
    assert n > 0, '未找到 %s' % en
    out = out.replace(en, zh)
    print('%-22s -> %-12s x%d' % (en, zh, n))

assert out.count('%%') == text.count('%%')
print('%% 转义校验通过 (%d 处)' % out.count('%%'))

enc = sys.argv[1] if len(sys.argv) > 1 else 'utf8bom'
if enc == 'utf8bom':
    data = b'\xef\xbb\xbf' + out.encode('utf-8')
    label = 'UTF-8 with BOM'
elif enc == 'utf8':
    data = out.encode('utf-8')
    label = 'UTF-8 no BOM'
elif enc == 'gbk':
    data = out.encode('gbk')
    label = 'GBK'
elif enc == 'meta':
    out2 = out.replace('<html.dialog>', '<html.dialog>\n<meta charset="utf-8">', 1)
    data = out2.encode('utf-8')
    label = 'UTF-8 no BOM + <meta charset=utf-8>'
else:
    raise SystemExit('unknown enc: %s' % enc)

open(DST, 'wb').write(data)
print('写出编码: %s  (%d bytes)' % (label, len(data)))
