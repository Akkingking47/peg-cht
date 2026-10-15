#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 DOCS · 词库自动命中填充器（纯查表，不涉翻译模型）。

用途：DOCS 里大量是**场景名/地名/单位名/装备名/表头**，而本作已有权威真源：
  · `pegww2\research\ww2-scn-map.tsv`（场景层 21,865 条）
  · `pegww2\research\ww2-eqp-map.tsv`（装备/单位名）
  · `work\strings-zh.txt` 等根级表（界面串）
本脚本按**整串精确匹配**把译文填进 _fill 表，并报告命中率；命中不了的留给翻译子代理。

纪律：只写 `_fill`；原文列与段号列一字不动；幂等（已有译文的行不覆盖）。
用法: python autofill_docs.py <批次|文件...>   [--apply]
"""
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
FILL = os.path.join(WS, "pegww2", "docs-zh", "_fill")

# 权威真源（按可信度排序，先命中先赢）
SOURCES = [
    os.path.join(RES, "ww2-scn-map.tsv"),
    os.path.join(RES, "ww2-eqp-map.tsv"),
    os.path.join(WS, "work", "strings-zh.utf8.txt"),
]

# 队列表头/标记词（表格里反复出现，直接给权威译法；实测这些都是 D5 高频未命中项）
MANUAL = {
    "BV": "辉煌胜利", "TV": "战术胜利", "Loss": "失败", "LOSS": "失败", "V": "胜利",
    "Win": "胜利", "WIN": "胜利", "Victory": "胜利", "Defeat": "失败",
    "Scenario": "场景", "Scenario name": "场景名", "Scenario Name": "场景名",
    "Map": "地图", "Map #": "地图#", "Map#": "地图#",
    "Players": "玩家数", "Turns": "回合数", "Date": "日期", "Notes": "备注", "Note": "备注",
    "Legend": "图例", "Normal Path": "正常路径", "Normal path": "正常路径",
    "Alternate Path": "备选路径", "Alternate path": "备选路径",
    "Alternate scenarios 1": "备选场景 1", "Alternate scenarios 2": "备选场景 2",
    "Alternate scenarios 3": "备选场景 3", "Alternate scenarios": "备选场景",
    "Alternative scenarios": "备选场景", "Choice scenarios": "可选场景",
    "Modified map": "改造地图", "Technique's modified map": "改造地图（作者自制）",
    "NA - Original map used": "无 —— 使用原始地图", "Original map used": "使用原始地图",
    "Campaign Path": "战役路径", "Prestige": "威望", "Core": "核心",
    "Core units": "核心单位", "Aux units": "辅助单位", "Auxiliary": "辅助单位",
    "Unit": "单位", "Units": "单位", "Equipment": "装备",
    "*.MAP files must be installed in Scenario (or Scenpac/Scenkor/Scennap/Scenacw) directory":
        "*.MAP 文件必须装入 Scenario（或 Scenpac/Scenkor/Scennap/Scenacw）目录",
    "*.S16 files must be installed in Map directory": "*.S16 文件必须装入 Map 目录",
}
# 说明：**地图文件名 stem（如 Oakridge/Volokol/Ciechano/BoBCarentan）按纪律保留原文**，不译。


# ⚠️ 护栏：**人名/厂牌**永不自动翻译（曾因词库里有人名而把 `Robert Mary` 自动译成「罗伯特·马里」，
#    跨 20 个文件一致地错——这正是「盲查表」那一类错误）。
NEVER_AUTOFILL = {
    "Robert Mary", "Mark Kirby", "Redball", "Luis Guzman", "Fred Chlanda", "Santiago Fuertes",
    "Jorge Gabitto", "J. Markham", "Steve Brown", "Dave Anderson", "D. Hone", "Doug Hone",
    "Narayan Sengupta", "N. Sengupta", "William Dickens", "Andreas Seidel", "Lasse Jensen",
    "Oronzo", "Dirk Kraemer", "John McNulty", "Jorge Federico Gabitto", "Pablo Schelgel",
    "The Latin Generals", "J Gabitto", "P Schlegel", "People's General", "PeG Suite", "SSI",
}

BATCHES = {
    "D5": None,   # 由命令行全量扫描 _fill 下 *.xls.cells.tsv
}


def load_sources():
    m = {}
    for p in SOURCES:
        if not os.path.isfile(p):
            continue
        enc = "utf-8-sig"
        try:
            rows = open(p, encoding=enc).read().split("\n")
        except Exception:
            continue
        n = 0
        for l in rows:
            s = l.rstrip("\r")
            if not s or s.startswith("#"):
                continue
            f = s.split("\t")
            if len(f) < 2:
                continue
            k, v = f[0].strip(), f[1].strip()
            if not k or not v or k in ("原文", "行号", "段号") or v in ("保留",):
                continue
            if k not in m:          # 先命中先赢（来源按可信度排序）
                m[k] = v
                n += 1
    return m


def base_lookup(table, s):
    """基名回退匹配：处理 `X (SSI)` / `X (#3 Lower)` / `X - Redux` 之类，用 X 的权威译名拼回后缀。

    仅用于**确知是"名字+标记"**的形状；纯缩写/文件名不在此列（留着即等于保留原文）。
    """
    m = re.match(r"^(.*?)\s*\((SSI|PG2|PeG)\)\s*$", s)
    if m:
        base = m.group(1).strip()
        suf = m.group(2)
        if base in table:
            return "%s（%s）" % (table[base], suf)
    m = re.match(r"^(.*?)\s*(\(#[0-9A-Za-z ]+\))\s*$", s)
    if m:
        base, suf = m.group(1).strip(), m.group(2)
        if base in table:
            return "%s %s" % (table[base], suf)
    return None


def main():
    apply_ = "--apply" in sys.argv
    table = load_sources()
    table.update({k: v for k, v in MANUAL.items()})
    print("真源条目 %d 条（含表头 %d）" % (len(table), len(MANUAL)))

    targets = []
    for dp, _, fs in os.walk(FILL):
        for f in fs:
            if not f.endswith(".tsv") or f.startswith("_task-"):
                continue
            targets.append(os.path.join(dp, f))
    targets.sort()
    tot = hit = 0
    for p in targets:
        lines = [l.rstrip("\n") for l in open(p, encoding="utf-8") if l.strip()]
        # 列布局：TXT/RTF 表 = (段号,原文,译文) → 译名列 idx2；XLS 表 = (表,行,列,原文,译文) → idx4
        head = [l for l in lines if l.startswith("#") or l.split("\t")[0].strip() in ("行号", "段号", "工作表")]
        rows = [l for l in lines if l not in head]
        idx = 4 if any("工作表" in h for h in head) else 2
        out, n, h = [], 0, 0
        for l in rows:
            c = l.split("\t")
            if len(c) <= idx:
                out.append(l)
                continue
            n += 1
            src = c[idx - 1].strip()
            if not c[idx].strip() and src in table and src not in NEVER_AUTOFILL:
                c[idx] = base_lookup(table, src) or table[src]
                h += 1
            elif not c[idx].strip() and src not in table:
                v = base_lookup(table, src)
                if v and src.split(" (")[0].strip() not in NEVER_AUTOFILL:
                    c[idx] = v
                    h += 1
            out.append("\t".join(c))
        tot += n
        hit += h
        if apply_ and h:
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(head + out) + "\n")
        if h:
            print("  %-56s 段 %4d  命中 %4d (%.0f%%)" % (os.path.relpath(p, FILL)[:56], n, h, 100.0 * h / max(1, n)))
    print()
    print("合计：文字格 %d，词库命中 %d（%.1f%%）%s" % (tot, hit, 100.0 * hit / max(1, tot),
                                                 "" if apply_ else "  ← dry-run（加 --apply 落盘）"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
