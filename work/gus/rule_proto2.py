# -*- coding: utf-8 -*-
"""方案 D 原型 v2：在 v1 的 195 条 token 之上，按「未覆盖 token Top 榜」逐轮补字典，
打印「字典规模 -> 覆盖率」曲线，用来判断方案 D 到底要建多大的表。"""
import rule_proto as R

BATCH2 = {
 # 未覆盖 Top 榜第一批
 "D": "师", "Rifle": "步兵", "B": "营", "ID": "步兵师", "L": "轻装",
 "FA": "野战炮", "G": "近卫", "m": "米", "CA": "军", "PD": "伞兵师",
 "ATb": "反坦克营", "R": "团", "P": "团", "RR": "侦察团", "H": "重型",
 "BP": "步兵旅", "Engb": "工兵营", "DStrzGw": "近卫步兵师", "RB": "步枪旅",
 "New": "新", "KM": "轻机枪", "AA": "防空", "M": "摩托化", "C": "加拿大",
 "St": "强击", "LD": "轻装师", "DCR": "预备装甲师", "N": "北", "Armored": "装甲",
 "US": "美国", "Stalin's": "斯大林的", "Blitz": "闪击", "Line": "防线",
 "PanzReg": "装甲团", "PzArtRgt": "装甲炮兵团", "e": "", "j.": "", "of": "",
 "THE": "", "OF": "", "a": "", "n": "", "de": "", "en": "",
 # 德军补充
 "PzAbt": "装甲营", "PzKorps": "装甲军", "Armee": "集团军", "Korps": "军",
 "Gren": "掷弹兵", "GrenDiv": "掷弹兵师", "Jag": "猎兵", "Jg": "猎兵",
 "GebirgsDiv": "山地师", "Geb": "山地", "Pion": "工兵", "Pi.": "工兵",
 "Nachr": "通信", "Kav": "骑兵", "Schutzen": "摩托化步兵", "Schutz": "摩托化步兵",
 "Fus": "燧发枪", "Radf": "自行车", "Sich": "警卫", "Ers": "补充",
 "Sturm": "突击", "Volks": "国民", "StuG": "突击炮", "Beob": "观测",
 "Schnelle": "快速", "leichte": "轻装", "schwere": "重型",
 # 空军补充
 "KGz.b.V.": "特种轰炸机联队", "Stab": "参谋部", "Flieger": "飞行",
 "Fallschirm": "伞降", "Fsch": "伞降", "Schlacht": "攻击机", "Nacht": "夜间",
 "Zerst": "驱逐", "Erg": "补充",
 # 苏军补充
 "Gv": "近卫", "Gvard": "近卫", "Gwardiejskaja": "近卫", "Diw": "师",
 "Str": "步兵", "Strelk": "步兵", "TankBrig": "坦克旅", "TkBr": "坦克旅",
 "MechKorps": "机械化军", "CavKorps": "骑兵军", "RifleDiv": "步兵师",
 "RifleBrig": "步兵旅", "RifleCorps": "步兵军", "Mortar": "迫击炮",
 "Howitz": "榴弹炮", "Howitzer": "榴弹炮", "Gun": "火炮", "AT": "反坦克",
 "AA": "防空", "AAAbn": "空降", "Airborne": "空降", "P": "团",
 # 波军补充
 "Dyw": "师", "Dywizja": "师", "Pulk": "团", "Pluton": "排", "Szwadron": "中队",
 "Batalion": "营", "Bat": "营", "Samodzielny": "独立", "Wielkopolska": "大波兰",
 "Pomorska": "波莫瑞", "Warszawska": "华沙", "Kawalerii": "骑兵",
 "Piechoty": "步兵", "Artylerii": "炮兵", "Zmotoryzowana": "摩托化",
 "Pancerna": "装甲", "Strzelcow": "步兵", "Lotnictwa": "航空",
 # 英美补充
 "Bde": "旅", "Bn": "营", "Co": "连", "Sqn": "中队", "Squadron": "中队",
 "Regt": "团", "Divs": "师", "LAA": "轻高炮", "HAA": "重高炮",
 "ATk": "反坦克", "Recce": "侦察", "Para": "伞兵", "Cdo": "突击队",
 "Commando": "突击队", "Gds": "近卫", "Hussars": "骠骑兵", "Dragoon": "龙骑兵",
 "Lancers": "枪骑兵", "Rifles": "步枪团", "Highlanders": "高地团",
 "RTR": "皇家坦克团", "RE": "皇家工兵", "RA": "皇家炮兵", "RAC": "皇家装甲兵",
 "AIF": "澳大利亚帝国军", "NZ": "新西兰", "SA": "南非", "Ind": "印度",
 "Natal": "纳塔尔", "Carabineers": "卡宾枪骑兵", "Skinners": "斯金纳",
 "Duke": "公爵", "Edinburgh": "爱丁堡", "Own": "直属", "Marine": "海军陆战队",
 "Assault": "突击", "Beach": "滩头", "Group": "集群", "Force": "部队",
 "Task": "特遣", "Det": "支队", "Base": "基地", "Depot": "补给站",
 # 地名通名补充
 "Point": "角", "Cape": "角", "Mountain": "山", "Mt": "山", "Ridge": "岭",
 "Valley": "谷", "Plain": "平原", "Desert": "沙漠", "Oasis": "绿洲",
 "Road": "路", "Railway": "铁路", "Bridge": "桥", "Bridgehead": "桥头堡",
 "Dock": "船坞", "Docks": "船坞", "Harbour": "港", "Harbor": "港",
 "Quay": "码头", "Pond": "池塘", "Creek": "溪", "Stream": "溪",
 "Wood": "树林", "Woods": "树林", "Park": "公园", "Gardens": "花园",
 "Village": "村", "Town": "镇", "City": "城", "Junction": "枢纽",
 "Crossroads": "十字路口", "Heights": "高地", "Ruin": "废墟", "Ruins": "废墟",
 "Farm": "农场", "Factory": "工厂", "Mine": "矿", "Mines": "矿区",
 "Camp": "营地", "Airbase": "空军基地", "Strip": "跑道", "Field": "机场",
 "Church": "教堂", "Castle": "城堡", "Palace": "宫殿", "Kloster": "修道院",
}


def main():
    R.TOK.update({k: v for k, v in BATCH2.items()})
    print("=== 合并 BATCH2 后 ===")
    R.main()


if __name__ == "__main__":
    main()
