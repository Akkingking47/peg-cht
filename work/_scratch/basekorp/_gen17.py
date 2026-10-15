# -*- coding: utf-8 -*-
"""生成 chunk-17 番号串汉化（zh-17.tsv）"""
import re

SRC = r"d:/DSH/军事游戏汉化/work/basekorp/chunks/in-17.tsv"
DST = r"d:/DSH/军事游戏汉化/work/basekorp/chunks/zh-17.tsv"

# 词级替换（作用于 draft）
TOK = [
    ("Coordination center", "协调中心"), ("training barracks", "训练营房"),
    ("orientation center", "入伍教育中心"), ("Airport Construction Equipment", "机场施工设备"),
    ("Barrack modules", "营房模块"), ("Aviation Fuel", "航空燃油"),
    ("Drinking Water", "饮用水"), ("Fuel Oil", "燃油"), ("Fuel oil", "燃油"),
    ("Contractors", "承包商"), ("Welders", "焊工"), ("Inspectors", "检验员"),
    ("Clerks", "文书"), ("National 近卫", "国民警卫队"),
    ("Wolfpack", "狼群"), ("Scout", "侦察"), ("planning", "策划"),
    ("Recon", "侦察"), ("recon", "侦察"), ("Eng", "工兵"),
    ("Grppe", "集群"), ("Gruppe", "集群"), ("Mob", "暴徒队"),
    ("Hole", "洞穴"), ("Lair", "巢穴"), ("sight", "观测哨"), ("Sight", "观测哨"),
    ("harbour", "港"), ("Armada", "舰队"), ("threads", "履带"), ("plating", "装甲板"),
    ("Seaweed", "海草"), ("Avenue", "大道"), ("Rangers", "游骑兵"), ("Hopping", "跳跃"),
    ("JAF", "日本空军"), ("FAF", "法国空军"), ("RCAF", "加拿大皇家空军"),
    ("AF", "空军"), ("Fgt", "战斗机"), ("BG", "轰炸机大队"), ("FB", "战斗轰炸机"),
    ("Home", "本土"), ("Chicago", "芝加哥"), ("Midwest", "中西部"),
    ("Michigan", "密歇根"), ("Indiana", "印第安纳"), ("Nebraska", "内布拉斯加"),
    ("Ohio", "俄亥俄"), ("Missouri", "密苏里"), ("Iowa", "艾奥瓦"),
    ("Kentucky", "肯塔基"), ("Ky", "肯塔基"), ("Scottish", "苏格兰"),
    ("Ranger", "游骑兵"), ("Defenders", "保卫者"), ("Berlin", "柏林"),
    ("Adolph Hitler", "阿道夫·希特勒"), ("Adolph", "阿道夫"), ("Hitler", "希特勒"), ("SA", "冲锋队"),
    ("Shellfield", "谢尔菲尔德"), ("Raeder", "雷德尔"), ("Eaker", "伊克尔"),
    ("Mitchell", "米切尔"), ("Resistance", "抵抗组织"),
    ("Lgt", "轻型"), ("Sub", "潜艇"),
    ("Indocrination", "思想灌输"), ("Sgt", "军士"),
    ("Virginia", "弗吉尼亚"), ("Netherlands", "荷兰"), ("Newes", "纽斯"),
]


