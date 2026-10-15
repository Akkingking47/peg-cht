# -*- coding: utf-8 -*-
"""地名译表 —— Cyber General 专属补充段（96 条）

★ 本段来源：D:\\PGForever1.021\\Cyber General\\Scenario\\mapnames.str
  该文件为 "格式 D"（名称在 20B 槽位内连续存放，见 cyber_names.py）。
  其中 1459 条真实地名 + 131 条河流名已被 place_A..Z.py / river_zh.py 覆盖，
  本文件补齐剩余 96 条：波兰语虚构专名、地形名、少数遗漏的真实地名。

★ 译法口径（沿用全局规则，并针对 Cyber General 这一"架空波兰科幻战役"调整）：
  - 虚构波兰语专名 → 按波兰语读音音译（不硬造意译）
  - 带明显语义的虚构名 → 意译（如 Dzungla=丛林、Bezludzie=荒原）
  - 通用地形名（records 0..13 之外出现的同义项）→ 与已译地形名保持一致
  - 真实地名 → 用中文圈通行译名（Lwow=利沃夫、Mitau=米塔瓦 …）

★ 长度硬约束：名称 ≤17 字节（5 汉字 = 15B）；本段全部遵守。
"""

PLACE_CYBER = {
    # ── 通用/地形名（与 records 0..13 口径一致）──────────────
    "Plaskowyz": "台地",
    "Jalowe wzgorza": "贫瘠丘陵",
    "Dzungla": "丛林",
    "Pole minowe": "雷场",
    "Bezludzie": "荒原",
    "Teren Zabudowany": "建筑区",
    "Baza": "基地",
    "Wioska": "村庄",
    "Niestabilne Urwisko": "崩崖",
    "Row": "沟壑",
    "Kosmodrom": "航天港",
    "Stacja": "站",
    "Dok kosmiczny": "太空船坞",
    "Stacja Komunikacyjna": "通信站",
    "Struktura": "建筑体",
    "Ladowisko": "着陆场",
    "Intestinum 1": "因特斯提努姆1",

    # ── 虚构波兰语专名（音译）──────────────────────────────
    "Gnozja": "格诺兹亚",
    "Sacrum": "萨克鲁姆",
    "Indust": "因杜斯特",
    "Kamienna": "卡缅纳",
    "Litania": "利塔尼亚",
    "Pastor": "帕斯托尔",
    "Hostia": "霍斯蒂亚",
    "Wolnomysl": "沃尔诺梅希尔",
    "Aresia": "阿雷西亚",
    "Hekatomba": "赫卡通巴",
    "Ekstasis": "埃克斯塔西斯",
    "Tolerance": "托勒兰策",
    "Pazernia": "帕泽尼亚",
    "Courtisane": "库尔蒂萨内",
    "Vulgaris": "武尔加里斯",
    "Neostradia": "内奥斯特拉",
    "Etnofilia": "埃特诺菲利亚",
    "Sacrofobis": "萨克罗福比斯",
    "Multicefalios": "穆尔蒂切法利",
    "Bimberpoj": "宾贝尔波伊",
    "Seksonia": "塞克索尼亚",
    "Bachusium": "巴库西乌姆",
    "Dementia": "德门提亚",
    "Warchlak": "瓦尔赫拉克",
    "Locha": "洛哈",
    "Plugawion": "普鲁加维翁",
    "Gach": "加赫",
    "Basior": "巴西奥尔",
    "Trzeszcze": "特热什切",
    "Darniak": "达尔尼亚克",
    "Gamrat": "加姆拉特",
    "Jucha": "尤哈",
    "Krykucha": "克雷库哈",
    "Legawiec": "莱加维茨",
    "Mykita": "梅基塔",
    "Pokot": "波科特",
    "Rabiec": "拉别茨",
    "Samura": "萨穆拉",
    "Siuta": "休塔",
    "Szydlarz": "希德拉日",
    "Wadera": "瓦德拉",
    "Kaszipsok": "卡希普索克",
    "Gruberon": "格鲁贝龙",
    "Awiaplok": "阿维亚普洛克",
    "Enklawa": "恩克拉瓦",
    "Borelioza": "博雷利奥扎",
    "Zadupie": "扎杜皮耶",
    "Kiepawnik": "凯帕夫尼克",
    "Burownia": "布罗夫尼亚",
    "Patelnia": "帕特尔尼亚",
    "Dekielin": "德凯林",
    "Celebron": "采莱布龙",
    "Albiowan": "阿尔比奥万",
    "Proz": "普罗兹",
    "Kosmos": "科斯莫斯",
    "Mr Syntetic": "合成先生",
    "Kompleks 04": "综合区 04",
    "Kompleks 07": "综合区 07",
    "Kompleks 11": "综合区 11",

    # ── 拉丁语/概念性虚构名 ────────────────────────────────
    "Alter Ego": "另一个我",
    "Ambitiosa": "安比提奥萨",
    "Anima Vilis": "卑微之魂",
    "Nihilis": "虚无主义",
    "Bellum Omnia": "全民之战",
    "Pauperes": "贫民",

    # ── 少数真实地名（原文件拼写与主表不同，单列）──────────
    "Karakose": "卡拉克塞",
    "Agri": "阿格里",
    "Lemberg": "伦贝格",
    "Lwow": "利沃夫",
    "Mesopotamia": "美索不达米亚",
    "Iraq": "伊拉克",
    "Mitau": "米塔瓦",
    "Yelgava": "叶尔加瓦",
    "Monastir": "莫纳斯提尔",
    "Bitola": "比托拉",
    "Persia": "波斯",
    "Iran": "伊朗",

    # ── 源文件笔误/拼接残留（保留原样语境，取可读译名）──────
    "Haag            Derb": "海牙",
    "PleStacja": "普莱站",
}
