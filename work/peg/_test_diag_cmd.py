# -*- coding: utf-8 -*-
"""自测「诊断-监听游戏日志.cmd」的批处理语法与 DBWIN 链路（把启动游戏换成 --selftest，不启动游戏）。"""
import os
import subprocess

SRC = r"D:\Program Files\PeG\诊断-监听游戏日志.cmd"
TMP = r"D:\DSH\军事游戏汉化\work\peg\out\_diag_cmd_test.cmd"

src = open(SRC, encoding="gbk").read()
out = src.replace("--w 1920 --h 1080", "--selftest").replace("\r\npause\r\n", "\r\nrem pause\r\n")
with open(TMP, "w", encoding="gbk", newline="") as f:
    f.write(out)
print("临时批处理：%s（%d 字节）" % (TMP, os.path.getsize(TMP)))
print("调用行：%s" % [l for l in out.split("\r\n") if "python" in l.lower()])
rc = subprocess.call(["cmd", "/c", TMP])          # 继承 stdio，不走管道
print("== cmd /c 返回码：%d" % rc)
