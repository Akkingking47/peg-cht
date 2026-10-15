# -*- coding: utf-8 -*-
"""从 panel_table_manifest.tsv 生成启动器用的面板表补丁清单（I 组）。

过滤规则（保守）：
  只取 role=RIGHT(+1120) 且 **宽度 <= 400** 的记录 —— 即「右边缘的小元素」
  （菜单、标签、按钮、提示框），与已经补过的工具栏按钮同属一组，必须一起 +1120
  才能对齐；宽度 > 400 的是跨屏长条（idx2 w=626、idx7 w=626、idx9 w=780），
  它们的正确改法是「右端拉伸」，本轮不动（用户没报这两条）。
每条记录要改 2 个 word：x1 @VA、x2 @VA+4（表布局：VA=x1, +2=y1, +4=x2, +6=y2）。
"""
import io, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
SRC = os.path.join(OUT, "panel_table_manifest.tsv")
DST = os.path.join(OUT, "panel_table_v1.tsv")

rows = io.open(SRC, encoding="utf-8").read().splitlines()
head = rows[0].split("\t")
out = ["idx\tva_x1\tx1\tva_x2\tx2\tdx"]
skipped = []
n = 0
for line in rows[1:]:
    c = line.split("\t")
    if len(c) < 13:
        continue
    role, dx, w = c[11], int(c[12]), int(c[6])
    if role != "RIGHT(+1120)":
        continue
    if w > 500:
        skipped.append((c[0], w))
        continue
    va1, x1, x2 = int(c[1]), int(c[2]), int(c[4])
    out.append("%s\t%X\t%d\t%X\t%d\t%d" % (c[0], va1, x1, va1 + 4, x2, dx))
    n += 1
io.open(DST, "w", encoding="utf-8").write("\n".join(out) + "\n")
print("写 %s：%d 条（跳过宽条 %s）" % (DST, n, skipped))
print("前 6 行：")
for l in out[:7]:
    print("  " + l)
