# -*- coding: utf-8 -*-
"""生成 zh/part-20.tsv：chunk-20 地名汉化(W/Z 段，末片)。"""
import io, os, sys

IN = r"D:\DSH\军事游戏汉化\work\atomic\chunks\chunk-20.tsv"
OUT = r"D:\DSH\军事游戏汉化\work\atomic\zh\part-20.tsv"

KEEP = []

# 专名精确映射(即整行映射，含括号别名与通名)
EXACT = {
    # ---- W 段 ----
    "Warta (Warthe)": "瓦尔塔河 (瓦尔特河)",
    "Warthe": "瓦尔特河",
    "Warzno (Warschnau)": "瓦尔兹诺 (瓦尔斯瑙)",
    "Wasbister": "瓦斯比斯特",
    "Wasiljewka": "瓦西列夫卡",
    "Wasiljewska": "瓦西列夫斯卡",
    "Water Sound": "沃特海峡",
    "Watergrasshill": "沃特格拉斯希尔",
    "Wateringhouse": "沃特林豪斯",
    "Weddel Sound": "韦德尔海峡",
    "Weener": "韦纳",
    "Weert": "韦尔特",
    "Wehdel": "韦德尔",
    "Wehrmacht": "国防军",
    "Weissenburg": "魏森堡",
    "Weiswampach": "魏斯万帕赫",
    "Wejherowo (Neustadt in Westpreussen)": "韦伊海罗沃 (西普鲁士新城)",
    "Wells-next-the-Sea": "滨海韦尔斯",
    "Welschap Airport": "韦尔斯哈普机场",
    "Welyka Biloserka (Bolshaya Belozerka)": "大比洛泽尔卡 (大别洛泽尔卡)",
    "Werbellinsee": "韦尔贝林湖",
    "Werchne Kumsky": "上库姆斯基",
    "Werchne Tsaritschinskij": "上察里岑斯基",
    "Wercken (Werken)": "韦尔肯 (韦尔肯)",
    "Werlte": "韦尔特",
    "Wernigerode": "韦尼格罗德",
    "Werra": "韦拉河",
    "Wesel": "韦塞尔",
    "Weser": "威悉河",
    "West Barsham": "西巴沙姆",
    "West Islip": "西艾斯利普",
    "West Kirby": "西柯比",
    "West Loch": "西湖",
    "West New York": "西纽约",
    "West Stourmouth": "西斯图尔茅斯",
    "West Swale River": "西斯韦尔河",
    "West Wickham": "西威克姆",
    "Westende Bains (Westende Bad)": "西恩德海滨 (西恩德海滨)",
    "Westenede": "韦斯特内德",
    "Westerdale": "韦斯特代尔",
    "Westerems": "韦斯特埃姆斯",
    "Western Desert Air Force": "西部沙漠空军",
    "Western Scheldt": "西斯海尔德",
    "Westerplatte": "西盘半岛",
    "Westerstede": "韦斯特施泰德",
    "Westerwoldsche Aa": "韦斯特沃尔德斯阿河",
    "Westgate on Sea": "滨海西门",
    "Westhampton Beach": "韦斯特汉普顿海滩",
    "Westkerke": "韦斯特凯尔克",
    "Westport": "韦斯特波特",
    "Westray Airport": "韦斯特雷机场",
    "Westwall": "西墙",
    "Westwood": "韦斯特伍德",
    "Weurt": "沃尔特",
    "Weverton": "韦弗顿",
    "Weyhe": "韦耶",
    "Wheeler Airforce Base": "惠勒空军基地",
    "White Army": "白军",
    "White Cliffs of Dover": "多佛白崖",
    "White Plains": "怀特普莱恩斯",
    "Whitechurch": "怀特彻奇",
    "Whitegate": "怀特盖特",
    "Whitegate Oil Refinery": "怀特盖特炼油厂",
    "Whitstable": "惠特斯特布尔",
    "Wick Airport": "威克机场",
    "Wick River": "威克河",
    "Wicklow": "威克洛",
    "Widnes": "威德尼斯",
    "Widuchowa (Fiddichow)": "维杜霍瓦 (菲迪霍)",
    "Wieczfnia": "维耶奇夫尼亚",
    "Wieliczka": "维利奇卡",
    "Wielki Kack (Gross Katz)": "大卡茨克 (大卡茨)",
    "Wien": "维也纳",
    "Wierzchucino (Wierschutzin)": "维耶日胡奇诺 (维耶舒钦)",
    "Wiesmoor": "维斯莫尔",
    "Wigan": "威根",
    "Wighton": "怀顿",
    "Wijchen": "韦亨",
    "Wildeshausen": "维尔德斯豪森",
    "Wilga": "维尔加河",
    "Wilhelmina canal": "威廉明娜运河",
    "Wilhelminakanaal": "威廉明娜运河",
    "Wilhelmshaven Port": "威廉港",
    "Willaston": "威拉斯顿",
    "Wimereux": "维姆勒",
    "Wimmenau": "维默瑙",
    "Winchelsea Beach": "温奇尔西海滩",
    "Windsor Hills": "温莎丘陵",
    "Wingates": "温盖茨",
    "Wingen-sur-Moder": "莫代尔河畔温根",
    "Wingles": "万格勒",
    "Winschoten": "温斯霍滕",
    "Winschoterdiep": "温斯霍滕运河",
    "Winsford": "温斯福德",
    "Winslow": "温斯洛",
    "Winter Line Fortifications": "冬季防线工事",
    "Wipper River": "维珀河",
    "Wisla Smiala": "维斯瓦河畔希米亚瓦",
    "Wisla river": "维斯瓦河",
    "Wisloujscie": "维斯瓦河口要塞",
    "Wisniewka": "维希涅夫卡",
    "Wissant": "维桑",
    "Wissembourg": "维桑堡",
    "Wittmund": "维特蒙德",
    "Wladyslawowo (Grossendorf)": "瓦迪斯瓦沃沃 (格罗森多夫)",
    "Wodjanskoje": "沃江斯科耶",
    "Wolfeze": "沃尔费泽",
    "Womanagh River": "沃马纳河",
    "Woodchurch": "伍德彻奇",
    "Workers and Peasants Red Air Fleet": "工农红色空军",
    "Wosnesenka": "沃兹涅先卡",
    "Woumen": "沃门",
    "Wriezen": "弗里岑",
    "Wright Army Airfield": "赖特陆军机场",
    "Wuerselen": "维尔塞伦",
    "Wulpen": "维尔彭",
    "Wupper": "乌珀河",
    "Wurm": "沃尔姆河",
    "Wyandanch": "怀恩丹奇",
    "Wye": "怀河",
    "Wyre": "怀尔河",
    "Wysokie": "维索基耶",
    "Wyszecino (Wischetzin)": "维谢奇诺 (维谢钦)",
    "Wyszkow": "维什库夫",
    # ---- X 段 ----
    "XVI Corpo/Camicie Nere Legion": "第16军/黑衫军军团",
    "XXIX/3º/133ª \"Littorio\"": "第29/第3/第133\"利托里奥\"",
    "XXX. Corps": "第30军",
    "Xewkija": "谢夫基贾",
    "Xinchangzhen": "新昌镇",
    "Xirdalan": "希尔达兰",
    "Xironomi": "希罗诺米",
    "Xirovrisi": "希罗夫里西",
    "Xylokastro": "克西洛卡斯特罗",
    # ---- Y 段 ----
    "Yablonka": "亚布隆卡",
    "Yagodnik Airfield": "亚戈德尼克机场",
    "Yagry": "亚格雷",
    "Yahorlyk Bay": "亚霍尔雷克湾",
    "Yakoulevo": "亚科夫列沃",
    "Yakovenkovo": "亚科文科沃",
    "Yakovlevichi": "亚科夫列维奇",
    "Yakovlevo": "亚科夫列沃",
    "Yakushkino": "亚库什基诺",
    "Yakymivka (Akimovka)": "亚基米夫卡 (阿基莫夫卡)",
    "Yalova": "亚洛瓦",
    "Yam-Ruchey": "亚姆-鲁切伊",
    "Yamy": "亚梅",
    "Yanghangzhen": "杨行镇",
    "Yapildak": "亚皮尔达克",
    "Yaroslavka": "雅罗斯拉夫卡",
    "Yaroslavl'": "雅罗斯拉夫尔",
    "Yaroslavskaya": "雅罗斯拉夫斯卡亚",
    "Yarovitskoye": "亚罗维茨科耶",
    "Yaselka (Nikolayevka)": "亚谢尔卡 (尼古拉耶夫卡)",
    "Yasinovskiy": "亚西诺夫斯基",
    "Yasma (Yashma)": "亚斯马 (亚什马)",
    "Yasna Poliana (Yasnaya Polyana)": "亚斯纳波利亚纳 (亚斯纳亚波利亚纳)",
    "Yasna Polyana": "亚斯纳波利亚纳",
    "Yasnaya Polyana": "亚斯纳亚波利亚纳",
    "Yauza River": "亚乌扎河",
    "Yavkyne": "亚夫基内",
    "Yavon' River": "亚翁河",
    "Yecha": "耶恰",
    "Yefremovka": "叶夫列莫夫卡",
    "Yegut": "叶古特",
    "Yekaterinovka": "叶卡捷里诺夫卡",
    "Yel'nya": "叶利尼亚",
    "Yelan River": "叶兰河",
    "Yelanchik": "叶兰奇克",
    "Yelanchik River": "叶兰奇克河",
    "Yelanskaya": "叶兰斯卡亚",
    "Yelcha": "叶尔恰",
    "Yelenev Kholm": "叶列涅夫霍尔姆",
    "Yeliseyevka": "叶利谢耶夫卡",
    "Yelizavetino": "叶利扎韦季诺",
    "Yelizavetinskoye": "叶利扎韦京斯科耶",
    "Yelizavetovka": "叶利扎韦托夫卡",
    "Yelizavetovka Airfield": "叶利扎韦托夫卡机场",
    "Yelizavetovskaya": "叶利扎韦托夫斯卡亚",
    "Yelovka": "叶洛夫卡",
    "Yelshanka": "叶尔尚卡",
    "Yelyzavetivka (Yelizavetka)": "叶利扎韦蒂夫卡 (叶利扎韦特卡)",
    "Yelyzavetivka (Yelizavetovka)": "叶利扎韦蒂夫卡 (叶利扎韦托夫卡)",
    "Yendovskiy": "延多夫斯基",
    "Yerditsy": "叶尔季齐",
    "Yerkovtsy": "叶尔科夫齐",
    "Yermolino (Yermolinskoye)": "叶尔莫利诺 (叶尔莫林斯科耶)",
    "Yermoshkino": "叶尔莫什基诺",
    "Yershovka": "叶尔绍夫卡",
    "Yerzovka": "叶尔佐夫卡",
    "Yesong River": "礼成江",
    "Yevetsko-Mykolaivka (Yevetskaya-Nikolayevka)": "叶韦茨科-米科拉伊夫卡 (叶韦茨卡亚-尼古拉耶夫卡)",
    "Yevseyev": "叶夫谢耶夫",
    "Yezhovka": "叶若夫卡",
    "Ylasommee": "于拉索梅",
    "Yokefleet Creek": "约克弗利特溪",
    "Yolagzi": "约拉格兹",
    "Yonan": "延安",
    "Yonkers": "扬克斯",
    "Yorkstown-Schwarzsee": "约克斯敦-黑湖",
    "Youghal": "约尔",
    "Youghal Bay": "约尔湾",
    "Youghal Harbour": "约尔港",
    "Ypres-Comines Canal": "伊普尔-科米讷运河",
    "Ypres-Yser Canal (Ieperlee)": "伊普尔-伊瑟尔运河 (伊珀尔莱)",
    "Yser (Ijzer)": "伊瑟尔河 (艾泽尔河)",
    "Yser River (Ijzer)": "伊瑟尔河 (艾泽尔河)",
    "Yssel river": "艾瑟尔河",
    "Yukki": "尤基",
    "Yuras": "尤拉斯",
    "Yurovka": "尤罗夫卡",
    "Yuryevka": "尤里耶夫卡",
    "Yuzhnaya": "尤日纳亚",
    "Yuzhny": "尤日内",
    "Yvetot-Bocage": "伊沃托-博卡日",
    # ---- Z 段 ----
    "ZG 26/ L 2": "ZG 26/ L 2",
    "Zabaryne": "扎巴里内",
    "Zabierzow": "扎别茹夫",
    "Zaborodye": "扎博罗季耶",
    "Zaborow": "扎博鲁夫",
    "Zaborye": "扎博里耶",
    "Zabrat Airport": "扎布拉特机场",
    "Zabrodzie": "扎布罗杰",
    "Zadar": "扎达尔",
    "Zafar el Qadima": "扎法尔盖迪马",
    "Zafarraya": "萨法拉亚",
    "Zagazig": "宰加济格",
    "Zagorye": "扎戈里耶",
    "Zagrivye": "扎格里维耶",
    "Zahna": "察纳",
    "Zaicana": "扎伊卡纳",
    "Zaichivske": "扎伊奇夫斯克",
    "Zakaznik Staroberdyanskyi Forest": "老别尔江斯克禁猎区森林",
    "Zakharov": "扎哈罗夫",
    "Zakharovo": "扎哈罗沃",
    "Zakharyevka": "扎哈里耶夫卡",
    "Zakroczyn": "扎克罗琴",
    "Zakumuiza (Woldenrade)": "扎库穆伊扎 (沃尔登拉德)",
    "Zaliv Obitochnyy": "奥比托奇内湾",
    "Zaliyem": "扎利耶姆",
    "Zaltbommel": "扎尔特博默尔",
    "Zamostye": "扎莫斯季耶",
    "Zamyatino": "扎米亚季诺",
    "Zandvoorde": "赞德福德",
    "Zanzibar": "桑给巴尔",
    "Zapadhovka": "扎帕多夫卡",
    "Zaplavskaya": "扎普拉夫斯卡亚",
    "Zaporizhzhia": "扎波罗热",
    "Zaporozhskaya": "扎波罗日斯卡亚",
    "Zaprudye": "扎普鲁季耶",
    "Zarat": "扎拉特",
    "Zarelye": "扎列利耶",
    "Zariza": "扎里扎",
    "Zarnowiec (Zarnowitz)": "扎尔诺维茨 (扎尔诺维茨)",
    "Zarren": "扎伦",
    "Zarrenbeek": "扎伦贝克",
    "Zarya": "扎里亚",
    "Zasillya": "扎西利亚",
    "Zatoka Gdanska (Danziger Bucht)": "格但斯克湾 (但泽湾)",
    "Zatoka Pucka (Putziger Wiek)": "普茨克湾 (普齐希湾)",
    "Zatuski": "扎图斯基",
    "Zavitne": "扎维特内",
    "Zaychiki": "扎伊奇基",
    "Zaymo-Obryv": "扎伊莫-奥布里夫",
    "Zaytsevo": "扎伊采沃",
    "Zdolbunov": "兹多尔布诺夫",
    "Zebbug": "泽布季",
    "Zehdenick": "采德尼克",
    "Zeist": "宰斯特",
    "Zeitz": "蔡茨",
    "Zelenaya Polyana": "泽列纳亚波利亚纳",
    "Zelenaya River (Zelena)": "泽列纳亚河 (泽列纳)",
    "Zelenaya Roshcha": "泽列纳亚罗夏",
    "Zelenaya height": "泽列纳亚高地",
    "Zelene": "泽列内",
    "Zelenij Lug (Zelenyy Lug)": "泽列尼卢格 (泽列内卢格)",
    "Zelenivka": "泽列尼夫卡",
    "Zelenki": "泽连基",
    "Zelenkino": "泽连基诺",
    "Zelenogorsk": "泽列诺戈尔斯克",
    "Zelenovka": "泽列诺夫卡",
    "Zelenyi Bor": "泽列内博尔",
    "Zelenyy Yar": "泽列内亚尔",
    "Zelistrzewo (Sellistrau)": "泽利斯特热沃 (塞利斯特劳)",
    "Zembra": "曾布拉岛",
    "Zembretta": "曾布雷塔岛",
    "Zemlijansk": "泽姆利扬斯克",
    "Zenbok": "曾博克",
    "Zerbicke": "采尔比克",
    "Zerbow": "采尔博",
    "Zerbst": "采尔布斯特",
    "Zernovoy": "泽尔诺沃伊",
    "Zetel": "采特尔",
    "Zety": "泽蒂",
    "Zevecote (Zevekote)": "泽弗科特 (泽弗科特)",
    "Zevenaar": "泽弗纳尔",
    "Zeynalabdin Tagiyev (Nasosnyy)": "泽纳拉布丁塔吉耶夫 (纳索斯内)",
    "Zharovikha": "扎罗维哈",
    "Zhelanya": "热拉尼亚",
    "Zhelepova": "热列波瓦",
    "Zheleznyy": "热列兹内",
    "Zhelyabovka": "热利亚博夫卡",
    "Zherebtsovo": "热列布佐沃",
    "Zhirki": "日尔基",
    "Zhitomir Counterattack": "日托米尔反击战",
    "Zhizhala": "日扎拉",
    "Zhoupuzhen": "周浦镇",
    "Zhukovo-Tatorskiy": "茹科沃-塔托尔斯基",
    "Zhulyany": "茹利亚内",
    "Zid'ki": "济季基",
    "Ziedini": "济耶迪尼",
    "Zielnowo (Sellnowo; Silnau)": "杰尔诺沃 (塞尔诺沃; 济尔瑙)",
    "Zielona": "杰洛纳",
    "Ziepniekkalns Forest": "济耶普涅卡尔恩斯森林",
    "Ziesar": "齐萨尔",
    "Zimnyatskiy": "济姆尼亚茨基",
    "Zinga": "津加",
    "Zira (Zyrya)": "济拉 (济里亚)",
    "Zirovac": "济罗瓦茨",
    "Zmagaylovka": "兹马盖洛夫卡",
    "Zmiyev": "兹米耶夫",
    "Znamenskoye": "兹纳缅斯科耶",
    "Znamyanka": "兹纳缅卡",
    "Zoersel": "祖尔瑟尔",
    "Zohlow": "措洛",
    "Zolataya Kosa": "佐洛塔亚科萨",
    "Zolotonosha": "佐洛托诺沙",
    "Zolotonoshka River": "佐洛托诺什卡河",
    "Zondereigen": "宗德赖根",
    "Zorbig": "措尔比希",
    "Zorgiani": "佐尔贾尼",
    "Zori": "佐里",
    "Zubarevka": "祖巴列夫卡",
    "Zubotryasivka (Zubotryaskovka)": "祖博特里亚西夫卡 (祖博特里亚斯科夫卡)",
    "Zubtsov": "祖布佐夫",
    "Zuid-Willemsvaart": "南威廉斯运河",
    "Zukowo (Zuckau)": "祖科沃 (楚考)",
    "Zundert": "宗德特",
    "Zuromin": "茹罗明",
    "Zut": "祖特",
    "Zvezdochka": "兹韦兹多奇卡",
    "Zvonkiy": "兹翁基",
    "Zwischenahner Meer": "茨维申纳湖",
    "Zybenko": "济边科",
    "Zyrardow": "日拉尔杜夫",
    # ---- 方括号 / 编制行 ----
    "[103]  Latashanka (Latoshinka)": "[103]  拉塔尚卡 (拉托申卡)",
    "[8]  Balka Ternovka": "[8]  捷尔诺夫卡沟",
    "hvArt/78thDiv.": "重炮/第78师",
    "hvArt/CCB/1stUS-ArmD": "重炮/CCB/美国第1装甲师",
    "la Cosa River": "拉科萨河",
    "liArt/CCB/1stUS-ArmD": "轻炮/CCB/美国第1装甲师",
    "s'Arenal": "萨雷纳尔",
    "s.Pz.Jg.Abt 559": "第559重型反坦克营",
    "schwere Artillerie-Abteilung 456": "第456重型炮兵营",
    "schwere Artillerie-Abteilung 457": "第457重型炮兵营",
    "Ð#ð#P$à$": "Ð#ð#P$à$",
    "Öskü": "厄什屈",
}

