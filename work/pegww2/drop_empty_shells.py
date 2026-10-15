#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2：把**空壳场景** `.SCN@0` 从 0 改回 1 ⇒ 不再进入『进行场景』列表（用户批准）。

对象：`ATM_scn29` / `ATM_scn34` —— `@0=0`（进列表）却既无 `_m.txt` 也无 `@11329` 指向的说明文件
      ⇒ 列表里占位、显不出名字，属 MOD 残留。改 1 字节即可摘除（`@0=1` = 战役专用/不进列表）。

纪律：默认 dry-run；`--apply` 才写；写前 `.orig-backup`（不存在才建）；写后回读校验；幂等。
"""
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
S = r"D:\Program Files\PeG-WW2\SCENARIO"
TARGETS = ("ATM_scn29.scn", "ATM_scn34.scn")


def main():
    apply_ = "--apply" in sys.argv
    print("=" * 96)
    print(f"空壳场景摘除（@0: 0→1）  模式={'[APPLY]' if apply_ else '[DRY-RUN]'}")
    print("=" * 96)
    for fn in TARGETS:
        p = os.path.join(S, fn)
        if not os.path.isfile(p):
            print(f"  {fn}: ❌ 不存在")
            continue
        b = bytearray(open(p, "rb").read())
        cur = b[0]
        if cur == 1:
            print(f"  {fn}: 已是 @0=1（幂等，跳过）")
            continue
        print(f"  {fn}: @0 {cur} → 1   （大小 {len(b)} B，其余字节不动）")
        if not apply_:
            continue
        bak = p + ".orig-backup"
        if not os.path.isfile(bak):
            shutil.copy2(p, bak)
            print(f"     备份 ⇒ {os.path.basename(bak)}")
        nb = bytearray(b)
        nb[0] = 1
        with open(p, "wb") as f:
            f.write(bytes(nb))
        back = open(p, "rb").read()
        ok = (back[0] == 1) and (back[1:] == bytes(b[1:]))
        print(f"     回读 {'✅ 通过' if ok else '❌ 失败'}（@0={back[0]}，其余字节一致={back[1:] == bytes(b[1:])}）")
    if not apply_:
        print("\n  ⇒ dry-run，未写入。加 --apply 落盘。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
