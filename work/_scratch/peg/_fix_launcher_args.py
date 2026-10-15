# -*- coding: utf-8 -*-
"""修 peg_launcher.py 的重复 argparse 参数（--dx/--keep-dx 定义了两次）并把 build_plan 调用改成三态 dxdy。"""
import io, re, sys

P = r"D:\DSH\军事游戏汉化\work\peg\peg_launcher.py"
src = io.open(P, encoding="utf-8").read()

DUP = '''    ap.add_argument("--dx", action="store_true",
                    help="额外打 K 组（res_diff_v4.tsv 的 165 条 dx/dy 位置行）——实测过粗，会移动左栏文字")
    ap.add_argument("--keep-dx", action="store_true", help="（兼容保留）同“不打 K 组”，现为默认")
'''
n = src.count(DUP)
print("旧重复块出现次数 =", n)
if n:
    assert n == 1, "重复块不止一处，人工检查"
    src = src.replace(DUP, "")

OLD_CALL = "dxdy=bool(a.dx) and not a.keep_dx)"
NEW_CALL = 'dxdy=("all" if a.dx_all else ("x" if a.dx else False)))'
print("旧调用出现次数 =", src.count(OLD_CALL))
if src.count(OLD_CALL) == 1:
    src = src.replace(OLD_CALL, NEW_CALL)

io.open(P, "w", encoding="utf-8", newline="").write(src)

# 复核
chk = io.open(P, encoding="utf-8").read()
print("复核 --dx 定义数 =", len(re.findall(r'add_argument\("--dx"', chk)))
print("复核 --dx-all 定义数 =", len(re.findall(r'add_argument\("--dx-all"', chk)))
print("复核 --keep-dx 定义数 =", len(re.findall(r'add_argument\("--keep-dx"', chk)))
print("复核新调用 =", chk.count(NEW_CALL), " 旧调用残留 =", chk.count(OLD_CALL))