# 整行覆盖
OV = {
    # 人名/短语/引语
    "HQ of Marshal Konstantin Serov": "康斯坦丁·谢罗夫元帅司令部",
    "Early Xmas present Fuhress, Moscow!": "提前的圣诞礼物 弗雷斯,莫斯科!",
    "HQ of Frau 'Frankopplan": "'Frankopplan夫人司令部",
    "\"Their probably just observers\".": "\"他们大概只是观察者。\"",
    "\"Isn't it a Lovely Day\"": "\"今天真是美好的一天\"",
    "Oil from 'Frauland": "来自'Frauland的石油",
    "A common housewife or SS Frau?": "普通家庭主妇还是党卫军夫人?",
    "Frau Gen. 'Lippsch's HQ": "'Lippsch's夫人将军司令部",
    "\"We got 'Em,tell the Hood to sail\".": "\"我们得手了,让胡德号起航.\"",
    "\"The French think it's Impregnable\"": "\"法国人以为它坚不可摧\"",
    "\"Get those Panzers to Beaumont": "\"把那些坦克调到博蒙",
    "\" IT has happened ILse\"": "\"这事终于还是发生了,伊尔莎\"",
    "U.S. Goverment officials": "美国政府官员",
    "'Down with ILsa Mob": "打倒伊尔莎暴徒队",
    "'The SS/BdM must go Mob": "党卫军/BdM必须滚蛋暴徒队",
    "'ILsa is the Devil Mob": "伊尔莎是魔鬼暴徒队",
    "'Nooks You got Your hands full'": "'Nooks 你手忙脚乱了'",
    "Gen. 'Patton/staff": "巴顿将军/参谋部",
    "Gen. 'Leslie/staff": "莱斯利将军/参谋部",
    "Gen. 'Bradley/staff": "布拉德利将军/参谋部",
    "Gen. 'Clarke/staff": "克拉克将军/参谋部",
    "Dv PL1": "波兰第1师", "Dv PL 2": "波兰第2师", "Dv PL 3": "波兰第3师",
    "Radar Equipment": "雷达设备",
    "Col. Newes/staff": "纽斯上校/参谋部",
    "'Resistance HQ": "抵抗组织司令部",
    "'Resistance planning HQ": "抵抗组织策划司令部",
    "'Gasson's Armor plating": "'Gasson's装甲板",
    "SS Eng/dv 'Coellar": "党卫军工兵师'Coellar",
    "Brit Gen. Franklin/staff": "英国富兰克林将军/参谋部",
    "Ranger dv 'Franklin": "游骑兵师'Franklin",
    "17th Chicago AT Gp": "第17芝加哥反坦克群",
    "19th Chicago AT Gp": "第19芝加哥反坦克群",
    "SS Cmmd West 'Arrareil": "党卫军西部司令部'Arrareil",
    "Plish 'Krasewa dv": "波兰'Krasewa师",
    "X-15th sight": "X-第15观测哨", "W-4 Sight": "W-第4观测哨",
    "Radar sight K": "雷达观测哨 K", "Radar sight L": "雷达观测哨 L",
    "Radar sight X7": "雷达观测哨 X7",
    "'Pennsylvania Avenue BG": "宾夕法尼亚大道轰炸机大队",
    "'Texas Rangers BG": "得克萨斯游骑兵轰炸机大队",
    "SS PZ Gp 'Nyhauss IV": "党卫军装甲群'Nyhauss第4",
    "SS PZ Gp 'Nyhauss V": "党卫军装甲群'Nyhauss第5",
    "HQ Remote": "后方司令部",
    # USS / 舰名
    "USS Virginia": "美国海军弗吉尼亚", "USS Delaware": "美国海军特拉华",
    "USS Georgia": "美国海军佐治亚", "USS Florida": "美国海军佛罗里达",
    "USS John Adams": "美国海军约翰·亚当斯", "USS George Washington": "美国海军乔治·华盛顿",
    "USS Ben Franklin": "美国海军本·富兰克林", "USS Abe Lincoln": "美国海军亚伯·林肯",
    "USS Paramount": "美国海军派拉蒙", "USS Dee Dee": "美国海军迪迪",
    "USS Riverside": "美国海军里弗赛德", "USS Ohio": "美国海军俄亥俄",
    "USS Clements": "美国海军克莱门茨", "USS Irving": "美国海军欧文",
    "USS Meadowland": "美国海军梅多兰", "USS Tiacondaroga": "美国海军提康德罗加",
    "USS Lexington": "美国海军列克星敦", "USS Columbia": "美国海军哥伦比亚",
    "USS Burlington": "美国海军伯灵顿", "USS Harpers Ferry": "美国海军哈珀斯费里",
}
# 空降师（draft 误作 空降旅师）
for _n in ("'Cloves", "'Carlington", "'Presley", "'Ashcroft", "'Huntsbrook"):
    OV["AB dv " + _n] = "空降师" + _n
# 地堡标记
for _i in ("01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
           "11", "12", "13", "14", "15"):
    OV["bk" + _i] = "地堡" + _i
