# -*- coding: utf-8 -*-
"""最终隔离：B3→B4 只差 6 字节，分别单独打上，看谁触发加载器崩溃。

P: 只改 .text  (FO 0x41ADC6: D8 48 -> 40 D9)
Q: 只改 .rdata (FO 0x51CB40: 00*4 -> 空中)
R: 两者都改（应等同 B4）
S: 只改 .rdata 但写的是"Air"（原文同字节，验证内容无关性）
"""
import hashlib
import os
import shutil
import subprocess
import sys

GAME = r"D:\OpenPG2"
EXE = os.path.join(GAME, "OpenGen.exe")
HERE = os.path.dirname(os.path.abspath(__file__))
PY = r"C:\Python314\python.exe"
B3 = os.path.join(HERE, "OpenGen.exe.B3")


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def variant(label, patches):
    if os.path.exists(EXE):
        os.chmod(EXE, 0o777)
    shutil.copyfile(B3, EXE)
    os.chmod(EXE, 0o777)
    d = bytearray(open(EXE, "rb").read())
    for fo, b in patches:
        assert d[fo:fo + len(b)] != b, "0x%X 无变化" % fo
        d[fo:fo + len(b)] = b
    open(EXE, "wb").write(bytes(d))
    r = subprocess.run([PY, os.path.join(HERE, "boottest.py"), "9"],
                       capture_output=True, text=True, cwd=HERE)
    v = "?"
    for line in r.stdout.splitlines():
        if "=> 判定" in line:
            v = line.split("判定：")[-1].strip()
    print(">>> %-38s md5=%s  %s" % (label, md5(EXE), v))
    sys.stdout.flush()


ZH_AIR = "空中".encode("gbk")     # BF D5 D6 D0
TEXT_ONLY = [(0x41ADC6, bytes.fromhex("40D9"))]
RDATA_ZH = [(0x51CB40, ZH_AIR)]
RDATA_ASCII = [(0x51CB40, b"Air\x00")]

print("P: 只改 .text")
variant("P 只改 .text(40 D9)", TEXT_ONLY)
print("\nQ: 只改 .rdata = 空中")
variant("Q 只改 .rdata=空中", RDATA_ZH)
print("\nS: 只改 .rdata = Air(原文同字节)")
variant("S 只改 .rdata=Air", RDATA_ASCII)
print("\nR: 两者都改")
variant("R .text+.rdata", TEXT_ONLY + RDATA_ZH)
