# -*- coding: utf-8 -*-
"""生成 part-19.tsv：chunk-19 地名汉化(T-W 段)。"""
import io, os, sys

IN = r"D:\DSH\军事游戏汉化\work\atomic\chunks\chunk-19.tsv"
OUT = r"D:\DSH\军事游戏汉化\work\atomic\zh\part-19.tsv"

# 通用通名后缀(末尾整词替换)
def suffix_zh(s):
    rules = [
        (" River", "河"), (" river", "河"), (" Lake", "湖"), (" lake", "湖"),
        (" Bay", "湾"), (" Canal", "运河"), (" Airfield", "机场"),
        (" Airport", "机场"), (" Airodrome", "机场"), (" Station", "站"),
        (" Island", "岛"), (" Sea", "海"), (" Point", "角"),
        (" Heights", "高地"), (" Forest", "森林"), (" Bridge", "桥"),
        (" Creek", "溪"), (" Beach", "海滩"), (" Abbey", "修道院"),
    ]
    for en, zh in rules:
        if s.endswith(en) and len(s) > len(en):
            return s[: -len(en)] + zh
    return None

# 专名精确映射(含通名已并入)
EXACT = {
    # T 段
    "Tuz Gölü": "图兹湖",
    "Tuzlov": "图兹洛夫",
    "Tuzlov River": "图兹洛夫河",
    "Tverskaya": "特维尔",
    "Tygelsjö": "蒂格尔瑟",
    "Tylmanowa": "蒂尔马诺瓦",
    "Tymoshivka (Timoshevka)": "季莫希夫卡(季莫舍夫卡)",
    "Tyttebaervik": "蒂特拜尔维克",
    "Twiss Green": "特维斯格林",
    "Tykhonivka (Tikhonovka)": "季霍尼夫卡(季霍诺夫卡)",
    # U 段
    "US Air Force": "美国空军",
    "US Army": "美国陆军",
    "US Rangers": "美国游骑兵",
    "USS Boise": "博伊西号",
    "USS Boise/Reconnaissance Wing": "博伊西号/侦察联队",
    "USS Dallas": "达拉斯号",
    "USS Maddox": "马多克斯号",
    "USS Savannah": "萨凡纳号",
    "USS Shubrick": "舒布里克号",
    "Udozero": "乌多泽罗",
    "Udarnyk (Neykirkh)": "乌达尔尼克(奈基尔希)",
    "Udy River": "乌德河",
    "Ugra River": "乌格拉河",
    "Uijongbu": "议政府",
    "Ukrainske (Nay Veg)": "乌克兰斯克(新路镇)",
    "Ukrainske (Otradnoye)": "乌克兰斯克(奥特拉德诺耶)",
    "Ulbrokas Forest": "乌尔布罗卡斯森林",
    "Ulyanovka": "乌里扬诺夫卡",
    "Ulyanovskiy": "乌里扬诺夫斯基",
    "Unecha": "乌涅恰",
    "Ungura Ezers": "温古拉湖",
    "Unstrut": "温斯特鲁特",
    "Upa River": "乌帕河",
    "Upenja": "乌佩尼亚",
    "Upper New York Bay": "上纽约湾",
    "Uram": "乌拉姆",
    "Urban Warfare in Moskva": "莫斯科城市战",
    "Urcel": "于尔塞勒",
    "Uritsk": "乌里茨克",
    "Usadishche": "乌萨季谢",
    "Usanli River": "乌桑雷河",
    "Usanli River (Yushanly)": "乌桑雷河(尤尚雷)",
    "Usatovo": "乌萨托沃",
    "Ushaki": "乌沙基",
    "Ushakov": "乌沙科夫",
    "Ushkovo": "乌什科沃",
    "Uspenka": "乌斯片卡",
    "Uspenovka": "乌斯佩诺夫卡",
    "Ussiya River": "乌西亚河",
    "Ust'-Demino": "乌斯季杰米诺",
    "Ust-Khoperskiy": "乌斯季霍佩尔斯基",
    "Ust-Labinsk": "乌斯季拉宾斯克",
    "Ust-Luga": "乌斯季卢加",
    "Ustrom River": "乌斯特罗姆河",
    "Utljuk Liman": "乌特柳克湾",
    "Uvarovo": "乌瓦罗沃",
    "Uzha River": "乌扎河",
    "Uzhakovo": "乌扎科沃",
    "Uzunlarske": "乌尊拉尔斯克",
    "Uzur-Nur lake": "乌祖尔淖尔湖",
    # V 段
    "Vafes": "瓦费斯",
    "Vaganovo": "瓦加诺沃",
    "Vailly-sur-Aisne": "艾讷河畔瓦伊",
    "Vainikkola": "瓦伊尼科拉",
    "Vainode (Wainoden)": "瓦伊诺德(瓦伊诺登)",
    "Vaivara": "瓦伊瓦拉",
    "Vakarjani": "瓦卡尔亚尼",
    "Vakulivka": "瓦库利夫卡",
    "Valdevaqueros": "巴尔德瓦克罗",
    "Valkenburg Airodrome": "法尔肯堡机场",
    "Valmiera (Volmari, Wolmar)": "瓦尔米耶拉(沃尔马里，沃尔玛)",
    "Valujec": "瓦卢耶茨",
    "Valuyevskiy": "瓦卢耶夫斯基",
    "Valyava": "瓦利亚瓦",
    "Vamos": "瓦莫斯",
    "Vange Creek": "万格溪",
    "Vansu Bridge": "万苏桥",
    "Vaqar (Vasqarr)": "瓦卡尔(瓦斯卡尔)",
    "Varenne River": "瓦雷讷河",
    "Varenovka": "瓦列诺夫卡",
    "Varenikovskaya": "瓦列尼科夫斯卡亚",
    "Varlamovskiy": "瓦尔拉莫夫斯基",
    "Vartava": "瓦尔塔瓦",
    "Vartry": "瓦特里",
    "Varvarivka": "瓦尔瓦里夫卡",
    "Vasilevo-Petrovskoe": "瓦西列沃彼得罗夫斯科耶",
    "Vasilyevo-Khanzhonovka": "瓦西列沃汉若诺夫卡",
    "Vasylivka": "瓦西利夫卡",
    "Vasylivka (Vasil'yevka)": "瓦西利夫卡(瓦西里耶夫卡)",
    "Vasylivka (Vasilyevka)": "瓦西利夫卡(瓦西里耶夫卡)",
    "Vasylivka-na-Dnipri (Vasilyevka)": "第聂伯河畔瓦西利夫卡(瓦西里耶夫卡)",
    "Vasiliko": "瓦西利科",
    "Vasilyevo": "瓦西列沃",
    "Vaskovo Airfield": "瓦斯科沃机场",
    "Vaslui River": "瓦斯卢伊河",
    "Vassvik (Forra)": "瓦斯维克(福拉)",
    "Vatican City": "梵蒂冈城",
    "Vavylove": "瓦维洛韦",
    "Veduga River": "韦杜加河",
    "Veerse Meer": "费尔斯湖",
    "Velencei-tó": "韦伦采湖",
    "Velez-Malaga": "贝莱斯马拉加",
    "Velichevo Ur-Shche": "韦利切沃乌尔谢",
    "Velika Koreniha": "大科雷尼哈",
    "Velikij Utluk (Bolshoy Utlyuk)": "大乌特柳克(大乌特柳克)",
    "Velikiy Khutor": "大胡托尔",
    "Velikovechnoye (Velikoye)": "韦利科韦奇诺耶(大村)",
    "Veliky Novgorod": "大诺夫哥罗德",
    "Velyka Kardashynka": "大卡尔达申卡",
    "Velyka Ternivka (Bolshaya Ternovka)": "大捷尔尼夫卡(大捷尔诺夫卡)",
    "Velykyi Kuialnyk River": "大库亚利尼克河",
    "Venlo-West": "芬洛西",
    "Venloue River": "芬卢河",
    "Venta (Windau)": "文塔(温道)",
    "Verson": "韦尔松",
    "Verebushka River": "韦列布什卡河",
    "Vereika River": "韦列伊卡河",
    "Verenda River": "韦伦达河",
    "Verguny-Pologi": "韦尔古内波洛吉",
    "Verkhivtseve (Verkhovtsevo)": "韦尔希夫采韦(韦尔霍夫采沃)",
    "Verkhne Tsaritsinskiy": "上察里岑斯基",
    "Verkhne-Pogromnoye": "上波格罗姆诺耶",
    "Verkhnebakanskiy": "上巴坎斯基",
    "Verkhnij Bishkin": "上比什金",
    "Verkhniy Tokmak": "上托克马克",
    "Verkhnodniprovsk (Verkhnedneprovsk)": "上第聂伯罗夫斯克(上第聂伯罗夫斯克)",
    "Verkhnyaya Akhtuba": "上阿赫图巴",
    "Verkhnyaya Yelshanka": "上叶尔尚卡",
    "Verni": "韦尔尼",
    "Vertyachiy": "韦尔佳奇",
    "Veryazha River": "韦里亚扎河",
    "Veselava": "韦谢拉瓦",
    "Vesele": "韦谢列",
    "Vesele (Veseloye)": "韦谢列(韦肖洛耶)",
    "Vesele Druhe (Veselyy Vtoroy)": "第二韦谢列(第二韦肖雷)",
    "Veselo-Voznesenka": "韦谢洛沃兹涅先卡",
    "Veselyi (Proletarskaya Diktatura)": "韦肖雷(无产阶级专政村)",
    "Veshenskaya (Vyoshenskaya)": "维奥申斯卡亚(维奥申斯卡亚)",
    "Viazma": "维亚济马",
    "Vichtbach": "菲特河",
    "Victoria (Rabat)": "维多利亚(拉巴特)",
    "Vie River": "维河",
    "Vierhnieie Turovo": "上图罗沃",
    "Vierville-sur-Mer": "滨海维耶维尔",
    "Vietnam People's Army HQ": "越南人民军总部",
    "Vigarano Mainarda": "维加拉诺迈纳尔达",
    "Vila Nova": "新镇",
    "Vila de Sao Sebastiao": "圣塞巴斯蒂昂镇",
    "Villa San Giovanni": "圣乔瓦尼镇",
    "Villafranca Tirrena": "蒂雷尼亚自由镇",
    "Villanueva de Algaidas": "阿尔盖达斯新镇",
    "Villanueva de Cauche": "考切新镇",
    "Villanueva del Rosario": "罗萨里奥新镇",
    "Villard": "维拉尔",
    "Vilsanka River": "维尔尚卡河",
    "Vinnovka": "温诺夫卡",
    "Vinogradnoye": "维诺格拉德诺耶",
    "Vishera River": "维舍拉河",
    "Vishnyovka (Tarkhan)": "维什尼奥夫卡(塔尔汉)",
    "Vitrivka (Vetrovka)": "维特里夫卡(韦特罗夫卡)",
    "Vladislavovka": "弗拉季斯拉沃夫卡",
    "Vladsloo (Vladslo)": "弗拉兹洛(弗拉兹洛)",
    "Vliegbasis Deelen": "德伦空军基地",
    "Vliegbasis Koksijde": "科克赛德空军基地",
    "Vodino (Vodyanoy)": "沃季诺(沃佳诺伊)",
    "Volgo-Donskoy Kanal": "伏尔加-顿河运河",
    "Volkel Airport": "福尔克尔机场",
    "Volkhov River": "沃尔霍夫河",
    "Volkssturm Aachen": "亚琛国民突击队",
    "Volkssturm Eifel": "艾费尔国民突击队",
    "Volma River": "沃尔马河",
    "Volodarskiy": "沃洛达尔斯基",
    "Voloshino": "沃洛希诺",
    "Voloske (Voloskoye)": "沃洛斯凯(沃洛斯科耶)",
    "Volost' River": "沃洛斯特河",
    "Volosta-Pyatnitsa": "沃洛斯塔皮亚特尼察",
    "Volyntsevo": "沃伦采沃",
    "Vop' River": "沃皮河",
    "Voronesh River": "沃罗涅日河",
    "Voronezskaya": "沃罗涅日斯卡亚",
    "Voronkov": "沃龙科夫",
    "Voronok": "沃罗诺克",
    "Vorontsova": "沃龙佐瓦",
    "Vorontsovka": "沃龙佐夫卡",
    "Vorontsovskaya": "沃龙佐夫斯卡亚",
    "Voroshilovo": "伏罗希洛沃",
    "Voskresenka": "沃斯克列先卡",
    "Voskresenske": "沃斯克列先斯凯",
    "Voskresenskoye": "沃斯克列先斯科耶",
    "Vovnihy (Vovnigi)": "沃夫尼希(沃夫尼吉)",
    "Voynosolovo": "沃伊诺索洛沃",
    "Vozdvizhenskaya": "沃兹德维任斯卡亚",
    "Voznesenka": "沃兹涅先卡",
    "Voznesenskoye": "沃兹涅先斯科耶",
    "Voznesenye": "沃兹涅谢尼耶",
    "Vozrozhdeniye (Kavantsari)": "沃兹罗日杰尼耶(卡万察里)",
    "Vsevolozhskiy": "弗谢沃洛日斯基",
    "Vtoroy Poltavskiy": "第二波尔塔夫斯基",
    "Vyacheslavka": "维亚切斯拉夫卡",
    "Vyazma Airport": "维亚济马机场",
    "Vyazma Airborne Operation": "维亚济马空降战役",
    "Vyazma-Bryanskaya": "维亚济马布良斯卡亚",
    "Vyazovka": "维亚佐夫卡",
    "Vyazovyy": "维亚佐维",
    "Vyborg (Viipuri)": "维堡(维普里)",
    "Vyboyevo": "维博耶沃",
    "Vydel": "维杰尔",
    "Vygostrov": "维戈斯特罗夫",
    "Vynohradne (Alt-Nassau)": "维诺赫拉德内(旧拿骚)",
    "Vyshestebliyevskaya": "维舍斯捷布利耶夫斯卡亚",
    "Vyskatko": "维斯喀特科",
    "Vysokopol'ye": "维索科波利耶",
    "Vysun River": "维孙河",
    # W 段
    "Waal river": "瓦尔河",
    "Wadi Tine River": "瓦迪廷河",
    "Waikiki Beach": "怀基基海滩",
    "Waipi'O Point": "怀皮奥角",
    "Walawa Heights": "瓦拉瓦高地",
    "Waltham Abbey": "沃尔瑟姆修道院",
    "Wami River": "瓦米河",
    "Ward River": "沃德河",
    "Warsaw Airport": "华沙机场",
}

