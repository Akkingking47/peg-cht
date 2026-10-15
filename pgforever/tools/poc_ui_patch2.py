# -*- coding: utf-8 -*-
"""
PGForever UI 汉化 POC 第二轮：判别实验
目的：区分「文件编码被误判」与「渲染层不支持 CJK」

设计（同一文件内并列对照）：
  tab1  数字实体（纯 ASCII 字节）        → 若正常显示，说明解析+渲染都 OK，问题在文件编码
  tab2  裸中文（UTF-8 无 BOM）           → 与 tab1 对照
  tab3  数字实体 + font-family: SimSun   → 测字体族是否影响
  tab4  裸中文  + font-family: SimSun
  tab5  数字实体 + font-family: Microsoft YaHei
  START/Exit 用实体
"""
import os

SRC = r'D:\DSH\军事游戏汉化\pgforever\backup\origin\Default\UI\menu.htm'
DST = r'D:\PGForever1.021\Default\UI\menu.htm'

text = open(SRC, 'rb').read().decode('utf-8')

# 战役 / 场景 / 载入存档 / 回放录像 / 联机对战 的十进制实体
E = {
    '战役': '&#25112;&#24441;',
    '场景': '&#22330;&#26223;',
    '载入存档': '&#36733;&#20837;&#23384;&#26723;',
    '回放录像': '&#22238;&#25918;&#24405;&#20687;',
    '联机对战': '&#32852;&#26426;&#23545;&#25112;',
}

RULES = [
    # tab1: 实体，无字体指定
    ('>Campaign<', '>%s<' % E['战役']),
    # tab2: 裸中文
    ('>Scenario<', '>场景<'),
    # tab3: 实体 + SimSun
    ('>Load Game<', '>%s<' % E['载入存档']),
    # tab4: 裸中文 + SimSun
    ('>Replay Game<', '>回放录像<'),
    # tab5: 实体 + Microsoft YaHei
    ('>Join Online Game<', '>%s<' % E['联机对战']),
    ('>START!<', '>&#24320;&#22987;<'),
    ('>Exit<', '>&#36864;&#20986;<'),
]

out = text
for en, zh in RULES:
    n = out.count(en)
    print('%-24s -> %-34s x%d' % (en, zh, n))
    assert n > 0, '未找到 %s' % en
    out = out.replace(en, zh)

# 给 tab3/tab4 与 tab5 各自加字体，需在替换后按可用文本定位
out = out.replace('<td.tab type="radio" name="mode">%s</td.tab>' % E['载入存档'],
                  '<td.tab type="radio" name="mode" style="font-family: SimSun">%s</td.tab>' % E['载入存档'])
out = out.replace('<td.tab type="radio" name="mode">回放录像</td.tab>',
                  '<td.tab type="radio" name="mode" style="font-family: SimSun">回放录像</td.tab>')
out = out.replace('<td.tab type="radio" name="mode">%s</td.tab>' % E['联机对战'],
                  '<td.tab type="radio" name="mode" style="font-family: \'Microsoft YaHei\'">%s</td.tab>' % E['联机对战'])

assert out.count('%%') == text.count('%%')
assert 'font-family: SimSun' in out and 'Microsoft YaHei' in out, '字体注入失败'
print('字体注入 OK，%% 转义校验通过')

open(DST, 'wb').write(out.encode('utf-8'))
print('written (UTF-8 no BOM): %s' % DST)
