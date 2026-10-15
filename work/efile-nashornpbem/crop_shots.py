# -*- coding: utf-8 -*-
"""Crop + upscale regions of the user's 4 clipboard screenshots for close reading."""
import os
from PIL import Image

SRC = r"C:\Users\Administrator\.workbuddy\clipboard-images"
OUT = r"D:/DSH/军事游戏汉化/work/efile-nashornpbem/out"
os.makedirs(OUT, exist_ok=True)

files = sorted(f for f in os.listdir(SRC)
               if f.startswith("clipboard-2026-09-24T05-00-09") and f.endswith(".jpg"))
print("found", files)

# (source file index, out name, rel box, scale)
JOBS = [
    (0, "z1-splash-bottom", (0.34, 0.945, 0.96, 1.000), 4),
    (1, "z2-dialog",        (0.340, 0.270, 0.660, 0.730), 3),
    (1, "z2-dialog-title",  (0.400, 0.285, 0.520, 0.320), 6),
    (2, "z3-topbar",        (0.400, 0.000, 0.600, 0.045), 6),
    (3, "z4-unitpanel",     (0.425, 0.290, 0.580, 0.730), 4),
    (3, "z4-bottombar",     (0.000, 0.945, 1.000, 1.000), 4),
]

for idx, name, box, scale in JOBS:
    p = os.path.join(SRC, files[idx])
    im = Image.open(p)
    W, H = im.size
    x0, y0, x1, y1 = (int(box[0] * W), int(box[1] * H), int(box[2] * W), int(box[3] * H))
    c = im.crop((x0, y0, x1, y1))
    c = c.resize((c.width * scale, c.height * scale), Image.LANCZOS)
    o = os.path.join(OUT, name + ".png")
    c.save(o)
    print("%-20s src=%dx%d box=%s -> %dx%d  %s" % (name, W, H, (x0, y0, x1, y1), c.width, c.height, o))
