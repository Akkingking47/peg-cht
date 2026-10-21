#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为 Usvsussr.cam 场景创建 场景名_i.txt（有下划线）副本。
.CAM 引用的是无下划线的 i.txt，若游戏按命名约定查找会找不到，回退显示 _m.txt。
创建副本确保两种查找方式都能命中。
用法: python fix_usvsussr_i_name.py [--apply]
"""
import io, os, re, shutil, sys
G = r"D:\Program Files\PeG-WW2"
SCN = os.path.join(G, "SCENARIO")
BK = r"d:\DSH\军事游戏汉化\pegww2\testbed\backup\SCENARIO"
STR = re.compile(rb"[\x20-\x7e]{3,}")
def cam_slots(path):
    raw = open(path, "rb").read()
    refs = [(m.start(), m.group().decode("latin-1")) for m in STR.finditer(raw)
            if re.search(r"(?i)\.(scn|txt)$", m.group().decode("latin-1"))]
    anchors = [r for r in refs if r[1].lower().endswith(".scn")]
    slots = []
    for k, (off, scnf) in enumerate(anchors):
        end = anchors[k+1][0] if k+1 < len(anchors) else len(raw)
        i_file = next((s for o, s in refs if off < o < end and not s.lower().endswith(".scn")
                       and re.search(r"(?i)(_i|i)\.txt$", s) and not re.search(r"(?i)(v|m|u|bv|tv|l)\.txt$", s)), "")
        slots.append((scnf, i_file))
    return slots
sys.stdout.reconfigure(encoding="utf-8")
apply_ = "--apply" in sys.argv
cnt = 0
for scnf, i_ref in cam_slots(os.path.join(SCN, "Usvsussr.cam")):
    stem = re.sub(r"(?i)\.scn$", "", scnf)
    expected = stem + "_i.txt"
    src = os.path.join(SCN, i_ref)
    dst = os.path.join(SCN, expected)
    if not os.path.isfile(src):
        print(f"  ⚠ 源不存在: {i_ref}"); continue
    if os.path.isfile(dst):
        print(f"  ⏭ 已存在: {expected}"); continue
    # backup 也同步
    bk_src = os.path.join(BK, i_ref)
    bk_dst = os.path.join(BK, expected)
    print(f"  {expected} ← {i_ref}")
    if apply_:
        shutil.copy2(src, dst)
        if os.path.isfile(bk_src) and not os.path.isfile(bk_dst):
            shutil.copy2(bk_src, bk_dst)
    cnt += 1
print(f"\n共 {cnt} 个 {'已创建' if apply_ else '（dry-run）'}")
