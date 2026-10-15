# -*- coding: utf-8 -*-
"""补写「缺失的场景描述文件」<stem>.txt（第 26 轮）
================================================================
背景：
  `.SCN` 偏移 11329（20 字节）＝「场景描述/简报文件名」。**原生 SSI 场景**该字段
  都带扩展名（`almaty3.txt`），文件也都存在；而 **14 个附加包场景**该字段**不带扩展名**：
    - `Scenario\\nspegu{01,10,13,16,19,25,27}`（Sengupta 朝鲜战役）
    - `Userscen\\{Crimson, Demise of Osma, Eome2, Land Reclamation, RetStal27, Revolution, Sarajevo}`
  这些场景**只有 `.ply`**，缺少引擎要的 `<名>.txt` ⇒ 开始游戏前**没有简报**。

  注：`.ply`(501B) 供「場景選擇」界面的描述框；`.txt` 供**开局简报**。两者是不同展示位。

做法：
  按原生场景（`Almaty3.TXT`）的格式补写：
      场景名
      <空行>
      描述
      <空行>
      N 回合(N Turns)
  ⚠️ 只**新增**文件；`.SCN` 一律不改。
"""
import os
import struct
import sys

ROOT = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG"
OUTDIR = os.path.join(ROOT, r"peg\testbed\scn-zh")