# 西班牙内战
SV = {
    "Third Battle of Kharkov": "第三次哈尔科夫战役",
    "Kursk Offensive": "库尔斯克攻势",
    "Second Battle of Kiev": "第二次基辅战役",
    "Clash at Orsha": "奥尔沙激战",
    "Belarusian Marshes": "白俄罗斯沼泽",
    "Gumbinnen": "贡宾嫩",
    "Siege of Stettin": "斯德丁围城战",
    "Ofensiva de Asturias": "阿斯图里亚斯攻势",
    "Campa de Torres": "托雷斯营地",
    "Puerto de El Musel [PORT]": "埃尔穆塞尔港[港]",
    "Cerro de Sta. Catalina": "圣卡塔利娜高地",
    "Ria de Villaviciosa": "比利亚维西奥萨河口",
    "Ferrocarril": "铁路",
    "Depositos de CAMPSA": "CAMPSA油库",
    "Linea del Sella": "塞利亚防线",
    "Lugo de Llanera": "卢戈德利亚内拉",
    "Lugones": "卢戈内斯",
    "Villar de Huergo": "比利亚尔德韦尔戈",
    "Monte Naranco": "纳兰科山",
    "Corredor de Oviedo (Suministros)": "奥维耶多走廊(补给)",
    "Rio Pilona": "皮洛尼亚河",
    "Sevares": "塞瓦雷斯",
    "La Felguera": "拉费尔格拉",
    "Sama de Langreo": "萨马德兰格雷奥",
    "San Martin del Rey Aurelio": "圣马丁德尔雷阿乌雷利奥",
    "Pola de Laviana": "波拉德拉维亚纳",
    "Rio Caudal": "考达尔河",
    "Rio Aller": "阿耶尔河",
    "Aller": "阿耶尔",
    "Estacion de Ujo": "乌霍车站",
    "Minas": "矿区",
    "Ujo": "乌霍",
    "2 Ban FET/1 Bda.": "长枪党第2旗队/第1旅",
    "5 Tab./4 Bda.": "第5塔博尔/第4旅",
    "B Melilla/4 Bda.": "梅利利亚营/第4旅",
    "Las Navas/4 Bda.": "拉斯纳瓦斯/第4旅",
    "1 Flandes/4 Bda.": "第1弗兰德斯/第4旅",
    "2 Flandes/4 Bda.": "第2弗兰德斯/第4旅",
    "6 San Marcial/4 Bda.": "第6圣马西亚尔/第4旅",
    "4 Bailen/4 Bda.": "第4巴伊伦/第4旅",
    "5 Victoria/4 Bda.": "第5维多利亚/第4旅",
    "3 Sicilia/4 Bda.": "第3西西里/第4旅",
    "8 Alava/4 Bda.": "第8阿拉瓦/第4旅",
    "2 Cen. Alava/4 Bda.": "第2阿拉瓦中央/第4旅",
    "T.Virgen Blanca/4 Bda.": "比尔亨布兰卡军团/第4旅",
    "Arapiles/2 Bda.": "阿拉皮莱斯/第2旅",
    "4 Ban./2 Bda.": "第4旗队/第2旅",
    "Ter. S.Miguel/2 Bda.": "圣米格尔军团/第2旅",
    "Ter. S.Ig.de Loyola/2 Bda.": "圣依纳爵·德·罗耀拉军团/第2旅",
    "N.S. del Camino/2 Bda.": "卡米诺圣母/第2旅",
    "1 Ban./2 Bda.": "第1旗队/第2旅",
    "2 Ban./2 Bda.": "第2旗队/第2旅",
    "2 San Marcial/3 Bda.": "第2圣马西亚尔/第3旅",
    "6 America/3 Bda.": "第6美洲/第3旅",
    "8 America/3 Bda.": "第8美洲/第3旅",
    "N.S. Begona/3 Bda.": "贝戈尼亚圣母/第3旅",
    "Ter. Oriamendi/3 Bda.": "奥里亚门迪军团/第3旅",
    "Ter. Zumalacarregui/3 Bda.": "苏马拉卡雷吉军团/第3旅",
    "(Nat. Airfield, out of the map)": "(国民军机场,地图外)",
    "''Ciriza''": "''西里萨''",
    "Jose Luis Diez": "何塞·路易斯·迪亚斯",
    "2 BM Movil/61 Div./[XVII]": "第2机动营/第61师/[XVII]",
    "1 BM Movil/61 Div./[XVII]": "第1机动营/第61师/[XVII]",
    "Batalla del Ebro": "埃布罗河战役",
    "Puesto de Mando": "指挥所",
    "Bon. Especial/[XV]": "特别营/[XV]",
    "Algiers harbour": "阿尔及尔港",
    "Spanish Fanatics": "西班牙狂热分子",
}
CEM = "/[东方集团军群]"
for _s, _d in [
    ("4 Ban./13 ID", "第4旗队"), ("6 Tabor Melilla/13 ID", "第6梅利利亚塔博尔"),
    ("4 Ban. Castilla/13 ID", "第4卡斯蒂利亚旗队"), ("1 Tabor Melilla/13 ID", "第1梅利利亚塔博尔"),
    ("6 Ban./13 ID", "第6旗队"), ("Ifni Btn./13 ID", "伊夫尼营"),
]:
    SV[_s + "/[CEM]"] = _d + "/第13步兵师" + CEM
