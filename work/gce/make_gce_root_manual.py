# -*- coding: utf-8 -*-
r"""生成 GCE 根级人工译表 `root-manual.tsv`（file \t src \t dst）。

口径来源：
  · 装备型号 / 舰级 / 编号 → **保留原文**（POLICY §五；donor 主流：`Akagi Class` 保留、
    AO 少数译「级」不代表主流，COMWW2 已因此剔除学得词 `Class→级`）⇒ 本表写**恒等条目**，
    使 `_pending_*` 报告归零、决定留痕。
  · 通名 / 编制 / 地名 → **译中文**（POLICY §四；GCE POLICY 同）
  · `(Capt.)` → 保留（全库惯例：KAISER/LUPO/OLGWW2/ROI/GCE 原文都用它，donor 差异为 0）
  · names.txt 人名 → 音译（donor 风格：`von Hotzendorff`→冯·霍岑多夫）

用法: python make_gce_root_manual.py   （产出 work\gce\root-manual.tsv）
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- names.txt
NAMES = {
    "Adroher": "阿德罗埃尔", "Aguado": "阿瓜多", "Aguirre": "阿吉雷", "Aguirreche": "阿吉雷切",
    "Aizpuru": "艾斯普鲁", "Alba": "阿尔瓦", "Alberdi": "阿尔贝尔迪", "Alberti": "阿尔贝蒂",
    "Alcázar": "阿尔卡萨尔", "Andrade": "安德拉德", "Ansaldo": "安萨尔多", "Antuña": "安图尼亚",
    "Aparicio": "阿帕里西奥", "Aranaz": "阿拉纳斯", "Arconada": "阿尔科纳达", "Arellano": "阿雷利亚诺",
    "Arenillas": "阿雷尼利亚斯", "Arquer": "阿尔克尔", "Arredondo": "阿雷东多", "Arrese": "阿雷塞",
    "Arámbarri": "阿拉姆巴里", "Arévalo": "阿雷瓦洛", "Ascaso": "阿斯卡索", "Ayerdi": "阿耶尔迪",
    "Azkue": "阿斯库埃", "Aznar": "阿斯纳尔", "Babini": "巴比尼", "Baleztena": "巴莱斯特纳",
    "Balthasar": "巴尔塔萨", "Barbeto": "巴尔贝托", "Barrau": "巴劳", "Barrios": "巴里奥斯",
    "Barrón": "巴龙", "Barwinski": "巴尔温斯基", "Bastico": "巴斯蒂科", "Batet": "巴泰特",
    "Bayo Giroud": "巴约·吉鲁", "Beigbéder": "贝格贝德尔", "Beldarráin": "贝尔达赖恩",
    "Beorlegui": "贝奥雷吉", "Berga": "贝尔加", "Bergonzoli": "贝尔贡佐利", "Bermúdez": "贝尔穆德斯",
    "Bernard": "贝尔纳", "Berthomieu": "贝托米厄", "Berti": "贝尔蒂", "Bertram": "贝特拉姆",
    "Besteiro": "贝斯泰罗", "Bitossi": "比托西", "Boddem": "博德姆", "Bonet": "博内特",
    "Bonomi": "博诺米", "Bonzano": "邦扎诺", "Brachet": "布拉谢", "Bravo": "布拉沃",
    "Brunner": "布伦纳", "Budini": "布迪尼", "Bustundui": "布斯通杜伊", "Butti": "布蒂",
    "Caballero": "卡瓦列罗", "Cabanellas": "卡瓦内利亚斯", "Canals": "卡纳尔斯", "Carreño": "卡雷尼奥",
    "Carré": "卡雷", "Castillo": "卡斯蒂略", "Cenni": "琴尼", "Cervantes": "塞万提斯",
    "Chevrier": "舍夫里耶", "Comorera": "科莫雷拉", "Condés": "孔德斯", "Cortés": "科尔特斯",
    "Cristóbal": "克里斯托瓦尔", "D'Amico": "达米科", "Daley": "戴利", "Demme": "德梅",
    "Desconocido": "未知", "Dirlewanger": "迪尔莱万格", "Domínguez": "多明格斯", "Dumont": "迪蒙",
    "Durruti": "杜鲁蒂", "Dávila": "达维拉", "Díaz Ramos": "迪亚斯·拉莫斯",
    "Díaz Tendero": "迪亚斯·滕德罗", "Díaz-Benjumea": "迪亚斯-本胡梅阿", "Díez": "迭斯",
    "Elizalde": "埃利萨尔德", "Ennßlen": "恩斯伦", "Erdozáin": "埃尔多萨因", "Errandonea": "埃兰多内阿",
    "Escobar": "埃斯科瓦尔", "Estartús": "埃斯塔图斯", "Expósito": "埃斯波西托", "Fal Conde": "法尔·孔德",
    "Faraudo": "法拉乌多", "Farina": "法里纳", "Fernández Cuesta": "费尔南德斯·库埃斯塔",
    "Frusci": "弗鲁希", "Fábregas": "法夫雷加斯", "Galarza": "加拉尔萨", "Galicz": "加利奇",
    "Galland": "加兰德", "Galán": "加兰", "Gambara": "甘巴拉", "Gamero": "加梅罗",
    "Gamir Ulibarri": "加米尔·乌利瓦里", "Garcerán": "加尔塞兰", "García Escámez": "加西亚·埃斯卡梅斯",
    "García Oliver": "加西亚·奥利韦尔", "García Sánchez": "加西亚·桑切斯",
    "García Valiño": "加西亚·巴利尼奥", "García Vivancos": "加西亚·比万科斯", "Garfias": "加尔菲亚斯",
    "Garriga": "加里加", "Gaucher": "戈谢", "Germán": "赫尔曼", "Girón": "希龙",
    "González": "冈萨雷斯", "González Gil": "冈萨雷斯·希尔", "González Peña": "冈萨雷斯·佩尼亚",
    "Gorkin": "戈尔金", "Gorricho": "戈里乔", "Guarner": "瓜尔内尔", "Guimpel": "金佩尔",
    "Gómez": "戈麦斯", "Gómez-Jordana": "戈麦斯-霍尔达纳", "Harder": "哈德",
    "Harlinghausen": "哈林豪森", "Hedilla": "埃迪利亚", "Hernández": "埃尔南德斯",
    "Hernández Saravia": "埃尔南德斯·萨拉维亚", "Herrera": "埃雷拉",
    "Herreros de Tejada": "埃雷罗斯·德·特哈达", "Herrmann": "赫尔曼", "Hidalgo": "伊达尔戈",
    "Huarte": "乌阿尔特", "Ibarrola": "伊巴罗拉", "Ibárruri": "伊巴露丽", "Iglesias": "伊格莱西亚斯",
    "Incenti": "因琴蒂", "Irezábal": "伊雷萨瓦尔", "Jiménez": "希门尼斯", "Jover": "霍韦尔",
    "Juliá": "胡利亚", "Jurado": "胡拉多", "Kahle": "卡勒", "Kléber": "克莱贝尔",
    "Kraft": "克拉夫特", "La Ferla": "拉费尔拉", "Labadie": "拉巴迪", "Lacalle": "拉卡列",
    "Lacasa": "拉卡萨", "Larrañaga": "拉腊尼亚加", "Lasarte": "拉萨尔特", "Lazcano": "拉斯卡诺",
    "Ledesma": "莱德斯马", "León": "莱昂", "Llano de la Encomienda": "利亚诺·德·拉·恩科米恩达",
    "Lucchini": "卢基尼", "Luckacs": "卢卡奇", "Líster": "利斯特",
    "López Bonaechea": "洛佩斯·博纳埃切阿", "López Iglesias": "洛佩斯·伊格莱西亚斯",
    "Lützow": "吕措", "Mantelli": "曼泰利", "Manzana": "曼萨纳", "Marchal": "马沙尔",
    "Mares": "马雷斯", "Marty": "马蒂", "Martí": "马蒂", "Masó": "马索", "Maurín": "毛林",
    "Mazón": "马松", "Mehnert": "梅纳特", "Menéndez": "梅嫩德斯", "Mera": "梅拉",
    "Merino": "梅里诺", "Merriman": "梅里曼", "Miaja": "米亚哈", "Michelini": "米凯利尼",
    "Millán Astray": "米连·阿斯特赖", "Miranda": "米兰达", "Molins": "莫林斯",
    "Monarca": "莫纳尔卡", "Monasterio": "莫纳斯特里奥", "Montaud": "蒙托",
    "Morquillas": "莫尔基利亚斯", "Moscardó": "莫斯卡多", "Mugarza": "穆加尔萨", "Muti": "穆蒂",
    "Muñoz Grandes": "穆尼奥斯·格兰德斯", "Mölders": "默尔德斯", "Nathan": "纳坦",
    "Navarro": "纳瓦罗", "Negrín": "内格林", "Neudörffer": "诺伊德尔费", "Neves": "内维斯",
    "Nin": "宁", "Nobili": "诺比利", "Núñez Maza": "努涅斯·马萨",
    "Núñez de Prado": "努涅斯·德·普拉多", "Oesau": "厄绍", "Oltra": "奥尔特拉",
    "Orbegozo": "奥尔贝戈索", "Ordóñez": "奥尔多涅斯", "Ortega": "奥尔特加",
    "Ortiz Ramírez": "奥尔蒂斯·拉米雷斯", "Ozcoidi": "奥斯库伊迪", "Pacciardi": "帕恰尔迪",
    "Pace": "帕切", "Palacio": "帕拉西奥", "Paladino": "帕拉迪诺", "Pallach": "帕利亚奇",
    "Pascual": "帕斯夸尔", "Pañeda": "帕涅达", "Pellicer": "佩利塞尔", "Perea": "佩雷亚",
    "Pignatelli": "皮尼亚泰利", "Planelles": "普拉内列斯", "Pozas": "波萨斯", "Prada": "普拉达",
    "Prados": "普拉多斯", "Prieto": "普列托", "Primo de Rivera": "普里莫·德·里维拉",
    "Prudent": "普吕当", "Puccini": "普契尼", "Puente": "普恩特", "Putz": "普茨",
    "Pérez": "佩雷斯", "Pérez Farras": "佩雷斯·法拉斯", "Pérez Garmendia": "佩雷斯·加门迪亚",
    "Rago": "拉戈", "Rebull": "雷布尔", "Redondo": "雷东多", "Rejano": "雷哈诺",
    "Renau": "雷瑙", "Renn": "伦", "Riaño": "里亚尼奥", "Ricci": "里奇",
    "Ridruejo": "里德鲁埃霍", "Rionda": "里翁达", "Rivas": "里瓦斯", "Roatta": "罗阿塔",
    "Roca": "罗卡", "Roces": "罗塞斯", "Rodilla": "罗迪利亚", "Rodríguez": "罗德里格斯",
    "Rodríguez Vega": "罗德里格斯·维加", "Rojo": "罗霍", "Romagnoli": "罗马尼奥利",
    "Rosa": "罗萨", "Rovira": "罗维拉", "Ruano": "鲁阿诺", "Ruiz de Alda": "鲁伊斯·德·阿尔达",
    "Runze": "伦策", "Russo": "鲁索", "Sagnier": "萨格尼尔",
    "Salas Larrazábal": "萨拉斯·拉拉萨瓦尔", "Saliquet": "萨利凯特", "Santana": "桑塔纳",
    "Sanz": "桑斯", "Saseta": "萨塞塔", "Schellmann": "舍尔曼", "Schlichting": "施利希廷",
    "Schweikard": "施韦卡尔德", "Seiler": "塞勒", "Serrano Súñer": "塞拉诺·苏涅尔",
    "Solano": "索拉诺", "Solchaga": "索尔查加", "Sotomayor": "索托马约尔", "Sperrle": "施佩勒",
    "Staimler": "施泰姆勒", "Stern": "斯特恩", "Stomatov": "斯托马托夫", "Stärcke": "施泰尔克",
    "Sáenz de Buruaga": "萨恩斯·德·布鲁阿加", "Sáinz": "萨因斯",
    "Sánchez Mazas": "桑切斯·马萨斯", "Sánchez Mora": "桑切斯·莫拉", "Tagüeña": "塔格尼亚",
    "Toral": "托拉尔", "Trautloft": "特劳特洛夫特", "Trelles": "特雷列斯", "Trettner": "特雷特纳",
    "Ulanovski": "乌兰诺夫斯基", "Urtizberea": "乌尔蒂斯贝雷阿", "Utrilla": "乌特里利亚",
    "Val": "巴尔", "Valdés": "巴尔德斯", "Vallejo": "巴列霍", "Varela": "巴雷拉",
    "Vega": "维加", "Vidal Munárriz": "比达尔·穆纳里斯", "Vidal y Planas": "比达尔-伊-普拉纳斯",
    "Vidali": "维达利", "Vidiella": "比迭利亚", "Vigón": "比贡", "Vila": "比拉",
    "Vilas": "比拉斯", "Villanova": "比利亚诺瓦", "Volkmann": "福尔克曼",
    "Wintringham": "温特林厄姆", "Wolff": "沃尔夫", "Yagüe": "亚圭", "Yoldi": "约尔迪",
    "Zaisser": "蔡塞尔", "Zarauza": "萨劳萨", "de Gracia": "德·格拉西亚",
    "de Lizarza": "德·利萨尔萨", "de Rada": "德·拉达", "de Rosa": "德·罗萨",
    "de Souza": "德·索萨", "de Tella": "德·特利亚", "del Burgo": "德尔·布尔戈",
    "del Rosal": "德尔·罗萨尔", "von Kessel": "冯·凯塞尔", "von Moreau": "冯·莫罗",
    "von Richthoffen": "冯·里希特霍芬", "von Thoma": "冯·托马", "Álvarez": "阿尔瓦雷斯",
}

# ---------------------------------------------------------------- nations.txt
NATIONS = {
    # 阵营（Sides）
    "Nacionales": "国民派", "Republicanos": "共和派", "Neutrales": "中立国",
    # 派系 / 组织（POLICY §五：政党/工会专有缩写保留原文）
    "CNT-FAI": "CNT-FAI", "POUM": "POUM",
    "Euzko Gudarostea": "巴斯克军",
    "Milicias Socialistas": "社会主义民兵",
    "Brigadas Internacionales": "国际纵队",
    "Tercios Requetés": "卡洛斯派军团",
    "Milicias Falange": "长枪党民兵",
    "Legion Condor": "秃鹰军团",
    "Milicias Comunistas": "共产主义民兵",
    "Corpo Truppe Volontarie": "意大利志愿军团",
    "Sin Usar": "未使用",
    # 国家 / 军队
    "Francia": "法国", "Gran Bretaña": "英国", "Portugal": "葡萄牙",
    "Ejército Nacional": "国民军", "Ejército Popular": "人民军",
}

# ---------------------------------------------------------------- strings_efile.txt
STRINGS = {
    # [sides]（会覆盖 nations.txt 的阵营名 ⇒ 与之一致）
    "Nationalists": "国民军", "Republicans": "共和军",
    # [classes]
    "Inf. Support": "步兵支援", "Not Used": "未使用",
    # [requisition]
    "Select Inf. Support": "选择步兵支援", "Select Not Used": "选择未使用",
    # 注释行（引擎跳过；与 donor 一致：原样保留）
    "*  add [movement2] section": "*  add [movement2] section",
    "*  to customize CUSTOM movement method...": "*  to customize CUSTOM movement method...",
    "*Custom movement": "*Custom movement",
    "*[movement2]": "*[movement2]",
}

# ---------------------------------------------------------------- equip.txt
EQUIP = {
    # —— 通名 / 编制（POLICY §四：必须译，不得音译）——
    "Aeródromo": "机场", "Alambrada": "铁丝网", "Automobile": "汽车", "Barricada": "街垒",
    "Base Logística": "后勤基地", "Batallón Castigo": "惩戒营",
    'Batería Costera de 12"': '12 英寸海岸炮台', 'Batería Costera de 4"': '4 英寸海岸炮台',
    'Batería Costera de 6"': '6 英寸海岸炮台', 'Batería Costera de 8"': '8 英寸海岸炮台',
    "Blocao": "碉堡", "Brigadists": "国际纵队战士", "Buque Mercante": "商船",
    "Búnker": "地堡", "Búnker Ametralladora": "机枪地堡",
    "Búnker Artillería Ligera": "轻型炮兵地堡", "Búnker Artillería Pesada": "重型炮兵地堡",
    "Búnker CC": "反坦克地堡", "Búnker CC Pesado": "重型反坦克地堡",
    "Búnker de Mando": "指挥地堡", "Búnker de Observación": "观察地堡",
    "Camicie Nere": "黑衫军", "Camión Blindado": "装甲卡车", "Camión Requisado": "征用卡车",
    "Columnas": "纵队", "Edificio Fortificado": "设防建筑", "Entrenched Troops": "据壕部队",
    "Ertzaintza Mot.": "巴斯克警察(摩托化)", "Fortín": "碉堡", "Fábrica": "工厂",
    "Gendarmerie": "宪兵", "Herramienta de Testeo de la AI": "AI 测试工具",
    "Hospital de Campaña": "野战医院", "Locomotora": "机车", "Mando": "指挥部",
    # ⚠️ 词级替换会误伤，逐条钉死（本条已被 人工 覆盖 ⇒ 词级不再参与）：
    #    `FlaK`/`Flak` 是 POLICY §五 明列**必须保留**的大写缩写（donor 主流 ATOMIC 也全保留）；
    #    `Clase General Mola` 是**舰级名**（含人名），整条保留；
    #    `Mot.` 按 donor（OLGWW2 `Mot. Pechota`→摩托化步兵）译「摩托化」。
    "Ertzaintza Mot.": "摩托化巴斯克警察",
    "Bersaglieri Mot.": "摩托化狙击兵",
    "Cab. Regulares": "骑兵 正规军",
    "Cazadores de Montaña": "山地猎兵",
    "Minas AP": "反步兵地雷", "Minas CC": "反坦克地雷", "Minas Marinas": "水雷",
    "Miqueletes-Miñones": "米克勒特斯-米尼奥内斯", "Muli da Soma": "驮骡",
    "Nave di Trasporto": "运输舰", "Nido Ametralladora": "机枪巢",
    "Nido di Mitragliatrice": "机枪巢", "Obstáculo Acuático": "水下障碍",
    "Obstáculos CC": "反坦克障碍", "Puente de Pontones": "浮桥", "Refugiados": "难民",
    "Slot Libre": "空位", "Stato Maggiore": "参谋部", "Submarino Costero": "近海潜艇",
    "Submarino Medio": "中型潜艇", "Submarino Oceánico": "远洋潜艇",
    "Torre de Observación": "观察塔", "Transporte Civil": "民用运输船", "Tren": "列车",
    "Tropa Atrincherada": "据壕部队", "Tropa Marinería": "水兵部队",
    "Truppe Trincerati": "据壕部队", "V Regimiento": "第5团",
    "Vagón Blindado": "装甲车厢", "Vagón Caja": "棚车", "Vagón Plataforma": "平板车",
    # ⚠️ donor「恒等保留」通道漏掉的**普通名词**（donor 自身漏译被当口径继承）——
    #    与 `Miqueletes`/`Muli da Soma` 同类，必须译；`Carriaggi*` 是意语「辎重」通名。
    "Motoristas": "摩托车兵", "Ertzaintza": "巴斯克警察", "Auto": "汽车",
    "Bicicletta": "自行车", "Carriaggi": "辎重队",
    "Carriaggi Leggeri": "轻型辎重队", "Carriaggi Pesanti": "重型辎重队",
}

# —— 保留原文（型号 / 舰级 / 编号 / 版本横幅）：写成恒等条目使报告归零、决定留痕 ——
KEEP_EQUIP = [
    "10.5cm leFH18", "105mm Schneider Mle 13", "107mm Meiji 38", "122mm obr 10/30",
    "152mm Putilov obr 09/30", "155mm Schneider M17", "15cm sFH18", "20mm SEMAG",
    "37mm PTP obr 30", "37mm Puteaux Mle 16", "40mm Arellano M33", "40mm Bofors wz.36",
    "45mm PTP obr 32", "7.62mm Maxim-Sokolov 10", "7.62mm mm AA", "7.6cm Erhardt leMW",
    "75mm Arisaka 98", "75mm Schneider M06", "75mm Schneider Pichi", "76.2mm Putilov obr 02/30",
    "76.2mm obr 31", "7mm Hotchkiss AA", "7mm Hotchkiss M14", "81mm Stokes-Brandt",
    "81mm Valero M33", "8mm Breda M37", "8mm Breda M37 CA", "8mm Fiat-Revelli M35",
    "8mm Fiat-Revelli Mod.14", "A-101 Papagayo", "AB 611", "Autocannone da 75/27",
    "BR.20 Cicogna", "Bilbao M.32", "Br.19", "Büssing-NAG", "CANT Z.501 Gabbiano",
    "CANT Z.501 Gaviota", "Ca.310 Libeccio", "Ceirano 50 CM", "Chevrolet 2.5t",
    "Cannone da 105/28", "Cannone da 149/35", "Cannone da 37/45", "Cannone da 47/32",
    "Cannone da 65/17", "Cannone da 75/27", "Cannone da 75/39 CA", "Cannone da 75/46 CA",
    "Cannone-Mitragl da 20/65",
    "Clase Alsedo", "Clase B", "Clase C", "Clase Canarias", "Clase Cervantes", "Clase Cervera",
    "Clase Ceuta", "Clase Churruca", "Clase Císcar", "Clase España", "Clase Jaime I",
    "Clase Lazaga", "Clase Libertad", "Clase Méndez Nuñez", "Clase Navarra",
    "Do 17E Bacalao", "Do 17F", "Do 17F Bacalao", "FA-1", "Fi 156 Storch", "G.50 Freccia",
    "GAZ AA", "GL.32", "He 111B Pedro", "He 112", "He 51 Cadena", "He 59 Zapatones",
    "He 70 Blitz", "He 70 Rayo", "He-51", "Hs 123 Angelito", "I-15 Curtiss (Capt.)",
    "I-152 Super Chato", "I-16 Mosca", "I-16 Rata (Capt.)", "I-16 Super Mosca",
    "Ju 52 Yunker", "Ju 86 Jumo", "Ju 87A Stuka", "Ju 87B Stuka", "Krupp L3H",
    "L3/35 Fiamme", "Me 109B Bertha", "Me 109B Messer", "Me 109C Caesar", "Me 109D Dora",
    "Me 109D Messer", "Me 109E Emil", "Me 109E Messer", "Mortaio da 260/9", "Mortaio da 81/14",
    "Obice da 100/17", "Obice da 149/12", "Paco", "Po 540", "PzKpfw IA Negrillo",
    "PzKpfw IB Negrillo", "R-5 Rasante", "Renault Ft-17", "Ro.37 Lince", "Ro.37 Romeo",
    "SB-2 Katiuska (Capt.)", "SM.79 Savoya", "SM.79 Sparviero", "SM.81 Pipistrello",
    "SM.81 Savoya", "Trubia-Naval", "Trubia-Naval (Capt.)", "UNL-35", "UNL-35 (Capt.)",
    "Error! BYEAR1900  VERSION: GCE Efile v.11/11/13",
    # —— 上一条 Ertzaintza Mot. 已移入 EQUIP（原为「巴斯克警察(摩托化)」）；此处列 FlaK 族 ——
    "8.8cm FlaK18", "2cm Flak30", "3.7cm FlaK18", "7.5cm Flak14", "Clase General Mola",
]


# —— 保留原文（引擎跳过 `*` 注释行；donor 一律不动）：恒等条目使报告归零 ——
KEEP_NATIONS = [
    "* Read carefully before editing!",
    "* Each line can be any lenght, but only first 96 chars will be read",
    "* Emply lines and those starting with * will be skipped.",
    "* Can replace any text but do no change the sequence of lines",
    "* Sides",
    "* Nations",
]


def main():
    rows = []
    for k, v in NAMES.items():
        rows.append(("names.txt", k, v))
    for k, v in NATIONS.items():
        rows.append(("nations.txt", k, v))
    for k in KEEP_NATIONS:
        rows.append(("nations.txt", k, k))
    for k, v in STRINGS.items():
        rows.append(("strings_efile.txt", k, v))
    for k, v in EQUIP.items():
        rows.append(("equip.txt", k, v))
    for k in KEEP_EQUIP:
        rows.append(("equip.txt", k, k))

    # 去重（同 file+src 只留一条）
    seen = set()
    ded = []
    for f, s, d in rows:
        if (f, s) in seen:
            continue
        seen.add((f, s))
        ded.append((f, s, d))

    out = os.path.join(HERE, "root-manual.tsv")
    with io.open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("file\tsrc\tdst\n")
        for f, s, d in ded:
            fh.write("%s\t%s\t%s\n" % (f, s, d))
    from collections import Counter
    c = Counter(f for f, _, _ in ded)
    print("已写 root-manual.tsv：%d 条（%s）" % (len(ded), " · ".join("%s %d" % kv for kv in sorted(c.items()))))


if __name__ == "__main__":
    main()
