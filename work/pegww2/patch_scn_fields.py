#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 PeG 经验修 `.SCN` 的两个配对字段（@11329 stem / @11349 位置标志）。

PeG 实证（其档案 P4）：
    @11349 = 0 ⇒ 引擎读 `SCENARIO\\<@11329>.TXT`
    @11349 = 1 ⇒ 引擎读 `USERSCEN\\<@11329>.PLY`
字段与文件实际位置/拼写不符时，引擎**找不到就回退**（本作表现为描述框显示 `_m.txt` 的地名列表）。
PeG 的做法是**改字段、不动文件**（补文件那两轮都无效，因为引擎压根没读对地方）。

本脚本默认 dry-run；`--apply` 才写，且先把原文件备份为 `<名>.orig-backup`，写完回读校验。
"""
import os
import shutil
import sys

G = r"D:\Program Files\PeG-WW2\SCENARIO"

# (场景文件, 字段偏移, 字段长度, 期望原值, 新值, 说明)
JOBS = [
    ("RM_usvsruss19.scn", 11329, 20, "RM_usvsurss19_i", "RM_usvsruss19_i",
     "MOD 把 @11329 拼错（多一个 s）⇒ 引擎找不到 RM_usvsruss19_i.txt"),
    ("ATM_scn02.scn", 11329, 20, "ATM_scn02", "ATM_scn02_i",
     "@11329 漏了 _i 后缀 ⇒ 引擎找不到 ATM_scn02_i.txt"),
    ("usvsussr14.scn", 11349, 1, "\x01", "\x00",
     "@11349=1（去 USERSCEN 找 .ply）但文件在 SCENARIO/usvsussr14.TXT ⇒ 改 0"),
]


def main():
    apply_ = "--apply" in sys.argv
    ok = 0
    for fn, off, ln, want_old, new, why in JOBS:
        p = os.path.join(G, fn)
        if not os.path.isfile(p):
            print(f"  ❌ 缺文件 {fn}")
            continue
        b = bytearray(open(p, "rb").read())
        cur = bytes(b[off:off + ln]).split(b"\x00")[0].decode("latin-1")
        if off == 11349:
            cur = chr(b[off])
        print(f"  {fn} @{off}: 现={cur!r}  期望={want_old!r}")
        if cur != want_old:
            print("     ⏭ 跳过（现值与预期不符，不冒险改）")
            continue
        nb = bytearray(b)
        if off == 11349:
            nb[off] = ord(new)
            chk = chr(nb[off])
        else:
            enc = new.encode("latin-1")[:ln].ljust(ln, b"\x00")
            nb[off:off + ln] = enc
            chk = bytes(nb[off:off + ln]).split(b"\x00")[0].decode("latin-1")
        print(f"     → 新值={chk!r}  （{why}）")
        if not apply_:
            ok += 1
            continue
        bak = p + ".orig-backup"
        if not os.path.isfile(bak):
            shutil.copy2(p, bak)
            print(f"     已备份 → {os.path.basename(bak)}")
        with open(p, "wb") as f:
            f.write(nb)
        back = open(p, "rb").read()
        got = chr(back[off]) if off == 11349 else bytes(back[off:off + ln]).split(b"\x00")[0].decode("latin-1")
        if got == chk and len(back) == len(b):
            print("     ✅ 回读校验通过")
            ok += 1
        else:
            print(f"     ❌ 回读校验失败（{got!r} / {len(back)} B）")
    print(f"\n{'[APPLY]' if apply_ else '[DRY-RUN]'} 处理 {ok}/{len(JOBS)} 条")


if __name__ == "__main__":
    main()
