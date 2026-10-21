#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「番号翻译」引入的**跨层多译**登记进 `glossary/layers/override.tsv`。

背景（用户裁定 2026-10-19）：
  本作真源里 542 行番号改成中文后，**其他 scope 层**（前作 OLG-WW2 等）里仍存着
  「番号原样保留」的旧写法 ⇒ 词库门报「跨层多译 / 通用层内多译（新偏离）」并拒绝构建。
  项目 D-3 规则：**同键多译一律走覆盖表，禁改层表主键** ⇒ 登记即可，不去动别人的层表。

判据：只登记**本次改过、且词库确实存在多值**的键（不批量登记、不误伤）。
纪律：幂等（已登记则跳过）· 默认 dry-run · `--apply` 才写 · 写前备份 `.pre-abbrreg`。

用法：python register_abbr_overrides.py [--apply]
"""
import argparse
import collections
import io
import os
import shutil
import sys

WS = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
RES = os.path.join(WS, "pegww2", "research")
OVR = os.path.join(WS, "glossary", "layers", "override.tsv")
LAYERS = [os.path.join(WS, "glossary", "layers", n) for n in
          ("common-glossary.tsv", "series-glossary.tsv", "scope-glossary.tsv",
           "short-glossary.tsv")]
TABLE = os.path.join(RES, "_番号-对照表.tsv")
REASON = "用户裁定2026-10-19·部队番号按战役国别翻译；旧层为番号原样保留写法"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    # 本次改过的键 → 新译文（番号改写表）
    changed = {}
    with io.open(TABLE, encoding="utf-8-sig") as fh:
        for raw in fh:
            s = raw.rstrip("\r\n")
            if not s or s.startswith("#") or s.startswith("表\t"):
                continue
            f = s.split("\t")
            if len(f) >= 4:
                changed.setdefault(f[1], set()).add(f[3])

    # ＋ 字形/漏译定点改写（fix_misc_batch 的 FIXED）—— 它们同样会撞旧层取值
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from fix_misc_batch import FIXED
        for k, (_old, rep) in FIXED.items():
            changed.setdefault(k, set()).add(rep)
    except Exception as e:                                  # noqa: BLE001
        print("（⚠️ 读不到 fix_misc_batch.FIXED：%s）" % e)

    # 词库各层的候选值
    by = collections.defaultdict(set)
    note = {}
    for p in LAYERS:
        if not os.path.isfile(p):
            continue
        with io.open(p, encoding="utf-8-sig") as fh:
            for raw in fh:
                s = raw.rstrip("\r\n")
                if not s or s.startswith("#"):
                    continue
                f = s.split("\t")
                if len(f) < 2 or f[0] == "en":
                    continue
                by[f[0]].add(f[1])
                if len(f) > 11 and f[11].strip():
                    note.setdefault(f[0], f[11].strip())

    # 已有登记 —— ⚠️ 必须按「键＋值」去重：门是按具体取值判「已登记」，
    # 只按键去重会漏掉「同键旧值已登记、新值未登记」这一型（实测踩过）
    have = set()
    if os.path.isfile(OVR):
        with io.open(OVR, encoding="utf-8-sig") as fh:
            for raw in fh:
                s = raw.rstrip("\r\n")
                if not s or s.startswith("#"):
                    continue
                f = s.split("\t")
                if len(f) >= 3 and f[0] != "en":
                    have.add((f[0], f[2]))

    rows = []
    for key in sorted(changed):
        vals = by.get(key, set())
        if len(vals) < 2:
            continue                       # 词库单值 ⇒ 无偏离，无需登记
        # ⚠️ 门判据是 `set(取值) <= override[键]`（全部取值都要登记）——
        # 只登记新值会漏掉旧层那个「番号原样保留」的取值（实测踩过）
        for v in sorted(vals | changed[key]):
            if (key, v) in have:
                continue                   # 幂等（键＋值）
            rows.append((key, "专项", v, REASON, note.get(key, "部队名")))

    print("本次改过 %d 键；词库存在多值且未登记 %d 键 → 待登记 %d 行"
          % (len(changed), len({r[0] for r in rows}), len(rows)))
    for r in rows[:12]:
        print("   %-34s ⇒ %s" % (r[0][:34], r[2][:38]))

    if args.apply and rows:
        shutil.copy2(OVR, OVR + ".pre-abbrreg")
        with io.open(OVR, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("# ── 番号缩写翻译（%s）──\n" % REASON)
            for r in rows:
                fh.write("\t".join(r) + "\n")
        print("已追加 %d 行 → %s（备份 .pre-abbrreg）" % (len(rows), os.path.relpath(OVR, WS)))
    elif not args.apply:
        print("（dry-run；加 --apply 才写）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
