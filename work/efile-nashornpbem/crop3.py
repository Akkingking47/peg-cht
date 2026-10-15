# -*- coding: utf-8 -*-
"""放大 2026-09-24 13:23 三张实机截图的关�键区域（纯取证，不改任何游戏文件）。"""
import os
from PIL import Image

SRC = r"C:/Users/Administrator/.workbuddy/clipboard-images"
OUT = r"D:/DSH/军事游戏汉化/work/efile-nashornpbem/out"
os.makedirs(OUT, exist_ok=True)

FILES = {
    "a": "clipboard-2026-09-24T05-23-53-789Z-864d247c.jpg",
    "b": "clipboard-2026-09-24T05-23-53-793Z-4aad95fe.jpg",
    "c": "clipboard-2026-09-24T05-23-53-797Z-cfb79b2c.jpg",
}

# (名字, x0, y0, x1, y1, zoom)
REGIONS = [
    ("topL",  100,   0,  400,  28, 3),
    ("topC",  770,   0, 1160,  28, 3),
    ("topR", 1350,   0, 1700,  28, 3),
    ("botL",  150, 1004,  520, 1040, 3),
    ("botR", 1280, 1004, 1920, 1040, 3),
]

def crop(im, box, z):
    c = im.crop(box)
    return c.resize((c.width * z, c.height * z), Image.NEAREST)

for tag, fn in FILES.items():
    p = os.path.join(SRC, fn)
    im = Image.open(p).convert("RGB")
    for name, x0, y0, x1, y1, z in REGIONS:
        crop(im, (x0, y0, x1, y1), z).save(os.path.join(OUT, "z5-%s-%s.png" % (tag, name)))
    # 中部大图：dialog / tooltip 区
    crop(im, (500, 150, 1000, 480), 2).save(os.path.join(OUT, "z5-%s-mid.png" % tag))
    print(tag, fn, im.size, "done")