for _s, _d in [
    ("1 Btn. de Palma", "第1帕尔马营"), ("7 Btn. S.Quintin", "第7圣金廷营"),
    ("184 Btn. Argel", "第184阿尔及尔营"), ("285 Btn. Tenerife", "第285特内里费营"),
    ("1 Ban. Soria", "第1索里亚旗队"), ("2 Ban. Burgos", "第2布尔戈斯旗队"),
]:
    SV[_s + "/4 ID/[CEM]"] = _d + "/第4步兵师" + CEM
for _s, _d in [
    ("12 Bon. Bailen 24", "第12巴伊伦营 第24"), ("19 Bon. Zamora 29", "第19萨莫拉营 第29"),
    ("7 Bon. Arapiles 7", "第7阿拉皮莱斯营 第7"), ("5 Bon. Flandes 5", "第5弗兰德斯营 第5"),
    ("7 Bon Valladolid 20", "第7巴利亚多利德营 第20"), ("17 Bon. Burgos 31", "第17布尔戈斯营 第31"),
    ("4 Bon. Gerona 18", "第4赫罗纳营 第18"), ("17 Bon. Merida 35", "第17梅里达营 第35"),
]:
    SV[_s + "/50 ID/[CEM]"] = _d + "/第50步兵师" + CEM
SV["18 Ban./50 ID/[CEM]"] = "第18旗队/第50步兵师" + CEM
SV["7 Ban./1 Div./[CEM]"] = "第7旗队/第1师" + CEM
SV["5 Ban./1 Div./[CEM]"] = "第5旗队/第1师" + CEM
for _s, _d in [
    ("1 Tetuan 1", "第1得土安 第1"), ("7 Larache 4", "第7拉腊什 第4"),
    ("5 Ceuta 3", "第5休达 第3"), ("5 Alhucemas 5", "第5阿卢塞马斯 第5"),
]:
    SV[_s + "/1 Div./[CEM]"] = _d + "/第1师" + CEM
for _s, _d in [
    ("2 Ban. Castilla", "第2卡斯蒂利亚旗队"), ("2 Ban. Navarra", "第2纳瓦拉旗队"),
    ("5 Ban. Navarra", "第5纳瓦拉旗队"), ("T. Lacar", "拉卡尔军团"),
    ("T. Montejurra", "蒙特胡拉军团"), ("8 America 23", "第8美洲 第23"),
]:
    SV[_s + "/1 Div./[CEM]"] = _d + "/第1师" + CEM
OV.update(SV)


def clean(s):
    for a, b in TOK:
        s = re.sub(r"(?<![A-Za-z])" + re.escape(a) + r"(?![A-Za-z])", b, s)
    s = s.replace("Gp10", "群第10")
    s = re.sub(r"(?<=[\u4e00-\u9fff]) ", "", s)
    s = re.sub(r"(?<=\d) (?=[\u4e00-\u9fff])", "", s)
    return s.strip()


rows = open(SRC, encoding="utf-8", newline="").read().split("\r\n")
rows = [r for r in rows if r != ""]
assert rows[0] == "src\tdraft\tfreq\tresid", rows[0]
rows = rows[1:]
print("输入行数:", len(rows))

out = []
for r in rows:
    cols = r.split("\t")
    src, draft = cols[0], cols[1]
    if src in OV:
        out.append((src, OV[src]))
    else:
        out.append((src, clean(draft)))

with open(DST, "w", encoding="utf-8", newline="") as f:
    for s, d in out:
        f.write(s + "\t" + d + "\r\n")
print("输出行数:", len(out))
