# -*- coding: utf-8 -*-
"""一次性：修正 gen_tmsg.py 末尾的汉字统计行（原写法取到的是 src 列）。"""
import io

P = r'D:\DSH\军事游戏汉化\work\basekorp\gen_tmsg.py'
s = io.open(P, encoding='utf-8').read()

old = ("    nz = sum(1 for _, d, _ in [(a, b, c) for a, b, c in out]\n"
       "             if any('\\u4e00' <= ch <= '\\u9fff' for ch in d))\n"
       "    pass\n")
new = "    nz = sum(1 for _, _, d in out if any('\\u4e00' <= ch <= '\\u9fff' for ch in d))\n"

assert old in s, 'old not found'
s = s.replace(old, new)
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('fixed')
