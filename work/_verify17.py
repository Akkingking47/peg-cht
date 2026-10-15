# -*- coding: utf-8 -*-
"""独立自检 part-17.tsv"""
import sys

SRC = r"d:/DSH/军事游戏汉化/work/atomic/chunks/chunk-17.tsv"
DST = r"d:/DSH/军事游戏汉化/work/atomic/zh/part-17.tsv"

ok = True


def fail(msg):
    global ok
    ok = False
    print("FAIL:", msg)


src_raw = open(SRC, "rb").read()
dst_raw = open(DST, "rb").read()

# 1 BOM
if dst_raw.startswith(b"\xef\xbb\xbf"):
    fail("输出含 BOM")

# 2 CRLF / 行尾
src_lines = src_raw.split(b"\r\n")
dst_lines = dst_raw.split(b"\r\n")
if src_lines[-1] != b"" or dst_lines[-1] != b"":
    fail("末尾缺少 CRLF 或存在多余内容")
if b"\n" in dst_raw.replace(b"\r\n", b""):
    fail("存在裸 LF")
src_l = src_lines[:-1]
dst_l = dst_lines[:-1]

# 3 行数
if len(src_l) != len(dst_l):
    fail("行数不一致 %d vs %d" % (len(src_l), len(dst_l)))
    sys.exit(1)
if len(dst_l) != 400:
    fail("输出行数 != 400")

kept = []
for i, (s, d) in enumerate(zip(src_l, dst_l), 1):
    # 4 恰好 1 个 TAB
    if d.count(b"\t") != 1:
        fail("第%d行 TAB 数=%d" % (i, d.count(b"\t")))
        continue
    a, b = d.split(b"\t")
    # 5 首列逐字节等于原文
    if a != s:
        fail("第%d行首列不匹配: %r != %r" % (i, a, s))
    # 6 空行/空译文
    if not b:
        fail("第%d行译文为空" % i)
    # 7 括号数量一致
    sd = s.decode("utf-8")
    dd = b.decode("utf-8")
    for ch in "/[]()":
        if sd.count(ch) != dd.count(ch):
            fail("第%d行 %r 数量不一致: %d vs %d [%s]" % (i, ch, sd.count(ch), dd.count(ch), sd))
    # 8 纯 ASCII 原文是否被误改（记录保留原文清单）
    if sd == dd:
        kept.append(sd)
    # 9 译文不应含拉丁字母的整行未译？仅统计
# 10 无空行
for i, d in enumerate(dst_l, 1):
    if not d.strip():
        fail("第%d行为空行" % i)

print("行数:", len(dst_l))
if kept:
    print("保留原文条目 (%d):" % len(kept))
    for k in kept:
        print("   ", k)
else:
    print("保留原文条目: 0")
print("CRLF:", b"\r\n" in dst_raw, " BOM:", dst_raw.startswith(b"\xef\xbb\xbf"))
print("RESULT:", "自检通过" if ok else "自检失败")
sys.exit(0 if ok else 1)
