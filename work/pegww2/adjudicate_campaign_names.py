#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""战役内「名栏 vs 说明」46 条逐条裁定表生成（**只读**，输出 TSV）。

裁定口径（用户 2026-10-19）：以该场 `.SCN` 实际引用的 `*.MAP`（战场）为仲裁主轴，
以「说明名(`_i` 名字行) / 自有 `_u.txt` 行0 / 战役前后场 / 原版英文原文」为佐证；
  改按说明名  名栏确系别的图的场景名被借来，且说明名合图或双票
  保留名栏    名栏合图（或名栏与说明互为「代号↔地名」表里关系）
  待实机      名栏/说明/`_u`/地图 互相矛盾，数据层定不了，留待实机画面裁定

产出：`pegww2/research/_战役-名栏裁定-20261019.tsv`
用法: python adjudicate_campaign_names.py
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2\SCENARIO"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
RES = os.path.join(WS, "pegww2", "research")
SRC = os.path.join(RES, "_战役-名栏与说明不符-20261019.tsv")
LED = os.path.join(RES, "_战役-场景与地图核准.tsv")
OUT = os.path.join(RES, "_战役-名栏裁定-20261019.tsv")

# 裁定：stem -> (裁定, 建议译名, 依据)
V = {
    # ---- 18 条「名栏疑借用」组 ----
    "ATM_scn13":  ("保留名栏", "", "名栏=鹅卵石行动(Operation Shingle=安齐奥登陆)，与 _u、地图 ANZIO 三证一致；说明「学生行动」属别场"),
    "G7Pzra707":  ("改按说明名", "西迪拜拉尼(Sidi Barrani)", "地图 TOBRUK=北非；名栏「萨凡纳'45」与 _u「田纳西'45」均为 '45 美本土名(借用)；说明合战场"),
    "G7Pzra711":  ("待实机", "", "名栏克里特 / 说明奥尔沙 / _u 向古斯塔夫防线 / 地图 DESSAU 四者互斥"),
    "ita02":      ("改按说明名", "埃特纳防线(Etna Line)", "地图 NSICILY=西西里，埃特纳火山在西西里；名栏「小土星(RTB#04)」属意战场景(借用)"),
    "LH_ger46med15": ("保留名栏", "", "名栏=希腊之战、说明=科林斯，代号↔地名互为表里(同战役成对出现)"),
    "r703":       ("改按说明名", "米乌斯河(Mius River) (#3)", "r7 战役为东线(德涅斯特河/敖德萨/塞瓦斯托波尔/彼列科普)；名栏「托布鲁克」系 RACE 借用"),
    "r706":       ("待实机", "", "名栏波内里车站 / 说明格罗兹尼(#6) / 地图 VLADIVOSTOK 互斥"),
    "RG_usvsruss12": ("待实机", "", "名栏「向圣洛推进」确系借用；说明维捷布斯克'46 与地图 VOLOKOL(沃洛科拉姆斯克) 不合"),
    "RM_usvsruss7": ("待实机", "", "名栏为套话「干得好，将军」/ 说明阿拉库尔 / 地图 KLIN(克林) 互斥"),
    "rtb10":      ("待实机", "", "名栏西乌克兰(#9) / 说明强渡维斯瓦河(RTB#19) / 地图 MOGILEV 互斥(编号亦不符)"),
    "s0032":      ("改按说明名", "破坏行动(Sabotage)", "名栏「坚守防线-第1部分」系 ATM_scn04(另图)借用；说明有独立名"),
    "s003":       ("改按说明名", "芬兰(Finland)", "地图 BELOMORS=白海/芬兰；战役序 破坏行动→芬兰→挪威；名栏「沃尔图诺」属意战(借用)"),
    "s004":       ("改按说明名", "挪威(Norway)", "战役序 芬兰→挪威→希腊；名栏「乌曼包围战」属东线(借用)"),
    "s0011":      ("改按说明名", "西西里(Sicily)", "地图 SICILY 与说明一致；名栏「约维克」属挪威(借用)"),
    "s0018":      ("改按说明名", "符拉迪沃斯托克(Vladivostok)", "地图 VLADIVOSTOK + 说明一致；名栏/_u「圣康坦」属西线(借用)"),
    "s0019":      ("改按说明名", "萨哈林(Sakhalin)：「恩格斯」行动", "地图 SAKHALIN + 说明 + _u 三证；名栏「日托米尔」及**地名字标**整套系 Zhytomyr 拿错"),
    "s0025":      ("待实机", "", "名栏塞维利亚 / 说明芝加哥 / _u 塔马波尔 / 地图 LONDON 互斥"),
    "s0030":      ("改按说明名", "选择 2(Choice 2)", "本场为分支选择场，同战役 s0029 名栏=「选项 1」；名栏「沃罗涅日」属借用"),
    # ---- 28 条「待判」组 ----
    "7Pzra719v":  ("待实机", "", "名栏奥廖尔突出部(#6) / 说明诺曼底(#19v) / 地图 SALERNO 互斥"),
    "ATM_scn12":  ("保留名栏", "", "名栏=向古斯塔夫防线推进，与 _u、地图 CASSINO(古斯塔夫防线) 三证一致；说明「勒热夫-维亚济马」属借用"),
    "DAK_DAK2":   ("保留名栏", "", "名栏「哈勒法亚隘口与塞卢姆之战」合图 SOLLUM；说明「闪电战！目标法国」属别场"),
    "DAK_Choice": ("保留名栏", "", "分支选择场(Choice1↔选择1)，仅译名未汉化，不属错配"),
    "DAK_SPChoice": ("保留名栏", "", "分支选择场(Choice2↔选择2)，同上"),
    "DAK_TU03":   ("改按说明名", "博讷(Bone)", "地图 BONA=博讷；名栏「斯摩棱斯克——渡过第聂伯河」属东线(借用)"),
    "G7Pzra714":  ("改按说明名", "海狮43(SeaLion43)", "地图 SOUTHENG=英格兰南部，同图=跳伞训练/朴茨茅斯-怀特岛；说明合图"),
    "G7Pzra715":  ("待实机", "", "名栏赤色威胁 / 说明基希讷乌 / _u 伦敦'44 / 地图 WINDSOR 互斥"),
    "G7Pzra716":  ("待实机", "", "名栏冬季风暴行动(#8) / 说明马耳他 / 地图 ARRACT(阿拉库尔) 互斥"),
    "GAW06":      ("保留名栏", "", "名栏/说明同指 Maginot line，仅「马奇诺/马其诺」用字不一(同源，另议译名统一)"),
    "LH_ger46med2": ("保留名栏", "", "名栏=火炬行动(代号)、说明=阿尔及尔(目标地)，互为表里"),
    "LH_ger46med4": ("保留名栏", "", "卡普里行动＝梅德宁反攻，代号↔地名互为表里"),
    "LH_ger46med5": ("保留名栏", "", "向日葵行动↔的黎波里，代号↔地名互为表里"),
    "LH_ger46med8": ("保留名栏", "", "十字军行动↔西迪拜拉尼，同属北非，互为表里"),
    "LH_ger46med13": ("保留名栏", "", "加里波利↔赫勒斯(滩头)，互为表里"),
    "LH_ger46med14": ("保留名栏", "", "加里波利第2部分↔阿里角(滩头)，互为表里"),
    "lah_it_02":  ("保留名栏", "", "名栏+_u 双票(强渡瓦尔塔河)；说明「白色方案」为战役总名"),
    "lah_it_08":  ("保留名栏", "", "名栏+_u 双票(乌曼包围战)"),
    "lah_it_13":  ("保留名栏", "", "名栏+_u+地图 PROK(普罗霍夫卡) 三证"),
    "lah_it_14":  ("保留名栏", "", "名栏+_u+地图 ZHITOMIR 三证"),
    "RM_usvsruss3": ("待实机", "", "名栏维堡 / 说明马德里攻势 / _u 圣康坦 / 地图 CIECHANO 互斥"),
    "RM_usvsruss8": ("待实机", "", "名栏马耳他 / 说明施图登特 / 地图 NORDWIND(北风行动) 互斥"),
    "RM_usvsruss9": ("保留名栏", "", "名栏+_u+地图 PROKHORV 三证(普罗霍夫卡车站)"),
    "rtb07":      ("改按说明名", "奥廖尔(Orel) (RTB#07)", "说明自带 RTB#07 编号=本场；名栏「卡拉奇(#1)」系 rtb01 借用"),
    "rtb24":      ("待实机", "", "名栏卡拉奇(#1) / 说明萨莱诺-重返欧洲 / 地图 DIEPPE 互斥"),
    "s0010":      ("保留名栏", "", "名栏「杰拉」合图 GELA；说明「卡昂——古德伍德」属借用"),
    "s0021":      ("改按说明名", "东京(Tokyo)", "说明+_u 双票(东京)；名栏「柏林之战(#7d10)」属外来"),
    "s0022":      ("改按说明名", "阿留申群岛(Aleutian Islands)", "地图 ATTU2=阿图岛(阿留申群岛)；名栏「刻赤(#4 下部)」属外来"),
}


