#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""名栏修复执行：66 个「名栏=简报段落」的场景 ⇒ 把真源里那一段的译文改写为**场景名**。

定名依据（全部来自 MOD 自身，不发明）：
  ① 41 条：MOD 已在 `<stem>.TXT` / `<stem>_u.txt` 第 0 行写了场景名 ⇒ 直接取该串（其译文真源里已有）
  ② 20 条：MOD 未写名 ⇒ 用**该场景所用地图名**（与本作既有惯例一致：VIIPURI⇒维堡、PROK⇒普罗霍罗夫卡）
  ③ 其余（DUNKIRK 等）：从文件名取
产出：
  research/_scn-fill-namefix.tsv  段落原文 → 场景名（供 apply_value_fill 并入真源）
  research/_m-名栏错位段落归档.tsv  66 段原文+译文全文**归档**（内容不丢，只是不再错位显示）
"""
import os
import re

WS = r"D:\DSH\军事游戏汉化"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
MAP = os.path.join(WS, "pegww2", "research", "ww2-scn-map.tsv")
FILL = os.path.join(WS, "pegww2", "research", "_scn-fill-namefix.tsv")
ARC = os.path.join(WS, "pegww2", "research", "_m-名栏错位段落归档.tsv")

# ② MOD 未写名 ⇒ 用地图名（中文按通行译名；括号内为该地图名出现在真源里的既有译法，若有一致则优先）
MAPNAME_ZH = {
    "BOBCARENTAN.MAP": "卡朗唐", "MAKNASSY.MAP": "马肯纳西", "AMIENS.MAP": "亚眠",
    "PROKHORV.MAP": "普罗霍罗夫卡", "DON.MAP": "顿河", "SEVASTOPOL.MAP": "塞瓦斯托波尔",
    "PEENEMUN.MAP": "佩内明德", "POLAND.MAP": "波兰", "DESSAU.MAP": "德绍",
    "MALTA.MAP": "马耳他", "SUEZ.MAP": "苏伊士", "WINDSOR.MAP": "温莎",
    "VIIPURI.MAP": "维堡", "CATANIA.MAP": "卡塔尼亚", "CASSINO.MAP": "卡西诺",
    "KLIN.MAP": "克林", "SOUMUSSA.MAP": "苏奥穆萨尔米", "PROKHOROVKA.MAP": "普罗霍罗夫卡",
    "PROKHORV": "普罗霍罗夫卡",
}
# ③ 从文件名取
STEM_ZH = {"DUNKIRK": "敦刻尔克"}


OPENERS = re.compile(r"(?i)^(herr\b|comrade\b|message from|congratulations|kongru|superb|excellent|good work|good job|well\b|you (have|managed|know)|it is your|if your|in this directory|of course|all right|these poles)")
ABBR = re.compile(r"\b(St|Mr|Mrs|Dr|No|Pt|Gen|Col|Maj|Capt|Lt|Sgt|Cpl|Pvt|Co|Div|Rgt|Bn|Sec|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec|WW|vs|etc)\.\s")


def looks_like_briefing(s):
    """⭐ v2 判据：**按内容**判「这一行是场景名还是简报」
    （v1 只用「长度 > 120」⇒ 漏掉英文较短的简报，如 saturn-R / s001 / selow / zs_wapo）"""
    core = ABBR.sub(r"\1 ", s)
    if OPENERS.match(s):
        return "简报开头词"
    if core.count(", ") >= 1 and len(s) > 30:
        return "含逗号长句"
    if len(re.findall(r"[.!?](\s|$)", core)) >= 2 and len(s) > 25:
        return "多句"
    if len(s) > 60:
        return "长(>60)"
    return ""


def fld(b, o, n=20):
    return b[o:o + n].split(b"\x00")[0].decode("latin-1")


def main():
    mp = {}
    with open(MAP, encoding="utf-8-sig") as f:
        for i, l in enumerate(f):
            if i < 4 or not l.strip():
                continue
            f2 = l.rstrip("\n").split("\t")
            if len(f2) >= 3 and f2[1].strip():
                mp[f2[0]] = f2[1]
    rows, no_name = [], []
    for fn in sorted(os.listdir(BK)):
        if not fn.lower().endswith("_m.txt"):
            continue
        st = fn[:-6]
        para = re.split(r"\r\n|\r|\n", open(os.path.join(BK, fn), "rb").read().decode("latin-1"))[0].strip()
        if not para or not looks_like_briefing(para):
            continue
        name, why = "", ""
        for suf in (".TXT", ".txt", "_i.txt", "_u.txt"):
            p = os.path.join(BK, st + suf)
            if os.path.isfile(p):
                first = re.split(r"\r\n|\r|\n", open(p, "rb").read().decode("latin-1"))[0].strip()
                if first and len(first) <= 120 and first.lower() != "dummy":
                    name, why = mp.get(first, ""), f"①MOD自写名 {first!r}"
                    break
        if not name:
            for cs in (st + ".scn", st.lower() + ".scn", st + ".SCN"):
                p = os.path.join(WS and r"D:\Program Files\PeG-WW2\SCENARIO", cs)
                if os.path.isfile(p):
                    b = open(p, "rb").read()
                    if len(b) > 11230:
                        mn = fld(b, 11210)
                        zh = MAPNAME_ZH.get(mn.upper(), "")
                        if zh:
                            name, why = zh, f"②地图名 {mn}"
                    break
        if not name:
            name, why = STEM_ZH.get(st.upper(), ""), "③文件名"
        if name:
            rows.append((st, para, name, why))
        else:
            no_name.append((st, para[:60]))
    with open(FILL, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 名栏修复：把「简报段落」的译文改写为**场景名**（MOD 数据问题修复）\n")
        f.write("原文\t译文\t说明\n")
        for st, para, name, why in rows:
            f.write(f"{para}\t{name}\t{why}\n")
    with open(ARC, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 名栏错位段落归档（原文 / 原译文）——内容不丢，只是不再在列表名栏错位显示\n")
        f.write("场景\t段落原文\t段落译文\n")
        for st, para, name, why in rows:
            f.write(f"{st}\t{para}\t{mp.get(para, '')}\n")
        for st, para in no_name:
            f.write(f"{st}\t(未定名，保持原样)\t\n")
    print(f"可修复 {len(rows)} 条 · 仍未定名 {len(no_name)} 条")
    for st, para, name, why in rows:
        print(f"  {st:16s} ⇒ {name:12s} （{why}）")
    print()
    print("仍未定名（保持原样，将如实报告）:")
    for st, para in no_name:
        print(f"  {st}: {para}")


if __name__ == "__main__":
    main()
