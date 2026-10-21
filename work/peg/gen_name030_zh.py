# -*- coding: utf-8 -*-
"""
PeG name030.txt（将领姓名表）中文化生成器
================================================================
格式：`姓   (国家)`   —— 名与国之间为 3 个空格
策略（与 OpenPG 前作"音译"基准的差异）：**能还原汉字的就还原，不音译**
  · 中日韩朝台越  ：按拼音/威妥玛/罗马字/汉越词 **还原汉字**
  · Rebels 组     ：真实历史人物 ⇒ 用**约定俗成中文译名**（秋瑾 / 毛泽东 / 坐牛 / 武元甲…）
  · 其他国家      ：音译（第二批）
未列入表的条目 ⇒ 原样保留（并在未命中清单中列出，便于补译）
"""
import os, re, sys

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


ROOT = WS
SRC = os.path.join(ROOT, r"peg\testbed\backup\name030.txt")
DST = os.path.join(ROOT, r"peg\testbed\name030.txt.zh.txt")

# ---------------- 国家名（与 Gui030 保持术语一致）----------------
COUNTRIES = {
    "United States": "美国", "Russia": "俄罗斯", "China": "中国", "Vietnam": "越南",
    "North Korea": "朝鲜", "South Korea": "韩国", "Thailand": "泰国", "Germany": "德国",
    "United Kingdom": "英国", "France": "法国", "Japan": "日本", "Singapore": "新加坡",
    "Indonesia": "印度尼西亚", "Australia": "澳大利亚", "Mongolia": "蒙古",
    "Taiwan": "中国台湾", "Ukraine": "乌克兰", "Kazakhstan": "哈萨克斯坦",
    "Malaysia": "马来西亚", "United Nations": "联合国", "India": "印度",
    "Pakistan": "巴基斯坦", "Iran": "伊朗", "Israel": "以色列",
    "Arab League": "阿拉伯联盟", "Brazil": "巴西", "Mexico": "墨西哥",
    "Venezuela": "委内瑞拉", "Myanmar": "缅甸", "US Marine Corps": "美国海军陆战队",
    "Rebels": "叛军",
}

