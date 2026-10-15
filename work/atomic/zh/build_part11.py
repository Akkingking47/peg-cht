# -*- coding: utf-8 -*-
"""chunk-11 -> part-11.tsv 汉化脚本（严格按 work/xscn/POLICY.md）。

输入：work/atomic/chunks/chunk-11.tsv   （400 行，单列地名/机构名/行动名）
输出：work/atomic/zh/part-11.tsv         （原文<TAB>译文，UTF-8 无 BOM，CRLF）

本片特点：L/M 开头地名为主（Langmo/Lanikai/Lanuvio/Laon/Li.../Ly.../Ma...），
          含大量「X (别名)」形式、少量机构名与行动名。

口径（与 part-01..10 保持一致）：
  - 地名：通行中文名优先，否则音译 + 通名后缀
      River→河 Lake/Ezers/Ozero/See→湖 Bay→湾 Sea→海
      Canal→运河 Airfield/Airport/Aerodrome→机场 Station→站
      Island→岛 Sound→海峡 Strait→海峡 Heights→高地 Hill→山
      Creek→溪 Channel→海峡 Bukt→湾 Strathmos→地峡
  - 括号内为别名 → 音译；通名部分一并译（Libauer See→利鲍湖）
  - [HILL]→[高地]，[FOREST]→[森林]（与 part-01/10 一致）
  - 行动名：Battle of X / Liberation of X / Landing at X / X Operation → 意译
  - 机构/编制：Luftflotte→航空队，Lokaler Volkssturm→地方国民突击队，
      MG Btl→机枪营，IR z.b.V→特设步兵团，leD→轻装师（保留 leD 缩写作 leD 亦可）
  - 装备/舰船/飞机型号保留原文（MHS Inglefield / MTB-73 / M1 Moscow）
  - 未知缩写（MAAF/12.ASC/324.Fighter Group 整行）→ 整行保留
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'chunks', 'chunk-11.tsv')
DST = os.path.join(HERE, 'part-11.tsv')

# 逐行译文（顺序与输入严格一致，共 400 条）
ZH = [
    '朗莫',                                     # 1 Langmo
    '拉尼凯',                                   # 2 Lanikai
    '兰科韦 (兰茨克罗内)',                       # 3 Lankove (Landskrone)
    '拉努维奥',                                 # 4 Lanuvio
    '拉昂',                                     # 5 Laon
    '拉帕努夫',                                 # 6 Lapanow
    '拉波明卡',                                 # 7 Lapominka
    '拉普捷沃',                                 # 8 Laptevo
    '拉普斯纳',                                 # 9 Lapusna
    '拉普斯纳河',                               # 10 Lapusna River
    '拉拉',                                     # 11 Laragh
    '拉奇蒙特',                                 # 12 Larchmont
    '拉尔代里亚',                               # 13 Larderia
    '拉尔多斯',                                 # 14 Lardos
    '拉尔加',                                   # 15 Larga
    '拉里姆纳',                                 # 16 Larimna
    '拉斯阿尔加米塔斯',                         # 17 Las Algamitas
    '拉斯托拉',                                 # 18 Lastola
    '拉斯特拉阿锡尼亚',                         # 19 Lastra a Signa
    '拉斯洛海吉山 (130 米) [高地]',              # 20 Laszlohegy (130 m) [HILL]
    '拉塔尚科',                                 # 21 Latashanko
    '拉滕',                                     # 22 Lathen
    '拉托诺沃',                                 # 23 Latonovo
    '劳伦斯贝格',                               # 24 Laurensberg
    '拉瓦舍沃',                                 # 25 Lavashevo
    '拉维尼',                                   # 26 Lavini
    '拉夫里奥',                                 # 27 Lavrion
    '劳灵溪',                                   # 28 Lawling Creek
    '拉亚',                                     # 29 Laya
    '莱察尔米',                                 # 30 Laytsalmi
    '医院船',                                   # 31 Lazarettschiff
    '拉扎列夫斯科耶',                           # 32 Lazarevskoye
    '拉扎罗',                                   # 33 Lazzaro
    '勒布尔圣莱奥纳尔',                         # 34 Le Bourg Saint-Leonard
    '勒沙尔梅尔',                               # 35 Le Charmel
    '勒迪亚芒',                                 # 36 Le Diamant
    '勒弗朗索瓦',                               # 37 Le Francois
    '勒马兰',                                   # 38 Le Marin
    '勒讷堡',                                   # 39 Le Neufbourg
    '勒帕讷 (德帕讷)',                           # 40 Le Panne (De Panne)
    '勒普雷舍尔',                               # 41 Le Precheur
    '勒罗贝尔',                                 # 42 Le Robert
    '勒罗泽尔',                                 # 43 Le Rozel
    '勒泰耶尔',                                 # 44 Le Teilleul
    '勒泰伊',                                   # 45 Le Theil
    '勒瓦尔特吕',                               # 46 Le Valtru
    '莱巴',                                     # 47 Leba
    '列别杰夫卡 (波卢斯塔诺克洪卡尼耶米)',       # 48 Lebedevka (Polustanok Khonkaniyemi)
    '列别季',                                   # 49 Lebedi
    '列比亚希耶',                               # 50 Lebiashie
    '勒比塞',                                   # 51 Lebisey
    '列布诺',                                   # 52 Lebno
    '列比亚日耶',                               # 53 Lebyazhye
    '莱基亚奥',                                 # 54 Lechaio
    '莱达',                                     # 55 Leda
    '莱德沙姆',                                 # 56 Ledsham
    '莱杜尔加',                                 # 57 Ledurga
    '莱尔',                                     # 58 Leer
    '莱芬赫 (莱芬厄)',                           # 59 Leffinghe (Leffinge)
    '莱吉奥诺沃',                               # 60 Legionowo
    '莱顿',                                     # 61 Leiden
    '利',                                       # 62 Leigh
    '利贝克',                                   # 63 Leigh Beck
    '莱讷',                                     # 64 Leine
    '莱索',                                     # 65 Leissow
    '莱克斯利普',                               # 66 Leixlip
    '莱克',                                     # 67 Lek
    '莱克 (莱克)',                               # 68 Leke
    '莱克内斯',                                 # 69 Leknes
    '伦巴赫',                                   # 70 Lembach
    '朗布雷',                                   # 71 Lembree
    '莱纳姆',                                   # 72 Lenham
    '列宁纳万',                                 # 73 Leninavan
    '列宁格勒 (圣彼得堡)',                       # 74 Leningrad (St. Petersburg)
    '列尼诺',                                   # 75 Lenino
    '列宁斯科耶',                               # 76 Leninskoye
    '朗斯',                                     # 77 Lens
    '伦斯维克',                                 # 78 Lensvik
    '伦蒂尼',                                   # 79 Lentini
    '伦维克',                                   # 80 Lenvik
    '伦维克马克',                               # 81 Lenvikmark
    '利奥尼亚',                                 # 82 Leonia
    '列奥尼多沃',                               # 83 Leonidovo
    '列奥诺沃',                                 # 84 Leonovo
    '莱奥瓦',                                   # 85 Leova
    '列佩利',                                   # 86 Lepel
    '莱尔河',                                   # 87 Lerre River
    '勒威克',                                   # 88 Lerwick
    '莱穆瓦捷达隆',                             # 89 Les Moitiers-d'Allonne
    '莱穆瓦捷昂博普图瓦',                       # 90 Les Moitiers-en-Bauptois
    '莱皮厄',                                   # 91 Les Pieux
    '莱特鲁瓦伊莱',                             # 92 Les Trois Ilets
    '列什切夫斯克',                             # 93 Leshchevsk
    '莱斯基',                                   # 94 Leski
    '列斯科洛沃',                               # 95 Leskolovo
    '莱希涅沃 (莱斯瑙)',                         # 96 Lesniewo (Lessnau)
    '列斯诺伊',                                 # 97 Lesnoy
    '列索巴扎',                                 # 98 Lesobaza
    '列索蓬克特·叶古特',                        # 99 Lesopunkt Yegut
    '莱特尼察',                                 # 100 Letnica
    '列特尼亚亚',                               # 101 Letnyaya
    '拉脱维亚骑兵营',                           # 102 Lettische Kavallerie-Abt.
    '勒伊苏库西',                               # 103 Leuilly-sous-Coucy
    '洛伊特',                                   # 104 Leuth
    '莱瓦迪亚地峡站',                           # 105 Levadia Strathmos Station
    '莱布赫特湾',                               # 106 Leybucht
    '莱普鲁切伊',                               # 107 Leypruchey
    '莱斯当昂西',                               # 108 Leysdown-on-Sea
    '莱什 (莱什)',                               # 109 Lezhe (Lesh)
    '莱齐采 (伦西茨)',                           # 110 Lezyce (Lensitz)
    '尔戈沃',                                   # 111 Lgovo
    '利安河',                                   # 112 Liane River
    '弗里斯兰解放',                             # 113 Liberation of Friesland
    '罗马解放',                                 # 114 Liberation of Rome
    '利卡塔',                                   # 115 Licata
    '利基河',                                   # 116 Licky River
    '利贝罗瑟',                                 # 117 Lieberose
    '大利耶拉尤格拉河 (大亚格尔河)',             # 118 Liela Jugla (Gross Jagel) River
    '利耶莱湖 (无法通行)',                       # 119 Lielais Lake (Impass)
    '利耶莱泽尔斯',                             # 120 Lielezers
    '利尔斯陶佩 (陶佩, 罗普)',                   # 121 Lielstraupe (Straupe, Roop)
    '利耶卢佩河',                               # 122 Lielupe River
    '利耶帕',                                   # 123 Liepa
    '利耶帕亚 (利鲍)',                           # 124 Liepaja (Libau)
    '利耶帕亚机场',                             # 125 Liepaja Airport
    '利耶帕亚湖 (利鲍湖)',                       # 126 Liepajas Ezers (Libauer See)
    '利耶普塞塔斯',                             # 127 Liepsetas
    '列特尔',                                   # 128 Liettres
    '列万',                                     # 129 Lievin
    '利加里亚',                                 # 130 Ligaria
    '利加特内',                                 # 131 Ligatne
    '利加特内河',                               # 132 Ligatne River
    '利贾',                                     # 133 Ligia
    '利科夫斯科耶',                             # 134 Likovskoye
    '利兰',                                     # 135 Liland
    '利兰斯卡尔',                               # 136 Lilandskar
    '利莱尔',                                   # 137 Lillers
    '利曼',                                     # 138 Liman
    '米乌斯潟湖',                               # 139 Liman Miusskiy
    '斯拉德基潟湖',                             # 140 Liman Sladkiy
    '利马诺瓦',                                 # 141 Limanowa
    '林巴日 (莱姆斯劳, 莱姆萨尔)',               # 142 Limbazi (Lemslau, Lemsal)
    '利姆港',                                   # 143 Limhamn
    '利姆内斯',                                 # 144 Limnes
    '利姆尼',                                   # 145 Limni
    '林道',                                     # 146 Lindau
    '林德赫斯特',                               # 147 Lindhurst
    '林多斯',                                   # 148 Lindos
    '利内茨',                                   # 149 Linec
    '林格河',                                   # 150 Linge river
    '林菲尔德',                                 # 151 Lingfield
    '利尼亚 (林德)',                             # 152 Linia (Linde)
    '利佩齐',                                   # 153 Lipetsy
    '利波夫卡河',                               # 154 Lipovka River
    '利波夫斯科耶湖',                           # 155 Lipovskoye Ozero
    '利珀',                                     # 156 Lippe
    '利里',                                     # 157 Liri
    '利斯古尔',                                 # 158 Lisgoold
    '利西诺斯',                                 # 159 Lisiy Nos
    '小岛',                                     # 160 Little Island
    '小颈湾',                                   # 161 Little Neck Bay
    '小沃尔辛厄姆',                             # 162 Little Walsingham
    '利特尔斯通昂西',                           # 163 Littlestone-on-Sea
    '利托里亚',                                 # 164 Littoria
    '柳博米里夫卡',                             # 165 Liubomyrivka
    '柳霍',                                     # 166 Liuho
    '利瓦迪',                                   # 167 Livadi
    '利物浦机场',                               # 168 Liverpool Airport
    '劳埃德港',                                 # 169 Lloyd Harbor
    '柳奇',                                     # 170 Lluc
    '柳奇马约尔',                               # 171 Llucmajor
    '洛运河 (洛瓦尔运河)',                       # 172 Lo Canal (Lovaart)
    '洛博伊基夫卡 (洛博伊科夫卡)',               # 173 Loboikivka (Loboykovka)
    '洛赫卡尔德',                               # 174 Loch Calder
    '洛赫格拉斯',                               # 175 Loch Glass
    '洛赫莫尔',                                 # 176 Loch Morle
    '尼斯湖',                                   # 177 Loch Ness
    '洛赫瓦滕',                                 # 178 Loch Watten
    '洛德',                                     # 179 Lode
    '洛德马',                                   # 180 Lodma
    '洛嫩',                                     # 181 Loenen
    '洛戈夫斯克',                               # 182 Logowskij
    '洛哈',                                     # 183 Loja
    '地方国民突击队',                           # 184 Lokaler Volkssturm
    '地方国民突击队',                           # 185 Lokaler Volksturm
    '洛克巴坦',                                 # 186 Lokbatan
    '洛科季',                                   # 187 Lokot
    '隆巴尔齐德 (隆巴尔兹德)',                   # 188 Lombartzyde (Lombardsijde)
    '隆马',                                     # 189 Lomma
    '隆马湾',                                   # 190 Lomma Bukt
    '罗蒙诺索夫 (奥拉宁鲍姆)',                   # 191 Lomonosov (Oranienbaum)
    '长滩',                                     # 192 Long Beach
    '长岛',                                     # 193 Long Island
    '长岛登陆',                                 # 194 Long Island Landing
    '长岛海峡',                                 # 195 Long Island Sound
    '朗霍普',                                   # 196 Longhope
    '隆格滨海',                                 # 197 Longues-sur-Mer
    '隆维利耶',                                 # 198 Longvilliers
    '洛 (洛)',                                   # 199 Loo (Lo)
    '洛潘河',                                   # 200 Lopan' River
    '洛波坚',                                   # 201 Lopoten'
    '洛斯巴里奥斯',                             # 202 Los Barrios
    '洛斯科尔蒂希略斯',                         # 203 Los Cortijillos
    '洛斯利亚诺斯',                             # 204 Los Lanos
    '洛斯利亚诺斯',                             # 205 Los Llanos
    '洛谢沃 (拉帕莱宁)',                         # 206 Losevo (Lappalainen)
    '洛希尼',                                   # 207 Losinj
    '洛斯米诺',                                 # 208 Losmino
    '格但斯克弗热什奇机场',                     # 209 Lotnisko Gdansk-Wrzeszcz
    '普茨克机场',                               # 210 Lotnisko Puck
    '洛特诺耶',                                 # 211 Lotnoie
    '劳登山',                                   # 212 Loudoun Heights
    '卢基夏',                                   # 213 Loukissia
    '卢萨基斯',                                 # 214 Lousakies
    '劳斯山',                                   # 215 Lousberg
    '卢特拉',                                   # 216 Loutra
    '卢特拉艾迪普苏',                           # 217 Loutra Aidhipsou
    '洛瓦尔',                                   # 218 Lovaart
    '洛瓦什拜雷尼厄尔多 [森林]',                 # 219 Lovasberenyi-erdo [FOREST]
    '洛维茨维尔',                               # 220 Lovettsville
    '下纽约湾',                                 # 221 Lower New York Bay
    '下莱茵河',                                 # 222 Lower Rhine river
    '洛扎诺夫卡',                               # 223 Lozanovka
    '洛宗河',                                   # 224 Lozon River
    '洛佐瓦特卡',                               # 225 Lozovatka
    '洛祖瓦特卡 (第二洛佐瓦特卡)',               # 226 Lozuvatka (Lozovatka Vtoraya)
    '洛祖瓦特卡河',                             # 227 Lozuvatka River
    '卢布斯科 (佐默费尔德)',                     # 228 Lubsko (Sommerfeld)
    '卢肯',                                     # 229 Lucan
    '卢卡斯溪',                                 # 230 Lucas Run
    '卢基亚',                                   # 231 Luchia
    '卢考',                                     # 232 Luckau
    '卢肯瓦尔德',                               # 233 Luckenwalde
    '卢多维西',                                 # 234 Ludowici
    '第2航空队',                                # 235 Luftflotte 2
    '第3航空队',                                # 236 Luftflotte 3
    '第4航空队',                                # 237 Luftflotte 4
    '卢加湾',                                   # 238 Luga Bay
    '卢加河',                                   # 239 Luga River
    '卢戈沃耶',                                 # 240 Lugovoye
    '卢基',                                     # 241 Luki
    '卢科夫希纳',                               # 242 Lukovshchina
    '卢克特',                                   # 243 Lukty
    '卢纳',                                     # 244 Luna
    '卢纳察尔斯科戈',                           # 245 Lunacharskogo
    '卢纳察尔斯科耶 (阿索夫斯克)',               # 246 Lunacharskoye (Asovske)
    '隆德',                                     # 247 Lund
    '卢涅沃',                                   # 248 Lunevo
    '卢帕雷韦',                                 # 249 Lupareve
    '卢卡',                                     # 250 Luqa
    '卢什涅',                                   # 251 Lushnje
    '卢斯克',                                   # 252 Lusk
    '卢茨克',                                   # 253 Lutsk
    '卢斯和沃格尔',                             # 254 Luz i Vogel
    '卢扎伊卡 (努尔米)',                         # 255 Luzhayka (Nurmi)
    '卢日齐',                                   # 256 Luzhitsy
    '卢日诺',                                   # 257 Luzhno
    '卢容卡河',                                 # 258 Luzhonka River
    '卢济诺 (卢辛)',                             # 259 Luzino (Lusin)
    '利亚霍沃',                                 # 260 Lyakhovo
    '利亚科沃 (拉科瓦)',                         # 261 Lyakovo (Lakova)
    '雷奇科沃',                                 # 262 Lychkovo
    '利德',                                     # 263 Lydd
    '利古里奥',                                 # 264 Lygourio
    '利曼斯科耶 (库丘古雷)',                     # 265 Lymanske (Kuchugury)
    '利曼齐',                                   # 266 Lymantsi
    '利马尼',                                   # 267 Lymany
    '林布鲁克',                                 # 268 Lynbrook
    '莱内斯',                                   # 269 Lyness
    '利尔凯亚',                                 # 270 Lyrkeia
    '雷希奇',                                   # 271 Lyshchichi
    '雷索戈尔卡',                               # 272 Lysogorka
    '利思',                                     # 273 Lyth
    '柳比莫夫',                                 # 274 Lyubimov
    '柳博利亚德',                               # 275 Lyubolyady
    '柳比米夫卡 (柳比莫夫卡)',                   # 276 Lyubymivka (Lyubimovka)
    '柳宾',                                     # 277 Lyubyn
    'M1 莫斯科',                                # 278 M1 Moscow
    'M1 莫斯科 斯摩棱斯克 奥尔沙 明斯克',        # 279 M1 Smolensk Orsha Minsk
    'MAAF/12.ASC/324.Fighter Group',            # 280 MAAF/12.ASC/324.Fighter Group
    'MAAF/12.ASC/47.Bomb Group',                # 281 MAAF/12.ASC/47.Bomb Group
    'MAAF/12.ASC/86.FB Group',                  # 282 MAAF/12.ASC/86.FB Group
    '第2机枪营/第200特设步兵团/第5轻装师',       # 283 MG Btl 2/IR z.b.V 200/5. leD
    '第8机枪营/第200特设步兵团/第5轻装师',       # 284 MG Btl 8/IR z.b.V 200/5. leD
    '机枪/第11步兵旅',                          # 285 MG/11thInfBrig.
    '机枪/第78师',                              # 286 MG/78thDiv.
    '机枪/布莱德部队',                          # 287 MG/BLADE FORCE
    '英格尔菲尔德号医疗船',                     # 288 MHS Inglefield
    'MTB-73',                                   # 289 MTB-73
    '马斯',                                     # 290 Maas
    '马斯河',                                   # 291 Maas river
    '马斯-瓦尔运河',                            # 292 Maas-Waal canal
    '马斯博梅尔',                               # 293 Maasbommel
    '格拉齐圣母村',                             # 294 Madonna delle Grazie
    '马夫舍奇',                                 # 295 Mafsheq
    '马加卢夫',                                 # 296 Magaluf
    '马格尔',                                   # 297 Maghull
    '马古拉',                                   # 298 Magoula
    '马格伦机场',                               # 299 Magrun Airfield
    '马古拉',                                   # 300 Magura
    '马扎尔阿尔马什',                           # 301 Magyaralmas
    '马希努伊',                                 # 302 Mahinui
    '马亚克 (帕夫洛娃)',                         # 303 Maiak (Pavlova)
    '马亚基',                                   # 304 Maiaki
    '梅德斯通',                                 # 305 Maidstone
    '主监狱',                                   # 306 Main Prison
    '曼特奈',                                   # 307 Maintenay
    '马约里',                                   # 308 Maiori
    '马卡罗夫卡',                               # 309 Makarovka
    '马卡罗沃',                                 # 310 Makarovo
    '马基夫卡 (马科夫卡)',                       # 311 Makivka (Makovka)
    '马科夫卡',                                 # 312 Makovka
    '马库夫',                                   # 313 Makow
    '马克罗尼索海峡',                           # 314 Makronisou Channel
    '马克西马',                                 # 315 Maksima
    '马克西莫夫',                               # 316 Maksimov
    '马克西莫夫卡 (阿泰涅梅茨基)',               # 317 Maksimovka (Atay Nemetskiy)
    '马克西姆·高尔基 (高尔基)',                  # 318 Maksyma Horkoho (Gor'kiy)
    '马克西姆·高尔基 (马克西姆·高尔基)',         # 319 Maksyma Horkoho (Maksim Gorkiy)
    '小布亚利克',                               # 320 Mal Bujalik
    '小别洛泽尔卡 (小别洛泽尔卡)',               # 321 Mala Biloserka (Malaya Belozerka)
    '小卡利尼夫卡 (卡利诺夫卡)',                 # 322 Mala Kalynivka (Kalinovka)
    '小卡尔达申卡',                             # 323 Mala Kardashynka
    '小科列尼哈',                               # 324 Mala Koreniha
    '马拉巴塔',                                 # 325 Malabata
    '马拉加',                                   # 326 Malaga
    '马拉海德',                                 # 327 Malahide
    '马拉卡萨',                                 # 328 Malakasa
    '马拉尔贝戈',                               # 329 Malalbergo
    '小克特穆克萨',                             # 330 Malaya Ketmuksa
    '小米亚格列卡',                             # 331 Malaya Myagreka
    '小涅克利诺夫卡 (帕夫洛夫斯基)',             # 332 Malaya Neklinovka (Pavlovskiy)
    '小乌尔祖加',                               # 333 Malaya Urzuga
    '小叶卡捷里诺夫卡',                         # 334 Malaya Yekaterinovka
    '马尔比亨',                                 # 335 Malburgen
    '小乌特柳克 (小乌特柳克)',                   # 336 Malij Utluk (Malyy Utlyuk)
    '马利诺夫卡',                               # 337 Malinovka
    '马尔默',                                   # 338 Malmö
    '马尔默布尔托夫塔机场',                     # 339 Malmö Bulltofta Airfield
    '小基尔萨诺夫卡',                           # 340 Malokirsanovka
    '小米哈伊利夫卡 (小米哈伊洛夫卡)',           # 341 Malomykhailivka (Malo-Mikhaylovka)
    '小彼得罗夫斯基',                           # 342 Malopetrovskiy
    '小索菲伊夫卡 (小索菲耶夫卡)',               # 343 Malosofiivka (Malaya Sofiyevka)
    '马耳他',                                   # 344 Malta
    '马尔维克',                                 # 345 Malvik
    '小卡茨 (小卡茨)',                           # 346 Maly Kack (Klein Katz)
    '马雷舍沃',                                 # 347 Malyshevo
    '小费奥多罗夫斯基',                         # 348 Malyy Fedorovskiy
    '小涅斯韦泰',                               # 349 Malyy Nesvetay
    '小普鲁德',                                 # 350 Malyy Prud
    '小沃尔霍韦茨河',                           # 351 Malyy Volkhovets River
    '小恰普尔尼基',                             # 352 Malyye Chapurniki
    '马马沙伊',                                 # 353 Mamashay
    '马马耶夫山岗 (102 高地)',                   # 354 Mamayev Kurgan (Heigh 102)
    '马马耶夫山岗 (102 高地)',                   # 355 Mamayev Kurgan (Height 102)
    '马纳科尔',                                 # 356 Manacor
    '马纳纳岛',                                 # 357 Manana Island
    '满洲作战',                                 # 358 Manchurian Operation
    '曼达',                                     # 359 Manda
    '曼迪卢',                                   # 360 Mandilou
    '曼杜迪翁',                                 # 361 Mandoudhion
    '曼德拉',                                   # 362 Mandra
    '曼吉特',                                   # 363 Mangit
    '曼哈西特',                                 # 364 Manhasset
    '曼哈西特湾',                               # 365 Manhasset Bay
    '曼哈顿 (纽约市)',                           # 366 Manhatten (NYC)
    '马尼尔瓦',                                 # 367 Manilva
    '曼内肯斯费勒 (曼内肯斯费勒)',               # 368 Mannekensveere (Mannekensvere)
    '曼海姆 (卡缅卡, 卡缅卡)',                   # 369 Mannheim (Kamenka, Kamjanka)
    '马诺伊林',                                 # 370 Manoylin
    '曼斯科夫',                                 # 371 Manskov
    '曼斯顿机场',                               # 372 Manston Aerodrome
    '马努佩 (埃绍)',                             # 373 Manupe (Echau)
    '马尼扬斯基河',                             # 374 Manyanskiy River
    '伊奥尼亚海',                               # 375 Mar Ionio
    '地中海',                                   # 376 Mar Mediterraneo
    '第勒尼安海',                               # 377 Mar Tirreno
    '马里扬斯卡亚',                             # 378 Mar'yanskaya
    '马拉蒂',                                   # 379 Marathi
    '马拉斯列耶夫卡',                           # 380 Marazleyevka
    '大理石拱门登陆区',                         # 381 Marble Arch Landing Area
    '马谢昂布里',                               # 382 Marchais-en-Brie
    '马尔凯',                                   # 383 Marche
    '马切尼利亚',                               # 384 Marchenilla
    '马尔恰纳',                                 # 385 Marciana
    '马尔恰纳马里纳',                           # 386 Marciana Marina
    '马尔达坎 (马尔达基扬内)',                   # 387 Mardakan (Mardakyany)
    '马尔德伊',                                 # 388 Mardeuil
    '马伦-凯塞尔',                              # 389 Maren-Kessel
    '马尔芬卡',                                 # 390 Marfinka
    '马尔福夫卡',                               # 391 Marfovka
    '马里亚多夫',                               # 392 Mariadorf
    '马里亚凯尔克',                             # 393 Mariakerke
    '马里亚尼夫卡',                             # 394 Marianivka
    '马里亚尼夫卡 (马里扬诺夫卡)',               # 395 Marianivka (Maryanovka)
    '玛丽-加朗特机场',                          # 396 Marie-Galante Airfield
    '玛丽霍尔姆',                               # 397 Marieholm
    '马里恩塔尔',                               # 398 Marienthal
    '马里恩塔尔 (马里扬诺夫卡)',                 # 399 Marienthal (Maryanovka)
    '马里戈',                                   # 400 Marigot
]


def main():
    src = open(SRC, 'rb').read().decode('utf-8')
    lines = src.split('\r\n')
    if lines and lines[-1] == '':
        lines = lines[:-1]
    assert len(lines) == 400, '输入行数不是 400: %d' % len(lines)
    assert len(ZH) == 400, '译文条数不是 400: %d' % len(ZH)

    out = ''.join(lines[i] + '\t' + ZH[i] + '\r\n' for i in range(400))
    with open(DST, 'wb') as f:
        f.write(out.encode('utf-8'))
    print('written %s (%d lines)' % (os.path.basename(DST), len(ZH)))


if __name__ == '__main__':
    main()
