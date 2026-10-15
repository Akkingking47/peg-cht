# -*- coding: utf-8 -*-
"""
BASEKORP equip.txt 兵种条目翻译（逐词替换，只替换词表内词；型号/载具名保留）
来源清单：work/basekorp/_equip-todo.txt（382 条唯一）
"""
import re

# 词表：(英文词, 中文)，按「长词优先」排序以避免子串误替
WORDS = [
    # --- 组合优先（放最前，避免逐词重复）---
    ("Genio Guastatori", "突击工兵"), ("Genio Alpini", "阿尔卑斯山地工兵"),
    ("Fanteria da Montagna", "山地步兵"), ("Fanteria Motorizzata", "摩托化步兵"),
    ("Infanterie de l'Air", "空降步兵"), ("Infanterie Legere d'Afrique", "非洲轻步兵"),
    ("Infanterie Legere", "轻步兵"), ("Infanterie Mecanisee", "机械化步兵"),
    ("Infanterie Motorisee", "摩托化步兵"), ("Infanterie Alpine", "阿尔卑斯步兵"),
    ("Infanterie Levant", "黎凡特步兵"), ("Infanterie de Marine", "海军步兵"),
    ("de Marine", "海军"), ("de l'Air", "空降"), ("d'Afrique", "非洲"),
    ("da Montagna", "山地"), ("Luftlande-Infanterie", "空降步兵"),
    ("Armoured train", "装甲列车"), ("Mounted Militia", "骑兵民兵"),
    ("Motor Infantry", "摩托化步兵"), ("Glider Infantry", "滑翔机步兵"),
    ("Marine Infantry", "海军陆战队步兵"), ("Armored Infantry", "装甲步兵"),
    ("Armoured Infantry", "装甲步兵"), ("Parachute Infantry", "伞降步兵"),
    ("Mountain Engineer", "山地工兵"), ("Mountain Engineers", "山地工兵"),
    ("Mountain Pioneer", "山土工兵"), ("Combat Engineers", "战斗工兵"),
    ("Airborne Engineers", "空降工兵"), ("Para Engineers", "伞降工兵"),
    ("Light Infantry", "轻步兵"), ("Bicycle Recon", "自行车侦察"),
    ("Cavalerie Colonial", "殖民地骑兵"), ("Colonial Cavalry", "殖民地骑兵"),
    ("Cavalerie Recon", "骑兵侦察"), ("Recon Cavalry", "骑兵侦察"),
    ("Infantry Transport", "步兵运输"), ("Supply Command", "补给司令部"),
    ("Troop Carrier", "部队运输车"), ("Carrier Mortar", "迫击炮运输车"),
    ("Carrier Recon", "侦察运输车"), ("Carrier MMG", "重机枪运输车"),
    ("Fuel Depot", "燃料仓库"),
    # --- 步兵类 ---
    ("Motorizzata", "摩托化"), ("Motorisee", "摩托化"), ("Mecanisee", "机械化"),
    ("Infanterie", "步兵"), ("Infantry", "步兵"), ("Fanteria", "步兵"),
    ("Piechota", "步兵"), ("Jalkavaki", "步兵"), ("Schutzen", "步兵"),
    ("Gornostrelky", "山地步兵"), ("Gorska", "山地步兵"),
    ("Armoured", "装甲"), ("Armored", "装甲"),
    ("Motor", "摩托化"), ("Mechanisee", "机械化"),
    ("Mountagna", "山地"), ("Alpine", "阿尔卑斯"), ("Alpini", "阿尔卑斯山地兵"),
    ("Gebirgsjager", "山地猎兵"), ("Gebirgsjäger", "山地猎兵"),
    ("Mountain", "山地"), ("Jaakari", "猎兵"), ("Jager", "猎兵"),
    ("Legere", "轻装"), ("Lichte", "轻装"), ("Light", "轻装"),
    ("Parachute", "伞降"), ("Paratrooper", "伞兵"), ("Paracadutisti", "伞兵"),
    ("Airborne", "空降"), ("Glider", "滑翔机"), ("Luftlande-Infanterie", "空降步兵"),
    ("SMG", "冲锋枪"), ("MG-Schutzen", "机枪步兵"), ("Ckm", "重机枪"),
    ("Spetsnaz", "特种部队"), ("Commando", "突击队"),
    ("Ghurka", "廓尔喀兵"), ("Scots", "苏格兰"),
    # --- 骑兵 ---
    ("Cavalerie", "骑兵"), ("Cavalry", "骑兵"), ("Kavallerie", "骑兵"),
    ("Mounted", "骑兵"), ("Colonial", "殖民地"),
    # --- 工兵 ---
    ("Engineers", "工兵"), ("Engineer", "工兵"), ("Pioneer", "工兵"),
    ("Sapeurs", "工兵"), ("Genio", "工兵"), ("Guastatori", "突击工兵"),
    ("Bridging", "架桥"), ("Minefield", "雷区"), ("Entrenched", "掘壕"),
    ("Landes-schutzen", "地方防卫军"), ("Landwehr", "地方军"),
    ("Volksturm", "国民突击队"),
    # --- 炮兵/防空 ---
    ("Mortar", "迫击炮"), ("mortar", "迫击炮"),
    ("Artillery", "炮兵"), ("Aty", "炮兵"), ("ATY", "炮兵"),
    ("Antitank", "反坦克"), ("Anti-Tank", "反坦克"),
    ("Flak", "高射炮"),
    # --- 支援/后勤 ---
    ("Limber", "前车"), ("Wagon", "马车"), ("Horse", "马匹"),
    ("Carrier", "运输车"), ("Transport", "运输"),
    ("Bicycle", "自行车"), ("Troop", "部队"),
    ("Supply", "补给"), ("Depot", "仓库"), ("Fuel", "燃料"),
    ("Bunker", "地堡"), ("Fortress", "要塞"), ("Fortificatii", "要塞"),
    ("Fort", "要塞"), ("Mobile", "机动"), ("Regional", "地方"),
    ("Levant", "黎凡特"), ("Garrison", "卫戍部队"),
    ("Reserve", "预备队"), ("Guards", "卫队"), ("Garden", "卫队"),
    ("Regulars", "正规军"), ("Militia", "民兵"), ("Cadre", "骨干"),
    ("Command", "司令部"), ("Support", "支援"), ("support", "支援"),
    ("Recon", "侦察"), ("Scout", "侦察兵"), ("Sniper", "狙击手"),
    ("Marines", "海军陆战队"), ("Marine", "海军陆战队"),
    ("Naval", "海军"), ("Coastal", "海岸"),
    ("Destroyed", "被摧毁"), ("Rockets", "火箭"), ("Rocks", "岩石"),
    ("Heavy", "重型"), ("Flatbed", "平板车"),
    ("Train", "列车"), ("Armoured train", "装甲列车"),
    # --- 国家/部队限定词 ---
    ("Royal", "皇家"), ("KNIL", "荷属东印度"), ("RSI", "意大利社会共和国"),
    ("FFL", "自由法国"), ("FFI", "法国内地军"),
    ("Bersaglieri", "狙击兵"), ("Granatieri", "掷弹兵"),
    # --- 其他 ---
    ("Paramilitary", "准军事部队"), ("Ship", "舰"), ("Mtr", "迫击炮"),
    ("Quad", "四联"), ("Sfl", "自行"), ("AC", "AC"), ("KM", "KM"),
]

