# -*- coding: utf-8 -*-
"""BASEKORP 散文层 · bom 块（81 条）译文生成。

莫克拉之战（Battle of Mokra，1939 波兰战役）地图单位标签与地名。
口径：德军单位缩写译中文（PzRgt→装甲团、ARgt→炮兵团、PiBat→工兵营、PzAbwAbt→反坦克营、
A.A.→侦察营、SchRgt→步枪团、leFlaKAbt→轻型高射炮营、Teile→一部）；
波军缩写译中文（p.ul.→枪骑兵团、dpanc→装甲师、psk→骑兵猎兵团、dak→骑兵炮兵营）；
纯数字/斜杠、大写缩写（LW/SG）与无从确证的波兰缩写原样保留；地名音译；叙事段译出。
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load_keys(path):
    keys = []
    with io.open(path, encoding="utf-8") as f:
        next(f, None)
        for ln in f:
            ln = ln.rstrip("\r\n")
            if ln:
                keys.append(ln.rsplit("\t", 1)[0])
    return keys


keys = load_keys(os.path.join(HERE, "bom_todo.tsv"))

DST = [
    "Clu 的莫克拉之战",
    "第19枪骑兵团",
    "第21枪骑兵团",
    "第12枪骑兵团",
    "第21装甲师",
    "第11徒步猎兵营",
    "第2骑兵猎兵团",
    "第2骑兵炮兵营",
    "4/84",
    "82 bmap",
    "4 sk",
    "8 sp",
    "7 b.ckm",
    "第12步枪团/第4装甲师",
    "第1/第36装甲团/第4装甲师",
    "第1/第103炮兵团/第4装甲师",
    "莫克拉 I",
    "莫克拉 II",
    "莫克拉 III",
    "第7侦察营一部",
    "第3/第31工兵营/第31步兵师",
    "第1/第62工兵营",
    "第12步兵团/第31步兵师",
    "第2/第36装甲团/第4装甲师",
    "第1/第31炮兵团/第31步兵师",
    "第77轻型高射炮营",
    "第2（重型）/第54炮兵团",
    "第3/第79工兵营/第4装甲师",
    "第35装甲团/第4装甲师",
    "第2+第3/第103炮兵团/第4装甲师",
    "第49反坦克营/第4装甲师",
    "LW",
    "SG",
    "27/7",
    "25/7",
    "74/7",
    "7/7",
    "7 重型/7",
    "7 工兵/7",
    "第1步枪团/第1装甲师",
    "第1装甲团/第1装甲师",
    "第2装甲团/第1装甲师",
    "第4侦察营/第1装甲师",
    "第37工兵营/第1装甲师",
    "第37反坦克营/第1装甲师",
    "帕日梅希采",
    "拿破仑",
    "兹博里",
    "栋布鲁夫卡",
    "科钦卡河",
    "利皮耶",
    "利什瓦尔特河",
    "库兹尼察",
    "戈米纳卡河",
    "扎亚奇基德鲁格",
    "雷别利采克罗莱夫斯基",
    "伊兹比斯卡",
    "比亚瓦奥克沙河",
    "克热皮采",
    "奥斯特罗维",
    "瓦皮恩尼克",
    "缅兹诺",
    "伊万诺维采",
    "维尔科维茨科",
    "科瓦奇科维采",
    "登布尼克",
    "奥帕图夫",
    "科钦",
    "瓦伦佐夫",
    "亚尼基",
    "沃博德诺",
    "克沃布茨克",
    "卡梅克",
    "潘基",
    "利比扎",
    "查尔尼拉斯",
    "希米亚维",
    "莫克拉之战",
    "莫克拉之战发生于1939年9月1日，地点在莫克拉村附近，位于克沃布茨克以北5公里、波兰琴斯托霍瓦西北23公里处。这是波兰入侵（第二次世界大战）最初的战斗之一，也是那场战役中波兰人少有的胜利之一。",
    "德国第4装甲师被逼回其在奥帕图夫和维尔科维茨科的初始阵地，只有第12步枪团抵达了伊兹比斯卡的铁路道口。然而，在得知德国第1装甲师已夺取克沃布茨克后，波军当夜向东南撤退至克沃布茨克东北的沃博德诺村，随后又撤到以东约12公里的第二道防线。",
    "双方伤亡都相当惨重。德军损失约800人（阵亡、失踪、被俘或重伤），以及100至160辆装甲车辆（其中至少50辆坦克）。波兰旅损失200人阵亡、300人负伤，另有300匹马和若干门火炮。第2骑兵炮兵营损失了近30%的人员，第21团损失近25%；被用作预备队的第12枪骑兵团损失了5名军官和216名士兵，包括阵亡和负伤者。[维基百科]",
]

if len(DST) != len(keys):
    print("FATAL: dst=%d keys=%d" % (len(DST), len(keys)))
    for i in range(max(len(DST), len(keys))):
        k = keys[i] if i < len(keys) else "<none>"
        d = DST[i] if i < len(DST) else "<none>"
        print("%4d K=%s | D=%s" % (i + 1, k[:60], d[:40]))
    sys.exit(1)

for i, d in enumerate(DST, 1):
    if "\t" in d:
        print("FATAL: tab at %d" % i)
        sys.exit(1)
    try:
        d.encode("gbk")
    except UnicodeEncodeError as e:
        print("FATAL: gbk at %d: %s" % (i, e))
        sys.exit(1)

with io.open(os.path.join(HERE, "zh-bom.tsv"), "w",
             encoding="utf-8", newline="\r\n") as f:
    f.write("src\tdst\r\n")
    for s, d in zip(keys, DST):
        f.write("%s\t%s\r\n" % (s, d))

print("zh-bom.tsv written: %d rows" % len(keys))
