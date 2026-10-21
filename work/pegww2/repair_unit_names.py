#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复「单位名单(`_u.txt`) 被整份拿错」的场景（**改写原文备份**，附存档 + 审计）。

背景（2026-10-19，用户实机截图）：
  `保卫帝国`＝`CAMP2.CAM`；其 `winter`（冬季风暴行动）一场的 `winter_u.txt`（单位名单）
  英文原版就是**别场的**内容：行0＝`Operation Avalanche - Part I`、正文＝萨莱诺地名
  （第勒尼安海/维苏威山/索伦托…）⇒ 实机把单位名显示成了地名。

判据与修法：
  · `_u.txt` 行0＝该场名、行1+＝**单位番号**（如 `2/11R`），与 `.SCN` 里的单位槽位**按序对应**；
  · 同场的 `<stem>.TXT`＝该场主表（行0＝名；单位段 + 地名段），**单位段即 `_u` 应有的内容**；
  · 本脚本把 `<stem>_u.txt`（备份）重写为 `[.TXT 行0] + .TXT 的单位段`，
    替换前的旧文件另存 `<stem>_u.txt.broken-orig`（不参与流水线），并写审计表。

用法: python repair_unit_names.py [--apply] winter [...]
"""
import io
import os
import re
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
RES = os.path.join(WS, "pegww2", "research")
LOG = os.path.join(RES, "_单位名单修复-20261019.tsv")
UNIT = re.compile(r"^[0-9O0-9A-Za-z]*[0-9][0-9A-Za-z/]*$")     # 番号式：含数字的短代号


def lines(path, enc="cp1252"):
    return io.open(path, encoding=enc, errors="replace").read().splitlines()


def real(i, n):
    return i.get(n.lower())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    apply_ = "--apply" in sys.argv
    stems = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not stems:
        print("用法: python repair_unit_names.py [--apply] <stem> ...")
        return 1
    rows = []
    for st in stems:
        u = real({n.lower(): n for n in os.listdir(BK)}, st + "_u.txt")
        t = real({n.lower(): n for n in os.listdir(BK)}, st + ".TXT") or \
            real({n.lower(): n for n in os.listdir(BK)}, st + ".txt")
        if not u or not t:
            print("  ❌ %-14s 备份缺 %s" % (st, "_u.txt" if not u else ".TXT"))
            continue
        up, tp = os.path.join(BK, u), os.path.join(BK, t)
        ul, tl = lines(up), lines(tp)
        # 单位段 = `.TXT` 行1 起、到「地名段起点」之前。地名段起点 = 该场 `_m.txt` 行1（首个地名）
        ml = lines(os.path.join(BK, (st + "_m.txt"))) if os.path.isfile(os.path.join(BK, st + "_m.txt")) else []
        cut, place0 = None, (ml[1].strip() if len(ml) > 1 and ml[1].strip() else "")
        if place0:
            for k in range(1, len(tl)):
                if tl[k].strip() == place0:
                    cut = k
                    break
        if cut is None:      # 回退：扫到首个「既非番号式、又像长地名」的行为止
            for k in range(1, len(tl)):
                s = tl[k].strip()
                if not s:
                    continue
                if UNIT.match(s) and any(ch.isdigit() for ch in s):
                    continue
                if len(s) <= 2 or s.isupper():
                    continue          # 允许 `R`/`L4` 这类短代号留在单位段
                cut = k
                break
        body = [x.strip() for x in tl[1:cut]] if cut else []
        body = [x for x in body if x]
        if len(body) < 3 or body == [x.strip() for x in ul[1:len(body) + 1]]:
            print("  ⏭ %-14s .TXT 单位段不可用或已一致（%d 条）" % (st, len(body)))
            continue
        new = [tl[0].strip()] + body
        rows.append([st, u, str(len(ul)), str(len(new)), tl[0].strip(), " | ".join(ul[1:4]), " | ".join(new[1:4])])
        print("  %-14s %s: %d 行 → %d 行  行0 %r → %r"
              % (st, u, len(ul), len(new), ul[0].strip(), new[0]))
        if apply_:
            arc = up + ".broken-orig"
            if not os.path.isfile(arc):
                shutil.copy2(up, arc)
            with io.open(up, "w", encoding="cp1252", newline="") as f:   # newline='' ⇒ 不自作翻译
                f.write("\r\n".join(new) + "\r\n")
            back = lines(up)
            assert len(back) == len(new) and back[0] == new[0], \
                "回读校验失败（%d/%d 行，行0=%r）" % (len(back), len(new), back[0] if back else "")
    if rows:
        head = not os.path.isfile(LOG)
        with io.open(LOG, "a", encoding="utf-8", newline="\n") as f:
            if head:
                f.write("# 单位名单(`_u.txt`)「整份拿错」修复留痕（改写原文备份；旧文件存为 `.broken-orig`）\n")
                f.write("场景\t_文件\t原行数\t新行数\t新行0(原文)\t原行1-3\t新行1-3\n")
            for r in rows:
                f.write("\t".join(r) + "\n")
        print("→ %s" % LOG)
    print("[APPLY]" if apply_ else "[DRY-RUN]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
