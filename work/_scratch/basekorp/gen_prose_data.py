# -*- coding: utf-8 -*-
"""生成 BASEKORP 散文层的两份译文数据：
  prose_dict.tsv  —— 全局高频固定行（模板/标题/套话），机器层复用
  zh-r00.tsv      —— r00 战役族（FALCIU）完整 LLM 译文，作示范块

两份都是 src->dst 行级映射；translate_prose.py 按 (file?)src 查表。

关键修正：r00info 等长段绝不从手写字符串当 key（易拼错），改为从源文件
直接按行号读出原文作 key，保证 100% 字节匹配。
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SC_SRC = r"D:\OpenPG2\EFILE_BASEKORP\SCENARIO"


def _rl(fn, idx):
    """读源文件第 idx 行（CRLF 分割），用于当字典 key，杜绝手抄错位。"""
    return open(os.path.join(SC_SRC, fn), "rb").read().decode("cp1252").split("\r\n")[idx].rstrip()


# —— 全局高频固定行（取自 lines-prose n>=4 的 148 条，剔除装饰行与长叙事）——
PROSE_DICT = {
    "VICTORY": "胜利",
    "BRILLIANT VICTORY": "辉煌胜利",
    "TACTICAL VICTORY": "战术胜利",
    "LOSS": "失败",
    "HISTORY": "历史背景",
    "History": "历史背景",
    "PLAYER ORDERS": "玩家命令",
    "PLAYER ORDERS:": "玩家命令：",
    "ORDERS": "命令",
    "ORDERS:": "命令：",
    "Orders :": "命令：",
    "Orders:": "命令：",
    "TACTICAL ORDERS:": "战术命令：",
    "RECONNAISSANCE:": "侦察：",
    "STRATEGIC SITUATION:": "战略态势：",
    "VICTORY CONDITIONS:": "胜利条件：",
    "ADDITIONAL INFORMATION": "附加信息",
    "NOTES: ": "注意：",
    "NOTE:": "注意：",
    "NOTE: All axis nations auxiliaries are under your command.": "注意：所有轴心国辅助部队归你指挥。",
    "Player Note:": "玩家备注：",
    "News: ": "战报：",
    "News:": "战报：",
    "CREDITS": "制作人员",
    "Credits:": "制作人员：",
    "Credits: Story line and campaign path by Adler.": "制作人员：剧情与战役路线由 Adler 设计。",
    "Credits: Story line, campaign path and scenario setup by Adler.": "制作人员：剧情、战役路线与场景设置由 Adler 设计。",
    "Historical Info:": "历史信息：",
    "Herr General,": "将军阁下，",
    "Herr General": "将军阁下",
    "Herr General!": "将军阁下！",
    "Gereral!": "将军！",
    "General!": "将军！",
    "Marshall!": "元帅！",
    "Hello General!": "你好，将军！",
    "Herr General, come in!": "将军阁下，请讲！",
    "Cheers!": "干杯！",
    "Congratulations. You have succeeded against all odds. Mateur and Tebourba are in our hands.": "祝贺你。你已逆势成功。马特尔和泰布尔巴已落入我们手中。",
    "Good luck.": "祝你好运。",
    "Good luck. ": "祝你好运。",
    "Good Luck!": "祝你好运！",
    "Good work.": "干得好。",
    "GOAL: Take all VH's!": "目标：夺取所有胜利点！",
    "Victory conditions: Capture all VHs.": "胜利条件：夺取所有胜利点。",
    "- Capture all VH.": "- 夺取所有胜利点。",
    "Capture all Victory Hexes to claim the victory!": "夺取所有胜利点以赢得胜利！",
    "Main reinforcements:": "主要增援：",
    "Reinforces: None.": "增援：无。",
    "- Strength lost on core units will be automatically replaced at HQ at the start of the next scenario.": "- 核心单位损失的兵力将在下一场景开始时于总部自动补充。",
    "- Strength lost on core units will not be automatically replaced at HQ at the start of the next scenario.": "- 核心单位损失的兵力将不会在下一场景开始时于总部自动补充。",
    "- New units can be acquired at HQ at the start of the next scenario.": "- 新单位可在下一场景开始时于总部获取。",
    "- New units cannot be acquired at HQ at the start of the next scenario.": "- 新单位无法在下一场景开始时于总部获取。",
    "- Units can be upgraded before the scenario.": "- 单位可在场景开始前升级。",
    "Recomended purchase:- Upgrades and overstrengthening.": "推荐购买：升级与超编强化。",
    "Equipment file: Basekorp ": "装备文件：Basekorp",
    "Player Country: Germany": "玩家国家：德国",
    "Version:  Apr-2019": "版本：2019年4月",
    "Modified by Brian Gosley aka Puma": "修改：Brian Gosley（又名 Puma）",
    "Two Player": "双人",
    "2 Players": "2 名玩家",
    "(If playing with rules do not buy any new units.)": "（若按规则游玩，请勿购买任何新单位。）",
    "XIX Corps Battleplan:-": "第19军作战计划：-",
    "A big thank you to Dragdasan for the magnificant map that he made for this scenario.": "特别感谢 Dragdasan 为本场景制作的精美地图。",
    "Thank you for playing this campaign to the very end. I hope you enjoyed it. Please register at OG Forums. I would appreciate it.": "感谢你坚持玩到战役终局。希望你喜欢。请在 OG 论坛注册，我将不胜感激。",
    "Well, that's the end of my short campaign.": "好吧，我的短篇战役到此结束。",
    "You have achieved all objectives, the mission was a complete success. Good work!": "你已完成所有目标，任务大获成功。干得好！",
    "You could not achieve your goals, the mission was a failure!": "你未能达成目标，任务失败！",
    "[You doofus, now go back and choose either a VICTORY or a TACTICAL VICTORY!]": "[你这笨蛋，回去选“胜利”或“战术胜利”！]",
}

# —— r00 战役族（FALCIU）完整 LLM 译文 ——
# key 全部从源文件按行号读出，避免手写长串错位。
R00 = {
    "r00info.txt": {
        _rl("r00info.txt", 0): "00. 法尔丘 1（1941年6月22日）",
        _rl("r00info.txt", 2): "亲爱的同志。今天，来自德国的法西斯军队已从波罗的海至乌克兰一线进攻我国边境。更糟的是，罗马尼亚已对我们宣战。局势看似严峻，但我们已做好准备。我们的红军是世界上最庞大的军队，拥有的坦克与飞机数量超过任何其他国家。胜利终将属于我们。",
        _rl("r00info.txt", 4): "你的部队隶属于驻扎在比萨拉比亚（原罗马尼亚领土）的第150步兵师。罗马尼亚人很可能很快在此发动攻势。为阻止其进攻并夺取合适的防御阵地以发起我军自己的攻势，你必须从法尔丘渡过普鲁特河、夺取桥梁并建立桥头堡。增援将尽可能及时抵达。当心罗马尼亚人——他们是在自己的土地上作战，必将殊死抵抗。你必须成功。祝你好运，同志！",
        _rl("r00info.txt", 6): "注意：你初始没有核心单位，需要自行购买。",
    },
    "r00endv.txt": {
        "VICTORY": "胜利",
        "Excellent, Comrade. You have shown that it is a mistake to think the Red Army is an easy prey! You are ordered to dig in, because the situation on other sections of the front causes us to send all reinforcements elsewhere. ": "太棒了，同志。你已证明，认为红军是易于捕食的猎物是个错误！你奉命就地固守，因为前线其他地段的局势要求我们抽调所有增援前往别处。",
    },
    "r00endbv.txt": {
        "BRILLIANT VICTORY": "辉煌胜利",
        "Brilliant, Comrade. You have shown that it is a mistake to think the Red Army is an easy prey! You are ordered to dig in, because the situation on other sections of the front causes us to send all reinforcements elsewhere. ": "出色，同志。你已证明，认为红军是易于捕食的猎物是个错误！你奉命就地固守，因为前线其他地段的局势要求我们抽调所有增援前往别处。",
    },
    "r00endtv.txt": {
        "TACTICAL VICTORY": "战术胜利",
        "Well done, Comrade. You have shown that it is a mistake to think the Red Army is an easy prey! You are ordered to dig in, because the situation on other sections of the front causes us to send all reinforcements elsewhere. ": "干得好，同志。你已证明，认为红军是易于捕食的猎物是个错误！你奉命就地固守，因为前线其他地段的局势要求我们抽调所有增援前往别处。",
    },
    "r00lost.txt": {
        "LOSS": "失败",
        "The Rumanians proved to be too strong for you. Because you are incompetent to lead Red Army troops you will be stripped of your insignia and serve as a regular soldier from now on!": "罗马尼亚人证明你无力应付。既然你无能指挥红军部队，你的军衔将被剥夺，从此以普通士兵身份服役！",
    },
}


def main():
    with io.open(os.path.join(HERE, "prose_dict.tsv"), "w",
                 encoding="utf-8", newline="\r\n") as f:
        f.write("src\tdst\r\n")
        for k, v in PROSE_DICT.items():
            f.write("%s\t%s\r\n" % (k, v))
    with io.open(os.path.join(HERE, "zh-r00.tsv"), "w",
                 encoding="utf-8", newline="\r\n") as f:
        f.write("file\tsrc\tdst\r\n")
        for fn, d in R00.items():
            for k, v in d.items():
                f.write("%s\t%s\t%s\r\n" % (fn, k, v))
    print("prose_dict %d 条 / r00 %d 条（%d 文件）" % (
        len(PROSE_DICT), sum(len(d) for d in R00.values()), len(R00)))


if __name__ == "__main__":
    main()