# ---------------- 姓名（唯一值 → 中文）----------------
NAMES = {
    # ===== 中国（拼音 / 威妥玛）=====
    "AI": "艾", "AN": "安", "BAI": "白", "CAO": "曹", "CHAI": "柴",
    "CHAN": "陈", "CHÉN": "陈", "CHI": "齐", "CHIANG": "蒋", "CHIN": "秦",
    "CHOW": "周", "CHU": "朱", "CHUNYUAN": "春元", "CONG": "丛", "CUI": "崔",
    "DAI": "戴", "DJANG": "张", "DUAN": "段", "FAN": "范", "FANG": "方",
    "FANQIN": "范钦", "FENG": "冯", "FU": "傅", "GAO": "高", "GE": "葛",
    "GONG": "龚", "GUO": "郭", "HÉ": "何", "HO": "何", "HONGBO": "洪波",
    "HSIAO": "萧", "HSU": "徐", "HU": "胡", "HUA": "华", "HUALING": "华玲",
    "HUÁNG": "黄", "HUANG": "黄", "JIANG": "江", "JIAO": "焦", "JING": "景",
    "KUANG": "邝", "KWAN": "关", "LAI": "赖", "LAM": "林", "LI": "李",
    "LIÁNG": "梁", "LIANLI": "莲丽", "LIN": "林", "LÍN": "林", "LING": "凌",
    "LU": "卢", "MA": "马", "MAO": "毛", "MEI": "梅", "MIAO": "苗",
    "MING": "明", "MINJIE": "敏杰", "NG": "吴", "NI": "倪", "PANG": "庞",
    "SHAO": "邵", "SUN": "孙", "TANG": "唐", "TSAI": "蔡", "TSUNG": "丛",
    "WÁNG": "王", "WANG": "王", "WEI": "魏", "WENYI": "文一", "WONG": "黄",
    "WÚ": "吴", "XIE": "谢", "XÚ": "徐", "YÁNG": "杨", "YEN": "严",
    "YENFEI": "燕飞", "YUAN": "袁", "ZHANG": "张", "ZHÀO": "赵", "ZHU": "朱",
    "ZONG": "宗", "CHOU": "周", "CHEN": "陈",

    # ===== 日本（罗马字 → 汉字）=====
    "AIKAWA": "相川", "ARAI": "新井", "DAIZU": "台津", "EIJI": "英二",
    "FUJITA": "藤田", "HASHIMOTO": "桥本", "HORII": "堀井", "INABE": "稻部",
    "ISHIOKA": "石冈", "IWASE": "岩濑", "JIRO": "次郎", "KAGI": "键",
    "KITAMURA": "北村", "MAKI": "牧", "MIYABE": "宫部", "MIYOKO": "美代子",
    "NAGAHAMA": "长滨", "OGURA": "小仓", "OIKAWA": "及川", "OMORO": "大诸",
    "SHIBATA": "柴田", "SHIMAYA": "岛谷", "TAKESHI": "武", "TANIDA": "谷田",
    "TATSUKICHI": "龙吉", "TSUTANI": "葛谷", "UMEZAKI": "梅崎",
    "WAJIMA": "轮岛", "YAMAGATA": "山形", "YOSHIKANE": "义兼",

    # ===== 韩国 / 朝鲜 =====
    "AHN": "安", "BAK": "朴", "CHAE": "蔡", "CHANG": "张", "CHO": "曹",
    "CHOL": "哲", "CHONG": "郑", "CHOY": "崔", "CHUN": "全", "CHUNG": "郑",
    "HAN": "韩", "HWANG": "黄", "JEONG": "郑", "JEUNG": "郑", "JHON": "全",
    "JIN": "陈", "KANG": "姜", "KOH": "高", "KOO": "具", "KWONG": "权",
    "LEE": "李", "LIM": "林", "MOON": "文", "NAM": "南", "OH": "吴",
    "PARK": "朴", "RAWN": "兰", "SOJU": "苏", "SONG": "宋", "SUNG": "成",
    "WON": "元", "WOO": "禹", "YOON": "尹", "YOUN": "尹", "YUN": "尹",

    # ===== 越南（汉越词 → 汉字）=====
    "BAN": "班", "BINH": "平", "BUI": "裴", "CHAU": "周", "CUNG": "宫",
    "CUU": "玖", "DINH": "丁", "DUONG": "杨", "HOANG": "黄", "KY": "纪",
    "NGO": "吴", "NGUYUN": "阮", "ONG": "翁", "PHAM": "范", "PHAN": "潘",
    "PHO": "傅", "THO": "寿", "TONG": "宋", "TRIEU": "赵",

    # ===== 缅甸（含华人姓）=====
    "AYE": "埃", "BIAN": "边", "GUAN": "关", "KALYAR": "卡利亚",
    "MIN": "敏", "MYINT": "敏", "PENG": "彭", "SHI": "石", "WIN": "温",

    # ===== Rebels：真实历史人物 → 约定俗成译名 =====
    "AUNG SAN": "昂山", "AZAD": "阿扎德", "BEN BELLA": "本·贝拉",
    "BONIFACIO": "博尼法西奥", "BUCHANAN": "布坎南", "CASTRO": "卡斯特罗",
    "GERONIMO": "杰罗尼莫", "GIAP": "武元甲", "GUEVARA": "格瓦拉",
    "HO": "胡志明", "KUN": "昆", "LAWRENCE": "劳伦斯", "MACHEL": "马谢尔",
    "MAHNO": "马赫诺", "MAO": "毛泽东", "MASUD": "马苏德", "NEWTON": "牛顿",
    "ORTEGA": "奥尔特加", "VARGAS": "巴尔加斯", "VILLA": "比利亚",
    "MALCOLM X": "马尔科姆·X", "ZAPATA": "萨帕塔", "ZERO": "泽罗",
    "TURNER": "特纳", "VESSEY": "维西", "QIU JIN": "秋瑾",
    "PHOOLAN DEVI": "普兰·德维", "GABRIEL PROSSER": "加布里埃尔·普罗瑟",
    "SITTING BULL": "坐牛", "LAS MARIPOSAS": "拉斯马里波萨斯",
}

