# -*- coding: utf-8 -*-
from PIL import Image
import os
SRC = r"C:\Users\Administrator\.workbuddy\clipboard-images"
OUT = r"D:/DSH/军事游戏汉化/work/efile-nashornpbem/out"
im4 = Image.open(os.path.join(SRC, "clipboard-2026-09-24T05-00-09-836Z-cb9becc6.jpg"))
W, H = im4.size
print("img4", W, H)


def crop(im, box, scale, name):
    c = im.crop(box)
    c = c.resize((c.width * scale, c.height * scale), Image.LANCZOS)
    p = os.path.join(OUT, name + ".png")
    c.save(p)
    print(name, c.size, p)


# panel title line (top of the unit panel)
crop(im4, (860, 322, 1020, 348), 9, "z4-paneltitle")
# panel name / U line
crop(im4, (860, 348, 1020, 400), 7, "z4-panelname")
im1 = Image.open(os.path.join(SRC, "clipboard-2026-09-24T05-00-09-829Z-2a1f8573.jpg"))
crop(im1, (700, 988, 1600, 1020), 4, "z1-splashbar")
