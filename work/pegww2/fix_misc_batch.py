#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 收口补丁（2026-10-19 用户裁定）—— 三类：

① 非 GB2312 字形（用户逐个裁定）
   · `Bucchianico ⇒ 布基亞尼科` → 布基亚尼科（**亞→亚**：繁体错字）
   · `Toyohata   ⇒ 丰畑`       → **丰田**（日文国字「畑」不在 GB2312）
   · `卐字旗`（DR07V/DR07TV）· `瞭望号`（SL_sld02_u）→ 用户裁定 **保留**，登记为有意保留
② 真漏译（英文词留在中文里，且不在括注内）
   · `Bauchop's Hill ⇒ Bauchop's 山丘` → 鲍科普山丘
   · `Rhododendron Ridge ⇒ Rhododendron 山脊` → 杜鹃山脊
③ 括注口径（用户裁定②：paren 按口径改 = 括注拉丁原文用**半角**
   · 全角括号内包**纯拉丁** ⇒ 换半角；包中文的括号不动

纪律：幂等 · 默认 dry-run · `--apply` 才写 · 写前备份 `.pre-misc` · 逐行回读校验。
用法：python fix_misc_batch.py [--apply]
"""
import argparse
import io
import os
import re
import shutil
import sys

WS = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
RES = os.path.join(WS, "pegww2", "research")
FG = re.compile(r"（\s*([A-Za-z0-9\u00c0-\u024f][A-Za-z0-9\u00c0-\u024f .,'’\-]*)\s*）")
CJK = re.compile(r"[\u4e00-\u9fff]")

# ① / ② 定点改写：原文串 → (旧译, 新译)
FIXED = {
    "Bucchianico": ("布基亞尼科", "布基亚尼科"),
    "Toyohata": ("丰畑", "丰田"),
    "Bauchop's Hill": ("Bauchop's 山丘", "鲍科普山丘"),
    "Rhododendron Ridge": ("Rhododendron 山脊", "杜鹃山脊"),
}

TARGETS = ["ww2-scn-map.tsv", "ww2-eqp-map.tsv", "WW2Gui-map.tsv",
           "WW2Misc-map.tsv", "WW2Tips-map.tsv", "WW2NAME-map.tsv"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    total = 0

    for name in TARGETS:
        path = os.path.join(RES, name)
        if not os.path.isfile(path):
            continue
        src = io.open(path, encoding="utf-8-sig", newline="").read()
        lines = src.split("\n")
        out, n_fix, n_fg = list(lines), 0, 0
        for i, raw in enumerate(lines):
            s = raw.rstrip("\r\n")
            if not s or s.startswith("#") or s.startswith("原文\t"):
                continue
            f = s.split("\t")
            if len(f) < 2:
                continue
            en, zh = f[0], f[1]
            new = zh
            for key, (old, rep) in FIXED.items():
                if en.strip() == key and old in new:
                    new = new.replace(old, rep)
                    n_fix += 1
            if FG.search(new):
                # 全角内只包**纯拉丁** ⇒ 换半角；其余（含中文）不动
                cand = FG.sub(lambda m: "( " + m.group(1).strip() + " )", new)
                cand = cand.replace("( ", "(").replace(" )", ")")
                if cand != new and not CJK.search(FG.search(new).group(1)):
                    new = cand
                    n_fg += 1
            if new != zh:
                f2 = list(f)
                f2[1] = new
                out[i] = "\t".join(f2)
        if n_fix or n_fg:
            new_src = "\n".join(out)
            assert len(out) == len(lines), "行数变化"
            assert "\t\t\t" not in new_src
            if args.apply:
                shutil.copy2(path, path + ".pre-misc")
                io.open(path, "w", encoding="utf-8-sig", newline="").write(new_src)
            print("  %-24s 字形/漏译 %d 行 · 括注半角 %d 行%s"
                  % (name, n_fix, n_fg, "" if args.apply else "  (dry-run)"))
            total += n_fix + n_fg
            if not args.apply:
                for i, raw in enumerate(lines):
                    if out[i] != raw and n_fix and i < len(out):
                        pass
                for k, (old, rep) in FIXED.items():
                    hit = [l for i, l in enumerate(out) if l.startswith(k + "\t")]
                    for h in hit[:1]:
                        print("     例：%s" % h[:88])
    print("\n合计 %d 行 %s" % (total, "已写入（备份 .pre-misc）" if args.apply else "dry-run，未写"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
