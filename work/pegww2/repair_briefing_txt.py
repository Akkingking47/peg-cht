#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复「场景简介面板(`.SCN` @11329 指向的 `.TXT`) 内容拿错」（**改写原文备份**，附存档 + 审计）。

背景（2026-10-19，用户实机截图「场景选择画面」）：
  `sedan.scn`（显示名=`SEDAN_m.txt` 行0「西线-26 色当 PeG:WW2」）的 @11329 = `S`，
  引擎据此读 `SCENARIO\\S.TXT`。而 `S.TXT` 实际是**另一场景**（"On the move" / 行军中，
  其 `_m` 载德绍—莱比锡地名）的单位/地名清单 ⇒ 简介面板整份显示成地名列表。

判据与修法：
  · `.SCN` 的 @11329 指向的 `.TXT` 就是**简介面板**的内容来源；
  · 本脚本把 `backup/<目标>.TXT` 重写为 `backup/<来源>.TXT`（同场应有的简介），
    旧文件另存 `<目标>.TXT.broken-orig`；随后走 gen_scn build → deploy_scn。

用法: python repair_briefing_txt.py [--apply]
"""
import io
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
RES = os.path.join(WS, "pegww2", "research")
LOG = os.path.join(RES, "_简介修复-20261019.tsv")

# (目标文件, 来源文件, 所属场景, 说明)
JOBS = [
    ("S.TXT", "S-R.TXT", "sedan.scn(西线-26 色当)",
     "@11329='S' 而 S.TXT 是别场(行军中/德绍)清单 ⇒ 换成色当简介"),
    ("Sl1-R.TXT", "SL1.TXT", "stlo-R.SCN / stlouk-R.SCN(向圣洛推进：重制版)",
     "@11329='Sl1-R' 而 Sl1-R 是别场(柏林之战 #7d10)清单 ⇒ 换成圣洛简介"),
    ("Kl-R.TXT", "KL.TXT", "klin-R.SCN(东线-10 克林：重制版)",
     "@11329='Kl-R' 而 Kl-R 是别场(先头部队)清单 ⇒ 换成克林简介"),
]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    apply_ = "--apply" in sys.argv
    rows = []
    for tgt, src, scn, why in JOBS:
        tp, sp = os.path.join(BK, tgt), os.path.join(BK, src)
        if not os.path.isfile(tp) or not os.path.isfile(sp):
            print("  ❌ %-10s 缺（目标=%s 来源=%s）" % (tgt, os.path.isfile(tp), os.path.isfile(sp)))
            continue
        tb = io.open(tp, "rb").read()
        sb = io.open(sp, "rb").read()
        if tb == sb:
            print("  ⏭ %-10s 已一致" % tgt)
            continue
        rows.append([scn, tgt, src, str(tb.count(b"\n") + 1), str(sb.count(b"\n") + 1), why])
        print("  %-10s ← %-10s (%d→%d 行)  %s" % (tgt, src, tb.count(b"\n") + 1, sb.count(b"\n") + 1, why))
        if apply_:
            arc = tp + ".broken-orig"
            if not os.path.isfile(arc):
                shutil.copy2(tp, arc)
            shutil.copy2(sp, tp)
            back = io.open(tp, "rb").read()
            assert back == sb, "回读校验失败（%s）" % tgt
    if rows:
        head = not os.path.isfile(LOG)
        with io.open(LOG, "a", encoding="utf-8", newline="\n") as f:
            if head:
                f.write("# 场景简介(`@11329`.TXT)「内容拿错」修复留痕（改写原文备份；旧文件存为 `.broken-orig`）\n")
                f.write("场景\t目标文件\t来源文件\t原行数\t新行数\t说明\n")
            for r in rows:
                f.write("\t".join(r) + "\n")
        print("→ %s" % LOG)
    print("[APPLY]" if apply_ else "[DRY-RUN]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
