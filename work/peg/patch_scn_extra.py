# -*- coding: utf-8 -*-
"""补全「场景名 / 场景标题 / 日期行 / N 人」等整行译文，追加到 scenario-long-zh.tsv。
这些行此前只被子串替换（如 `Siege of Sarajevo` → `Siege of 萨拉热窝`），故半中半英。
键 = 备份文件里的原始整行（精确匹配）。"""
import os

ROOT = r"D:\DSH\军事游戏汉化"
OUT = os.path.join(ROOT, r"peg\research\scenario-long-zh.tsv")

PAIRS = [
    # ---- Scenario 地图图名 / 场景标题 ----
    ("Map of Almaty.", "阿拉木图地图"),
    ("Map of Ekaterinburg.", "叶卡捷琳堡地图"),
    ("Map of Irkutsk.", "伊尔库茨克地图"),
    ("Map of Penang", "槟城地图"),
    ("Map of Pusan.", "釜山地图"),
    ("Map of Sakhalin", "萨哈林地图"),
    ("Map of Taejon", "大田地图"),
    ("Map of Ulan Ude", "乌兰乌德地图"),
    ("Map of Vladivostok.", "符拉迪沃斯托克地图"),
    ("Repulse at Astrakhan", "阿斯特拉罕击退"),
    ("Clash at Bangkok", "曼谷冲突"),
    ("Charge at Chir", "奇尔冲锋"),
    ("Hordes at Ekaterinburg", "叶卡捷琳堡蜂拥"),
    ("Fury in Hanoi", "河内之怒"),
    ("Pocketing Irkutsk", "合围伊尔库茨克"),
    ("Rally at Kazan", "喀山集结"),
    ("Crazy for Kazan", "喀山狂想"),
    ("Crashing Khabarovsk", "强袭哈巴罗夫斯克"),
    ("Strike on Kontum", "昆嵩突击"),
    ("Redemption for Pusan", "釜山雪耻"),
    ("Payback at Penang", "槟城回击"),
    ("Breakout at Seoul", "首尔突围"),
    ("Sacking Sakhalin", "洗劫萨哈林"),
    ("Siege of Singapore", "围攻新加坡"),
    ("Trading Blows in Taejon", "大田交手"),
    ("Defiance at Ulan Ude", "乌兰乌德抗命"),
    ("The Road from Vladivostok", "从符拉迪沃斯托克出发之路"),
    ("Advance on Vladivostok", "向符拉迪沃斯托克推进"),
    ("Havoc at Almaty", "阿拉木图鏖战"),
    ("Siege of Sarajevo (2 Players)", "围攻萨拉热窝（2 人）"),
    ("Return to Stalingrad 2.7", "重返斯大林格勒 2.7"),
    ("KazanRebel", "喀山叛军"),
    ("Trang Bang River", "庄旁河"),
    # ---- 战役小标题 ----
    ("Eastern Mini-Campaign (12 Scenarios)", "东方小型战役（12 个剧本）"),
    ("Eastern Mini-Campaign (6 Scenarios)", "东方小型战役（6 个剧本）"),
    ("Western Mini-Campaign (11 Scenarios)", "西方小型战役（11 个剧本）"),
    ("Western Mini-Campaign (6 Scenarios)", "西方小型战役（6 个剧本）"),
    # ---- 「国名, 地名」行 ----
    ("Chir, Russia", "奇尔，俄罗斯"),
    ("Khabarovsk, Russia", "哈巴罗夫斯克，俄罗斯"),
    ("Irkutsk, Siberia, Russia", "伊尔库茨克，西伯利亚，俄罗斯"),
    ("Ulan Ude, Siberia, Russia", "乌兰乌德，西伯利亚，俄罗斯"),
    ("Ulan Ude, Russia", "乌兰乌德，俄罗斯"),
    ("Penang, Malayasia", "槟城，马来西亚"),
    # ---- 带日期的场景标题 ----
    ("Operation Viper - June 18th, 2012", "蝰蛇行动 - 2012 年 6 月 18 日"),
    ("Operation 'Sawad' - November 11th, 2012", "「萨瓦德」行动 - 2012 年 11 月 11 日"),
    ("Ia Drang - April 14th, 2015", "德浪 - 2015 年 4 月 14 日"),
    ("Asian Clash - June 18th, 2015", "亚洲冲突 - 2015 年 6 月 18 日"),
    ("Tet Offensive - January 30th, 2016", "春节攻势 - 2016 年 1 月 30 日"),
    ("Laos Counteroffensive - February 17th, 2016", "老挝反攻 - 2016 年 2 月 17 日"),
    ("Attack of the Plei Me Camp - March 19th, 2015", "波来美营地之战 - 2015 年 3 月 19 日"),
    ("Attack on Khe Sanh - August 15th, 2015", "溪山攻防战 - 2015 年 8 月 15 日"),
    ("Crossing Pakistani Border - July 20th, 2012", "越巴基斯坦边境 - 2012 年 7 月 20 日"),
    ("Escape from Vung Tau - December 29th, 2014", "逃离头顿 - 2014 年 12 月 29 日"),
    ("Homeland Attack in Punjab - May 14th, 2012", "旁遮普本土遭袭 - 2012 年 5 月 14 日"),
    ("Military Region IV Crisis - May 4th, 2015", "第四军区危机 - 2015 年 5 月 4 日"),
    ("Operation 'High Jump' - August 10th, 2012", "「高跳」行动 - 2012 年 8 月 10 日"),
    ("Raid at Bingh Gia - December 28th, 2014", "平嘉突袭 - 2014 年 12 月 28 日"),
    ("Riots in Bangladesh - April 7th, 2012", "孟加拉国骚乱 - 2012 年 4 月 7 日"),
    ("Strike on Kontum - July 3rd, 2015", "昆嵩突击 - 2015 年 7 月 3 日"),
    ("The Rebels' Nest - July 11th, 2016", "叛军之巢 - 2016 年 7 月 11 日"),
    ("Liberation of Hainoi - June 6th, 2016", "解放河内 - 2016 年 6 月 6 日"),
    ("Liberation of Ho Chi Minh - April 24th, 2016", "解放胡志明市 - 2016 年 4 月 24 日"),
    ("New Year's Eve, 2000: Korea Revisited", "2000 年除夕：再临朝鲜"),
    # ---- N 人（推荐多人）—— 去掉丑陋的双括号 ----
    ("2 Player (Multiplayer recommended)", "2 人（推荐多人对战）"),
    ("2 Player (Mulitplayer recommended)", "2 人（推荐多人对战）"),
    ("3 Player (Multiplayer recommended)", "3 人（推荐多人对战）"),
    ("4 Player (Multiplayer recommended)", "4 人（推荐多人对战）"),
    ("4 Player (Mulitplayer recommended)", "4 人（推荐多人对战）"),
    # ---- ns4PlayNotes 里漏掉的英文行 ----
    ("Missed a BV by one turn.", "差一个回合错失大胜。"),
    ("Now it's on to Singapore.", "接下来就轮到新加坡了。"),
    ("Europe finally was resurgent blitzing through in the most convincing show of strength thus far, with a BV attained in 7 out of 16 or so turns.  I divided my forces with two thirds in the north and one third deployed with some Russian auxiliaries in the south.  In spite of forgetting to move any of my southern units on the second turn, the northern wing sliced through the expected bottlenecks of Ekaterinaberg and the famed WWII tank factory at Uralmash next to it.  Lost my German AVLB and another (sigh) recon.  Other than that, the biggest problem we had was running out of ammunition.  My units suffered very few casualties.  The 100% air superiority helped as well.",
     "欧洲人终于重振旗鼓，以迄今最令人信服的强势姿态一路闪击，16 个回合里用约 7 个回合拿下大胜。我把部队三分之二放在北面，三分之一与若干俄罗斯辅助部队一起部署在南面。尽管第二回合忘了调动南面的部队，北翼还是像切黄油一样穿过了叶卡捷琳堡的预期的瓶颈地带，以及旁边那座二战著名的乌拉尔机械厂坦克厂。折损了我的德国 AVLB 架桥车，还有一支侦察单位（唉）。除此之外，最大的问题是弹药告罄。我的部队伤亡极少，百分之百的制空权也帮了大忙。"),
    ("I ignored all of the Supply Hexes, even the airfields, except for the ones on Singapore Island.  That enabled me to rapidly capture all of my primary objectvies.  I thought the AVLB would come in handy, but it didn't.  BV in 7 out of 16 turns.",
     "我把所有补给格都放着不管，连机场也不例外，只占了新加坡岛上的那几个。这让我得以迅速拿下全部主要目标。本以为 AVLB 架桥车能派上用场，结果没有。16 个回合里用 7 个回合拿下大胜。"),
    ("Turn 4 saw me capture Bangkok and then a few moments later lose one of my air missions all together when it was ambushed by three ADs, all six or seven hexes away, when I was bravely trying to finish off a five strength Chinese tank.",
     "第 4 回合我拿下了曼谷，可没过多久，就有一次空中任务在英勇地试图收掉一辆只剩五点兵力的中国坦克时，被六七个格子外的三个防空单位伏击、全军覆没。"),
    ("But it was all over on T7.  BV in 7 of 16.", "但到第 7 回合一切就结束了。16 个回合里用 7 个回合拿下大胜。"),
    ("Upgraded the 155 Mk 3 to a GCT, for better firepower and better protection.", "把 155 Mk 3 升级成了 GCT，火力更猛、防护更好。"),
]


def main():
    assert len(set(k for k, _ in PAIRS)) == len(PAIRS), "键有重复"
    with open(OUT, "a", encoding="utf-8", newline="\n") as f:
        for k, v in PAIRS:
            assert "\t" not in k and "\t" not in v
            assert "\n" not in k and "\n" not in v
            f.write(k + "\t" + v + "\n")
    print(f"追加 {len(PAIRS)} 条 → {OUT}")


if __name__ == "__main__":
    main()
