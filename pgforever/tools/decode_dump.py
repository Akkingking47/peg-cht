# -*- coding: utf-8 -*-
r"""把 dump 到的 HTML 区域按 UTF-16LE 正确解码并分析结构。"""
import re

path = r'D:\DSH\军事游戏汉化\pgforever\poc\html_dump\regions.txt'
t = open(path, encoding='utf-8').read()

# 从 U(utf16) 行里提取字符串（repr 形式）
for line in t.split('\n'):
    if line.strip().startswith('U(utf16):'):
        s = line.strip()[len('U(utf16): '):]
        s = eval(s)  # repr -> str
        print('== 原始 utf16 解码（可能错位） ==')
        print(s[:1500])
        print()
        # 尝试修正错位：看起来是 1 字节偏移
        print('== 尝试整体重排（按可见字符重建） ==')
        # 找到连续的 CJK/ASCII 可读片段
        chunks = re.findall(r'[\u4e00-\u9fff\uff00-\uffef\u3000-\u303fA-Za-z0-9 .,<>/=#:"\'_\-—（）——]{6,}', s)
        for c in chunks[:30]:
            print('   ', repr(c))