# 需保留原文、但脚本里显式声明的条目(用于报告)
EXPLICIT_KEEP = {"ZG 26/ L 2", "Ð#ð#P$à$"}


def main():
    with io.open(IN, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    src_lines = raw.split("\r\n")
    if src_lines and src_lines[-1] == "":
        src_lines.pop()
    n = len(src_lines)

    out = []
    for s in src_lines:
        if s in EXACT:
            zh = EXACT[s]
            if zh == s:
                KEEP.append(s)
        else:
            KEEP.append(s)
            zh = s
        out.append(s + "\t" + zh)

    data = "\r\n".join(out) + "\r\n"
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, "wb") as f:
        f.write(data.encode("utf-8"))

    # ---------- 自检 ----------
    with io.open(OUT, "rb") as f:
        bras = f.read()
    errs = []
    if bras.startswith(b"\xef\xbb\xbf"):
        errs.append("存在 BOM")
    txt = bras.decode("utf-8")
    olines = txt.split("\r\n")
    if olines and olines[-1] == "":
        olines.pop()
    if len(olines) != n:
        errs.append("行数不一致 in=%d out=%d" % (n, len(olines)))
    for i, (a, b) in enumerate(zip(src_lines, olines), 1):
        if b.count("\t") != 1:
            errs.append("第%d行 TAB 数=%d" % (i, b.count("\t")))
            continue
        first, second = b.split("\t", 1)
        if first != a:
            errs.append("第%d行首列不符: %r vs %r" % (i, first, a))
        if second.strip() == "":
            errs.append("第%d行译文为空" % i)
        if a.count("/") != second.count("/"):
            errs.append("第%d行 '/' 数不符 %d vs %d" % (i, a.count("/"), second.count("/")))
        if a.count("[") != second.count("[") or a.count("]") != second.count("]"):
            errs.append("第%d行 '[]' 数不符" % i)
        if a.count("(") != second.count("(") or a.count(")") != second.count(")"):
            errs.append("第%d行 '()' 数不符" % i)
    if "\n\n" in txt.replace("\r\n", "\n"):
        errs.append("存在空行")
    if b"\r\n" not in bras:
        errs.append("不是 CRLF 行尾")

    print("输入行数:", n)
    print("输出行数:", len(olines))
    print("保留原文条数:", len(KEEP))
    for k in KEEP:
        print("  KEEP:", repr(k))
    if errs:
        print("自检失败:")
        for e in errs[:50]:
            print("  -", e)
        sys.exit(1)
    print("自检通过")


if __name__ == "__main__":
    main()
