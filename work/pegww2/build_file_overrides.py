#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 per-file 覆盖表：把「名栏被填成简报」的 `_m.txt` 第0行，按**文件+行号**改成该场景自己的名。

与旧做法的区别（关键）：
  · 旧：改真源里那个字符串的译文 ⇒ 同一串在别的文件里是正文简报时被连带改错（误伤 36 键）
  · 新：只改「这一个文件的这一行」⇒ 别的文件用同一串照样显示简报 ✓

产出：research/_scn-file-overrides.tsv（子目录 / 文件 / 行号 / 期望原文 / 译文）
"""
import os
import re

WS = r"D:\DSH\军事游戏汉化"
BK = os.path.join(WS, "pegww2", "testbed", "backup")
GAME = r"D:\Program Files\PeG-WW2"
OUT = os.path.join(WS, "pegww2", "research", "_scn-file-overrides.tsv")
USR = os.path.join(GAME, "USERSCEN")
GAME_SCN = os.path.join(GAME, "SCENARIO")

MAPNAME_ZH = {
    "BOBCARENTAN.MAP": "卡朗唐", "MAKNASSY.MAP": "马肯纳西", "AMIENS.MAP": "亚眠",
    "PROKHORV.MAP": "普罗霍罗夫卡", "DON.MAP": "顿河", "SEVASTOPOL.MAP": "塞瓦斯托波尔",
    "PEENEMUN.MAP": "佩内明德", "POLAND.MAP": "波兰", "DESSAU.MAP": "德绍",
    "MALTA.MAP": "马耳他", "SUEZ.MAP": "苏伊士", "WINDSOR.MAP": "温莎",
    "VIIPURI.MAP": "维堡", "CATANIA.MAP": "卡塔尼亚", "CASSINO.MAP": "卡西诺",
    "KLIN.MAP": "克林", "SOUMUSSA.MAP": "苏奥穆萨尔米", "OAKRIDGE.MAP": "橡树岭",
    "GARAMLAH.MAP": "加拉姆拉", "BERLIN.MAP": "柏林", "ENGLAND.MAP": "英格兰",
    "TOBRUK.MAP": "图卜鲁格", "RATOBRUK.MAP": "拉斯图卜鲁格", "RUHR.MAP": "鲁尔",
    "GOTHIC.MAP": "哥特防线", "GAZALA.MAP": "加扎拉", "PORTSAID.MAP": "塞得港",
    "KANEV.MAP": "卡涅夫", "PONYRI.MAP": "波内里", "DRKITIL.MAP": "基蒂尔",
}
STEM_ZH = {"DUNKIRK": "敦刻尔克", "F": "", "O": "", "P": "", "WR": ""}

OPENERS = re.compile(r"(?i)^(herr\b|comrade\b|message from|congratulations|kongru|superb|excellent|good work|good job|well\b|you (have|managed|know)|it is your|if your|in this directory|of course|all right|these poles)")
ABBR = re.compile(r"\b(St|Mr|Mrs|Dr|No|Pt|Gen|Col|Maj|Capt|Lt|Sgt|Cpl|Pvt|Co|Div|Rgt|Bn|Sec|WW|vs|etc)\.\s")
DATE = re.compile(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(st|nd|rd|th)?,?\s*\d{4}\b|\b\d{1,2}/\d{1,2}/\d{4}\b", re.I)


def is_briefing(s):
    core = ABBR.sub(r"\1 ", DATE.sub(" ", s))
    if OPENERS.match(s):
        return True
    if core.count(", ") >= 1 and len(s) > 30:
        return True
    if len(re.findall(r"[.!?](\s|$)", core)) >= 2 and len(s) > 25:
        return True
    return len(s) > 60


def fld(b, o, n=20):
    return b[o:o + n].split(b"\x00")[0].decode("latin-1")


def main():
    # ⭐ 必须有**中文**：候选名是 MOD 的英文串 ⇒ 先查真源里它的既有译文，再退回地图名映射
    mp = {}
    MAPF = os.path.join(WS, "pegww2", "research", "ww2-scn-map.tsv")
    for i, l in enumerate(open(MAPF, encoding="utf-8-sig")):
        if i < 4 or not l.strip():
            continue
        f2 = l.rstrip("\n").split("\t")
        if len(f2) >= 3 and f2[1].strip():
            mp[f2[0]] = f2[1]
    rows = []
    skipped = []
    for sub in ("SCENARIO", "USERSCEN"):
        d = os.path.join(BK, sub)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith("_m.txt"):
                continue
            st = fn[:-6]
            line0 = re.split(r"\r\n|\r|\n", open(os.path.join(d, fn), "rb").read().decode("latin-1"))[0].strip()
            if not line0 or not is_briefing(line0):
                continue
            zh = ""
            for suf in (".TXT", ".txt", "_i.txt", "_u.txt"):
                q = os.path.join(d, st + suf)
                if os.path.isfile(q):
                    first = re.split(r"\r\n|\r|\n", open(q, "rb").read().decode("latin-1"))[0].strip()
                    if first and not is_briefing(first) and first.lower() != "dummy":
                        zh = mp.get(first, "")
                        break
            if not zh:
                # ⭐ 正确来源：`@11329` 指向的说明文件**第 0 行就是场景标题**
                #    （PeG 实证 P3：描述框第 0 行被当标题吞掉 ⇒ 它就是标题）
                #    ⚠️ 曾用「地图名」兜底 ⇒ 是**猜测**（同一地图被多场景共用 ⇒ 出现多个同名场景）⇒ 已废止
                for cs in (st + ".scn", st.lower() + ".scn", st + ".SCN"):
                    q = os.path.join(GAME, sub, cs)
                    if not os.path.isfile(q):
                        continue
                    b = open(q, "rb").read()
                    if len(b) <= 11350:
                        break
                    intro = fld(b, 11329)
                    flag = b[11349]
                    for dd, ff in ((USR, ".ply"), (GAME_SCN, ".TXT")) if flag else ((GAME_SCN, ".TXT"), (USR, ".ply")):
                        for nm in (intro + ff, intro + ff.lower()):
                            qq = os.path.join(dd, nm)
                            if os.path.isfile(qq):
                                t2 = re.split(r"\r\n|\r|\n", open(qq, "rb").read().decode("latin-1"))
                                if t2:
                                    first = t2[0].strip()
                                    if first and not is_briefing(first):
                                        zh = mp.get(first, "")
                                break
                        if zh:
                            break
                    break
            if not zh:
                zh = STEM_ZH.get(st.upper(), "")
            if zh:
                rows.append((sub, fn, 0, line0, zh))
            else:
                skipped.append(st)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("# per-file 覆盖（名栏修复）：只改这一个文件的这一行，不影响别处同串正文\n")
        f.write("子目录\t文件\t行号\t期望原文\t译文\n")
        for r in rows:
            f.write("\t".join(str(x).replace("\t", " ") for x in r) + "\n")
    print(f"per-file 覆盖 {len(rows)} 条 → {os.path.relpath(OUT, WS)}")
    print(f"  未定名（跳过）{len(skipped)}: {skipped[:12]}")
    for r in rows[:8]:
        print(f"    {r[1]:18s} ⇒ {r[4]}")


if __name__ == "__main__":
    main()
