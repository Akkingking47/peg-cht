# -*- coding: utf-8 -*-
"""测用户四张截图的几何：品红残留、纯黑区、图2/图3 差异（战略地图破碎量）。"""
import sys
from PIL import Image
import numpy as np

IMGS = [
    ("fig1_moreopt", r"C:\Users\Administrator\.dsh\attachments\v1\objects\44\4412e1c4607d302ec9fab40b5226b733cdc9395e41d30a113937cceafee0f90f"),
    ("fig2_strat_broken", r"C:\Users\Administrator\.dsh\attachments\v1\objects\1c\1c3b6f6ad83eb8b40bfd1e2403feb0fddba87613903aa94c43aaaf4bcc7a8d33"),
    ("fig3_strat_ok", r"C:\Users\Administrator\.dsh\attachments\v1\objects\a7\a70ee1b5d6e31f7872345dd47da886a798b397240e09381b0dd49419a5ef2965"),
    ("fig4_subui", r"C:\Users\Administrator\.dsh\attachments\v1\objects\3a\3abd6006e2b79f17c7e015b53c2bd5affd617780e289cb46cb0bbb038bb6c75a"),
]

def bbox(mask):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()), int(len(xs)))

arrs = {}
for name, p in IMGS:
    im = Image.open(p).convert("RGB")
    a = np.asarray(im).astype(np.int16)
    arrs[name] = a
    R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    magenta = (R > 180) & (G < 90) & (B > 180)
    black = (R < 12) & (G < 12) & (B < 12)
    print("==", name, a.shape)
    print("  品红:", bbox(magenta))
    print("  纯黑:", bbox(black))
    # 每列黑像素数（找竖带）
    bc = black.sum(axis=0)
    cols = [int(x) for x in np.nonzero(bc > a.shape[0] * 0.5)[0]]
    print("  黑列(>50%高):", (cols[0], cols[-1], len(cols)) if cols else None)

# 图2 vs 图3：差异区（战略地图破碎量）
d = np.abs(arrs["fig2_strat_broken"] - arrs["fig3_strat_ok"]).sum(axis=2)
diff = d > 40
print("== fig2 vs fig3 差异 bbox:", bbox(diff))
# 逐列差异计数，看破碎的横向范围
dc = diff.sum(axis=0)
runs, start = [], None
for x, v in enumerate(dc):
    if v > 1000 and start is None:
        start = x
    elif v <= 1000 and start is not None:
        runs.append((start, x - 1)); start = None
if start is not None:
    runs.append((start, len(dc) - 1))
print("  差异列段(>1000):", runs)
