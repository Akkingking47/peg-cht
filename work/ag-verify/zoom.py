# -*- coding: utf-8 -*-
"""放大用户实机截图的「能力」行与单位名行，便于肉眼核对。"""
import os
from PIL import Image

SRC = r"C:\Users\Administrator\.workbuddy\clipboard-images"
OUT = r"D:\DSH\军事游戏汉化\work\ag-verify"
os.makedirs(OUT, exist_ok=True)

F1 = os.path.join(SRC, "clipboard-2026-09-24T14-31-03-783Z-e809df37.png")
F2 = os.path.join(SRC, "clipboard-2026-09-24T14-31-03-784Z-ef0d4833.png")

JOBS = [
    (F1, "u1-ability", (0.0, 0.00, 1.0, 0.075), 8),   # 顶部「能力 -」
    (F1, "u1-unitname", (0.0, 0.22, 1.0, 0.34), 6),   # 单位名
    (F1, "u1-left", (0.0, 0.02, 0.42, 0.24), 8),      # STOP / Main / U:11
    (F2, "u2-ability", (0.0, 0.00, 1.0, 0.075), 8),
    (F2, "u2-unitname", (0.0, 0.22, 1.0, 0.34), 6),
    (F2, "u2-left", (0.0, 0.02, 0.42, 0.24), 8),
]

for f, name, box, sc in JOBS:
    im = Image.open(f).convert("RGB")
    W, H = im.size
    px = (int(box[0] * W), int(box[1] * H), int(box[2] * W), int(box[3] * H))
    c = im.crop(px)
    c = c.resize((c.width * sc, c.height * sc), Image.NEAREST)
    p = os.path.join(OUT, name + ".png")
    c.save(p)
    print("%-14s %s  %dx%d -> %dx%d" % (name, px, c.width // sc, c.height // sc, c.width, c.height))