# ---------------- 第二批：其他国家音译 ----------------
NAMES.update({
    # ===== 美国 / 英国 / 澳大利亚 / 海军陆战队（英语姓氏）=====
    "ADAMS": "亚当斯", "ALVES": "阿尔维斯", "ANDREWS": "安德鲁斯",
    "ARMSTRONG": "阿姆斯特朗", "BERRY": "贝里", "BILLINGS": "比林斯",
    "BRAUN": "布劳恩", "BRIDGES": "布里奇斯", "BROWN": "布朗",
    "BUTLER": "巴特勒", "CAMPBELL": "坎贝尔", "CARR": "卡尔",
    "CARTER": "卡特", "CATES": "凯茨", "CHAMBERLAIN": "张伯伦",
    "CHARLES": "查尔斯", "CHASTAIN": "查斯坦", "CLIFFORD": "克利福德",
    "CONROE": "康罗", "COX": "考克斯", "DANNEBERG": "丹尼伯格",
    "DAVIS": "戴维斯", "DECKER": "德克尔", "DUNN": "邓恩", "EATON": "伊顿",
    "EDWARDS": "爱德华兹", "ELLIOT": "埃利奥特", "FIELDER": "菲尔德",
    "FILIPPOFF": "菲利波夫", "FINNEGAN": "芬尼根", "FORD": "福特",
    "FRANKS": "弗兰克斯", "FULLER": "富勒", "GOMEZ": "戈麦斯",
    "GRAHAM": "格雷厄姆", "GROTEBOER": "格罗特布尔", "HARRIBEY": "哈里贝",
    "HARRIS": "哈里斯", "HAUSMAN": "豪斯曼", "HAYES": "海斯",
    "HUNTER": "亨特", "ILLIAN": "伊利安", "JONES": "琼斯",
    "KEPPLERS": "凯普勒", "KIRBY": "柯比", "KOWALSKI": "科瓦尔斯基",
    "KROMREY": "克罗姆雷", "LANG": "朗", "LAWRY": "劳里", "LEWIS": "刘易斯",
    "LINDEMANN": "林德曼", "LOPEZ": "洛佩斯", "LORENZO": "洛伦佐",
    "LOUNSBURY": "朗斯伯里", "MARKHAM": "马卡姆", "MARTINEZ": "马丁内斯",
    "MCCAY": "麦凯", "MEYER": "迈耶", "MICAL": "米卡尔", "MILLER": "米勒",
    "MINARDI": "米纳尔迪", "MURPHY": "墨菲", "MURRAY": "默里",
    "NICHOLS": "尼科尔斯", "NIELSEN": "尼尔森", "NORMAN": "诺曼",
    "PALMER": "帕尔默", "PENA": "佩纳", "PETERSON": "彼得森",
    "REMER": "雷默", "REYNOLDS": "雷诺兹", "RICHARDS": "理查兹",
    "ROGERS": "罗杰斯", "ROSESTONE": "罗斯通", "SANDERS": "桑德斯",
    "SENGUPTA": "森古普塔", "SULLIVAN": "沙利文", "TAYLOR": "泰勒",
    "THOMAS": "托马斯", "THOMPSON": "汤普森", "WAGENET": "瓦格内",
    "WALLICK": "沃利克", "WHISLER": "惠斯勒", "WHITE": "怀特",
    "WILLIAMS": "威廉姆斯", "WYMAN": "怀曼",
    "ABBOT": "阿博特", "ASHTON": "阿什顿", "BALDWIN": "鲍德温",
    "BLAIR": "布莱尔", "BOWEN": "鲍恩", "CHESTERON": "切斯特伦",
    "COLLINS": "柯林斯", "COOPER": "库珀", "EVANS": "埃文斯",
    "FITZGIBBON": "菲茨吉本", "HAWKINS": "霍金斯", "LONGFORD": "朗福德",
    "LOVEJOY": "洛夫乔伊", "MANSFIELD": "曼斯菲尔德", "MELVILLE": "梅尔维尔",
    "MONTGOMERY": "蒙哥马利", "PLUMB": "普拉姆", "POOLE": "普尔",
    "RIMMER": "里默", "ROBERTS": "罗伯茨", "ROTH": "罗斯",
    "STENTON": "斯滕顿", "STOWE": "斯托", "THORNE": "索恩",
    "TREVOR": "特雷弗", "WATSON": "沃森", "WEBSTER": "韦伯斯特",
    "WOLFE": "沃尔夫", "WRIGHT": "赖特",
    "BAIRD": "贝尔德", "BOSWELL": "博斯韦尔", "BURKE": "伯克",
    "CLARKE": "克拉克", "CULLEN": "卡伦", "DOUGLAS": "道格拉斯",
    "GOUCK": "高克", "HOWISON": "豪伊森", "LAWLESS": "劳利斯",
    "LYTTON": "利顿", "MACAULEY": "麦考利", "MAITLAND": "梅特兰",
    "MCCULLOCH": "麦卡洛克", "PARNELL": "帕内尔", "QUINN": "奎因",
    "STANLEY": "斯坦利", "WADDELL": "沃德尔", "WILLARD": "威拉德",
})

