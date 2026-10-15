# -*- coding: utf-8 -*-
"""生成两个诊断批处理（GBK + CRLF，命令全 ASCII）+ 快捷方式。"""
import os
import subprocess

PEG = r"D:\Program Files\PeG"
SCRIPT = r"D:\DSH\军事游戏汉化\work\peg\diag_ddraw.py"
PY = r"C:\Python314\python.exe"

main = [
    "@echo off",
    "chcp 936 >nul",
    "title PeG diaq: DDrawCompat layer + call log",
    "echo ==============================================================",
    "echo   diaq mode: temporary DDrawCompat display layer + full DirectDraw log",
    "echo ==============================================================",
    "echo.",
    "echo   This window will:",
    "echo     1) swap ddraw.dll to DDrawCompat 0.7.1 (original is backed up)",
    "echo     2) start the game in 16:9 with all patches, logging game + DDraw calls",
    "echo     3) swap the original ddraw.dll back after you quit the game",
    "echo.",
    "echo   Play 2-3 minutes and check these four things - remember which got BETTER:",
    "echo     A) hover a toolbar button: is the magenta box gone?",
    "echo     B) black holes / mouse trails on the map: still there?",
    "echo     C) More Options / strategy map / sub-screens: position correct?",
    "echo     D) clicking a button: still need to aim ~100px to the left?",
    "echo.",
    "echo   Then quit the game normally. When this window ends, send me these two:",
    "echo     (number of game log lines) and (number of DDrawCompat log lines)",
    "echo ==============================================================",
    "echo.",
    '"' + PY + '" "' + SCRIPT + '" --w 1920 --h 1080 --exe "%~dp0PeG030.exe"',
    "echo.",
    "pause",
    "",
]

restore = [
    "@echo off",
    "chcp 936 >nul",
    "title PeG restore display layer",
    "echo restoring ddraw.dll ...",
    '"' + PY + '" "' + SCRIPT + '" --restore',
    "echo.",
    "pause",
    "",
]

for name, lines in (("诊断-换显示层采日志.cmd", main), ("还原显示层.cmd", restore)):
    path = os.path.join(PEG, name)
    with open(path, "w", encoding="gbk", newline="") as f:
        f.write("\r\n".join(lines))
    raw = open(path, "rb").read()
    assert b"\n" not in raw.replace(b"\r\n", b""), "存在裸 LF"
    print("已写入 %s（%d 字节，%d 行，全 CRLF）" % (path, len(raw), raw.count(b"\r\n")))

lnk_cmd = os.path.join(PEG, "诊断-换显示层采日志.cmd")
ps = (
    "$sh = New-Object -ComObject WScript.Shell; "
    "$l = $sh.CreateShortcut('%s'); "
    "$l.TargetPath = '%s'; $l.WorkingDirectory = '%s'; "
    "$l.IconLocation = '%s\\PeG030.exe,0'; "
    "$l.Description = 'PeG diaq: DDrawCompat layer + DirectDraw call log'; $l.Save()"
    % (os.path.join(PEG, "诊断-换显示层采日志.lnk"), lnk_cmd, PEG, PEG)
)
subprocess.call(["powershell", "-NoProfile", "-Command", ps])
print("快捷方式：%s" % os.path.join(PEG, "诊断-换显示层采日志.lnk"))
