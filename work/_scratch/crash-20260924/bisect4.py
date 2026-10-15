# -*- coding: utf-8 -*-
"""聚焦复现：B3(含Gnd) / B4(再加Air) 交替各跑 2 次 + 两个判别变体。

变体 C：把 Air 指到空洞，但空洞里**写回与原文完全相同的字节 "Air"**
        ⇒ 唯一差别只剩「地址」。若仍崩 ⇒ 引擎对该地址有依赖（比较/查表）。
变体 E：只做 Air 一条（空洞 +0 处放「空中」）⇒ 判别地址 vs 内容。
"""
import hashlib
import importlib.util
import io
import contextlib
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


def load():
    spec = importlib.util.spec_from_file_location("up", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def boot(label):
    r = subprocess.run([PY, os.path.join(HERE, "boottest.py"), "9"],
                       capture_output=True, text=True, cwd=HERE)
    v = "?"
    for line in r.stdout.splitlines():
        if "=> 判定" in line:
            v = line.split("判定：")[-1].strip()
    print("    >>> %-34s md5=%s  %s" % (label, md5(EXE), v))
    sys.stdout.flush()
    return v


def run_variant(label, redirect):
    if os.path.exists(EXE):
        os.chmod(EXE, 0o777)
    shutil.copyfile(BASE, EXE)
    os.chmod(EXE, 0o777)
    m = load()
    m.REDIRECT = list(redirect)
    sys.argv = ["unitpanel_patch.py", "--apply"]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        m.main()
    out = buf.getvalue()
    err = [l.strip() for l in out.splitlines() if "!!" in l]
    if err:
        print("    !! 脚本报错: %s" % err)
    return boot(label)


m0 = load()
IP = list(m0.INPLACE)
RD = list(m0.REDIRECT)          # TBD, OTP, Gnd, Air, %s (Mv=%d)
AIR = RD[3]

print("=== 交替复现 ===")
for i in (1, 2):
    run_variant("第%d轮 B3 原地+TBD+OTP+Gnd" % i, IP and RD[:3])
    run_variant("第%d轮 B4 原地+上+Gnd+Air" % i, RD[:4])

print("\n=== 变体 C：Air 指到空洞但空洞内字节 = 原文 'Air'（只换地址） ===")
run_variant("C Air->hole 内容=Air", RD[:3] + [(0x513AD8, 0x41ADC6, "Air", "Air")])

print("\n=== 变体 E：只做 Air 一条，空洞从 +0 开始 ===")
run_variant("E 只 Air(hole+0)", [AIR])

print("\n=== 变体 F：只做 Gnd 一条，空洞从 +0 开始 ===")
run_variant("F 只 Gnd(hole+0)", [RD[2]])
