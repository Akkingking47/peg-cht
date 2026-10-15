# -*- coding: utf-8 -*-
"""自检 zh-17.tsv"""
import re

SRC = r"d:/DSH/军事游戏汉化/work/basekorp/chunks/in-17.tsv"
DST = r"d:/DSH/军事游戏汉化/work/basekorp/chunks/zh-17.tsv"

raw = open(DST, "rb").read()
src = open(SRC, "rb").read()
ok = True


def fail(m):
    global ok
    ok = False
    print("FAIL:", m)


if raw.startswith(b"\xef\xbb\xbf"):
    fail("输出含 BOM")
if b"\n" in raw.replace(b"\r\n", b""):
    fail("存在裸 LF")
if not raw.endswith(b"\r\n"):
    fail("末尾缺少 CRLF")

dl = raw.decode("utf-8").split("\r\n")
sl = src.decode("utf-8").rstrip("\r\n").split("\r\n")[1:]
if dl[-1] != "":
    fail("末尾多余内容")
dl = dl[:-1]
if len(dl) != 731:
    fail("行数 %d != 731" % len(dl))
if len(sl) != len(dl):
    fail("与输入行数不一致 %d vs %d" % (len(sl), len(dl)))

bad_tab = 0
for i, line in enumerate(dl):
    parts = line.split("\t")
    if len(parts) != 2:
        fail("第%d行列数=%d" % (i + 2, len(parts)))
    if line.strip() == "":
        fail("第%d行空" % (i + 2))

for i, (a, b) in enumerate(zip(sl, dl)):
    if a.split("\t")[0] != b.split("\t")[0]:
        fail("第%d行 src 不一致" % (i + 2))

# 残留英文检测
ALLOW = set(list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"))
KEEP = re.compile(
    r"('[A-Za-z][A-Za-z'\.]*|''[A-Za-z]+''|/[A-Za-z]{1,3}/|ZKGX|ZXKG|ZKGH|ZGJ|"
    r"\[[A-Za-z0-9]+\]|\bBdM\b|\bDiv\.\b|\bXVII\b|\bXV\b|\bdv\b|\bGp\b|\br\b|\bE\b|\bH\b|"
    r"\bT\b|\bB\b|\bC\b|\bK\b|\bL\b|\bIV\b|\bV\b|\bAF\b|\bAT\b|PL|CAMPSA|N\.S\.|N\.Y\.|"
    r"L\.A\.|S\.Ig\.|S\.Miguel|T\.|Ter\.|Cen\.|Sta\.|SOURCE)")
for i, line in enumerate(dl):
    s = line.split("\t")[1]
    s2 = KEEP.sub("", s)
    words = re.findall(r"[A-Za-z][A-Za-z\.']*", s2)
    if words:
        ok = False
        print("RESID %d: %s ||| %s" % (i + 2, words, line))

print("行数:", len(dl), "| 全部检查通过" if ok else "| 存在问题")
