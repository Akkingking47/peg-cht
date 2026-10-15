# -*- coding: utf-8 -*-
"""把 6 个小块（dasreich/lssah/camp/bchoice/europe/germany）待译行配对 LLM 译文。
src 从各 todo 原样读取（零手抄错位）；dst 按同序配对。
内容 = 战役简介/元数据/分支菜单/章节列表。
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
DEC = re.compile(r'^([\s_*=.®¯Â\-]+)(.*)$')

def load(block):
    todo = os.path.join(HERE, block + "_todo.tsv")
    rows = []
    with open(todo, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            s = line.rstrip("\r\n")
            if not s.strip():
                continue
            rows.append(s.rsplit("\t", 1)[0])
    return rows

def emit(block, rows, dst):
    assert len(rows) == len(dst), "%s 行数不符: %d vs %d" % (block, len(rows), len(dst))
    out = os.path.join(HERE, "zh-" + block + ".tsv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write("src\tdst\n")
        for s, d in zip(rows, dst):
            m = DEC.match(s)
            if m and m.group(2).strip():
                d = m.group(1) + d
            f.write(s + "\t" + d + "\n")
    print("写出", out, len(rows), "条")

# ---- dasreich (5) ----
emit("dasreich", load("dasreich"), [
    "11.   “帝国”师",
    "场景数：33",
    "战役设计者：Jurgen Smet",
    "本“帝国”师战役让你指挥党卫军部队——党卫军“武装”师（SS-Verfuegungstruppe）、党卫军“帝国”师（SS-Division Das Reich）、党卫军装甲掷弹兵“帝国”师（SS-Panzergrenadier-Division Das Reich）和第2党卫军装甲师“帝国”师。该师是经典的党卫军师之一，很快以勇敢无畏赢得了声誉。",
    "该师部队转战波兰、荷兰、比利时、法国、巴尔干、俄国、诺曼底、阿登、匈牙利、维也纳和布拉格。这是一场营级规模的闪电战式战役。",
])

# ---- lssah (5) ----
emit("lssah", load("lssah"), [
    "“我的荣誉即忠诚”——警卫旗队",
    "场景数：18",
    "战役设计者：Technique",
    "第1党卫军“警卫旗队”师战役",
    "你将指挥希特勒的精锐卫队，从早期作为精锐摩托化旅，一路成长为完整装甲师，经历一场场史诗战役。你将转战波兰、荷兰、法国、巴尔干和苏联，在证明你部战斗技能的过程中，把你的士兵推向极限。",
])

# ---- camp (13) ----
emit("camp", load("camp"), [
    "14.  闪电战 2008",
    "版本：2019年2月",
    "装备文件：Basekorps",
    "场景数/最长路线：32",
    "战役设计者：Craig Miller",
    "战役转换/修改者：Brian Gosley（即 Puma）",
    "你将指挥部队从西班牙内战，一路打到二战初期的一次次“闪电”胜利——以及更远！",
    "06.  Sapper 的轴心国战役 9.0 BK",
    "版本：2019年4月",
    "场景数：22",
    "玩家阵营：意大利及轴心国",
    "战役设计者：Sapper",
    "你将指挥从埃塞俄比亚调往西班牙的意大利军团，加入轴心国讨伐世界共产主义的“圣战”，1937—1944年。",
])

# ---- bchoice (19) ----
emit("bchoice", load("bchoice"), [
    "选择一",
    "第1回合：1940 比利时",
    "第2回合：1941 托布鲁克、希腊和马耳他",
    "第3回合：1941 俄国——巴巴罗萨",
    "第4回合：1942 选择2以查看更多选择",
    "选择二",
    "第1回合：希腊群岛 1942年2月。",
    "第2回合：俄国日尔科夫斯基 1942年12月。",
    "第3回合：巴尔干 1943年8月。",
    "第4回合：更多选择",
    "俄国卡涅夫 1943年11月",
    "卡昂 1944年6月",
    "海峡 1945年9月",
    "加拿大 1946年1月",
    "选择三",
    "第1回合：俄国卡涅夫 1943年11月",
    "第2回合：卡昂 1944年6月",
    "第3回合：海峡 1945年9月",
    "第4回合：加拿大 1946年1月",
])

# ---- europe (9) ----
emit("europe", load("europe"), [
    "04.  欧洲战争",
    "场景数：25",
    "战役设计者：George 等",
    "1939年，奥地利、捷克和摩拉维亚已被占领。现在我们要用国防军的力量去对付庞大的波兰军队。",
    "本战役共25个场景，辅助单位非常有限。你将依靠核心部队作战。波兰、法国、俄国等都需要被征服。",
    "组建一支约30个单位的联合核心部队。本战役没有特殊规则或窍门，只有大量战斗。",
    "懂得何时坚守、撤退或推进，将是你最大的盟友。",
    "威望靠夺取获得，所以你需要保持机动。",
    "要当心，大多数双发、三发和四发轰炸机以及要塞被摧毁时都会炸毁所在格。",
])

# ---- germany (27) ----
emit("germany", load("germany"), [
    "03.  德国战争",
    "由 Brian Gosley 于2019年2月转换为 BaseKorp",
    "战争开始了。本战役将经历：",
    "建议威望设为 100—125。",
    "第一章",
    "西班牙内战，你将指挥佛朗哥将军麾下的部队。",
    "1939年征服波兰。",
    "黄色方案，1940年进攻法国。",
    "对英战争，海狮行动。",
    "入侵巴尔干。",
    "空降突击克里特岛。",
    "第二章",
    "1941年巴巴罗萨行动",
    "斯摩棱斯克、维亚济马。",
    "1941年莫斯科。",
    "第三章",
    "1942年铁木辛哥反攻",
    "沃罗涅日、顿河。",
    "高加索",
    "第四章",
    "1943年库尔斯克。",
    "假想机遇。",
    "图拉。",
    "1943年莫斯科",
    "第五章",
    "1944/45年西线/东线",
    "HF&GL……",
])
