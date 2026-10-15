# -*- coding: utf-8 -*-
"""生成「诊断-监听游戏日志」批处理（GBK + CRLF，命令全 ASCII，中文只出现在 echo 里）。

cmd.exe 解析批处理依赖 CRLF；只含 LF 时跨行块会解析失败、窗口一闪而过。
"""
import os

CMD = r"D:\Program Files\PeG\诊断-监听游戏日志.cmd"
DIAG = r"D:\DSH\军事游戏汉化\work\peg\diag_run.py"
LOG = r"D:\DSH\军事游戏汉化\work\peg\out\game-debugview.txt"

lines = [
    "@echo off",
    "chcp 936 >nul",
    "title PeG 诊断：监听游戏自身日志（16:9 运行）",
    "echo ==============================================================",
    "echo   PeG 诊断模式：游戏照常启动（16:9），本窗口实时显示游戏自己的日志",
    "echo ==============================================================",
    "echo.",
    "echo   请照常玩 2-3 分钟，把这三个问题各做一遍：",
    "echo      1) 打开「更多选项」",
    "echo      2) 打开战略地图，然后移动鼠标",
    "echo      3) 打开子界面（装备/单位信息等）",
    "echo   然后从游戏里正常退出（回主菜单退出游戏），本窗口会自动结束。",
    "echo.",
    "echo   结束后把本窗口最后几行发给我即可；完整日志在：",
    "echo      " + LOG,
    "echo ==============================================================",
    "echo.",
    '"C:\\Python314\\python.exe" "' + DIAG + '" --w 1920 --h 1080 --exe "%~dp0PeG030.exe"',
    "echo.",
    "echo 诊断结束。日志：" + LOG,
    "pause",
    "",
]
data = "\r\n".join(lines)
with open(CMD, "w", encoding="gbk", newline="") as f:
    f.write(data)
raw = open(CMD, "rb").read()
print("已写入 %s（%d 字节）" % (CMD, len(raw)))
print("含 CR：%s  含裸 LF：%s" % (raw.count(b"\r\n") > 0, b"\n" in raw.replace(b"\r\n", b"")))
print("首行：%r" % raw.split(b"\r\n")[0])
# 校验：整份必须以 GBK 解出、且每行都是 CRLF
txt = raw.decode("gbk")
assert "\n" not in txt.replace("\r\n", ""), "存在裸 LF"
print("全部 %d 行均以 CRLF 结尾 ✓" % (txt.count("\r\n")))
