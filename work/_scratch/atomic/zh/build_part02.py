# -*- coding: utf-8 -*-
"""chunk-02 -> part-02.tsv 汉化脚本（严格按 POLICY.md）。

输入：work/atomic/chunks/chunk-02.tsv          （400 行，单列）
输出：work/atomic/zh/part-02.tsv                （原文<TAB>译文，UTF-8 无 BOM，CRLF）

策略（自顶向下，命中即停）：
  L0  整行精确词典（含引号/多段特殊项）
  L1  逐段词典（长键优先，词边界匹配）
  L2  「数字+单位后缀」同段合并 → 第N单位（与 POLICY 示例一致：333 IR→第333步兵团）
  L3  英文序数后缀去除（137th Br→137旅）
  L4  地名分段词典 + 通名后缀
  L5  未命中 → 保留原文
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'chunks', 'chunk-02.tsv')
DST = os.path.join(HERE, 'part-02.tsv')

# ============================================================ L0 整行词典
EXACT = {
    # ---- 德语：NN. Name -> 第NN名（POLICY 口径）----
    '36. Volksgrenadier-Division': '第36国民掷弹兵师',
    '361. Volksgrenadier-Division': '第361国民掷弹兵师',
    '533. Volksgrenadier-Division': '第533国民掷弹兵师',
    '49. Infanterie-Division': '第49步兵师',
    '709. Infanterie-Division': '第709步兵师',
    '711. Infanterie-Division': '第711步兵师',
    '716. Infanterie-Division': '第716步兵师',
    '719. Infanterie-Divison': '第719步兵师',
    '84. Infanterie-Division': '第84步兵师',
    '85. Infanterie-Division': '第85步兵师',
    '89. Infanterie-Division': '第89步兵师',
    '91. Infanterie-Division': '第91步兵师',
    '439th Ost-Batallion': '第439东方营',
    '561. Ost-Battalion': '第561东方营',
    '561. Ost-battalion': '第561东方营',
    '649. Ost-Battalion': '第649东方营',
    '926.Festungsbattalion': '第926要塞营',
    '429.Coastal Battalion': '第429海岸营',
    '455.Frontier Guards': '第455边防警卫队',
    '526.Frontier Guards': '第526边防警卫队',
    # ---- 德/英 机构名（同段内保留原文核心，只译通名）----
    '362.XX/Divisionskommando': '362.XX/师司令部',
    '4.XX/Divisionskommando': '4.XX/师司令部',
    '76.XXX/29.XX/Divisionsstab': '76.XXX/29.XX/师部',
    '362.XX/Field Hospital': '362.XX/野战医院',
    '5.XXXX/Field Hospital': '5.XXXX/野战医院',
    '7.XXXX/Field Hospital': '7.XXXX/野战医院',
    '46.XX/Royal Engineers': '46.XX/皇家工兵',
    '7.XX/Royal Engineers': '7.XX/皇家工兵',
    '8.XXXX/Military Police': '8.XXXX/军事警察',
    '46.XX/201.Bridging Platoon': '46.XX/第201架桥排',
    '7.XXXX/ 540th Engineer Shore III': '7.XXXX/ 第540工兵海岸III',
    '8. XXXX HQ (Montgomery)': '第8集团军群司令部 (蒙哥马利)',
    # ---- 编制（德语）----
    '4./Kriegslazarett 572/5. leD': '4./第572战地医院/5. leD',
    # ---- 编制（英美）----
    '3rd Army': '第3集团军',
    '6th Army': '第6集团军',
    '7th Army': '第7集团军',
    '9th Army': '第9集团军',
    '5th Panzer Army': '第5装甲集团军',
    '6th Panzer Army': '第6装甲集团军',
    '5th Guards Tank Army': '第5近卫坦克集团军',
    '4th Tank Army': '第4坦克集团军',
    '3rd Canadian Division': '第3加拿大师',
    '3rd Division': '第3师',
    '3rd Independent Flamethrowers Rgt.': '第3独立喷火团',
    '3rd/17thParaReg.': '第3/第17伞兵团',
    '3rd/78thDiv.': '第3/第78师',
    '53rdRTR/78thDiv.': '第53RTR/第78师',
    '365th G.a.F': '第365 G.a.F',
    '3rd/CCB/1stUS-ArmD': '第3/CCB/美国第1装甲师',
    '3rdArt/78thDiv.': '第3炮兵/第78师',
    '3rdInf/CCB/1stUS-Arm': '第3步兵/CCB/美国第1集团军',
    'Airrfield  Volkel': '沃尔克尔机场',
    'AA/78thDiv.': '防空/第78师',
    'AT/78thDiv.': '反坦克/第78师',
    'AA/CCB/1stUS-ArmD': '防空/CCB/美国第1装甲师',
    'A/17thLancer/BLADE': 'A/第17枪骑兵/BLADE',
    'A/21stLancer/BLADE': 'A/第21枪骑兵/BLADE',
    'A/571stUS-Airborne': 'A/美国第571空降',
    '67thFighterSqdr./RAF': '第67战斗机中队/皇家空军',
    '70thFighterSqdr./RAF': '第70战斗机中队/皇家空军',
    '81. Squadron/Desert Air Force': '第81中队/沙漠航空队',
    '88th HAA Rgt/8.Army': '第88重高射炮团/第8集团军',
    '64th Medium Rgt/XXX Corps': '第64中型炮兵团/第30军',
    '7th Medium Rgt/XXX Corps': '第7中型炮兵团/第30军',
    '6615.Ranger Force/1.II': '6615.游骑兵部队/1.II',
    '6615.Ranger Force/3.II': '6615.游骑兵部队/3.II',
    '7.XXXX/1.Ranger II': '7.XXXX/1.游骑兵II',
    '7.XXXX/2. Ranger II': '7.XXXX/2. 游骑兵II',
    '7.XXXX/4. Ranger II': '7.XXXX/4. 游骑兵II',
    '9.Bomb/Regia Aero': '9.Bomb/意大利皇家空军',
    '8 BPC': '第8 BPC',
    '5. Schnellbootflotille': '第5鱼雷艇支队',
    '9. Schnellbootflotille': '第9鱼雷艇支队',
    '4.Self-Propelled Artillery Bn': '第4自行火炮营',
    '401 Tactical Fighter Squadron': '第401战术战斗机中队',
    '44th Infantry Division': '第44步兵师',
    '45h Artillery Regiment': '第45炮兵团',
    '45th Infantry Division': '第45步兵师',
    '49th Infantry Division': '第49步兵师',
    '4th Indian Division': '第4印度师',
    '4th Moroccan Tabor': '第4摩洛哥塔博尔',
    '50th Infantry Division': '第50步兵师',
    '51st (Highland) Division': '第51(高地)师',
    '51st Highland Division': '第51高地师',
    '53.Motorcycle Company': '第53摩托车连',
    '505th Parachute Inf.Rg.': '第505伞兵步兵团',
    '506th Heavy Tank Battalion': '第506重型坦克营',
    '506th Tank Batallion': '第506坦克营',
    '509.III Parachute Infantry': '第509伞兵步兵',
    '59th Infantry Division': '第59步兵师',
    '5th Infantry Brigade': '第5步兵旅',
    '5th Parachute Division': '第5伞兵师',
    '6th Airborne Division': '第6空降师',
    '6th Bridge Engineers': '第6架桥工兵',
    '70th Infantry Division': '第70步兵师',
    '751stTank Battalion': '第751坦克营',
    '79th Infantry Division': '第79步兵师',
    '7th Armoured Division': '第7装甲师',
    '7th Royal Tank Regiment': '第7皇家坦克团',
    '82.III Parachute Infantry': '第82伞兵步兵',
    '82nd Airborne Division': '第82空降师',
    '87.Fighter Wing': '第87战斗机联队',
    '57.Bombardment Wing': '第57轰炸机联队',
    '675th Artillery Regiment': '第675炮兵团',
    '894th Tank Destroyer Battalion': '第894坦克歼击营',
    '9th Australian Division': '第9澳大利亚师',
    '9th Infantry Division': '第9步兵师',
    'Airborne Field Command': '空降野战司令部',
    # ---- 地名通名短语 ----
    'Air Force': '空军',
    'Airfields in Tunisia': '突尼斯机场',
    'Airfields in northern Africa': '北非机场',
    'Airfield-Defence': '机场防御',
    'Air battle over Malta': '马耳他空战',
    'Abandoned': '废弃',
    'Abandoned Hospital': '废弃医院',
    'Abandoned Trucks': '废弃卡车',
    'Albertkanaal': '阿尔贝特运河',
    'Aegean Sea': '爱琴海',
    'Alboran Sea': '阿尔沃兰海',
    'Abu Qir Bay': '阿布基尔湾',
    'Albano Lake': '阿尔巴诺湖',
    'Abu Qir Lighthouse': '阿布基尔灯塔',
    'Alexandria Lighthouse': '亚历山大灯塔',
    'A Tablada': '塔布拉达',
    'Algeciras': '阿尔赫西拉斯',
    'Age': '阿格',
    '77th Infantry Rgt "Lupi di Toscana"': '第77步兵团「托斯卡纳之狼」',
    '4ª Divisione Livorno/28.III': '第4利沃诺师/28.III',
    '4ª Divisione Livorno/33.III': '第4利沃诺师/33.III',
    '4ª Divisione Livorno/34.III': '第4利沃诺师/34.III',
    '4ª Divisione Livorno/4.II': '第4利沃诺师/4.II',
    '54ª Divisione Napoli/5.III': '第54那不勒斯师/5.III',
    '54ª Divisione Napoli/54.I': '第54那不勒斯师/54.I',
    '54ª Divisione Napoli/54.II': '第54那不勒斯师/54.II',
    '54ª Divisione Napoli/75.III': '第54那不勒斯师/75.III',
    '54ª Divisione Napoli/76.III': '第54那不勒斯师/76.III',
    '4.XX "Livorno"/28.III': '第4利沃诺军/28.III',
    '4.XX "Livorno"/33.III': '第4利沃诺军/33.III',
    '4.XX "Livorno"/34.III': '第4利沃诺军/34.III',
    '4.XX "Livorno"/Semoventi L40 II': '第4利沃诺军/Semoventi L40 II',
    '4.XX / I,II Gruppo artiglieria': '第4利沃诺军 / 第1、2炮兵群',
    '4.XX / III,IV Gruppo artiglieria': '第4利沃诺军 / 第3、4炮兵群',
    '5.XX/11.X/Highlanders': '5.XX/11.X/高地人',
    '5.XX/11.X/Irish': '5.XX/11.X/爱尔兰人',
    '5.XX/11.X/Perth': '5.XX/11.X/珀斯',
    '3rd/17thParaReg.': '第3/第17伞兵团',
}

# ============================================================ L1 分段词典
# （长键优先；词边界由脚本按 "非字母数字守卫" 判定）
SEG = [
    # ---- 英语编制（复合优先）----
    ('Tactical Fighter Squadron', '战术战斗机中队'),
    ('Bombardment Wing', '轰炸机联队'),
    ('Fighter Squadron', '战斗机中队'),
    ('Fighter Wing', '战斗机联队'),
    ('Tank Destroyer Battalion', '坦克歼击营'),
    ('Heavy Tank Battalion', '重型坦克营'),
    ('Tank Battalion', '坦克营'),
    ('Tank Batallion', '坦克营'),
    ('Artillery Regiment', '炮兵团'),
    ('Parachute Infantry', '伞兵步兵'),
    ('Parachute Inf.Rg.', '伞兵步兵团'),
    ('Parachute Division', '伞兵师'),
    ('Airborne Division', '空降师'),
    ('Armoured Division', '装甲师'),
    ('Canadian Division', '加拿大师'),
    ('Indian Division', '印度师'),
    ('Infantry Division', '步兵师'),
    ('Infantry Brigade', '步兵旅'),
    ('Infantry Rgt', '步兵团'),
    ('Motorcycle Company', '摩托车连'),
    ('Bridge Engineers', '架桥工兵'),
    ('Medium Rgt', '中型炮兵团'),
    ('Highland Division', '高地师'),
    ('Moroccan Tabor', '摩洛哥塔博尔'),
    ('Guards Tank Army', '近卫坦克集团军'),
    ('Panzer Army', '装甲集团军'),
    ('Tank Regiment', '坦克团'),
    ('Desert Air Force', '沙漠航空队'),
    ('Field Hospital', '野战医院'),
    ('Military Police', '军事警察'),
    ('Royal Engineers', '皇家工兵'),
    ('Divisionskommando', '师司令部'),
    ('Divisionsstab', '师部'),
    ('Kriegslazarett', '战地医院'),
    ('Ost-Batallion', '东方营'),
    ('Ost-Battalion', '东方营'),
    ('Ost-battalion', '东方营'),
    ('Festungsbattalion', '要塞营'),
    ('Infanterie-Division', '步兵师'),
    ('Infanterie-Divison', '步兵师'),
    ('Volksgrenadier-Division', '国民掷弹兵师'),
    ('Bridging Platoon', '架桥排'),
    ('Coastal Battalion', '海岸营'),
    ('Frontier Guards', '边防警卫队'),
    ('Tank Army', '坦克集团军'),
    ('Air Force', '空军'),
    ('Field Command', '野战司令部'),
    ('Highlanders', '高地人'),
    ('Irish', '爱尔兰人'),
    ('Perth', '珀斯'),
    # ---- 意/法专名（引号内外同形）----
    ('Bologna', '博洛尼亚'),
    ('Trento', '特伦托'),
    ('Trieste', '的里雅斯特'),
    ('Napoli', '那不勒斯'),
    ('Livorno', '利沃诺'),
    ('Aosta', '奥斯塔'),
    ('Sicilia', '西西里'),
    ('Valtellina', '瓦尔泰利纳'),
    ('Folgore', '福尔戈雷'),
    ('Bersaglieri', '狙击兵'),
    ('Bers.Autoblido', '狙击兵装甲车'),
    ('Bers.', '狙击兵'),
    ('Divisione', '师'),
    ('Gruppo artiglieria', '炮兵群'),
    ('Goumiers Marocains', '摩洛哥古姆'),
    ('Choc Commando', '突击队'),
    ('Choc', '突击'),
    ('Semoventi L40', 'Semoventi L40'),
    # ---- 外语机场前缀（保留前缀原文 + 通名）----
]

# 通名后缀（尾词，允许前置修饰词，如 West Airfield / River Canal）
SUFFIX = [
    ('Airfield', '机场'), ('Airport', '机场'),
    ('Lighthouse', '灯塔'), ('Liman', '潟湖'),
    ('Canal', '运河'), ('River', '河'),
    ('Bay', '湾'), ('Sea', '海'), ('Lake', '湖'),
    ('Airrfield', '机场'),
]

# 方位词（地名前置修饰）
DIRECTION = {'West': '西', 'East': '东', 'North': '北', 'South': '南',
             'Upper': '上', 'Lower': '下', 'New': '新', 'Old': '旧',
             'Great': '大', 'Central': '中', 'North-West': '西北',
             'North-East': '东北', 'South-West': '西南', 'South-East': '东南'}

# ============================================================ L2 单位后缀（可与数字合并）
UNIT = [
    ('Tank Destroyer Battalion', '坦克歼击营'),
    ('Heavy Tank Battalion', '重型坦克营'),
    ('Tank Battalion', '坦克营'),
    ('Tank Batallion', '坦克营'),
    ('Artillery Regiment', '炮兵团'),
    ('Parachute Division', '伞兵师'),
    ('Airborne Division', '空降师'),
    ('Armoured Division', '装甲师'),
    ('Infantry Division', '步兵师'),
    ('Infantry Brigade', '步兵旅'),
    ('Tank Regiment', '坦克团'),
    ('Fighter Wing', '战斗机联队'),
    ('Bombardment Wing', '轰炸机联队'),
    ('Fighter Squadron', '战斗机中队'),
    ('Flamethrowers Rgt.', '喷火团'),
    ('Infantry Rgt', '步兵团'),
    ('Ost-Batallion', '东方营'),
    ('Ost-Battalion', '东方营'),
    ('Ost-battalion', '东方营'),
    ('Festungsbattalion', '要塞营'),
    ('Coastal Battalion', '海岸营'),
    ('Frontier Guards', '边防警卫队'),
    ('Medium Rgt', '中型炮兵团'),
    ('Tank Army', '坦克集团军'),
    ('Panzer Army', '装甲集团军'),
    ('Army', '集团军'),
    ('Corps', '军'),
    ('Division', '师'),
    ('Brigade', '旅'),
    ('Regiment', '团'),
    ('Battalion', '营'),
    ('Batallion', '营'),
    ('Company', '连'),
    ('Platoon', '排'),
    ('Squadron', '中队'),
    ('Wing', '联队'),
]

# ============================================================ L4 地名分段词典（音译）
PLACE = {
    # 埃及 / 中东 / 北非
    'Abu El Matamir': '阿布马塔米尔', 'Abu Hammad': '阿布哈马德',
    'Abu Hummus': '阿布胡穆斯', 'Abu Qir': '阿布基尔', 'Abu Shroff': '阿布舒罗夫',
    'Abu Sir': '阿布西尔', 'Abu Suweir': '阿布苏韦尔',
    'Al Faidiya': '法伊迪耶', 'Al Jabal Akhdar': '绿山',
    'Al Makili': '马基利', 'Al Muaddiyah': '穆阿迪耶', 'Al Qubba': '库巴',
    'Al Tmimi': '泰米米', 'Alam el Dakar': '阿拉姆达卡尔',
    'Ajdabiyah': '艾季达比耶', 'Akerman': '阿克曼',
    # 意大利
    'Acquafondata': '阿夸丰达塔', 'Alife': '阿利费', 'Altavilla': '阿尔塔维拉',
    'Albano Laziale': '阿尔巴诺拉齐亚莱', 'Anagni': '阿纳尼',
    'Comiso': '科米索', 'Lampedusa': '兰佩杜萨', 'Pantelleria': '潘泰莱里亚',
    'Trapani': '特拉帕尼', 'Catania': '卡塔尼亚', 'Palermo': '巴勒莫',
    'Calabria': '卡拉布里亚', 'Reggio di Calabria': '雷焦卡拉布里亚',
    'Fontanarossa': '丰塔纳罗萨', 'Punta Raisi': '蓬塔拉伊西',
    # 法国
    'Ableteuse': '阿布勒特斯', 'Aillette': '艾莱特', 'Aire-sur-la-Lys': '利斯河畔艾尔',
    'Aisne': '埃纳', 'Allemant': '阿勒芒', 'Amifontaine': '阿米丰坦',
    'Aire': '艾尔',
    # 德国 / 奥地利 / 荷兰 / 比利时
    'Ahlhorn': '阿尔霍恩', 'Abanerowo': '阿巴涅罗沃', 'Abbey Wood': '阿比伍德',
    'Abee': '阿贝', 'Abinsk': '阿宾斯克', 'Abram': '阿布拉姆', 'Abramovo': '阿布拉莫沃',
    'Abuls': '阿布尔斯', 'Achuyevo': '阿丘耶沃', 'Adamivka': '阿达米夫卡',
    'Adamovka': '阿达莫夫卡', 'Adinkerke': '阿丁凯尔克', 'Adleri': '阿德列里',
    'Addison': '艾迪生', 'Afips': '阿菲普斯', 'Afipskiy': '阿菲普斯基',
    'Afonasovo': '阿福纳索沃', 'Afonino': '阿福尼诺',
    'Agrafenovka': '阿格拉费诺夫卡', 'Akatovka': '阿卡托夫卡',
    'Akhtanizovskaya': '阿赫塔尼佐夫斯卡亚', 'Akhtyrskiy': '阿赫特尔斯基',
    'Akhtuba': '阿赫图巴', 'Akmashske': '阿克马什斯克',
    'Aksaj Jesaulowskij': '阿克萨伊叶绍洛夫斯基',
    'Aksaj Kurmojarskij': '阿克萨伊库尔莫亚尔斯基',
    'Aksay': '阿克萨伊', 'Aksayskaya': '阿克萨伊斯卡亚',
    'Akulifchi': '阿库利夫奇', 'Aleksandrino': '亚历山德里诺',
    'Aleksandrovka': '亚历山德罗夫卡', 'Aleksandrovskaya': '亚历山德罗夫斯卡亚',
    'Aleksandrovskiy': '亚历山德罗夫斯基', 'Alekseikovo': '阿列克谢伊科沃',
    'Alekseveka': '阿列克谢耶夫卡', 'Alekseyevo-Tuzlovka': '阿列克谢耶沃-图兹洛夫卡',
    'Aleksino': '阿列克西诺', 'Alexandrovka': '亚历山德罗夫卡',
    'Alfarnatejo': '阿尔法纳特霍', 'Alferovo': '阿尔费罗沃', 'Algaida': '阿尔盖达',
    'Aliartos': '阿利亚尔托斯', 'Alimos': '阿利莫斯',
    'Adzhalynskiy': '阿贾雷恩斯基',
    'Akhtanizovskiy': '阿赫塔尼佐夫斯基',
    # 希腊 / 爱琴海 / 地中海
    'Acharnes': '阿哈内斯', 'Afandou': '阿凡杜', 'Agia Kyriaki': '圣基里亚基',
    'Agia Marina': '圣玛丽娜', 'Agioi Theodoroi': '圣塞奥多里',
    'Agios Georgios': '圣乔治奥斯', 'Agriovotanon': '阿格里奥沃塔农',
    'Aidhipsos': '艾迪普索斯', 'Aidonia': '艾多尼亚', 'Aith': '艾斯',
    'Aegina': '埃伊纳', 'Akraifnion': '阿克莱夫尼翁', 'Akrotiri': '阿克罗蒂里',
    'Alcitepe': '阿尔奇特佩', 'Alyki': '阿利基', 'Amigdalokefali': '阿米格达洛克法利',
    'Aeradrom Mhic Easmainn': '埃斯蒙德机场',
    'Aerfort Bhaile Atha Cliath': '都柏林机场',    'Aerfort Chorcai': '科克机场', 'Aerfort Weston': '韦斯顿机场',
    'Cork Airport': '科克机场', 'Aerodrom Militar de Pollenca': '波连萨军用机场',
    'Aerodromo Velez-Malaga': '贝莱斯-马拉加机场',
    'Aerodromo da Achada': '阿沙达机场', 'Lajes Airfield': '拉日什机场',
    'Aerodromo de Son Bonet': '松博内特机场',
    'Aeroport Anapa': '阿纳帕机场', 'Aeroport Cherbourg-Manche': '瑟堡-芒什机场',
    'Aeroport de Caen-Carpiquet': '卡昂-卡尔皮凯机场',
    'Aeroport de Son Sant Joan': '松圣若安机场', 'Aeroport de Tanger': '丹吉尔机场',
    'Aeroporto di Catania-Fontanarossa': '卡塔尼亚-丰塔纳罗萨机场',
    'Aeroporto di Comiso': '科米索机场', 'Aeroporto di Lampedusa': '兰佩杜萨机场',
    'Aeroporto di Palermo-Punta Raisi': '巴勒莫-蓬塔拉伊西机场',
    'Aeroporto di Pantelleria': '潘泰莱里亚机场',
    'Aeroporto di Reggio di Calabria': '雷焦卡拉布里亚机场',
    'Aeroporto di Trapani': '特拉帕尼机场',
    'Airfield Eindhoven': '埃因霍温机场', 'Airfield Gilze am Rhein': '莱茵河畔吉尔泽机场',
    'Airfield Heesch': '海斯赫机场', 'Airfield Volkel': '沃尔克尔机场',
    'Airfield Woensdrecht': '沃尔恩德雷赫特机场',
    'Abeid Amani Karume International Airport': '阿贝德·阿马尼·卡鲁梅国际机场',
    'Aire Canal': '艾尔运河', 'Airon River': '艾龙河', 'Airou River': '艾鲁河',
    'Aa River Canal': '阿河运河', 'Aa River': '阿河',
    'Ages ezers': '阿格斯湖',
    'Aizpute': '艾兹普泰', 'Hasenpoth': '哈森波特',
    'Aidipsos': '艾迪普索斯',
    'Acerno': '阿切尔诺', 'Aiea': '艾亚', 'Aina Haina': '艾纳海纳',
    'Ainsdale': '安斯代尔', 'Akranes': '阿克拉内斯', 'Aksnes': '阿克内斯',
    'Alcudia': '阿尔库迪亚',
}

# 括号内注解通常为别名/说明，若可译则译，不可译则原样保留
PAREN = {
    'Adamovka': '阿达莫夫卡', 'Hasenpoth': '哈森波特', 'Agedabia': '艾季达比耶',
    'Cork Airport': '科克机场', 'Lajes Airfield': '拉日什机场',
    'PORT': '港口',
}

# 词边界守卫：数字后可紧跟字母（7thMediumRgt / 3rdArt），故前置守卫不看数字
GUARD = r'(?<![A-Za-z])%s(?![A-Za-z])'


def seg_replace(text, pairs):
    """按词边界逐段替换（长键优先）。"""
    for k, v in sorted(pairs, key=lambda x: -len(x[0])):
        text = re.sub(GUARD % re.escape(k), v.replace('\\', '\\\\'), text)
    return text


def strip_ordinal(text):
    """去英文序数后缀 / 意葡语 º ª / 法语 -e （POLICY 硬规则 1）。"""
    t = re.sub(r'(\d+)(st|nd|rd|th)(?![A-Za-z])', r'\1', text)
    t = re.sub(r'(\d+)[ºª]', r'\1', t)
    return t


def normalize_punct(text):
    """仅清理机械替换产生的尾随空格；其余空格一律保留。"""
    text = re.sub(r' (?=[/])', '', text)
    return text


def fix_punct(t):
    """恢复原文的空格/逗号布局（机械替换只按词替换，不夹带多余空格）。"""
    t = re.sub(r'[ ]*(/)[ ]*', r'\1', t)          # 斜杠两侧不留空格
    t = re.sub(r', (?=[IVX]+[,.])', ',', t)        # I,II -> I,II
    # 数字/序号 与 中文单位名 之间补一个空格（第7中型炮兵团 -> 第7 中型炮兵团）
    t = re.sub(r'(第[\dA-Za-z]*)([\u4e00-\u9fff])', r'\1 \2', t)
    return t


def translate(line):
    # ---- L0 整行词典 ----
    if line in EXACT:
        return EXACT[line]

    # 纯德文编制/坐标代号：整行保留（非自然语言）
    if re.fullmatch(r'(?:[\dA-Za-z]+\.(?:X{1,4}|I{1,3})(?:/[\dA-Za-z.]+)*)', line):
        return line

    t = line

    # ---- L0b 方位 + 通名（West Airfield / East Canal）----
    for suf, zh in SUFFIX:
        pat = (r'(?<![0-9A-Za-z])(' + '|'.join(DIRECTION) + r')[ ]+'
               + re.escape(suf) + r'(?![A-Za-z])')
        t = re.sub(pat, lambda m: DIRECTION[m.group(1)] + zh, t)

    # ---- L4 地名整段（含多词专名）----
    t = seg_replace(t, [(k, v) for k, v in PLACE.items()])

    # ---- L1 编制/机构分段 ----
    t = seg_replace(t, SEG)

    # ---- L2 数字 + 单位后缀 合并 → 第N单位 ----
    for suf, zh in UNIT:
        pat = r'(?<![0-9A-Za-z])(\d+)(?:st|nd|rd|th)?[ ]?' + re.escape(suf) + r'(?![A-Za-z])'
        t = re.sub(pat, lambda m: '第%s%s' % (m.group(1), zh), t)

    # ---- L2b 通名后缀（前置修饰词一并音译）----
    for suf, zh in SUFFIX:
        pat = (r'(?<![0-9A-Za-z])([A-Z][A-Za-z]*)[ ]+' + re.escape(suf)
               + r'(?![A-Za-z])')
        t = re.sub(pat, lambda m: PLACE.get(m.group(1), m.group(1)) + zh, t)
        t = re.sub(GUARD % re.escape(suf), zh, t)

    # 未音译前缀 + 通名之间不留空格（Adzhalynskiy Liman -> Adzhalynskiy潟湖）
    t = re.sub(r'([A-Za-z])[ ]+(' + '|'.join(zh for _, zh in SUFFIX) + r')',
               r'\1\2', t)
    # 中文专名 + 通名同样不留空格（阿布苏韦尔 Airfield -> 阿布苏韦尔机场）
    t = re.sub(r'([\u4e00-\u9fff])[ ]+(' + '|'.join(zh for _, zh in SUFFIX) + r')',
               r'\1\2', t)
    # ---- L3 去序数后缀 ----
    t = strip_ordinal(t)

    # 括号内别名与主名相同则去重（Aerfort Chorcai (Cork Airport) -> 科克机场）
    def paren_sub(m):
        inner = m.group(1)
        if inner in PAREN:
            return '(' + PAREN[inner] + ')'
        i2 = seg_replace(inner, [(k, v) for k, v in PLACE.items()])
        i2 = seg_replace(i2, SEG)
        if i2 != inner:
            return '(' + i2 + ')'
        return m.group(0)
    t = re.sub(r'\(([^()]*)\)', paren_sub, t)

    # ---- L5 短语清理：多余空格 ----
    t = re.sub(r'\s+', ' ', t)
    t = fix_punct(t)
    return t


def main():
    raw = io.open(SRC, encoding='utf-8', newline='').read()
    lines = raw.split('\r\n')
    if lines and lines[-1] == '':
        lines.pop()
    n_in = len(lines)

    out = [ln + '\t' + translate(ln) for ln in lines]
    io.open(DST, 'w', encoding='utf-8', newline='').write('\r\n'.join(out) + '\r\n')

    # ------------------------- 自检 -------------------------
    b = io.open(DST, 'rb').read()
    print('输入 %d 行 / 输出 %d 行' % (n_in, len(out)))
    print('BOM=%s  CRLF=%d  LF=%d  行尾换行=%s'
          % (b[:3] == b'\xef\xbb\xbf', b.count(b'\r\n'),
             b.count(b'\n'), b.endswith(b'\r\n')))
    bad = 0
    for i, (s, o) in enumerate(zip(lines, out), 1):
        p = o.split('\t')
        if len(p) != 2 or p[0] != s:
            print('  !! 行%d 列对齐异常 %r' % (i, o)); bad += 1; continue
        for ch in '/[]()':
            if p[1].count(ch) != s.count(ch):
                print('  !! 行%d %s 数量不符 [%s] -> [%s]' % (i, ch, s, p[1])); bad += 1
    print('对齐/分隔符异常:', bad)

    kept = [s for s, o in zip(lines, out) if o.split('\t')[1] == s]
    print('整行保留原文: %d 行' % len(kept))
    return kept


if __name__ == '__main__':
    main()
