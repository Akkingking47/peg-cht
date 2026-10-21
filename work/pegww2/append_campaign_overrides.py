#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把本轮「战役内名栏核准」的 per-file 覆盖写入 `_scn-file-overrides.tsv`（幂等追加）。

两类：
  ① 15 条 行0 改名（依 `_战役-名栏裁定-20261019.tsv`）
  ② s0019 行1-15 地名字标 → 换为同图同域场景 `usvsussr9_m.txt` 的萨哈林地名（行数一致 16）

行0 的「期望原文」从**原文备份**取（cp1252），译文为我方定名；幂等：同 (文件,行号) 已存在则跳过。
用法: python append_campaign_overrides.py [--apply]
"""
import io
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
G = r"D:\Program Files\PeG-WW2\SCENARIO"
OVF = os.path.join(WS, "pegww2", "research", "_scn-file-overrides.tsv")

NAMES = {
    "ita02": "埃特纳防线(Etna Line)",
    "r703": "米乌斯河(Mius River) (#3)",
    "rtb07": "奥廖尔(Orel) (RTB#07)",
    "DAK_TU03": "博讷(Bone)",
    "G7Pzra707": "西迪拜拉尼(Sidi Barrani)",
    "G7Pzra714": "海狮43(SeaLion43)",
    "s0011": "西西里(Sicily)",
    "s0018": "符拉迪沃斯托克(Vladivostok)",
    "s0019": "萨哈林(Sakhalin)：「恩格斯」行动",
    "s0021": "东京(Tokyo)",
    "s0022": "阿留申群岛(Aleutian Islands)",
    "s003": "芬兰(Finland)",
    "s004": "挪威(Norway)",
    "s0032": "破坏行动(Sabotage)",
    "s0030": "选择 2(Choice 2)",
}
NOTE = {
    "ita02": "图 NSICILY=西西里，埃特纳在岛上；名栏「小土星(RTB#04)」属意战",
    "r703": "r7=东线战役序列；名栏「托布鲁克」系 RACE 借用",
    "rtb07": "说明自带 RTB#07；名栏「卡拉奇(#1)」系 rtb01 借用",
    "DAK_TU03": "图 BONA=博讷；名栏「斯摩棱斯克」属东线",
    "G7Pzra707": "图 TOBRUK=北非；名栏/`_u` 是 '45 美本土名(借用)",
    "G7Pzra714": "图 SOUTHENG=英格兰南部(同图=朴茨茅斯-怀特岛)",
    "s0011": "图 SICILY；名栏「约维克」属挪威(借用)",
    "s0018": "图 VLADIVOSTOK + 说明；名栏/`_u`「圣康坦」属西线",
    "s0019": "图 SAKHALIN + 说明 + `_u`；名栏及行1+地名字标整套系 Zhytomyr 拿错",
    "s0021": "说明 + `_u` 双票；名栏「柏林之战(#7d10)」属外来",
    "s0022": "图 ATTU2=阿图岛(阿留申)；名栏「刻赤(#4 下部)」属外来",
    "s003": "图 BELOMORS=白海/芬兰；战役序 破坏行动→芬兰→挪威",
    "s004": "战役序 芬兰→挪威→希腊；名栏「乌曼包围战」属东线",
    "s0032": "名栏「坚守防线-第1部分」系 ATM_scn04(另图) 借用",
    "s0030": "分支选择场；同战役 s0029=「选项 1」",
}


def l0(root, name, enc, k):
    p = os.path.join(root, name)
    if not os.path.isfile(p):
        return None
    ls = io.open(p, encoding=enc, errors="replace").read().splitlines()
    return ls[k].strip() if len(ls) > k else None


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    apply_ = "--apply" in sys.argv
    have = set()
    txt = io.open(OVF, encoding="utf-8-sig").read().splitlines()
    for j, l in enumerate(txt):
        if j < 2 or not l.strip() or l.startswith("#"):
            continue
        c = l.split("\t")
        if len(c) >= 3 and c[2].strip().isdigit():
            have.add((c[0].strip(), c[1].strip(), int(c[2])))

    new = []
    for st, zh in NAMES.items():
        en = l0(BK, st + "_m.txt", "cp1252", 0)
        if en is None:
            print("!! 备份缺 %s_m.txt" % st)
            continue
        if ("SCENARIO", st + "_m.txt", 0) in have:
            print("  已存在，跳过 %s" % st)
            continue
        new.append("SCENARIO\t%s_m.txt\t0\t%s\t%s\t证据：%s" % (st, en, zh, NOTE[st]))

    # s0019 行1-15 地名字标 ← usvsussr9 同图同域
    for i in range(1, 16):
        en = l0(BK, "s0019_m.txt", "cp1252", i)
        zh = l0(G, "usvsussr9_m.txt", "gbk", i)
        if en is None or zh is None:
            print("!! s0019 行%d 取原文/译文失败" % i)
            continue
        if ("SCENARIO", "s0019_m.txt", i) in have:
            print("  已存在，跳过 s0019 行%d" % i)
            continue
        new.append("SCENARIO\ts0019_m.txt\t%d\t%s\t%s\t地名字标：换为同图同域「侵萨哈林」地名" % (i, en, zh))

    print("待追加 %d 行" % len(new))
    for x in new:
        print("  " + x[:100])
    if apply_ and new:
        with io.open(OVF, "a", encoding="utf-8", newline="\n") as f:
            f.write("\n# —— 第 5 批（2026-10-19 · 战役内名栏核准：地图为仲裁主轴，说明名/_u/前后场/原版英文为佐证）——\n")
            for x in new:
                f.write(x + "\n")
        print("已追加到 %s" % OVF)
    elif new:
        print("(dry-run，未追加；加 --apply 落盘)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
