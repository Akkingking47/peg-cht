#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**可再生成性验收**：分层词库能否重建各层表？（治本件的验收标准）

判据（用户要的"引用率"其实就该这么验）：
  对层表每一行，看它的译文**能否从分层词库复现**：
    · `命中`    = 该译文出现在词库中该原文的候选里
    · `多值`    = 词库对该原文有多种译法（需按 层/scope 裁定，属**词库需收敛**的信号）
    · `缺失`    = 词库根本没有该原文（需入库）

另外产出一份**投影样张**：按 pg-cht `apply_glossary` 的策略
（整行命中→替换；整行分词全命中→拼接；否则保留原文），从**英文原件**生成界面层表，
用来证明"词库 → 层表"这条路真能跑通。

用法: python materialize.py [--apply]
"""
import collections
import io
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
GL = os.path.join(WS, "glossary")
LAY = os.path.join(GL, "layers")
EVID = os.path.join(GL, "evidence")
RES = os.path.join(WS, "pegww2", "research")
BKUI = os.path.join(WS, "pegww2", "testbed", "backup", "text", "WW2Gui.txt")

TARGETS = [
    ("界面层表 WW2Gui-map.tsv", os.path.join(RES, "WW2Gui-map.tsv"), 1, 2),
    ("装备层表 ww2-eqp-map.tsv", os.path.join(RES, "ww2-eqp-map.tsv"), 0, 1),
    ("场景层表 ww2-scn-map.tsv", os.path.join(RES, "ww2-scn-map.tsv"), 0, 1),
]
# ⭐ 层表 = 词库的**派生物**：这五张表可由词库重新生成（第 2 项治本）
PROJECT_TABLES = [
    ("pegww2/research/WW2Gui-map.tsv", os.path.join(RES, "WW2Gui-map.tsv"), 1, 2, "PEGWW2_UI"),
    ("pegww2/research/WW2Misc-map.tsv", os.path.join(RES, "WW2Misc-map.tsv"), 1, 2, "PEGWW2_UI"),
    ("pegww2/research/WW2Tips-map.tsv", os.path.join(RES, "WW2Tips-map.tsv"), 1, 2, "PEGWW2_UI"),
    ("pegww2/research/ww2-eqp-map.tsv", os.path.join(RES, "ww2-eqp-map.tsv"), 0, 1, "PEGWW2_EQP"),
    ("pegww2/research/ww2-scn-map.tsv", os.path.join(RES, "ww2-scn-map.tsv"), 0, 1, "PEGWW2_SCN"),
    ("peg/research/gui030-zh.tsv", os.path.join(WS, "peg", "research", "gui030-zh.tsv"), 1, 2, "PEG_UI"),
]


def load_override_rules():
    """`override.tsv` 的**按用途分工**规则：(en, 用途) → 译法。

    ⚠️ 词库 `note` 列混了两套词表（PFS 分段 / 语义类别），所以"同原文按用途分工"必须
    **显式登记**在这里，派生时先查它；否则同一张表里 `Air Defense` 兵种/数值两译派生不出来。
    """
    rules = {}
    p = os.path.join(LAY, "override.tsv")
    if not os.path.isfile(p):
        return rules
    for l in io.open(p, encoding="utf-8"):
        if l.startswith("#") or l.startswith("en\t"):
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) >= 5 and c[0].strip() and c[2].strip():
            for use in c[4].split("|"):
                if use.strip():
                    rules[(c[0].strip(), use.strip())] = c[2].strip()
    return rules


def load_faction_rules():
    """`faction-terms.tsv`：(en, 阵营) → 译名。**同一原文按"谁的文本"取不同名字**。

    例：`Amur River` 苏/俄⇒阿穆尔河、中⇒黑龙江；`Zitadelle` 德⇒堡垒行动、
    苏方文本指同一战役⇒库尔斯克会战（见 glossary/阵营视角-约定.md）。
    """
    r = {}
    p = os.path.join(LAY, "faction-terms.tsv")
    if not os.path.isfile(p):
        return r
    for l in io.open(p, encoding="utf-8"):
        if l.startswith("#") or l.startswith("en\t"):
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) >= 3 and c[0].strip() and c[1].strip() and c[2].strip():
            r[(c[0].strip(), c[1].strip())] = c[2].strip()
    return r


def derive(by, en, scope, use="", faction=""):
    """按「**阵营** → override用途 → 用途+本项目层 → 本项目层 → 用途 → 兵种类 → 跨层」取译名。

    ⚠️ 必须带**阵营**与**用途**两个维度：
      · 阵营：`Amur River` 在苏方文本＝阿穆尔河、中方文本＝黑龙江（都对）；
      · 用途：同一张表里 `Air Defense` 兵种＝防空 / 数值＝对空防御。
    """
    if faction and (en, faction) in FRULE:
        return FRULE[(en, faction)], "阵营"
    if use and (en, use) in ORULE:
        return ORULE[(en, use)], "override用途"
    cands = by.get(en)
    if not cands:
        return "", "缺失"
    for pred, how in ((lambda z, la, sc, nt: sc == scope and use and nt == use, "用途+本项目层"),
                      (lambda z, la, sc, nt: sc == scope, "本项目层"),
                      (lambda z, la, sc, nt: use and nt == use, "用途"),
                      # ⚠️ 值模式表（如 WW2Misc）没有行号 ⇒ 拿不到 PFS 用途；
                      #    它的条目是**兵种/属性标签**，故优先取标注为兵种类的译法。
                      (lambda z, la, sc, nt: nt in ("主库:UNIT", "兵种") or "EQUIPMENT CLASS" in nt, "兵种类"),
                      (lambda z, la, sc, nt: True, "跨层")):
        hit = [z for z, la, sc, nt in cands if pred(z, la, sc, nt)]
        if len(set(hit)) == 1:
            return hit[0], how
    return cands[0][0], "多值取首"


def pfs_segs():
    """行号 → PFS 用途（界面层表用；值模式表没有用途）。"""
    out, cur = {}, None
    p = os.path.join(WS, "work", "peg", "pfs", "GUI-Segmented.txt")
    if not os.path.isfile(p):
        return out
    for l in io.open(p, encoding="cp1252", errors="replace"):
        c = l.split("|")
        if len(c) < 3:
            continue
        num = c[2].strip()
        if not num:
            continue
        if num.replace(".", "").isdigit():
            if cur:
                out[int(float(num))] = cur
        else:
            cur = num
    return out


def write_tables(by, apply_):
    """从词库重新生成各层表（`*.regen.tsv`），并核验与现行表是否一致。"""
    seg = pfs_segs()
    print("\n=== 层表作**派生物**：由词库重新生成 ===")
    tot = diff_tot = 0
    for tag, path, ec, zc, scope in PROJECT_TABLES:
        if not os.path.isfile(path):
            continue
        out, n, diff = [], 0, []
        for l in io.open(path, encoding="utf-8-sig"):
            s = l.rstrip("\n")
            if s.startswith("#"):
                out.append(s)
                continue
            c = s.split("\t")
            if len(c) <= max(ec, zc) or not c[ec].strip() or c[ec].lower() in SKIP:
                out.append(s)
                continue
            en, zh = c[ec].strip(), c[zc].strip()
            use = seg.get(int(c[0])) if (ec == 1 and c[0].strip().isdigit()) else ""
            d, how = derive(by, en, scope, use or "")
            # ⚠️ 只在**内容**不同时才改写：仅有空白差异（前导/尾随空格）时保留原样 ——
            #    空白可能是有意的（对齐），派生不该动它。
            if d and d.strip() != zh.strip():
                diff.append((en, zh, d, how))
            if d and d.strip() != zh.strip():
                c[zc] = d
            out.append("\t".join(c))
            n += 1
        tot += n
        diff_tot += len(diff)
        if apply_:
            os.makedirs(EVID, exist_ok=True)
            io.open(os.path.join(EVID, "regen-" + os.path.basename(path)), "w",
                    encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
        print("   %-36s 行 %-6d 派生不一致 %d" % (tag, n, len(diff)))
        for en, zh, d, how in diff[:3]:
            print("      ⚠️ %-30s 表=%-14s 词库派生=%s（%s）" % (en[:30], zh[:14], d[:14], how))
    print("   ⇒ 合计 %d 行 · **派生不一致 %d 处**%s" % (tot, diff_tot, "（=0 ⇒ 层表确为词库派生物）" if diff_tot == 0 else ""))
    return diff_tot


SKIP = ("原文", "行号", "en", "english", "檔類", "档类")


def load_layers():
    by = collections.defaultdict(list)      # en -> [(zh, layer, scope, 用途note)]
    for fn in ("common-glossary.tsv", "series-glossary.tsv", "scope-glossary.tsv"):
        p = os.path.join(LAY, fn)
        if not os.path.isfile(p):
            continue
        for l in io.open(p, encoding="utf-8"):
            if l.startswith("#") or l.startswith("en\t"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 12:
                by[c[0]].append((c[1], c[8], c[3], c[11]))
            elif len(c) >= 9:
                by[c[0]].append((c[1], c[8], c[3], ""))
    return by


def main():
    apply_ = "--apply" in sys.argv
    by = load_layers()
    global ORULE, FRULE
    ORULE = load_override_rules()
    FRULE = load_faction_rules()
    print("词库候选原文 %d 条（三层合并）" % len(by))
    print()
    print("%-26s %8s %8s %8s %8s" % ("层表", "行数", "单值命中", "多值", "缺失/不一致"))
    print("-" * 64)
    rep = ["可再生成性验收", "=" * 60, "词库候选原文 %d 条" % len(by), ""]
    for tag, path, ec, zc in TARGETS:
        if not os.path.isfile(path):
            continue
        n = hit = multi = miss = 0
        sample_miss = []
        for l in io.open(path, encoding="utf-8-sig"):
            if l.startswith("#"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) <= max(ec, zc) or not c[ec].strip():
                continue
            en, zh = c[ec].strip(), c[zc].strip()
            if not zh or en.lower() in ("原文", "行号", "en", "english", "檔類", "档类"):
                continue                                    # 跳表头，别把表头当"缺失"
            n += 1
            cands = [x[0] for x in by.get(en, ())]
            if not cands:
                miss += 1                                   # 词库根本没这个原文 ⇒ 未入库
                if len(sample_miss) < 3:
                    sample_miss.append(("[未入库] " + en, zh))
            elif zh in cands:
                if len(set(cands)) > 1:
                    multi += 1                              # 可复现，但同原文有多值
                else:
                    hit += 1
            else:
                # ⚠️ 踩点：这里原写成 multi ⇒ 把"译文不在候选里"错算成多值，导致"缺失 0"**假绿**。
                #    正确语义：词库有该原文、但译法与层表**不一致** ⇒ 必须进收敛清单。
                miss += 1
                if len(sample_miss) < 3:
                    sample_miss.append(("[不一致] " + en, zh + " ←库:" + "/".join(dict.fromkeys(cands))[:24]))
        print("%-26s %8d %8d %8d %8d" % (tag, n, hit, multi, miss))
        rep.append("%-26s 行 %d · 命中 %d · 多值 %d · 缺失 %d" % (tag, n, hit, multi, miss))
        for en, zh in sample_miss:
            rep.append("      缺失样例: %-34s → %s" % (en[:34], zh[:20]))

    # 投影样张：从英文原件生成界面层表（pg-cht 策略）
    if os.path.isfile(BKUI):
        raw = io.open(BKUI, encoding="cp1252", errors="replace").read().split("\n")
        out = []
        for i, en in enumerate(raw, 1):
            key = en.strip()
            zh, how = "", ""
            if key and key in by:
                zh, how = by[key][0][0], "整行命中"
            elif key and len(key.split()) >= 2 and all(w in by for w in key.split()):
                zh, how = "".join(by[w][0][0] for w in key.split()), "分词拼接"
            out.append((i, key, zh, how))
        n_hit = sum(1 for _a, _b, z, _h in out if z)
        print("\n投影样张（WW2Gui 英文原件 → 词库生成）：%d 行，可生成 %d 行（%.0f%%），其余保留原文"
              % (len(out), n_hit, 100.0 * n_hit / max(1, len(out))))
        rep += ["", "投影样张（apply_glossary 策略）：%d 行，可生成 %d 行（%.0f%%）"
                % (len(out), n_hit, 100.0 * n_hit / max(1, len(out)))]
        if apply_:
            os.makedirs(EVID, exist_ok=True)
            with io.open(os.path.join(EVID, "materialize-WW2Gui.tsv"), "w", encoding="utf-8", newline="\n") as f:
                f.write("# 投影样张：行号\t原文\t词库生成\t命中方式（其余保留原文=hybrid）\n")
                for a, b, z, h in out:
                    f.write("%d\t%s\t%s\t%s\n" % (a, b, z, h))
    rep += ["", "判据：命中=可从词库复现；多值=词库对该原文有多种译法（需按层/scope 收敛）；缺失=未入库"]
    if "--write-tables" in sys.argv:
        d = write_tables(by, apply_)
        rep += ["", "层表派生核验：不一致 %d 处" % d]
    if apply_:
        os.makedirs(EVID, exist_ok=True)
        io.open(os.path.join(EVID, "materialize-report.txt"), "w", encoding="utf-8").write("\n".join(rep) + "\n")
        print("\n报告 → glossary/evidence/materialize-report.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