KEEP = []  # 保留原文行

def main():
    with io.open(IN, "r", encoding="utf-8") as f:
        src = f.read()
    # 保持原行尾风格探测
    lines = src.split("\r\n") if "\r\n" in src else src.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    n = len(lines)

    out = []
    for s in lines:
        if s in EXACT:
            zh = EXACT[s]
        else:
            suf = suffix_zh(s)
            if suf is not None:
                head = s[: -len(s.split()[-1]) - 1] if False else None
                base = s[: s.rfind(" ")]
                if base in EXACT:
                    zh = EXACT[base] + suf[-1:] if False else EXACT[base] + suf
                    # 若 EXACT[base] 已含通名则不加；简单处理：直接拼接后缀
                    zh = EXACT[base] + suf
                else:
                    zh = None
            else:
                zh = None
            if zh is None:
                KEEP.append(s)
                zh = s
        out.append(s + "\t" + zh)

    # 写文件：UTF-8 无 BOM，CRLF
    data = "\r\n".join(out) + "\r\n"
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, "wb") as f:
        f.write(data.encode("utf-8"))

    # ---------- 自检 ----------
    with io.open(OUT, "rb") as f:
        raw = f.read()
    errs = []
    if raw.startswith(b"\xef\xbb\xbf"):
        errs.append("存在 BOM")
    txt = raw.decode("utf-8")
    olines = txt.split("\r\n")
    if olines and olines[-1] == "":
        olines.pop()
    if len(olines) != n:
        errs.append("行数不一致 in=%d out=%d" % (n, len(olines)))
    for i, (a, b) in enumerate(zip(lines, olines), 1):
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

    print("输入行数:", n)
    print("输出行数:", len(olines))
    print("保留原文条数:", len(KEEP))
    for k in KEEP:
        print("  KEEP:", k)
    if errs:
        print("自检失败:")
        for e in errs[:50]:
            print("  -", e)
        sys.exit(1)
    print("自检通过")

if __name__ == "__main__":
    main()
