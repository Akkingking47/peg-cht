# -*- coding: utf-8 -*-
"""截图取证：把一张实机截图按区域裁剪并最近邻放大，便于逐像素判读。

用法：
    python crop_shot.py <源png> [前缀]

产物落在 work/peg/out/ 下，命名 <前缀>-<区域名>.png。
区域与倍率在 BOXES 里改；坐标是**截图坐标**（含窗口边框），不是游戏内容坐标。
"""
import os
import sys

from PIL import Image

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


OUT = os.path.join(WS, "work", "peg", "out")

# (区域名, (left, top, right, bottom), 放大倍率)
BOXES = [
    ("right-col", (790, 20, 1040, 620), 2),
    ("tip-zoom", (786, 25, 1040, 200), 5),
    ("btn-zoom", (715, 25, 985, 200), 4),
    ("right-edge", (925, 20, 1040, 807), 2),
    ("icon-zoom", (800, 25, 975, 165), 4),
    ("bottom-right", (860, 520, 1040, 807), 2),
    ("bottom-bar", (0, 560, 1040, 660), 1),
    ("bottom-strip", (0, 630, 1040, 807), 1),
    ("top-bar", (0, 20, 1040, 60), 2),
]


def main():
    if len(sys.argv) < 2:
        print("用法: python crop_shot.py <源png> [前缀]")
        return 1
    src = sys.argv[1]
    prefix = sys.argv[2] if len(sys.argv) > 2 else "shot"
    im = Image.open(src).convert("RGB")
    print("源尺寸:", im.size, src)
    for name, box, scale in BOXES:
        box = (max(0, box[0]), max(0, box[1]),
               min(im.width, box[2]), min(im.height, box[3]))
        c = im.crop(box)
        if scale != 1:
            c = c.resize((c.width * scale, c.height * scale), Image.NEAREST)
        p = os.path.join(OUT, "%s-%s.png" % (prefix, name))
        c.save(p)
        print("  %-14s %-12s x%d -> %s" % (name, str(box), scale, p))
    return 0


if __name__ == "__main__":
    sys.exit(main())
