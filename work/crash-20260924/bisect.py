# -*- coding: utf-8 -*-
"""逐版本启动二分：把候选 exe 覆盖到游戏目录，跑 boottest，汇总结果。"""
import hashlib
import os
import shutil
import subprocess
import sys

GAME = r"D:\OpenPG2"
EXE = os.path.join(GAME, "OpenGen.exe")
HERE = os.path.dirname(os.path.abspath(__file__))
PY = r"C:\Python314\python.exe"

CANDIDATES = [
    ("before-maphud b97c9117(48条)", r"D:\DSH\军事游戏汉化\backup\OpenGen.exe.before-maphud"),
    ("before-unitpanel 1640811c(22:45可用)", r"D:\DSH\军事游戏汉化\backup\OpenGen.exe.before-unitpanel"),
    ("before-unitlabel 2f4a4ba7", r"D:\DSH\军事游戏汉化\backup\OpenGen.exe.before-unitlabel"),
    ("before-dialogs279", r"D:\DSH\军事游戏汉化\backup\OpenGen.exe.before-dialogs279"),
]


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def test(path):
    # 注意：不能用 copy2 —— 备份里的只读属性会被复制到目标，导致后续覆盖 PermissionError
    if os.path.exists(EXE):
        os.chmod(EXE, 0o777)
    shutil.copyfile(path, EXE)
    os.chmod(EXE, 0o777)
    r = subprocess.run([PY, os.path.join(HERE, "boottest.py"), "9"],
                       capture_output=True, text=True, cwd=HERE)
    out = r.stdout
    verdict = "?"
    for line in out.splitlines():
        if "判定" in line:
            verdict = line.split("：")[-1]
    return verdict, out


def main():
    for name, path in CANDIDATES:
        if not os.path.exists(path):
            print("跳过（不存在）: %s" % name)
            continue
        print("=" * 70)
        print("%s   md5=%s" % (name, md5(path)))
        v, out = test(path)
        print("   判定: %s" % v)
        for line in out.splitlines():
            if "进程已退出" in line or "窗口" in line or "hwnd=" in line:
                print("   " + line.strip())
        sys.stdout.flush()
    # 还原为崩溃版，保持现场
    shutil.copy2(os.path.join(HERE, "OpenGen.exe.at-crash"), EXE)
    print("=" * 70)
    print("已还原现场 exe (d8d53a0d)")


if __name__ == "__main__":
    main()