# stem -> (子目录, 场景名, 描述正文, 回合数)
ENTRIES = [
    # ---- Scenario\nspegu* ----
    ("Scenario", "nspegu01", "保卫首尔",
     "中国(China)与朝鲜(North Korea)军队看来即将突袭首尔(Seoul)。不惜一切代价阻止他们。", 12),
    ("Scenario", "nspegu10", "退回大田",
     "中华人民共和国(People's Republic of China)已向朝鲜(North Korea)承诺增援，以发动新一轮攻势。"
     "你必须夺取大田(Taejon)、控制北上鸟致院(Choch'iwan)的公路，并肃清半岛西岸北上至洪城(Hongsong)的地区。"
     "别让我失望，指挥官。到目前为止，尽管你已尽力，这场战争打得实在糟糕。", 14),
    ("Scenario", "nspegu13", "釜山最后一人",
     "自我们宣战以来，已过去漫长的三个月。其间我们遭遇了诸多灾难，包括首尔(Seoul)和大田(Taejon)。"
     "现在你必须守住釜山(Pusan)，就像几十年前海军陆战队那样。如果你能救下釜山，我们或许还能从日本(Japan)运来增援。"
     "你要从釜山(Pusan)港出击，夺取马山(Masan)、蔚山(Ulsan)和密阳(Miryang)，作为解放韩国首都首尔(Seoul)的垫脚石。"
     "韩国军队的残部将在那里提供协助。祝你好运。", 14),
    ("Scenario", "nspegu16", "夺回大田",
     "中华人民共和国(People's Republic of China)已向朝鲜(North Korea)承诺增援，以发动新一轮攻势。"
     "我们对釜山(Pusan)港的控制太过脆弱，无法采取守势；必须在中国大军压来之前冲出这个死角。"
     "你必须夺取大田(Taejon)、控制北上鸟致院(Choch'iwan)的公路，并肃清半岛西岸北上至洪城(Hongsong)的地区。", 14),
    ("Scenario", "nspegu19", "盟军进军首尔",
     "中国(China)与朝鲜(North Korea)军队似乎已在首尔(Seoul)站稳脚跟，但夺回全城就看你的了。"
     "别让我失望，指挥官！", 12),
    ("Scenario", "nspegu25", "强攻伏尔加格勒",
     "美国(America)调动兵力，赶在这个备受打击的国家彻底崩溃之前支援其俄罗斯(Russia)盟友。"
     "他们发动攻势，以强攻伏尔加格勒(Volgograd)把中华人民共和国(People's Republic of China)逐出乌拉尔(Urals)。", 6),
    ("Scenario", "nspegu27", "再攻伏尔加格勒！",
     "美国(America)调动兵力，赶在这个备受打击的国家彻底崩溃之前支援其俄罗斯(Russia)盟友。"
     "他们发动攻势，以强攻伏尔加格勒(Volgograd)把中华人民共和国(People's Republic of China)逐出乌拉尔(Urals)。", 6),
    # ---- Userscen\* ----
    ("Userscen", "Crimson", "赤色风暴",
     "俄罗斯(Russia)叛军已夺取并控制了阿尔乔姆(Artem)城郊的洲际弹道导弹(ICBM)基地，还控制了该城。"
     "忠于政府的部队已将叛军包围，但要把他们彻底清除并不容易。你手上的兵力有限，却训练有素，"
     "还有不错的空中支援和三个精锐空降营可供调配。", 8),
    ("Userscen", "Demise of Osma", "奥萨马·本·拉登的覆灭",
     "塔利班(Taliban)部队已退守坎大哈(Kandahar)老巢。联军受命发动最后攻势，彻底击败塔利班(Taliban)和基地组织(al-Qaida)。"
     "用南北两支战斗群拿下坎大哈(Kandahar)和拉什卡尔加(Lashkar gah)。接下来，肃清低地内一切残余抵抗。"
     "然后，用空中机动部队除掉奥萨马(Osama)。", 16),
    ("Userscen", "Eome2", "敌人的敌人",
     "美国第一远征军(I MEF)奉命绕过河内(Hanoi)，以便让越南(Vietnam)流亡部队夺回该城及其周边港口地区。"
     "为支援他们，越南方面已请美国(America)和法国(France)出手相助。", 16),
    ("Userscen", "Land Reclamation", "收复失地",
     "自 1945 年以来，日本(Japan)的北方诸岛一直非法握在俄罗斯(Russia)手中。中国的侵略给了我们一个机会，"
     "收复理应属于我们的领土。作为我们出兵的回报，美国(America)将不再反对我们重新夺取并控制这些岛屿。"
     "作为日本帝国陆军参谋本部的一员，将军，这项任务就交给你了。", 18),
    ("Userscen", "RetStal27", "重返斯大林格勒 2.7",
     "经过多年战争，西方部队终于挡住了中国的推进。如今，时隔 69 年，德国和意大利军队重返斯大林格勒(Stalingrad)"
     "——这一次是来帮助他们的俄罗斯(Russia)盟友，把中国军队赶出该城。俄军将从东面直接攻城，"
     "而南面的德意军队须先歼灭顿河—伏尔加运河(Don-Volga Canal)上的蒙古据点，再与俄军会合，"
     "对西斯大林格勒发起最后攻击。", 6),
    ("Userscen", "Revolution", "革命",
     "中国(China)叛军已决定与美国(America)联手打击新加坡(Singapore)。"
     "计划是破坏中国的基础设施，好迫使中国政府让步。", 25),
    ("Userscen", "Sarajevo", "围攻萨拉热窝（2 人）",
     "萨拉热窝(Sarajevo)已被围困 6 个月。塞尔维亚(Serbia)军队已准备好发动最后攻势，"
     "阿尔坎(Arkan)之虎扼守着通往多布里尼亚(Dobrinja)的北路。"
     "波黑一方拼死防御，仍在等待那支本应前来解围的援军……", 10),
]


def main():
    dry = "--dry" in sys.argv
    n = 0
    for sub, stem, name, desc, turns in ENTRIES:
        body = f"{name}\r\n\r\n{desc}\r\n\r\n{turns} 回合({turns} Turns)"
        # ⚠️ 受限的是 .SCN@11329 里的**文件名**（20 字节，含 ".txt"），不是显示名
        assert len(stem) + 4 <= 20, f"{stem}: 文件名+扩展名超出 .SCN 的 20 字节字段"
        data = body.encode("gbk")
        for t in (os.path.join(OUTDIR, sub, stem + ".txt"),
                  os.path.join(GAME, sub, stem + ".txt")):
            exists = os.path.exists(t)
            if not dry:
                os.makedirs(os.path.dirname(t), exist_ok=True)
                open(t, "wb").write(data)
            print(f"  {'改写' if exists else '新建'} {sub}\\{stem}.txt  ({len(data)}B)")
        n += 1
    print(f"\n{'[dry] ' if dry else ''}共处理 {n} 个场景描述文件（nspegu* 7 + Userscen 7）")


if __name__ == "__main__":
    main()
