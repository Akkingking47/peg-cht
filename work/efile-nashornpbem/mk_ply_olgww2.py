# -*- coding: utf-8 -*-
"""写 OLGWW2 的 5 个 .ply 场景简报中文版。

输出：GBK(936) 无 BOM、CRLF；同时写入 SCENARIO\\ 与 TEXT-ZH\\SCENARIO\\。
双语言块（西/英）合并为**单一中文块**（实测引擎只显示第一块）。
"""
import os

ROOT = r"D:/OpenPG2/EFILE_OLGWW2"
DIRS = [os.path.join(ROOT, "SCENARIO"), os.path.join(ROOT, "TEXT-ZH", "SCENARIO")]

FILES = {}

FILES["barceint.ply"] = """通往巴塞罗那之路

地图: 巴塞罗那 (编号 757)
资料库: OLGWW2 1.75 或更高
类型: 历史

西班牙内战正随着国民军对加泰罗尼亚的攻势而走向终局。埃布罗河战役之后，共和军已十分虚弱，只能一路不断地后撤。

本图及最新地图请从以下地址获取: http://www.gilestiel.eu/MapFinder/index.php

作者 Santiago Fuertes - The Latin Generals 2011 - http://gilestiel.nerim.net/lg/
"""

FILES["canalalbert_i.ply"] = """阿尔贝特运河
(1940年5月10-12日)

将军，德国人期待已久的进攻已经开始。今晨德军已越过荷兰边境，数小时内即将抵达我们位于阿尔贝特运河之后的"掩护阵地"。凭借坚固的埃本-埃马尔要塞，你必须尽可能长时间地把德军阻于掩护阵地，以便我军以及法英盟友能占领 KW 防线上的阵地——那是预定进行决战的主要抵抗线。因此，绝不能让德军夺取阿尔贝特运河上的桥梁。

如形势需要，你可获得骑兵军的部分增援。

胜利条件: 守住 7 个胜利点得大胜，4 个得小胜，2 个得战术胜利。

提示: 在德军夺取桥梁之前将其炸毁

地图: 阿尔贝特运河 (828)

Paqueo, 2010年12月
"""

FILES["chaco1.ply"] = """博克龙堡

地图: 博克龙 (编号 862)
资料库: OLGWW2 1.75 或更高
类型: 历史

巴拉圭军队试图夺回博克龙堡，将玻利维亚人逐出该地区。从历史上看，缺水与北查科的孤绝，才是玻利维亚军队最难对付的敌人。

本图及最新地图请从以下地址获取: http://www.gilestiel.eu/MapFinder/index.php

作者 Santiago Fuertes - The Latin Generals 2010 - http://gilestiel.nerim.net/lg/
"""

FILES["getteriver.ply"] = """赫特河简介

德军越过阿尔贝特运河后，比利时军队已奉命撤往 KW 防线。为掩护这次撤退，骑兵军（第1骑兵师与第2骑兵师）须在迪斯特与蒂尔莱蒙之间的赫特河上建立防线。据情报，预计德军步兵将对哈伦镇发起猛烈进攻。

你的任务是在各渡口尽可能久地挡住德军，以便盟军各部完成重新部署。

请注意，在更南面的小赫特河，法国骑兵军正与德军第16装甲军交战，德军装甲部队很可能支援其步兵的攻势。

地图: 哈伦 (379)

Paqueo, 2010年9月
"""

FILES["nice_sfb.ply"] = """一定要拿下尼斯！

"我只需要几千名死者，好让我能以打过仗的人的身份，坐在和会的桌边。"（皮埃特罗·巴多里奥将军，意大利皇家陆军总参谋长）

"1940年6月10日这一天，那只握着匕首的手，已将它刺进了邻国的后背。"（富兰克林·D·罗斯福，美国总统，就意大利对法宣战发表）

当法国的局势日渐明朗时，墨索里尼以为这是件轻松的差事，便趁机攫取其索取的阿尔卑斯领土以及尼斯城周边地区。然而这场入侵很快证明，对意大利人而言并不轻松——法军对入侵者在阿尔卑斯山毫不留情。

试着比意大利人干得更漂亮吧，为墨索里尼的新意大利帝国多添几块法国领土。

*提示* 意大利皇家空军需要一条机场来补给飞机。用你的工兵在合适位置修建一条。

20 回合。

地图: 尼斯 (编号 127)
资料库: OLGWW2 1.0 或更高
类型: 历史

本图及最新地图请从以下地址获取: http://www.gilestiel.eu/MapFinder/index.php

作者 Santiago Fuertes - The Latin Generals 2010 - http://gilestiel.nerim.net/lg/
"""


def main():
    for name, text in FILES.items():
        data = text.replace("\r\n", "\n").replace("\n", "\r\n").encode("gbk")
        for d in DIRS:
            p = os.path.join(d, name)
            tmp = p + ".new"
            open(tmp, "wb").write(data)
            back = open(tmp, "rb").read()
            assert back == data, name
            os.replace(tmp, p)
            han = sum(1 for c in back.decode("gbk") if "\u4e00" <= c <= "\u9fff")
            print("OK  %-46s %5d B  汉字 %4d" % (p.replace("D:/OpenPG2/", ""), len(data), han))


main()
