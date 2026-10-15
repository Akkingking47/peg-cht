# -*- coding: utf-8 -*-
"""从 1640811C 基线重建整条 exe 补丁链，每一步都做启动验证。

链：unitpanel(换新空洞) -> unitdlg -> maphud -> zhfix
"""
import hashlib
import io
import contextlib
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


def md5(p=EXE):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def put_base():
    if os.path.exists(EXE):
        os.chmod(EXE, 0o777)
    shutil.copyfile(BASE, EXE)
    os.chmod(EXE, 0o777)


def run(script, *args):
    r = subprocess.run([PY, os.path.join(WK, script)] + list(args),
                       capture_output=True, text=True, cwd=WK)
    return (r.stdout or "") + (r.stderr or "")


def boot(label, save_as=None):
    r = subprocess.run([PY, os.path.join(HERE, "boottest.py"), "9"],
                       capture_output=True, text=True, cwd=HERE)
    v = "?"
    for line in r.stdout.splitlines():
        if "=> 判定" in line:
            v = line.split("判定：")[-1].strip()
    ok = v.startswith("OK")
    print(">>> %-34s md5=%s  %s  %s" % (label, md5(), v, "✅" if ok else "❌"))
    if save_as:
        shutil.copyfile(EXE, os.path.join(HERE, save_as))
    sys.stdout.flush()
    return ok


print("=== 0) 基线 1640811C ===")
put_base()
boot("基线 before-unitpanel")

print("\n=== 1) unitpanel_patch.py（新空洞 0x4B1A9A）===")
out = run("unitpanel_patch.py", "--apply")
print(out[-1200:])
ok1 = boot("1 unitpanel 18 条", "chain-1-unitpanel.exe")

print("\n=== 2) unitdlg_patch.py ===")
out = run("unitdlg_patch.py", "--apply")
print(out[-1200:])
ok2 = boot("2 unitdlg 26 条", "chain-2-unitdlg.exe")

print("\n=== 3) maphud_patch.py（49 条）===")
out = run("maphud_patch.py", "--apply")
print(out[-1500:])
ok3 = boot("3 maphud 49 条", "chain-3-maphud.exe")

print("\n=== 4) exe_zhfix.py（SH for Owner → SH 归属方）===")
out = run("exe_zhfix.py", "--tsv", "zhfix-maphud.tsv", "--apply")
print(out[-800:])
ok4 = boot("4 zhfix", "chain-4-final.exe")

print("\n汇总: %s" % ["OK" if x else "CRASH" for x in (ok1, ok2, ok3, ok4)])
print("最终 md5 = %s" % md5())
