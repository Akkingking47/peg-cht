#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「Profile 型」译法问题的**批定修正**（用户 2026-10-12 批准）。

批准范围（其余一律不动）：
  ① `WW2Gui-map.tsv` 行 95  `Profile`      概况 → **轮廓**（与手册一致；原文＝单位轮廓/曝露度）
  ② `WW2Gui-map.tsv` 行 307 `Sharpshooter` 神射手 → **精准射手**（解开与行295 `Marksman` 的撞名；与手册一致）
  ③ `ww2-eqp-map.tsv`  16 条 `w/Pferden`   马拉 → **骡马牵引**（该族唯一破格项，同族皆「XX牵引」）
  ④ `ww2-eqp-map.tsv`  `Ferdinand`        象式 → **斐迪南**（与 `Elefant` 象式 区分；现两条同名）

未批准、**保持原样**：`Ground Taker` · `Indirect Defense` · `River Assault` · 战斗记录组「击杀/击毁」。

用法:
  python fix_profile_class.py            # dry-run
  python fix_profile_class.py --apply    # 备份后写入
"""
import hashlib
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
BK = os.path.join(WS, "backup", "glossary-before-profile-fix")

# (文件, 匹配方式, 定位, 旧, 新)
GUI_EDITS = [
    ("WW2Gui-map.tsv", "95", "概况", "轮廓"),
    ("WW2Gui-map.tsv", "307", "神射手", "精准射手"),
]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def main():
    apply_ = "--apply" in sys.argv
    plan = []

    # ---- ①② 行号定位的 GUI 改动 ----
    p = os.path.join(RES, "WW2Gui-map.tsv")
    lines = open(p, encoding="utf-8").read().split("\n")
    for fn, no, old, new in GUI_EDITS:
        for i, l in enumerate(lines):
            c = l.split("\t")
            if c and c[0].strip() == no and len(c) >= 3 and c[2].strip() == old:
                plan.append((p, i, l, "\t".join(c[:2] + [new] + c[3:])))
                break
        else:
            print("  ⚠️ 未找到 行%s 的 %r" % (no, old))

    # ---- ③ w/Pferden 一族：只在该行内把「马拉」换成「骡马牵引」 ----
    pe = os.path.join(RES, "ww2-eqp-map.tsv")
    plines = open(pe, encoding="utf-8").read().split("\n")
    n_pf = 0
    for i, l in enumerate(plines):
        c = l.split("\t")
        if len(c) >= 2 and "w/Pferden" in c[0] and "马拉" in c[1]:
            nc = list(c)
            nc[1] = c[1].replace("马拉", "骡马牵引")
            plan.append((pe, i, l, "\t".join(nc)))
            n_pf += 1

    # ---- ④ Ferdinand → 斐迪南（Elefant 保持 象式）----
    for i, l in enumerate(plines):
        c = l.split("\t")
        if len(c) >= 3 and c[0].strip() == "Ferdinand" and c[1].strip() == "象式":
            nc = list(c)
            nc[1] = "斐迪南"
            plan.append((pe, i, l, "\t".join(nc)))
            break
    else:
        print("  ⚠️ 未找到 Ferdinand/象式")

    print("=== 修正计划 %d 条（w/Pferden %d 条）===" % (len(plan), n_pf))
    for path, i, old, new in plan:
        print("  %-18s 行%-4d %s" % (os.path.basename(path), i + 1, new.strip()[:78]))
    if not apply_:
        print("\n（dry-run；加 --apply 执行）")
        return 0

    # ---- 备份（幂等，逐个哈希校验）----
    os.makedirs(BK, exist_ok=True)
    for path in {x[0] for x in plan}:
        b = os.path.join(BK, os.path.basename(path))
        if not os.path.isfile(b):
            shutil.copy2(path, b)
        if sha(path) != sha(b):
            print("  ✗ 备份校验不符：%s ⇒ 终止" % path)
            return 1
    print("  备份就绪 → %s" % BK)

    # ---- 写入 ----
    for path in {x[0] for x in plan}:
        ls = open(path, encoding="utf-8").read().split("\n")
        for pp, i, old, new in plan:
            if pp == path:
                assert ls[i] == old, "行%d 已被改动，终止" % (i + 1)
                ls[i] = new
        open(path, "w", encoding="utf-8", newline="\n").write("\n".join(ls))
        print("  ✅ 已写 %s" % os.path.basename(path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
