# -*- coding: utf-8 -*-
"""在 48 条补丁内部二分：逐步重放 unitpanel_patch / unitdlg_patch 并测启动。"""
import hashlib
import os
import shutil
import subprocess
import sys

GAME = r"D:\OpenPG2"
EXE = os.path.join(GAME, "OpenGen.exe")
WK = r"D:\DSH\军事游戏汉化\work\exe"
HERE = os.path.dirname(os.path.abspath(__file__))
PY = r"C:\Python314\python.exe"

BASE = r"D:\DSH\军事游戏汉化\backup\OpenGen.exe.before-unitpanel"


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def put_base(path):
    if os.path.exists(EXE):
        os.chmod(EXE, 0o777)
    shutil.copyfile(path, EXE)
    os.chmod(EXE, 0o777)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=WK)
    return r.stdout + r.stderr


def boot(label):
    r = subprocess.run([PY, os.path.join(HERE, "boottest.py"), "9"],
                       capture_output=True, text=True, cwd=HERE)
    verdict = "?"
    for line in r.stdout.splitlines():
        if "判定：" in line and "=> 判定" in line:
            verdict = line.split("判定：")[-1]
    print(">>> %s | md5=%s | %s" % (label, md5(EXE), verdict))
    sys.stdout.flush()
    return verdict


def main():
    put_base(BASE)
    print("基线 before-unitpanel md5=%s" % md5(EXE))
    boot("基线 1640811c")

    print("\n--- 重放 unitpanel_patch.py (13 原地 + 5 改指针) ---")
    out = run([PY, os.path.join(WK, "unitpanel_patch.py"), "--apply"])
    print(out[-1500:])
    boot("step1 unitpanel 20 条")

    print("\n--- 重放 unitdlg_patch.py (16 原地 + 2 补遗 + 6 多行块 + 2 改指针) ---")
    out = run([PY, os.path.join(WK, "unitdlg_patch.py"), "--apply"])
    print(out[-2000:])
    boot("step2 unitdlg 28 条")


if __name__ == "__main__":
    main()
