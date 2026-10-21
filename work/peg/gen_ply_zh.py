# -*- coding: utf-8 -*-
"""PeG `.ply`（场景描述，定长 NUL 填充）中文化。
⚠️ `.ply` 才是「場景選擇」界面下方描述框真正的来源；此前只译了 `.txt`，故描述框全英文。
规则：保留**原始字节长度**、NUL 填充、原换行风格；内容超长则报错不落盘。
用法：python work/peg/gen_ply_zh.py build | deploy
"""
import os, sys, shutil

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


ROOT = WS
BACKUP = os.path.join(ROOT, r"peg\testbed\backup")
OUTDIR = os.path.join(ROOT, r"peg\testbed\scn-zh")

T = {
# ⚠️ 第 28 轮：**第 0 行必须是标题**（描述框只显示第 1 行起，标题行会被吞掉）。
"Scenario/nspegu01.ply":
 "保卫首尔\n\n"
 "中国(China)与朝鲜(North Korea)军队看来即将突袭首尔(Seoul)。不惜一切代价阻止他们。",

"Scenario/nspegu10.ply":
 "退回大田\n\n"
 "中华人民共和国(People's Republic of China)已向朝鲜(North Korea)承诺增援，以发动新一轮攻势。"
 "你必须夺取大田(Taejon)、控制北上鸟致院(Choch'iwan)的公路，并肃清半岛西岸北上至洪城(Hongsong)的地区。"
 "别让我失望，指挥官。到目前为止，尽管你已尽力，这场战争打得实在糟糕。",

"Scenario/nspegu13.ply":
 "釜山最后一人\n\n"
 "自我们宣战以来，已过去漫长的三个月。其间我们遭遇了诸多灾难，包括首尔(Seoul)和大田(Taejon)。"
 "现在你必须守住釜山(Pusan)，就像几十年前海军陆战队那样。如果你能救下釜山，我们或许还能从日本(Japan)运来增援。"
 "你要从釜山(Pusan)港出击，夺取马山(Masan)、蔚山(Ulsan)和密阳(Miryang)，"
 "作为解放韩国首都首尔(Seoul)的垫脚石。韩国军队的残部将在那里提供协助。祝你好运。",

"Scenario/nspegu16.ply":
 "夺回大田\n\n"
 "中华人民共和国(People's Republic of China)已向朝鲜(North Korea)承诺增援，以发动新一轮攻势。"
 "我们对釜山(Pusan)港的控制太过脆弱，无法采取守势；必须在中国大军压来之前冲出这个死角。"
 "你必须夺取大田(Taejon)、控制北上鸟致院(Choch'iwan)的公路，并肃清半岛西岸北上至洪城(Hongsong)的地区。",

"Scenario/nspegu19.ply":
 "盟军进军首尔\n\n"
 "中国(China)与朝鲜(North Korea)军队似乎已在首尔(Seoul)站稳脚跟，但夺回全城就看你的了。别让我失望，指挥官！",

"Scenario/nspegu25.ply":
 "强攻伏尔加格勒\n\n"
 "美国(America)调动兵力，赶在这个备受打击的国家彻底崩溃之前支援其俄罗斯(Russia)盟友。"
 "他们发动攻势，以强攻伏尔加格勒(Volgograd)把中华人民共和国(People's Republic of China)"
 "逐出乌拉尔(Urals)。\n\n2 人（推荐多人对战）\n\n6 个回合",

"Scenario/nspegu27.ply":
 "强攻伏尔加格勒\n\n"
 "美国(America)调动兵力，赶在这个备受打击的国家彻底崩溃之前支援其俄罗斯(Russia)盟友。"
 "他们发动攻势，以强攻伏尔加格勒(Volgograd)把中华人民共和国(People's Republic of China)"
 "逐出乌拉尔(Urals)。\nNarayan Sengupta\nv.1.1，2001 年 7 月 3 日",

"Userscen/Crimson.ply":
 "赤色风暴\n\n"
 "俄罗斯(Russia)叛军已夺取并控制了阿尔乔姆(Artem)城郊的洲际弹道导弹(ICBM)基地，还控制了该城。"
 "忠于政府的部队已将叛军包围，但要把他们彻底清除并不容易。你手上的兵力有限，却训练有素，"
 "还有不错的空中支援和三个精锐空降营可供调配。",

"Userscen/Demise of Osma.ply":
 "奥萨马之死\n\n"
 "塔利班(Taliban)部队已退守坎大哈(Kandahar)老巢。联军受命发动最后攻势，"
 "彻底击败塔利班(Taliban)和基地组织(al-Qaida)。用南北两支战斗群拿下坎大哈(Kandahar)"
 "和拉什卡尔加(Lashkar gah)。接下来，肃清低地内一切残余抵抗。"
 "然后，用空中机动部队除掉奥萨马(Osama)。共 16 回合",

"Userscen/Eome2.ply":
 "敌人的敌人\n\n"
 "美国第一远征军(I MEF)奉命绕过河内(Hanoi)，以便让越南(Vietnam)流亡部队夺回该城及其周边港口地区。"
 "为支援他们，越南方面已请美国(America)和法国(France)出手相助。共 16 回合",

"Userscen/Land Reclamation.ply":
 "收复失地\n\n"
 "自 1945 年以来，日本(Japan)的北方诸岛一直非法握在俄罗斯(Russia)手中。"
 "中国的侵略给了我们一个机会，收复理应属于我们的领土。"
 "作为我们出兵的回报，美国(America)将不再反对我们重新夺取并控制这些岛屿。"
 "作为日本帝国陆军参谋本部的一员，将军，这项任务就交给你了。",

"Userscen/RetStal27.ply":
 "重返斯大林格勒\n01/01/2011\n\n"
 "经过多年战争，西方部队终于挡住了中国的推进。如今，时隔 69 年，"
 "德国和意大利军队重返斯大林格勒(Stalingrad)——这一次是来帮助他们的俄罗斯(Russia)盟友，"
 "把中国军队赶出该城。俄军将从东面直接攻城，而南面的德意军队须先歼灭"
 "顿河—伏尔加运河(Don-Volga Canal)上的蒙古据点，再与俄军会合，"
 "对西斯大林格勒发起最后攻击。\n\n请使用 5 Stars 装备文件",

"Userscen/Revolution.ply":
 "革命\n\n"
 "中国(China)叛军已决定与美国(America)联手打击新加坡(Singapore)。"
 "计划是破坏中国的基础设施，好迫使中国政府让步。",

"Userscen/Sarajevo.ply":
 "围攻萨拉热窝\n28/10/1992\n"
 "萨拉热窝(Sarajevo)已被围困 6 个月。\n\n"
 "塞尔维亚(Serbia)军队已准备好发动最后攻势，阿尔坎(Arkan)之虎扼守着通往"
 "多布里尼亚(Dobrinja)的北路。\n"
 "波黑一方拼死防御，仍在等待那支本应前来解围的援军……",
}


