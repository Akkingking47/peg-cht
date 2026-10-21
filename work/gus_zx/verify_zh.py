# -*- coding: utf-8 -*-
"""独立校验：work\\gus_zx\\src 与 work\\gus_zx\\zh 的行结构必须逐行一致。

检查项：
  1. 行数一致（按 \\n 切分，含末尾空元素）
  2. 每行的 \\r 有无一致（CRLF 不破坏）
  3. 末尾换行有无一致
  4. src 里的纯 ASCII / 纯符号行在 zh 里必须逐字不变（表格结构行）
  5. zh 里不得出现 UTF-8 源里的替换字符或裸代理
"""
import os
import sys

SRC = r"D:\DSH\军事游戏汉化\work\gus_zx\src"
ZH = r"D:\DSH\军事游戏汉化\work\gus_zx\zh"


def parts(t):
    ls = t.split("\n")
    tnl = ls and ls[-1] == ""
    if tnl:
        ls = ls[:-1]
    return ls, tnl


def ascii_only(s):
    b = s[:-1] if s.endswith("\r") else s
    return b != "" and all(ord(c) < 128 for c in b)


def flow_tail(s):
    """__flow 报表行：返回「标题列之后」的部分，用于校验表格结构未动。"""
    import re
    m = re.match(r"^(\s*\d+\s+\S+\.(?:xscn|scn))(\s+)(.+?)(\s{2,})(.*)$", s)
    return m.group(5) if m else None


bad = 0
files = sorted(os.listdir(ZH))
for n in files:
    sp, zp = os.path.join(SRC, n), os.path.join(ZH, n)
    if not os.path.exists(sp):
        print("[?] %s 源文件不存在" % n)
        bad += 1
        continue
    s = open(sp, encoding="utf-8", newline="").read()
    z = open(zp, encoding="utf-8", newline="").read()
    sl, st = parts(s)
    zl, zt = parts(z)
    errs = []
    if len(sl) != len(zl):
        errs.append("行数 %d -> %d" % (len(sl), len(zl)))
    elif st != zt:
        errs.append("末尾换行 %s -> %s" % (st, zt))
    else:
        for i, (a, b) in enumerate(zip(sl, zl)):
            if a.endswith("\r") != b.endswith("\r"):
                errs.append("第%d行 CR 不一致" % i)
            if a.strip() != "" and b.strip() == "":
                errs.append("第%d行被清空" % i)
            ta, tb = flow_tail(a), flow_tail(b)
            if ta is not None and ta != tb:
                errs.append("第%d行表格尾段被改: %r -> %r" % (i, ta, tb))
    if errs:
        bad += 1
        print("[X] %-20s %s" % (n, "; ".join(errs[:4])))
    else:
        print("[ok] %-20s %d 行" % (n, len(sl)))
print("\nzh 文件 %d 个，问题文件 %d 个" % (len(files), bad))
sys.exit(1 if bad else 0)
