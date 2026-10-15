#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**偏离分桶**（收敛前置）：把"同原文多译"分成三类，只留真正要动手的那一类。

分桶规则（可审）：
  A **跨项目差异**  参与 scope 全是别的游戏/efile（`EFILE_*`）或含 `PEGWW2_*` 与 `EFILE_*` 混合
                    ⇒ 不同作品各自成词，**合法**，登记即可（scope-diff）
  B **同形异义**    各译法**无共同汉字**（如 Ranger 游骑兵(美军)/突击队(英军)、March 马奇/三月）
                    ⇒ 语境不同，**合法**，登记（scope-diff）
  C **同家族待收敛** 参与 scope 全在 `PEG`/`PEGWW2` 家族内，且非 B
                    ⇒ **要动手**：按"本作界面层为准"收敛，或登记"前作未同步"
输出：`layers/converge-list.tsv`（分桶清单）+ 追加登记到 `layers/scope-diff.tsv`

用法: python converge_plan.py [--apply]
"""
import collections
import io
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
GL = os.path.join(WS, "glossary")
LAY = os.path.join(GL, "layers")
RES = os.path.join(WS, "pegww2", "research")
PRES = os.path.join(WS, "peg", "research")
TABLES = [("WW2Gui-map.tsv", os.path.join(RES, "WW2Gui-map.tsv"), 1, 2, "PEGWW2_UI"),
          ("ww2-eqp-map.tsv", os.path.join(RES, "ww2-eqp-map.tsv"), 0, 1, "PEGWW2_EQP"),
          ("ww2-scn-map.tsv", os.path.join(RES, "ww2-scn-map.tsv"), 0, 1, "PEGWW2_SCN")]
SKIP = ("原文", "行号", "en", "english", "檔類", "档类")


def hanzi(s):
    return {c for c in s if "\u4e00" <= c <= "\u9fff"}


def load_override():
    """`override.tsv`：`en | 层 | 覆盖为 | 理由 | 用途` ⇒ `{en: {覆盖为…}}`（**只收「用途」列非空的行**，
    因为只有这类才是"同原文按用途分工"的显式登记）。

    ⚠️ 列序与 `scope-diff.tsv` **不同**：值在第 3 列（索引 2）、用途在第 5 列（索引 4）。
    """
    ov = collections.defaultdict(set)
    p = os.path.join(LAY, "override.tsv")
    if os.path.isfile(p):
        for l in io.open(p, encoding="utf-8"):
            if l.startswith("#") or l.startswith("en\t"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 5 and c[2].strip() and c[4].strip():
                for v in c[2].replace("|", "\t").split("\t"):
                    if v.strip():
                        ov[c[0].strip()].add(v.strip())
    return ov


def main():
    apply_ = "--apply" in sys.argv
    by = collections.defaultdict(list)
    for fn in ("common-glossary.tsv", "series-glossary.tsv", "scope-glossary.tsv"):
        for l in io.open(os.path.join(LAY, fn), encoding="utf-8"):
            if l.startswith("#") or l.startswith("en\t"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 9:
                by[c[0]].append((c[1], c[8], c[3]))

    buckets = {"A跨项目差异": [], "B同形异义": [], "C同家族待收敛": [], "用途分工": []}
    FAM = ("PEG_UI", "PEG_BASE", "PEGWW2_UI", "PEGWW2_DOCS")
    OV = load_override()
    for en, lst in by.items():
        zs = sorted({z for z, _la, _sc in lst})
        if len(zs) < 2:
            continue
        scopes = sorted({sc for _z, _la, sc in lst})
        fam_zh = sorted({z for z, _la, sc in lst if sc in FAM})
        # ⓪ 家族内两种译法，但**已按用途显式分工登记**（override.tsv 第 5 列）⇒ 合法，不是"待收敛"。
        #    踩过（W22）：`Air Transport` 空中运输/空运 · `Naval Transport` · `AT` · `Air Defense`
        #    4 组被判成 C 桶"同家族待收敛"，其实它们的分工早已逐条登记（兵种名 vs 按钮/数值），
        #    属**有意分工** —— 分桶时没读 override.tsv 的用途列，把合法分工当成了缺陷。
        if len(fam_zh) >= 2 and en in OV and set(fam_zh) <= OV[en]:
            buckets["用途分工"].append((en, zs, scopes, "按用途分工（override.tsv 已登记）"))
            continue
        # ① 家族内自己就不一致 ⇒ C（**优先判**：这才是"系列层该收敛"的地方。
        #    若先用"无共同汉字"启发式，`Profile` 概况/轮廓 会被误判成同形异义）
        if len(fam_zh) >= 2:
            why = "同家族不一致（本作界面层为准）" if set(fam_zh) == set(zs) else "含家族内不一致（另有跨项目译法）"
            buckets["C同家族待收敛"].append((en, zs, scopes, why))
            continue
        hs = [hanzi(z) for z in zs]
        if all(hs) and not set.intersection(*hs):
            buckets["B同形异义"].append((en, zs, scopes, "各译法无共同汉字 ⇒ 语境不同"))
        else:
            buckets["A跨项目差异"].append((en, zs, scopes, "跨作品/efile 各自成词"))

    # 层表与词库「不一致」清单（金标：表里有、词库给的却是别的）
    mism = []
    for tag, path, ec, zc, scope in TABLES:
        if not os.path.isfile(path):
            continue
        cnt = 0
        for l in io.open(path, encoding="utf-8-sig"):
            if l.startswith("#"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) <= max(ec, zc) or not c[ec].strip():
                continue
            en, zh = c[ec].strip(), c[zc].strip()
            if not zh or en.lower() in SKIP:
                continue
            cands = {z for z, _la, _sc in by.get(en, ())}
            if cands and zh not in cands:
                mism.append((tag, en, zh, "/".join(sorted(cands))[:30]))
                cnt += 1
        print("   %-20s 表内有、词库给别的：%d 处" % (tag, cnt))

    print()
    for k, v in buckets.items():
        print("=== %s : %d 条 ===" % (k, len(v)))
        for en, zs, scopes, why in v[:10]:
            print("   %-24s %s  [%s]" % (en[:24], " ｜ ".join(zs)[:60], "/".join(scopes)[:34]))
    print("\n表↔库不一致 %d 处（前 12）：" % len(mism))
    for tag, en, zh, ca in mism[:12]:
        print("   %-14s %-26s 表=%-14s 库=%s" % (tag, en[:26], zh[:14], ca))

    if not apply_:
        print("\n（dry-run；加 --apply 写 converge-list.tsv / scope-diff.tsv）")
        return 0
    with io.open(os.path.join(LAY, "converge-list.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# 偏离分桶：A/B 合法（登记 scope-diff 即可）· 用途分工=已登记的有意分工 · C 需动手收敛 · D 表↔库不一致\n")
        f.write("桶\ten\t各译法\tscopes\t理由\n")
        for k, v in buckets.items():
            for en, zs, scopes, why in v:
                f.write("%s\t%s\t%s\t%s\t%s\n" % (k, en, "|".join(zs), "|".join(scopes), why))
        for tag, en, zh, ca in mism:
            f.write("D表↔库不一致\t%s\t表=%s|库=%s\t%s\t需裁定\n" % (en, zh, ca, tag))
    # ⚠️ 写盘前先把「本轮分桶没产出」的既有登记读出来保留：本文件是 `"w"` 整体重写，
    #    否则任何手工/历史登记一次重跑就没了（踩过）。
    new_en = set()
    for k in ("A跨项目差异", "B同形异义", "用途分工", "C同家族待收敛"):
        new_en |= {en for en, _z, _s, _w in buckets[k]}
    keep_old = []
    old_p = os.path.join(LAY, "scope-diff.tsv")
    if os.path.isfile(old_p):
        for l in io.open(old_p, encoding="utf-8"):
            if l.startswith("#") or l.startswith("en\t") or not l.strip():
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 4 and c[0].strip() and c[0].strip() not in new_en:
                keep_old.append(l.rstrip("\n"))
    with io.open(os.path.join(LAY, "scope-diff.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# 跨项目/同形异义/前作未同步：**允许不同**（登记后不再报错；由 converge_plan.py 产出）\n")
        f.write("# 类别：A跨项目差异（别的游戏/efile 各自成词）｜B同形异义（同一拼写、不同意思）"
                "｜用途分工（override.tsv 第 5 列已登记）｜前作未同步（本作界面层为准）\n")
        f.write("en\t各译法\t类别\t理由\n")
        for k in ("A跨项目差异", "B同形异义", "用途分工"):
            for en, zs, scopes, why in buckets[k]:
                f.write("%s\t%s\t%s\t%s（scopes=%s）\n" % (en, "|".join(zs), k, why, "|".join(scopes)))
        # C：家族内不一致 ⇒ 按用户裁决「本作界面层为准」登记为「前作未同步」。
        # ⚠️ **全部写入**（含已在 override.tsv 登记过的）：否则它们在别的作品里的语感
        #    （如 `AT` 在 OLGWW2 是"反坦克营"）会没人登记 ⇒ 门报"未登记"。
        #    两张表在 `layer_gate.py` 里取并集，重叠无害。
        n_c = 0
        for en, zs, scopes, why in buckets["C同家族待收敛"]:
            tag = "另有 override 分工登记" if en in OV else "本作界面层为准"
            f.write("%s\t%s\t前作未同步\t%s（%s；scopes=%s）\n"
                    % (en, "|".join(zs), why, tag, "|".join(scopes)))
            n_c += 1
        for l in keep_old:                     # 保留本轮分桶没产出的既有登记
            f.write(l + "\n")
    print("\n已写 converge-list.tsv（%d 条）· scope-diff.tsv（%d 条自动登记，其中用途分工 %d · 前作未同步 %d · 保留既有 %d 条）"
          % (sum(len(v) for v in buckets.values()) + len(mism),
             len(buckets["A跨项目差异"]) + len(buckets["B同形异义"]) + len(buckets["用途分工"]) + n_c + len(keep_old),
             len(buckets["用途分工"]), n_c, len(keep_old)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
