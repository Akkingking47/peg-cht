# -*- coding: utf-8 -*-
r"""生成 KAISER 根级两份输入：
  `root-words.tsv`   —— 词级表（token \t 中文），来源＝4 份子代理分片，去误译项 + 覆写
  `root-manual.tsv`  —— 整行人工表（file \t src \t dst），nations / strings_efile / equip 特例

用法: python make_kaiser_root_manual.py
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))

# ── 1. 词表：合并 4 份分片 ───────────────────────────────────────────
DROP = {
    # 这些 token 造成「词序/语义错位」，改为整行人工表处理
    "Powers", "Char", "Life", "Safari", "Cai", "Carrier", "Plane",
    "Sub", "Watch", "Hopper", "Camp", "Battle",
}
OVERRIDE = {
    "Guides": "向导兵",
}

# 国别/限定形容词 + 长尾通名（子代理未覆盖或需统一）
EXTRA_WORDS = {
    # 国别/民族（作限定词）
    "Bedouin": "贝都因", "Bedouins": "贝都因", "Mahdist": "马赫迪", "Ansar": "安萨尔",
    "Hadendoa": "哈登多阿", "Afghan": "阿富汗", "Sikh": "锡克", "Bengal": "孟加拉",
    "Bombay": "孟买", "Natal": "纳塔尔", "Sudanese": "苏丹", "Canadian": "加拿大",
    "Can.": "加拿大", "Aus.": "澳大利亚", "Aust.": "澳大利亚", "Australian": "澳大利亚",
    "N.Z.": "新西兰", "S. African": "南非", "E. African": "东非", "African": "非洲",
    "Indian": "印度", "Royal": "皇家", "Provincial": "省属", "Colored": "有色人种",
    "Asian": "亚洲", "Tribal": "部落", "Native": "土著", "Light": "轻型",
    "Imperiale": "帝国", "Kraljeva": "皇家", "Akademische": "学院", "Albanian": "阿尔巴尼亚",
    "Albanische": "阿尔巴尼亚", "Jewish": "犹太", "Bulgarian": "保加利亚",
    "Swedish": "瑞典", "Herero": "赫雷罗", "Maji-Maji": "马吉马吉", "Egyptian": "埃及",
    "Beiyang": "北洋", "Xinjun": "新军", "Kansu": "甘肃", "Manchu": "满洲",
    "Mongol": "蒙古", "Town": "城镇", "Camel": "骆驼", "Pack": "驮运",
    "Mine": "水雷", "Submarine": "潜艇", "Fin.": "芬兰", "Est.": "爱沙尼亚",
    # 长尾通名
    "Extranjeros": "外籍", "Bronce": "青铜", "Soma": "驮运", "Pied": "徒步",
    "Linea": "线列", "Ligne": "线列", "Alay": "团", "Alayri": "团", "Hücum": "突击",
    "Yerlesik": "驻防", "Kitoku": "机动", "Hei": "兵", "Sangaku": "山地",
    "Tetsudo": "铁道", "Tawa": "塔", "Baei": "防卫", "Jitensha": "自行车",
    "Sztabowa": "参谋", "Armii": "军", "Chorofylaki": "宪兵", "Kebur": "皇家",
    "Zabagna": "卫队", "Yekegnt": "侦察", "Feresegna": "骑兵", "Deldey": "桥梁",
    "Agenagn": "部队", "Mehandisoch": "工兵", "Wagon": "马车",
    # 第二批：民族/兵种/长尾名词（子代理因冷僻未收，此处据史料定）
    "Angry": "愤怒的", "Mob": "暴民", "Arab": "阿拉伯", "Araplar": "阿拉伯人",
    "Zealot": "狂战士", "Askari": "阿斯卡里", "Bedeviler": "贝都因人",
    "Bolshevik": "布尔什维克", "Bosniaken": "波斯尼亚人", "Boxer": "义和团",
    "Burghers": "市民兵", "Chieftains": "酋长", "Druzina": "民团", "Drujini": "民团",
    "Eastern": "东部", "Civilians": "平民", "Estonians": "爱沙尼亚人",
    "Fedayi": "费达伊", "Feres": "骑兵", "Finns": "芬兰人", "Finsky": "芬兰",
    "Slaves": "奴隶", "Freed": "获释", "Freischar": "自由军团", "Gurkhas": "廓尔喀兵",
    "Hajduci": "海杜克", "Yeomanry": "义勇骑兵", "Service": "勤务队",
    "Irish": "爱尔兰", "Bde.": "旅", "Iron": "铁", "Jugoslovenske": "南斯拉夫",
    "Katanga": "加丹加", "Katipuneros": "卡蒂普南", "Komiti": "科米塔吉",
    "Laager": "车阵", "Lanceiros": "枪骑兵", "Loopgrawe": "战壕", "Lovak": "马",
    "Merchant": "商船", "Vessel": "船只", "Misir": "埃及", "Moros": "摩洛人",
    "Motocyklisticky": "摩托兵", "Mototsikly": "摩托车", "Muhafiz": "守备队",
    "Mujahedeen": "圣战者", "Mujahedeens": "圣战者", "Oudayas": "乌达雅",
    "Partidas": "游击队", "Pipers": "风笛手", "Poles": "波兰人",
    "Politofylaki": "宪兵", "Purgoni": "塔楼", "Ranchers": "牧场主",
    "Reservny": "预备", "Rezervistai": "预备役", "Road": "道路", "Block": "路障",
    "Seressaner": "塞雷萨纳", "Shipwreck": "沉船", "Shturmovoy": "突击",
    "Shturmovoi": "突击", "Sichovy": "西奇", "Skerpskutters": "狙击手",
    "Sosakutai": "侦察队", "Spahis": "斯帕希骑兵", "Spartakisten": "斯巴达克团",
    "Stabs": "参谋部", "Statek": "船只", "Uzbrojony": "武装",
    "Straznica": "边防哨所", "Suksi": "滑雪板", "Swaar": "重型", "Wa": "马车",
    "Synozhupannyki": "蓝袍兵", "Sirozhupannyki": "灰袍兵",
    "Szállítóoszlop": "运输纵队", "Sorkatona": "民兵", "Taxi": "出租车",
    "Tercios": "步兵团", "Vascongados": "巴斯克", "Trocha": "封锁线",
    "Turkestansky": "突厥斯坦", "Tinclad": "铁甲舰", "Union": "联邦",
    "Vadász": "猎兵", "Vagoni": "车厢", "Vapor": "蒸汽船", "Vedur": "机车",
    "Veld": "野战", "Opdrag": "指挥部", "Versorgungslager": "补给仓库",
    "Vezumnieks": "班长", "Vezérkar": "总参谋部", "Volksmarine": "人民海军",
    "Volkswehr": "人民卫队", "Wacht": "哨兵", "Western": "西部",
    "Yilderim": "伊尔迪里姆", "Zeleni": "绿色", "Kadar": "干部", "Zeribah": "栅栏",
    "Zhandarmsky": "宪兵", "Zuavi": "佐阿夫兵", "Zuavos": "佐阿夫兵",
    "Zuhaf": "佐阿夫", "Zulu": "祖鲁", "Chest": "胸", "Horns": "犄角", "Loins": "腰部",
    "Zwiad": "侦察", "Rowerowy": "自行车", "Çerkezce": "切尔克斯", "Áloga": "骑乘",
    "Schutztruppe": "殖民部队", "Algaja": "新兵", "Armiansky": "亚美尼亚",
    "Basibozuk": "巴希布祖克", "Bitsikli": "自行车兵", "Cetnici": "切特尼克",
    "Chobutsu-Sha": "装甲车", "Dashnaktsakanner": "达什纳克", "Daglari": "山地",
    "Donskiye": "顿河", "Kazaky": "哥萨克", "Frivilligkaaren": "志愿军",
    "Führung": "指挥", "Shtabshi": "参谋部", "Gari": "车辆", "Garibaldini": "加里波第派",
    "Hemionikon": "半连", "Hretasayl": "骑兵", "Hulan": "枪骑兵", "Inorodtsy": "异族人",
    "Iunkerebi": "士官", "Kasha": "车辆", "Sokosha": "装甲车", "Kegresse": "凯格雷斯",
    "Kirasiry": "胸甲骑兵", "Kocar": "马车", "Kola": "车", "Milliye": "民族军",
    "Küsten": "海岸", "Militseisky": "民兵", "Periskopmast": "潜望镜桅",
    "Plastunsky": "普拉斯通", "Odbrana": "防线", "Poslednja": "最后",
    "Raitininkai": "骑兵", "Raut.": "铁道", "Sapieru": "工兵", "Dalas": "部队",
    "Sargyba": "哨兵", "Sasazghvro": "边防", "Jarebi": "军", "Sibirskiye": "西伯利亚",
    "Kavkazskiye": "高加索", "Skopiá": "狙击手", "Tyaha": "炮兵", "Vazhka": "重型",
    "Vol.": "志愿军", "Ouest": "西部", "Kuperjanow": "库佩尔亚诺夫",
    # 第三批：奥匈/波兰/匈牙利/格鲁吉亚等小语种长尾
    "Kaiserschützen": "皇帝射手", "Landesschützen": "州射手",
    "Kartuli": "格鲁吉亚", "Legioni": "军团", "Kuruma": "车",
    "Laka": "轻便", "Zaprega": "马车", "Szwolezerowie": "轻骑兵",
    "Vörös": "红色", "Örség": "卫队", "Vöröskatona": "红军士兵",
    "Vörössipkás": "红帽兵", "Várõrség": "要塞卫队",
    "Motocyklista": "摩托兵", "Predzvedna": "侦察",
    "Feltkommando": "战地指挥部", "Parancsnokság": "司令部",
    "Partizanu": "游击队", "Platfórma": "平板车", "Platporma": "平板车",
    "Arménienne": "亚美尼亚",
    "Etrangère": "外籍", "Familiy": "家族", "Soujekuskunnat": "民卫队",
    "Masina": "车辆", "Rossiori": "罗西奥里",
}

words = {}
for i in ("01", "02", "03", "04"):
    p = os.path.join(HERE, "_tok_dst_part%02d.txt" % int(i))
    if not os.path.exists(p):
        raise SystemExit("缺分片 " + p)
    for ln in io.open(p, encoding="utf-8", newline="").read().replace("\r\n", "\n").split("\n"):
        if not ln.strip():
            continue
        c = ln.split("\t")
        if len(c) < 2 or not c[0].strip():
            continue
        k, v = c[0].strip(), c[1].strip()
        if k in DROP or not v:
            continue
        words[k] = OVERRIDE.get(k, v)

for _k, _v in EXTRA_WORDS.items():
    words.setdefault(_k, _v)

with io.open(os.path.join(HERE, "root-words.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("token\tdst\n")
    for k in sorted(words):
        f.write("%s\t%s\n" % (k, words[k]))
print("root-words.tsv：%d 条（剔除 %d）" % (len(words), len(DROP)))

# ── 2. 整行人工表 ───────────────────────────────────────────────────
NATIONS = {
    "Abyssinia": "阿比西尼亚", "Afganistan": "阿富汗",
    "Anarchist Ukraine": "无政府主义乌克兰", "Armenia": "亚美尼亚",
    "Austrian Empire": "奥地利帝国", "Austro-Hungarian Empire": "奥匈帝国",
    "Azerbaijan": "阿塞拜疆", "Baden": "巴登", "Bavaria": "巴伐利亚",
    "Boer States": "布尔人国家", "British Empire": "大英帝国",
    "Carlist Spain": "卡洛斯派西班牙", "Central Lithuania": "中立陶宛",
    "Central Powers": "同盟国", "Chinese Revolutionaries": "中国革命党人",
    "Cossack Hosts": "哥萨克军", "Czechoslovak Legion": "捷克斯洛伐克军团",
    "Egypt": "埃及", "Empire of China": "中华帝国", "Empire of Vietnam": "越南帝国",
    "Entente": "协约国", "French Empire": "法兰西帝国", "Garibaldines": "加里波第派",
    "Georgia": "格鲁吉亚", "German Revolutionaries": "德国革命党人",
    "Hannover": "汉诺威", "Indian Nations": "印第安诸部", "Indigenous": "土著",
    "Kingdom of Hungary": "匈牙利王国", "Kingdom of Morocco": "摩洛哥王国",
    "Kingdom of The Two Sicilies": "两西西里王国", "Mexican Empire": "墨西哥帝国",
    "Montenegro": "黑山", "Neutral": "中立", "Papal States": "教宗国",
    "Piedmont-Sardinia": "皮埃蒙特-撒丁", "Prussia": "普鲁士", "Qing China": "大清",
    "Red China": "赤色中国", "Red Russia": "赤色俄国", "Red Germany": "赤色德国", "Red Hungary": "赤色匈牙利",
    "Republic of China": "中华民国", "Republic of San Marco": "圣马可共和国",
    "Rif": "里夫", "Russian Empire": "俄罗斯帝国", "Russian Green Armies": "俄罗斯绿军",
    "Spain": "西班牙", "Sudan": "苏丹", "Sultanate of Zanzibar": "桑给巴尔苏丹国",
    "Ukraine": "乌克兰", "Union States": "联邦各州", "Württemberg": "符腾堡",
    # 自动译出的半成品（补全）
    "Arab Rebels": "阿拉伯叛军", "Rebels/Revolutionaries": "叛军/革命者",
    "German Freikorps": "德意志自由军团",
    "Mexican Rebels": "墨西哥叛军", "Cuban Rebels": "古巴叛军",
    "Philippine Rebels": "菲律宾叛军",
}

STRINGS = {
    "Auxiliary Ship": "辅助舰", "Central Powers": "同盟国", "Entente": "协约国",
    "Gallop": "疾驰", "Heavy Bomber/Zeppelin": "重型轰炸机/飞艇",
    "Machine Guns": "机枪", "Select Auxiliary Ship": "选择辅助舰",
    "Select Heavy Bomber/Zeppelin": "选择重型轰炸机/飞艇",
    "Select Machine Guns": "选择机枪", "Select Ship of the Line": "选择战列舰",
    "Ship of the Line": "战列舰", "Support Weapons": "支援武器",
    # 半成品补全
    "Heavy Cavalry/Tanks": "重型骑兵/坦克",
    "Light Cavalry/Recon": "轻型骑兵/侦察",
    "Bomber/Scout": "轰炸机/侦察机",
}

EQUIP = {
    # Marine：德语 Marine=海军，英/法 Marine=海军陆战队 ⇒ 逐行定
    "Marine": "海军", "Marine 20": "海军 20", "Marine-ExpdKorps": "海军远征队",
    "7.62mm Maxim Marine": "7.62mm Maxim 海军型",
    # 复合词词序
    "Arm. Sea Transport": "装甲海上运输", "Sea Mines": "水雷",
    "Curtiss 1912 Sea Plane": "Curtiss 1912 水上飞机",
    "Farman MF.11 Sea Plane": "Farman MF.11 水上飞机",
    "Farman MF.7 Sea Plane": "Farman MF.7 水上飞机",
    "Sopwith Gunbus Sea Plane": "Sopwith Gunbus 水上飞机",
    "Hopper Barge": "泥驳", "Tunul de Camp cal.75mm": "75mm 野战炮",
    "Gun Carrier MkI": "火炮载具 MkI", "5\" Gun Carrier MkI": "5\" 火炮载具 MkI",
    "Central Powers": "同盟国",
    "Life Guards": "近卫骑兵", "Life Guards 03": "近卫骑兵 03", "Life Guards 82": "近卫骑兵 82",
    "Guides Infantry": "向导步兵",
    "Mehal Safari": "中央军", "Mehal Safari 17": "中央军 17",
    "Cai Ferate": "铁路", "Cai Ferate 19": "铁路 19",
    "Sub hunter": "反潜舰", "Submerged Sub": "潜航潜艇", "Surfaced Sub": "水面潜艇",
    "Watch Tower": "瞭望塔",
    "Battle Cruiser": "战列巡洋舰", "Light Cruiser": "轻巡洋舰",
    "Auxiliary Cruiser": "辅助巡洋舰",
    "Armored Train": "装甲列车", "Armored Train Guns": "装甲列车炮",
    "Supply Base": "补给基地", "Supply Dump": "补给站",
    "Sail Ship of the Line": "风帆战列舰", "Steam Ship of the Line": "蒸汽战列舰",
    "Sail Frigate": "风帆护卫舰", "Steam Frigate": "蒸汽护卫舰",
    "Sail Corvette": "风帆轻巡航舰", "Steam Corvette": "蒸汽轻巡航舰",
    "Sail Brigantine": "风帆双桅帆船", "Steam Brigantine": "蒸汽双桅帆船",
    "Sail Schooner": "风帆纵帆船", "Steam Schooner": "蒸汽纵帆船",
    "Steam Gunboat": "蒸汽炮艇", "Seaplane Tender": "水上飞机供应舰",
    # 「虚词单位名」——含介词/冠词者整行定译（词级替换会留半截，故不走词表）
    "Infanterie de Ligne": "线列步兵", "Infanterie de Ligne 09": "线列步兵 09",
    "Infanterie de 2.Ligne": "二线步兵", "Infanterie de 2.Ligne 15": "二线步兵 15",
    "Infanterie de Forteresse 15": "要塞步兵 15",
    "Chasseurs de Forteresse": "要塞猎兵", "Grenadiers de Forteresse": "要塞掷弹兵",
    "Carabiniers de Forteresse": "要塞卡宾枪骑兵",
    "Chasseurs a Cheval": "骑马猎兵", "Chasseurs a Cheval 00": "骑马猎兵 00",
    "Chasseurs a Cheval 15": "骑马猎兵 15",
    "Chasseurs à Pied 09": "徒步猎兵 09", "Chasseurs à Pied 15": "徒步猎兵 15",
    "Chasseurs à Pied 00": "徒步猎兵 00",
    "Cavalleria di Linea": "线列骑兵", "Cavalleria di Linea 09": "线列骑兵 09",
    "Cavalleria di Linea 17": "线列骑兵 17",
    "Garde a Cheval": "骑马卫队", "Gendarmerie a Cheval": "骑马宪兵",
    "Muli da Soma": "驮骡", "Muli da Soma 09": "驮骡 09",
    "Explorador a Caballo": "骑马侦察兵", "Explorador a Caballo 12": "骑马侦察兵 12",
    "Explorador a Caballo 95": "骑马侦察兵 95",
    "Caçadores a Cavalo": "骑马猎兵", "Caçadores a Cavalo 17": "骑马猎兵 17",
    "Esploratore a Cavallo": "骑马侦察兵", "Esploratore a Cavallo 09": "骑马侦察兵 09",
    "Esploratore a Cavallo 17": "骑马侦察兵 17",
    "Jäger zu Pferde": "骑马猎兵", "Jaeger zu Pferde": "骑马猎兵",
    "Jäger zu Pferde 10": "骑马猎兵 10",
    "Turn de Garda": "瞭望塔",
    "Torre de Vigilancia": "瞭望塔",
    "Entrincheirado de Infantaria": "据壕步兵",
    "Entrincheirado de Infantaria 17": "据壕步兵 17",
    "Piechota w Okopach": "据壕步兵",
    "Tercio de Extranjeros": "外籍军团",
    "Tropa de Marinería": "水兵部队", "Tropa de Marinería 00": "水兵部队 00",
    "Infantería de Marina 12": "海军陆战队 12",
    "Infantería de Marina 95": "海军陆战队 95",
    "Cazadores de Montaña 12": "山地猎兵 12",
    "Guerrilla a Caballo": "骑马游击队",
    "Revolucionarios a Caballo": "骑马革命军",
    "Partisans de Gers": "热尔游击队",
    "Troupes de Transport": "运输部队", "Troupes de Transport 15": "运输部队 15",
    "Frégate à Voile": "风帆护卫舰", "Corvette à Vapeur": "蒸汽轻巡航舰",
    "Canonnière à Vapeur": "蒸汽炮艇",
    "Fragata de Vela": "风帆护卫舰", "Navío de Vela": "风帆战列舰",
    "Goleta de Vela": "风帆纵帆船", "Bergantín de Vela": "风帆双桅帆船",
    "Corbeta de Vela": "风帆轻巡航舰",
    "Trattore Pavesi Tipo A": "Pavesi A 型牵引车",
    "76.2mm Wagon Artyleryjski Typu I": "76.2mm 炮兵马车 I 型",
    "75mm Wagon Artyleryjski Typu II": "76.2mm 炮兵马车 II 型",
    "149mm Armata wz.A": "149mm 火炮 A 型",
    # 第三批
    "Radio Station": "电台", "Wagón Plataforma": "平板车",
    "Platforma": "平板车", "Platformu": "平板车", "Platvorm": "平板车",
    "Légion Arménienne": "亚美尼亚军团", "Légion Etrangère": "外籍军团",
    "Sultan's Familiy": "苏丹家族", "Sultan's Bodyguard": "苏丹卫队",
    "Kartuli Legioni": "格鲁吉亚军团", "Laka Zaprega": "轻便马车",
    "Vörös Örség": "红色卫队", "Vöröskatona": "红军士兵", "Vörössipkás": "红帽兵",
    "Várõrség": "要塞卫队", "Predzvedna Motocyklista": "摩托侦察兵",
    "Feltkommando": "战地指挥部", "Cavalerie Voorloper": "骑兵前卫",
    "Excelsior Bde.": "埃克塞尔西奥旅", "Irish Bde.": "爱尔兰旅",
    "Irish Transvaal Bde.": "爱尔兰德兰士瓦旅", "Iron Bde.": "铁旅",
    "Vol. de l'Ouest": "西部志愿军", "Vol. Kuperjanow": "库佩尔亚诺夫部队",
    # 罗马尼亚语词序（Munte=山地，须前置）
    "Vanatori Munte": "山地猎兵", "Vanatori Munte 18": "山地猎兵 18",
    "Pioneri Munte": "山地工兵",
}

rows = []
for k, v in NATIONS.items():
    rows.append(("nations.txt", k, v))
for k, v in STRINGS.items():
    rows.append(("strings_efile.txt", k, v))
for k, v in EQUIP.items():
    rows.append(("equip.txt", k, v))

# ── names.txt：8 份子代理音译，按行配对 ─────────────────────────────
_nm = 0
for i in range(1, 9):
    tp = os.path.join(HERE, "_nm_todo_part%02d.txt" % i)
    dp = os.path.join(HERE, "_nm_dst_part%02d.txt" % i)
    src = [l.rstrip("\n") for l in io.open(tp, encoding="utf-8").read().split("\n") if l.strip()]
    dst = [l.rstrip("\n") for l in io.open(dp, encoding="utf-8").read().split("\n") if l.strip()]
    if len(src) != len(dst):
        raise SystemExit("names part%02d 行数不符 %d/%d" % (i, len(src), len(dst)))
    for a, b in zip(src, dst):
        b = b.strip()
        if not b or "\t" in b:
            raise SystemExit("names 译文非法 part%02d: %r -> %r" % (i, a, b))
        rows.append(("names.txt", a.strip(), b))
        _nm += 1
# 子代理个别修正（混排/漏译）
for _k, _v in {"de la Guardia": "德·拉·瓜迪亚"}.items():
    rows.append(("names.txt", _k, _v))
    _nm += 1
print("names.txt 人工条目 %d" % _nm)

with io.open(os.path.join(HERE, "root-manual.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("file\tsrc\tdst\n")
    for a, b, c in rows:
        f.write("%s\t%s\t%s\n" % (a, b, c))
print("root-manual.tsv：%d 条（nations %d / strings %d / equip %d）"
      % (len(rows), len(NATIONS), len(STRINGS), len(EQUIP)))
