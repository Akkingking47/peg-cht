# -*- coding: utf-8 -*-
r"""把 translate_prose 产出的 full 文件按 md5 组铺到 TEXT-ZH\SCENARIO。

只读 deploy_manifest.tsv（full rep + 组内文件列表），把 out/<rep> 字节原样
写到 TEXT-ZH\SCENARIO\<每个文件名>。空行/装饰/字节全部保真。
"""
import os
import io

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = r"D:\OpenPG2"
ZH = os.path.join(GAME, "EFILE_BASEKORP", "TEXT-ZH", "SCENARIO")
OUT = os.path.join(HERE, "out_prose")
MANI = os.path.join(HERE, "deploy_manifest.tsv")
os.makedirs(ZH, exist_ok=True)

n = 0
with io.open(MANI, encoding="utf-8") as f:
    next(f, None)
    for ln in f:
        p = ln.rstrip("\r\n").split("\t")
        if len(p) < 2:
            continue
        rep, files = p[0], p[1]
        src = os.path.join(OUT, rep)
        if not os.path.exists(src):
            print("  ⚠️ 缺 out/%s" % rep)
            continue
        data = open(src, "rb").read()
        for fn in files.split(","):
            if not fn:
                continue
            with open(os.path.join(ZH, fn), "wb") as w:
                w.write(data)
            n += 1
print("部署文件 %d（覆盖 TEXT-ZH\\SCENARIO）" % n)