def build():
    bad = 0
    for rel, zh in T.items():
        src = os.path.join(BACKUP, rel.replace("/", os.sep))
        if not os.path.exists(src):
            print(f"❌ 缺备份 {rel}"); bad += 1; continue
        orig = open(src, "rb").read()
        nsize = len(orig)
        # 原换行风格
        if b"\r\n" in orig: eol = "\r\n"
        elif b"\n" in orig:  eol = "\n"
        else:                eol = "\n"
        body = zh.replace("\n", eol)
        try:
            enc = body.encode("gbk")
        except UnicodeEncodeError as e:
            print(f"❌ {rel} GBK 编码失败：{e}"); bad += 1; continue
        if len(enc) > nsize:
            print(f"❌ {rel} 超长：译文 {len(enc)}B > 原 {nsize}B"); bad += 1; continue
        out = enc + b"\x00" * (nsize - len(enc))
        assert len(out) == nsize
        dst = os.path.join(OUTDIR, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "wb").write(out)
        print(f"  ✓ {rel:32s} {len(enc):4d}B / {nsize}B")
    print(f"生成完毕，异常 {bad} 个")


def deploy():
    n = 0
    for rel in T:
        src = os.path.join(OUTDIR, rel.replace("/", os.sep))
        dst = os.path.join(GAME, rel.replace("/", os.sep))
        if os.path.exists(src) and os.path.exists(dst):
            shutil.copy2(src, dst); n += 1
    print(f"已部署 {n} 个 .ply")


if __name__ == "__main__":
    (deploy if (len(sys.argv) > 1 and sys.argv[1] == "deploy") else build)()
