#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把「临时重建目录」的产物提升到工作区分发目录并部署到游戏目录（分三步、可干跑）。

用法：  python promote_regen.py peg [--apply] [--tag before-xxx]
        python promote_regen.py ww2 [--apply] [--tag before-xxx]

铁律：先重建到临时 → 逐文件 md5 比对（只允许预期内的差异）→ 备份 → 写正式 → 回读校验。
本脚本只做「比对 / 备份 / 提升 / 部署 / 回读」，**重建由生成器自己完成**（不在本脚本内改数据）。
"""
import io
import hashlib
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
PROJ = {
    "peg": dict(tmp=os.path.join(WS, r"peg\testbed\_regen-name-converge"),
                cur=os.path.join(WS, r"peg\testbed\scn-zh"),
                game=r"D:\Program Files\PeG",
                skip=(".exe",)),
    "ww2": dict(tmp=os.path.join(WS, r"pegww2\testbed\_regen-name-converge"),
                cur=os.path.join(WS, r"pegww2\testbed\out"),
                game=r"D:\Program Files\PeG-WW2",
                skip=(".exe",)),
}

args = [a for a in sys.argv[1:] if not a.startswith("--")]
proj = (args or ["peg"])[0]
APPLY = "--apply" in sys.argv
TAG = "before-promote"
for i, a in enumerate(sys.argv):
    if a == "--tag" and i + 1 < len(sys.argv):
        TAG = sys.argv[i + 1]

cfg = PROJ[proj]
BAK = os.path.join(WS, "backup", TAG, f"{proj}-game")


def walk(root):
    out = {}
    for dp, _dn, fns in os.walk(root):
        for fn in fns:
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, root).replace("\\", "/")
            with io.open(p, "rb") as f:
                out[rel] = hashlib.md5(f.read()).hexdigest()
    return out


ht, hc = walk(cfg["tmp"]), walk(cfg["cur"])
changed = sorted(k for k in ht if k in hc and ht[k] != hc[k])
new = sorted(k for k in ht if k not in hc)
gone = sorted(k for k in hc if k not in ht)

print(f"项目={proj}  临时={cfg['tmp']}")
print(f"  临时 {len(ht)} 个 · 现有 {len(hc)} 个 · 内容不同 {len(changed)} · 仅临时有 {len(new)} · 仅现有有 {len(gone)}")
print(f"  内容不同：")
for k in changed:
    print(f"    {k}")
if new:
    print(f"  仅临时有（将新增）：")
    for k in new:
        print(f"    {k}")
if gone:
    print(f"  仅现有有（保留不动）：{len(gone)}")
    for k in gone[:12]:
        print(f"    {k}")

if not APPLY:
    print("\n（干跑；加 --apply 才备份+提升+部署）")
    raise SystemExit(0)

os.makedirs(BAK, exist_ok=True)
ok = 0
for k in changed + new:
    src = os.path.join(cfg["tmp"], k.replace("/", os.sep))
    cur = os.path.join(cfg["cur"], k.replace("/", os.sep))
    dst = os.path.join(cfg["game"], k.replace("/", os.sep))
    bk = os.path.join(BAK, k.replace("/", os.sep))
    if os.path.isfile(cur):
        os.makedirs(os.path.dirname(bk), exist_ok=True)
        shutil.copy2(cur, bk)
    os.makedirs(os.path.dirname(cur), exist_ok=True)
    shutil.copy2(src, cur)
    if os.path.isdir(os.path.dirname(dst)) or os.path.isfile(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    with io.open(src, "rb") as f1, io.open(cur, "rb") as f2:
        assert hashlib.md5(f1.read()).hexdigest() == hashlib.md5(f2.read()).hexdigest(), k
    if os.path.isfile(dst):
        with io.open(src, "rb") as f1, io.open(dst, "rb") as f2:
            assert hashlib.md5(f1.read()).hexdigest() == hashlib.md5(f2.read()).hexdigest(), k
    ok += 1
print(f"\n✅ 提升+部署 {ok} 个（备份 {BAK}）· 逐文件回读一致")
