# -*- coding: utf-8 -*-
"""离线验证：各候选字体在 12px 下渲染 "Main U:11 第19军团" 的字距表现。

目的：判断游戏中拉丁字符重叠是「字体本身问题」还是「引擎排版假设」。
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = r"D:\DSH\军事游戏汉化\work\ag-verify"
os.makedirs(OUT, exist_ok=True)

CANDS = [
    (r"D:\OpenPG2\FONTS\deng.ttf", "deng(游戏在用)"),
    (r"D:\OpenPG2\FONTS\verdana.ttf", "verdana(原版)"),
    (r"C:\Windows\Fonts\simhei.ttf", "simhei 黑体"),
    (r"C:\Windows\Fonts\simsun.ttc", "simsun 宋体"),
    (r"C:\Windows\Fonts\simkai.ttf", "simkai 楷体"),
    (r"C:\Windows\Fonts\simfang.ttf", "simfang 仿宋"),
    (r"C:\Windows\Fonts\msyh.ttc", "msyh 雅黑"),
]
TEXT = "Main U:11 第19军团"
SIZE = 12

rows = []
for path, name in CANDS:
    if not os.path.exists(path):
        print("%-16s 不存在" % name)
        continue
    try:
        f = ImageFont.truetype(path, SIZE)
    except Exception as e:
        print("%-16s 载入失败 %s" % (name, e))
        continue
    # 逐字 advance
    adv = []
    for ch in "Main":
        adv.append(f.getlength(ch))
    han = f.getlength("能")
    lat = f.getlength("MM")
    rows.append((name, path, adv, han, lat))
    print("%-16s 'M'=%.1f 'a'=%.1f 'i'=%.1f 'n'=%.1f | '能'=%.1f | 'MM'=%.1f | Main=%.1f"
          % (name, adv[0], adv[1], adv[2], adv[3], han, lat, sum(adv)))

# 拼一张对比图
W = 460
im = Image.new("RGB", (W, 30 * len(rows) + 10), (24, 24, 24))
dr = ImageDraw.Draw(im)
y = 5
for name, path, adv, han, lat in rows:
    f = ImageFont.truetype(path, SIZE)
    dr.text((6, y), TEXT, font=f, fill=(240, 240, 240))
    dr.text((330, y), "%.0f/%.0f" % (sum(adv), han), font=ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 10),
            fill=(160, 200, 255))
    y += 30
im = im.resize((W * 2, im.height * 2), Image.NEAREST)
p = os.path.join(OUT, "font-compare.png")
im.save(p)
print("saved", p)