# 不参与替换的（型号/缩写/编号）
KEEP = {
    "SS", "MG", "AT", "AA", "AD", "SP", "FJ", "PR", "HQ", "AB", "AK", "BCh",
    "GAZ-AA", "Mtr", "M1", "B-17B", "B-17G", "Crusader", "Staghound",
    "M10", "LC", "DD", "MMG", "AS", "GR", "CR", "AM", "PR", "PSZ",
}

WORDS.sort(key=lambda x: -len(x[0]))

def translate(s):
    out = s
    for en, zh in WORDS:
        # 词边界替换；后面不紧跟数字（避免 Flak38/MG34 被误替）
        pat = re.compile(r'\b' + re.escape(en) + r'\b(?!\d)')
        out = pat.sub(zh, out)
    # (off map) -> （地图外）
    out = re.sub(r'\(\s*off map\s*\)', '（地图外）', out, flags=re.I)
    return out

if __name__ == "__main__":
    todo = [l.rstrip("\n") for l in open("work/basekorp/_equip-todo.txt", encoding="utf-8") if l.strip()]
    for t in todo:
        print(f"{t}\t{translate(t)}")


def build():
    import json, os, sys
    sys.path.insert(0, "work/basekorp")
    GAME = "D:/OpenPG2/EFILE_BASEKORP"
    OUT = GAME + "/TEXT-ZH"
    cm = {}
    for mp in ['work/ao/_equip-crossmap.json', 'work/atomic/_equip-crossmap.json']:
        cm.update(json.load(open(mp, encoding="utf-8")))
    lp = json.load(open('work/basekorp/_olgww2-equip-linepairs.json', encoding='utf-8'))

    def split_keep(text):
        parts = text.split("\n"); out = []
        for p in parts:
            cr = p.endswith("\r"); out.append((p[:-1] if cr else p, cr))
        return out
    def join_keep(rows):
        return "\n".join(c + ("\r" if cr else "") for c, cr in rows)

    src = split_keep(open(f"{GAME}/equip.txt", "rb").read().decode("cp1252"))
    rows = []
    n_word = n_full = n_keep = 0
    for core, cr in src:
        s = core.strip()
        if not s:
            rows.append((core, cr)); continue
        if s in cm:
            rows.append((cm[s], cr)); n_full += 1
        elif s in lp:
            rows.append((lp[s], cr)); n_full += 1
        else:
            zh = translate(s)
            if zh != s:
                rows.append((zh, cr)); n_word += 1
            else:
                rows.append((core, cr)); n_keep += 1      # 型号/载具名保留
    text = join_keep(rows)
    data = text.encode("gbk")
    tmp = OUT + "/equip.txt.new"
    open(tmp, "wb").write(data)
    assert open(tmp, "rb").read() == data
    os.replace(tmp, OUT + "/equip.txt")
    n = sum(1 for r in rows if any(0x4e00 <= ord(c) <= 0x9fff for c in r[0]))
    print(f"equip.txt: {len(rows)} 行, {n} 行含汉字")
    print(f"  整行复用 {n_full} / 词级翻译 {n_word} / 型号保留 {n_keep}")
