#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 阶段2.1：原版备份（只读游戏目录 ⇒ 写入工作区）。

铁律：备份与覆盖分两条命令；本脚本**只备份，绝不写游戏目录**。
产出：pegww2/testbed/backup/{exe,text}/... + backup-manifest.tsv（含 sha256 与大小）
幂等：已存在且 sha 一致则跳过；sha 不一致则报冲突（不覆盖备份）。
"""
import hashlib
import io
import os
import re
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2"
DEST = os.path.join(WS, "pegww2", "testbed", "backup")
HERE = os.path.dirname(os.path.abspath(__file__))
_REPORT = os.path.join(HERE, "recon3-out", "backup-report.txt")
_sink = io.StringIO()


class _Tee:
    def __init__(self, *s):
        self.s = s

    def write(self, x):
        for t in self.s:
            t.write(x)
        return len(x)

    def flush(self):
        for t in self.s:
            t.flush()


sys.stdout = _Tee(sys.stdout, _sink)

# 12 个 efile（modgen 引擎，同一构建）+ 根级文本载体
EXES = [
    "Germany 46.exe", "Germany DAK.exe", "Germany East.exe", "Germany West.exe",
    "Great Britain.exe", "Great Britain 46.exe", "SS Germany East.exe", "SS Germany West.exe",
    "USA.exe", "USA 46.exe", "USSR.exe", "USSR 46.exe",
]
TEXTS = [
    "WW2Gui.txt", "WW2Misc.txt", "WW2NAME.TXT", "WW2Tips.TXT",
    "ww2-eqp.txt", "ww2-eqp.aux", "ww2-eqp.eqp", "PEOPLES.INT",
]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_one(src, dst, rows, kind):
    if not os.path.isfile(src):
        print(f"  缺: {src}")
        return
    s = sha(src)
    if os.path.isfile(dst):
        if sha(dst) == s:
            print(f"  已备份(一致): {os.path.relpath(dst, WS)}")
            rows.append((kind, os.path.basename(src), os.path.getsize(src), s, "已存在一致"))
            return
        print(f"  ⚠ 冲突: {os.path.relpath(dst, WS)} 与源不一致 ⇒ 跳过不覆盖")
        rows.append((kind, os.path.basename(src), os.path.getsize(src), s, "冲突跳过"))
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    assert sha(dst) == s, "回读校验失败"
    print(f"  备份并回读校验 OK: {os.path.relpath(dst, WS)}")
    rows.append((kind, os.path.basename(src), os.path.getsize(src), s, "新建+回读一致"))


def main():
    print("=" * 90)
    print("PeG-WW2 原版备份（绝不写游戏目录）")
    print("=" * 90)
    rows = []
    print("\n[exe]")
    for f in EXES:
        copy_one(os.path.join(GAME, f), os.path.join(DEST, "exe", f), rows, "exe")
    print("\n[text]")
    for f in TEXTS:
        copy_one(os.path.join(GAME, f), os.path.join(DEST, "text", f), rows, "text")

    man = os.path.join(DEST, "backup-manifest.tsv")
    with open(man, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("kind\tname\tbytes\tsha256\tstatus\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
    print(f"\n清单: {man}  ({len(rows)} 条)")


if __name__ == "__main__":
    main()
    os.makedirs(os.path.dirname(_REPORT), exist_ok=True)
    with open(_REPORT, "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
