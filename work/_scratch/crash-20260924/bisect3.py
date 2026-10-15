# -*- coding: utf-8 -*-
"""在 unitpanel_patch.py 内部二分：
  A. 只做 13 条原地替换
  B. 原地 + REDIRECT[:k]  (k=1..5)   —— 找出一条就崩的那条
"""
import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys

GAME = r"D:\OpenPG2"
EXE = os.path.join(GAME, "OpenGen.exe")
HERE = os.path.dirname(os.path.abspath(__file__))
PY = r"C:\Python314\python.exe"
BASE = r"D:\DSH\军事游戏汉化\backup\OpenGen.exe.before-unitpanel"
SCRIPT = r"D:\DSH\军事游戏汉化\work\exe\unitpanel_patch.py"


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def put_base():
    if os.path.exists(EXE):
        os.chmod(EXE, 0o777)
    shutil.copyfile(BASE, EXE)
    os.chmod(EXE, 0o777)


def load():
    spec = importlib.util.spec_from_file_location("up", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def apply_with(inplace, redirect):
    put_base()
    m = load()
    m.INPLACE = inplace
    m.REDIRECT = redirect
    sys.argv = ["unitpanel_patch.py", "--apply"]
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        m.main()
    out = buf.getvalue()
    bad = [l for l in out.splitlines() if "!!" in l or "错误" in l]
    return out, bad


def boot(label):
    r = subprocess.run([PY, os.path.join(HERE, "boottest.py"), "9"],
                       capture_output=True, text=True, cwd=HERE)
    v = "?"
    for line in r.stdout.splitlines():
        if "=> 判定" in line:
            v = line.split("判定：")[-1].strip()
    print(">>> %-28s md5=%s  %s" % (label, md5(EXE), v))
    sys.stdout.flush()
    return v


m0 = load()
FULL_IP = list(m0.INPLACE)
FULL_RD = list(m0.REDIRECT)

# A. 只原地
out, bad = apply_with(FULL_IP, [])
print("A 只原地: %d 条, 错误 %s" % (len(FULL_IP), bad or "无"))
boot("A 只 13 原地")

# B. 前缀
for k in range(1, len(FULL_RD) + 1):
    sub = FULL_RD[:k]
    out, bad = apply_with(FULL_IP, sub)
    print("\nB%d: %s  错误 %s" % (k, [e[2] for e in sub], bad or "无"))
    for line in out.splitlines():
        if "新VA" in line or "空洞占用" in line:
            print("   " + line.strip())
    boot("B%d 原地+前%d条改指针" % (k, k))