# ---------------- 第三批：欧洲 / 南亚 / 中东 / 拉美 / 东南亚 ----------------
NAMES.update({
    # ===== 联合国（印欧混合）=====
    "AJAGAONKAR": "阿贾冈卡尔", "ALLA": "阿拉", "BAPAT": "巴帕特", "BEDI": "贝迪",
    "BHUPATHIRAJU": "布帕蒂拉朱", "BOURGOIN": "布尔瓜", "CHARY": "查里",
    "CHATURVEDI": "查图尔维迪", "CIESLAK": "切斯瓦克", "CLAUSEL": "克洛泽尔",
    "D'ALLEAUME": "达莱奥姆", "DATLA": "达特拉", "DE GIRARDIN": "德吉拉尔丹",
    "DEFORFES": "德福尔夫", "DESAIX": "德赛", "DOSHI": "多希", "DUNDU": "敦杜",
    "DUPAUL": "迪波尔", "EBERHARDT": "埃伯哈特", "EISLER": "艾斯勒",
    "GADIRAJU": "加迪拉朱", "GERG": "格", "GUE": "盖", "HILGER": "希尔格",
    "JOHANSSON": "约翰松", "KAMATH": "卡马斯", "KAPADIA": "卡帕迪亚",
    "KAUR": "考尔", "KHANNA": "坎纳", "KIRTIPATI": "基尔蒂帕蒂",
    "LACLERC": "拉克莱尔", "LAKKAMRAJU": "拉卡姆拉朱", "MAHALE": "马哈莱",
    "MALAVIYA": "马拉维亚", "MALETHIA": "马莱西亚", "MATHURE": "马图雷",
    "MITTAL": "米塔尔", "MOHITE": "莫希特", "MONIOTTE": "莫尼奥特",
    "MUELLER": "米勒", "MUPPALA": "穆帕拉", "NAIK": "奈克", "NAYAK": "纳亚克",
    "OLSSON": "奥尔松", "PILLAI": "皮莱", "POLIGNAC": "波利尼亚克",
    "RAM": "拉姆", "RAMACHANDRAN": "拉马钱德兰", "REDDY": "雷迪",
    "REINHARDT": "莱因哈特", "SAHU": "萨胡", "SASTRI": "萨斯特里",
    "SAXENA": "萨克塞纳", "SCHAUBACH": "绍巴赫", "SINGH": "辛格",
    "STOECKL": "施特克尔", "SUTARIA": "苏塔里亚", "THIBAULT": "蒂博",
    "UPPALAPATI": "乌帕拉帕蒂", "VALIVARTHI": "瓦利瓦尔蒂", "VARMA": "瓦尔马",
    "WAGH": "瓦格", "WEISMANN": "魏斯曼", "WOUTERS": "沃特斯",
    # ===== 印度 =====
    "AHLUWALIA": "阿卢瓦利亚", "ALLU": "阿卢", "ARORA": "阿罗拉",
    "BANDOPADHYAY": "班多帕迪亚伊", "BIRDI": "比尔迪", "BUDDHARAJU": "佛陀拉朱",
    "CHATTERJEE": "查特吉", "DESAI": "德赛", "DESHMUKH": "德什穆克",
    "DHUNDHARA": "敦达拉", "DUMRA": "杜姆拉", "GHOSH": "戈什",
    "GOUNDER": "冈德", "INAMPUDI": "伊南普迪", "INDUKURI": "因杜库里",
    "IYENGAR": "艾扬格", "KAKKAR": "卡卡尔", "KANDPAL": "坎德帕尔",
    "KANDURI": "坎杜里", "KANUMURI": "卡努穆里", "KARADWAL": "卡拉德瓦尔",
    "KUNAPULI": "库纳普利", "LEKKALA": "莱卡拉", "MANDAL": "曼达尔",
    "MEHTA": "梅塔", "MENDA": "门达", "MUDUNURI": "穆杜努里",
    "MURDESHWAR": "穆尔德什瓦尔", "NAIR": "奈尔",
    "PANGANAMAMULA": "潘加纳马穆拉", "PANI": "帕尼", "PARANJAPE": "帕兰贾佩",
    "PATEL": "帕特尔", "PATIL": "帕蒂尔", "PENMATSA": "彭马察",
    "PRAJAPATI": "普拉贾帕蒂", "RAI": "拉伊", "RALLAPALLI": "拉帕利",
    "RAMAN": "拉曼", "RAY": "罗伊", "SABHERWALL": "萨贝尔瓦尔",
    "SANGHAVI": "桑哈维", "SANGWAL": "桑瓦尔", "SHARMA": "夏尔马",
    "SHENOY": "谢诺伊", "SHINDE": "辛德", "SINHA": "辛哈",
    "SRIDHARA": "斯里达拉", "UDYAVAR": "乌迪亚瓦尔", "UPADHYAY": "乌帕迪亚伊",
    "VAJIPAYAJULA": "瓦吉帕亚朱拉", "VALLADARES": "巴利亚达雷斯",
    "WALAWALAKAR": "瓦拉瓦拉卡尔", "WALEED": "瓦利德",
    # ===== 俄罗斯 / 乌克兰 / 哈萨克斯坦 =====
    "ACHKINA": "阿奇金娜", "ALEXEYEV": "阿列克谢耶夫", "BAGRITSKY": "巴格里茨基",
    "BOLONIKOV": "博洛尼科夫", "BOTVINOV": "博特维诺夫",
    "CHEBOKSAROV": "切博克萨罗夫", "CHEKOV": "契诃夫", "CHERNIGOV": "切尔尼戈夫",
    "CHILOVA": "奇洛娃", "DEMTCHENKO": "杰姆琴科", "DMITRIEV": "德米特里耶夫",
    "DVALISCHVILI": "德瓦利什维利", "EGOROVA": "叶戈罗娃",
    "FYODEROV": "费奥多罗夫", "GOPOUA": "戈波瓦", "GRIGORIEV": "格里戈里耶夫",
    "GUSAKOV": "古萨科夫", "IGNATIEV": "伊格纳季耶夫", "KAMENEV": "加米涅夫",
    "KAZANTSEV": "卡赞采夫", "KOROLEVA": "科罗廖娃", "KOSOROTOV": "科索罗托夫",
    "KRAKOVSKY": "克拉科夫斯基", "LEDOVSKAYA": "列多夫斯卡娅",
    "NIKOLAYEVA": "尼古拉耶娃", "OGURISOVA": "奥古里索娃",
    "ORENKHOVA": "奥连霍娃", "PAZOVA": "帕佐娃", "PETRIKOV": "彼得里科夫",
    "POPOV": "波波夫", "SHELYUKIN": "舍柳金", "SHISHKOVA": "希什科娃",
    "TCHERKASSOVA": "切尔卡索娃", "TORSHIN": "托尔申", "UMAROV": "乌马罗夫",
    "VOROBIOV": "沃罗比奥夫", "VOSLENSKY": "沃斯连斯基", "YAKUNIN": "亚库宁",
    "YASINSKY": "亚辛斯基", "ZHDANOV": "日丹诺夫",
    "ABISHEV": "阿比舍夫", "BUKSMAN": "布克斯曼", "FELGENGAUER": "费尔根豪尔",
    "KARIBZHANOV": "卡里布扎诺夫", "KAZHEGLDIN": "卡热格利丁",
    "KEKILBAEV": "克基尔巴耶夫", "KOZYBAEV": "科济巴耶夫",
    "NAZARBAEV": "纳扎尔巴耶夫", "NURMAGAMBETOV": "努尔马甘别托夫",
    "OTUNBAEVA": "奥通巴耶娃", "SHAIKENOV": "沙伊克诺夫",
    "SHARDABAEV": "沙尔达巴耶夫", "SOLZHENITSYNS": "索尔仁尼琴",
    "SULEIMENOV": "苏莱梅诺夫", "SUPRUNYUK": "苏普鲁纽克", "SUPUNOK": "苏普诺克",
    "TATIMOV": "塔季莫夫", "TERESHCHENKO": "捷列先科",
    "TUYAKBAEV": "图亚克巴耶夫", "ZATULIN": "扎图林",
    # ===== 德国 / 法国 =====
    "AUERSWALD": "奥尔斯瓦尔德", "BERNSTORFF": "伯恩斯托夫", "ERHARD": "艾哈德",
    "FRIELINGHAUS": "弗里林豪斯", "GLOCKAUER": "格洛克奥尔", "HACKL": "哈克尔",
    "HAUENSTEIN": "豪恩施泰因", "HEISS": "海斯", "HERRMANN": "赫尔曼",
    "JAEGER": "耶格尔", "KROEGEL": "克罗格尔", "LINDER": "林德",
    "NEUNER": "诺伊纳", "SCHIMDT": "施密特", "SCHUTZ": "舒茨",
    "VOGT": "福格特", "WALDHAUSEN": "瓦尔德豪森", "WEILL": "魏尔",
    "WOELLER": "沃勒",
    "AUGEREAU": "奥热罗", "BRUNETIERE": "布吕内蒂耶尔", "CHARRIERE": "沙里耶尔",
    "CHATILLON": "沙蒂永", "D'ARGENLIEU": "达尔让利厄", "DEBELLE": "德贝尔",
    "DUPUIS": "迪皮伊", "FLEURIEU": "弗勒里厄", "L'OLIVE": "洛利夫",
    "LACHAPELLE": "拉沙佩勒", "LANNES": "拉纳", "LAVOLLEE": "拉沃莱",
    "MARBOT": "马尔博", "MAUDUIT": "莫迪", "MONVEL": "蒙维尔",
    "OLIVIER": "奥利维耶", "RAUCOURT": "罗库尔", "ROCARD": "罗卡尔",
    # ===== 巴基斯坦 / 以色列 / 阿拉伯 / 伊朗 =====
    "AFRIDI": "阿夫里迪", "AMINI": "阿米尼", "BAIG": "贝格", "BALOCH": "俾路支",
    "BARANZAI": "巴兰扎伊", "BARLAS": "巴尔拉斯", "BIJARANI": "比贾拉尼",
    "BIZENJO": "比曾乔", "BROHI": "布罗希", "BUGTI": "布格蒂",
    "GHAZNAVI": "加兹纳维", "GHILZAI": "吉尔扎伊", "GICHKI": "吉奇基",
    "JAKHRANI": "贾赫拉尼", "JAMOTE": "贾莫特", "JOYO": "乔约",
    "KARMAZKHEL": "卡尔马兹克尔", "KASHANI": "卡沙尼", "KAYANI": "卡亚尼",
    "KERMANI": "克尔马尼", "KHORASANI": "霍拉桑尼", "KHUHRO": "库赫罗",
    "MALIK": "马利克", "MARWAT": "马尔瓦特", "MIRZA": "米尔扎",
    "PANHWAR": "潘瓦尔", "POPALZAI": "波帕尔扎伊", "SYED": "赛义德",
    "THEBO": "特博", "ZAMANI": "扎马尼",
    "AFROM": "阿夫罗姆", "ANCHER": "安切尔", "APFEL": "阿普费尔",
    "BERMAN": "伯曼", "BUERGER": "比格尔", "CRONENBERG": "克罗嫩贝格",
    "DRESSNER": "德雷斯纳", "EPELBOIM": "埃佩尔博伊姆", "FASSMANN": "法斯曼",
    "FRANKENBERGER": "弗兰肯贝格尔", "GITZOK": "吉佐克", "GOODMAN": "古德曼",
    "GOUDSMIDT": "豪兹米特", "JESI": "耶西", "KASDAN": "卡斯丹",
    "LEEUW": "莱乌", "LEHRMAN": "莱尔曼", "LEWIN": "莱温", "LIPMAN": "利普曼",
    "LURYI": "卢里伊", "LÖBL": "勒布尔", "MAIER": "迈尔",
    "MOISCHEL": "莫伊舍尔", "ÖTINGER": "厄廷格", "PEREC": "佩雷茨",
    "PINE": "派恩", "STEINER": "施泰纳", "VEKSLER": "维克勒斯",
    "VERULI": "韦鲁利", "WINTERMANN": "温特曼",
    "AJJAJ": "阿贾吉", "AS": "阿斯", "ATHIR": "阿提尔", "BASIR": "巴西尔",
    "FIRYABI": "菲里亚比", "GHALLABI": "加拉比", "HALALI": "哈拉利",
    "HARITH": "哈里斯", "HASAN": "哈桑", "HAWARI": "哈瓦里", "HAYY": "哈伊",
    "JARMI": "贾尔米", "JUNAYD": "朱奈德", "KAYSANI": "凯萨尼",
    "MADINI": "马迪尼", "MUAFA": "穆阿法", "MURRI": "穆里",
    "NAJIRAMI": "纳吉拉米", "RAQASHI": "拉卡希", "RIYASHI": "里亚希",
    "SABI": "萨比", "SAIB": "萨伊卜", "SHARANI": "沙拉尼", "SILUF": "西卢夫",
    "SULAMI": "苏拉米", "TALAQANI": "塔拉卡尼", "WASITI": "瓦西提",
    "ZAJJAJI": "扎贾吉", "ZAYYAT": "扎亚特", "ZUHAYR": "祖海尔",
    "ABOLFAZEL": "阿博尔法兹尔", "ALI": "阿里", "ALMASI": "阿尔马西",
    "AMIN": "阿明", "BABALI": "巴巴利", "BAHRAMI": "巴赫拉米",
    "BAKHSHI": "巴赫希", "BOZORGMEHR": "博佐尔格梅赫尔", "DARVISHI": "达尔维希",
    "ESHAGHI": "埃沙吉", "FAR": "法尔", "FARAHMAND": "法拉赫曼德",
    "GHEZELBASH": "盖泽尔巴什", "HAJIVAND": "哈吉万德",
    "HEMATKHAH": "赫马特卡赫", "JALALI": "贾拉利", "KAZEMI": "卡泽米",
    "KIANI": "基亚尼", "MAKOUEI": "马库埃伊", "MARGEN": "马尔根",
    "MOHAMMADY": "穆罕默迪", "NAGHILOO": "纳吉卢", "PILBALA": "皮尔巴拉",
    "RAYHANIANPOUR": "雷哈尼安普尔", "REISY": "雷西", "SABOURI": "萨布里",
    "SARVI": "萨尔维", "TAVAKOLI": "塔瓦科利", "TAVASSOLY": "塔瓦索利",
    # ===== 拉美（西/葡语）=====
    "AMARAL": "阿马拉尔", "AZEVEDO": "阿泽维多", "BERNARDES": "贝尔纳德斯",
    "BORGES": "博尔赫斯", "BRANCO": "布兰科", "CARDOSO": "卡多佐",
    "CARVALHO": "卡瓦略", "CAVALCANTI": "卡瓦尔坎蒂", "COSTA": "科斯塔",
    "COUTO": "科托", "CÂMARA": "卡马拉", "DA MATA": "达马塔",
    "DO NASCIMENTO": "多纳西门托", "FAGUNDES": "法贡德斯",
    "FERREIRA": "费雷拉", "GARCIA": "加西亚", "GIL": "吉尔", "JAIME": "海梅",
    "LIMA": "利马", "LINS": "林斯", "LOPES": "洛佩斯", "MEDEIROS": "梅代罗斯",
    "MENDONÇA": "门东萨", "MENEZES": "梅内泽斯", "MORAES": "莫赖斯",
    "MOREIRA": "莫雷拉", "NEVES": "内维斯", "PINTO": "平托", "PIRES": "皮雷斯",
    "REIS": "雷斯", "RIBEIRO": "里贝罗", "SANCHES": "桑切斯",
    "SANTOS": "桑托斯", "SILVA": "席尔瓦", "SOUSA": "索萨", "SÁ": "萨",
    "TAVARES": "塔瓦雷斯", "TORRES": "托雷斯", "ÁLVARES": "阿尔瓦雷斯",
    "ALONSO": "阿隆索", "BLANCO": "布兰科", "CEBALLOS": "塞瓦略斯",
    "DELGADO": "德尔加多", "DÍEZ": "迭斯", "GARCÍA": "加西亚",
    "GUTIÉRREZ": "古铁雷斯", "GÓMEZ": "戈麦斯", "HERNÁNDEZ": "埃尔南德斯",
    "JIMÉNEZ": "希门尼斯", "MARTÍNEZ": "马丁内斯", "MORALES": "莫拉莱斯",
    "MUÑOZ": "穆尼奥斯", "NAVARRO": "纳瓦罗", "PÉREZ": "佩雷斯",
    "RODRÍGUEZ": "罗德里格斯", "ROMERO": "罗梅罗", "RUBIO": "鲁维奥",
    "RUIZ": "鲁伊斯", "SANZ": "桑斯", "SERRANO": "塞拉诺",
    "SÁNCHEZ": "桑切斯", "VÁZQUEZ": "巴斯克斯", "ÁLVAREZ": "阿尔瓦雷斯",
    "DOMÍNGUEZ": "多明格斯", "FERNÁNDEZ": "费尔南德斯", "GONZÁLEZ": "冈萨雷斯",
    "LÓPEZ": "洛佩斯", "SUÁREZ": "苏亚雷斯",
    # ===== 蒙古 / 东南亚 =====
    "ALTANSUKH": "阿勒坦苏赫", "ATANKHUYAG": "阿坦胡亚格", "BATBILIG": "巴特毕力格",
    "BATTUL": "巴图勒", "BAZARYN": "巴扎林", "DANZANDARJA": "丹赞达尔扎",
    "DEMCHIGGARAV": "德姆奇加拉夫", "DORJSUREN": "道尔吉苏伦", "DUUCHIN": "杜钦",
    "ENEBAYAR": "恩赫巴亚尔", "GANBOLD": "甘博勒德", "JAMGAN": "扎姆甘",
    "JUGDERNAMJIL": "朱格德尔纳姆吉勒", "KHISHBAATAR": "希什巴特尔",
    "KHOLOGDORI": "霍洛格多里", "NATSAGDORI": "纳察格多里",
    "OTRYAD": "奥特里亚德", "PUREDORG": "普雷多尔格",
    "SANJAASUREN": "桑扎苏伦", "URTNASAN": "乌尔特纳桑",
    "BANTOW": "班托", "BUNYAKET": "汶亚吉", "CHITPATIMA": "奇帕蒂马",
    "CHOMANAND": "乔马南", "DANGPIAM": "当皮亚姆", "HOMARARUEN": "霍马拉伦",
    "INCHAREON": "英差伦", "INTHARAPI": "因塔拉皮", "INTPORN": "因蓬",
    "JANTHANA": "占塔纳", "JAROENSIRI": "乍伦西里", "JAYANAMA": "差亚南",
    "KANGRANG": "冈让", "KAWRUANG": "考鲁昂", "KEOLATSAMI": "胶拉沙米",
    "MOOLSAN": "穆桑", "NAMWONG": "南旺", "NATENEE": "纳特尼",
    "PARIBATRA": "帕里巴特拉", "SIRIPOOL": "西里蓬",
    "ARBI": "阿尔比", "BASUKI": "巴苏基", "DEPHIOS": "德菲奥斯",
    "DHARSONO": "达尔索诺", "DIPOYANTI": "迪波扬蒂", "FINARSIH": "菲纳西",
    "HABIBIE": "哈比比", "HARAHAP": "哈拉哈普", "KANTONO": "坎托诺",
    "KUSUMA": "库苏马", "LAPAINI": "拉帕伊尼", "MAINAKY": "迈纳基",
    "NAIPOSPOS": "奈波斯波斯", "NITISASTRO": "尼蒂萨斯特罗", "PUTU": "普图",
    "SUSANTI": "苏珊蒂", "SUSENO": "苏塞诺", "TEDJAKUSAMA": "特贾库萨马",
    "THIO": "蒂奥", "YUDHANI": "尤达尼",
    "BALA": "巴拉", "CAXTON": "卡克斯顿", "CHOO": "朱", "DEE": "迪",
    "FOOK": "福", "GHAFUR": "加富尔", "KIM": "金", "LAN": "兰",
    "LEONG": "梁", "LOOI": "吕", "NOOR": "努尔", "SAMAT": "萨马特",
    "SIAN": "西安", "SODHY": "索迪", "SUBAGJA": "苏巴贾",
    "WIHARDJA": "维哈尔贾", "YUSOFF": "尤索夫",
})