def idx(root):
    return {n.lower(): n for n in os.listdir(root) if os.path.isfile(os.path.join(root, n))}


G, B = idx(GAME), idx(BK)


def rd(i, root, name, k=0, enc="gbk"):
    real = i.get(name.lower())
    if not real:
        return ""
    try:
        ls = io.open(os.path.join(root, real), encoding=enc, errors="replace").read().splitlines()
    except Exception:
        return ""
    return ls[k].strip() if len(ls) > k else ""


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    seq = {}
    for l in io.open(LED, encoding="utf-8"):
        if not l.strip() or l.startswith("#"):
            continue
        c = l.rstrip("\n").split("\t")
        if c[0] == "战役":
            continue
        seq[(c[1], c[3])] = c[12]

    rows, miss = [], []
    for l in io.open(SRC, encoding="utf-8"):
        if not l.strip() or l.startswith("#"):
            continue
        c = l.rstrip("\n").split("\t")
        if c[0] == "战役":
            continue
        if c[9] not in ("名栏疑借用·改按说明名", "待判"):
            continue
        camp, cf, idxn, stem, M, I, MP = c[0], c[1], c[2], c[3], c[4], c[5], c[7]
        v = V.get(stem)
        if not v:
            miss.append(stem)
            v = ("?", "", "")
        rows.append([
            camp, cf, idxn, stem, M, I, MP, seq.get((cf, stem), ""),
            rd(B, BK, stem + "_m.txt", 0, "cp1252"), rd(B, BK, stem + "_i.txt", 0, "cp1252"),
            rd(B, BK, stem + "_u.txt", 0, "cp1252"),
            v[0], v[1], v[2],
        ])

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 战役内「名栏(_m.txt 行0) vs 说明(_i.txt 名字行)」46 条逐条裁定（只读产出）\n")
        f.write("# 仲裁主轴=该场 .SCN 实际引用的 *.MAP；佐证=_i 名 / _u.txt 行0 / 战役前后场 / 原版英文\n")
        f.write("战役\t战役文件\t场次\t场景\t名栏\t说明名\t地图\t战役序列\t英文名栏\t英文说明\t英文_u\t裁定\t建议译名\t依据\n")
        for r in rows:
            f.write("\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in r) + "\n")

    from collections import Counter
    c = Counter(r[11] for r in rows)
    print("裁定 %d 条：%s" % (len(rows), "  ".join("%s=%d" % kv for kv in c.most_common())))
    if miss:
        print("!! 未覆盖的 stem:", miss)
    for r in rows:
        if r[11] == "改按说明名":
            print("  改  %-15s %s → %s" % (r[3], r[4][:26], r[12][:30]))
    print("→ %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