PAT = re.compile(r"^(.*?)(\s+)\((.*?)\)(\s*)$")


def main():
    raw = open(SRC, "rb").read()
    lines = raw.split(b"\r\n")
    out, miss, used = [], [], set()
    for i, lb in enumerate(lines, 1):
        s = lb.decode("cp1252")
        if not s.strip():
            out.append(lb)
            continue
        m = PAT.match(s)
        if not m:
            out.append(lb)
            miss.append((i, s, "格式不符"))
            continue
        nm, sp, ctry, tail = m.group(1).strip(), m.group(2), m.group(3).strip(), m.group(4)
        zh_n = NAMES.get(nm)
        zh_c = COUNTRIES.get(ctry)
        if zh_n is None or zh_c is None:
            out.append(lb)
            miss.append((i, s, "名" if zh_n is None else "" + ("国家" if zh_c is None else "")))
            continue
        out.append(f"{zh_n}{sp}({zh_c}){tail}".encode("gbk"))
        used.add(nm)

    n = len(lines)
    if len(out) != n:
        print(f"❌ 行数不一致 {len(out)} != {n}")
        sys.exit(1)

    data = b"\r\n".join(out)
    open(DST, "wb").write(data)
    print(f"原文 {n} 行 / {len(raw)} B  →  成品 {len(data)} B")
    print(f"  译 {n - len(miss)} 行 / 未命中 {len(miss)} 行")
    # 完全未用到的映射（拼写检查）
    unused = [k for k in NAMES if k not in used]
    if unused:
        print(f"  ⚠️ 名字表有 {len(unused)} 条未用到：{unused[:20]}")

    p = os.path.join(ROOT, r"peg\testbed\_untranslated_name030.txt")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# name030 未命中 {len(miss)} 行\n")
        for i, s, why in miss:
            f.write(f"{i}\t{s}\t{why}\n")
    print(f"  未命中清单：{p}")


if __name__ == "__main__":
    main()
