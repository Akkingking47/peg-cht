# -*- coding: utf-8 -*-
"""chunk-10 -> part-10.tsv 汉化脚本（严格按 work/xscn/POLICY.md）。

输入：work/atomic/chunks/chunk-10.tsv   （400 行，单列地名/机构名）
输出：work/atomic/zh/part-10.tsv         （原文<TAB>译文，UTF-8 无 BOM，CRLF）

本片特点：K/L 开头地名为主，含匈牙利语（Kiscseripuszta/Kisfalud）与俄/乌语地名。

口径（与 part-01..05/07 保持一致）：
  - 地名：通行中文名优先，否则音译 + 通名后缀
      River→河 Lake/Ozero/Meer/Ezers→湖  Bay→湾  Sea→海  Gulf/Kolpos→湾
      Canal→运河  Airfield/Airport/Air Base/Airstrip→机场/空军基地
      Station→站  Island→岛  Hill/hegy→山  Pond→池  Liman→潟湖
      Farm→农庄  Fortification→要塞  Forts→炮台  Port→港  Bridgehead→桥头堡
  - 匈牙利语 hegy→山；Kis-→小，Nagy-→大；-puszta→普斯塔；-falud→法卢德
  - 机构：Kommando→司令部；Kriegsmarine→海军；Intel HQ→情报司令部
  - [HILL]→[高地]（与 part-01 一致）
  - (Impass)→(无法通行)；(Stinl) 无义 → 音译
  - 未知缩写（LRDG）/纯编号（Kommando/164. leADiv 中的 164.）→ 保留原文
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'chunks', 'chunk-10.tsv')
DST = os.path.join(HERE, 'part-10.tsv')

# 逐行译文（顺序与输入严格一致，共 400 条）
ZH = [
    '基尔西诺',                                   # 1 Kirsino
    '基什切里普斯塔',                             # 2 Kiscseripuszta (匈)
    '基谢尔泽尔什 (斯廷尔) 湖 (无法通行)',        # 3 Kiserzers (Stinl) Lake (Impass)
    '基谢捷夫',                                   # 4 Kisetev
    '基什法卢德',                                 # 5 Kisfalud (匈)
    '基舍沃',                                     # 6 Kishevo
    '基希讷乌 (基希讷乌)',                        # 7 Kishinev (Chisinau)
    '基斯洛夫',                                   # 8 Kislov
    '基萨莫斯',                                   # 9 Kissamos
    '基什韦伦采',                                 # 10 Kisvelence (匈)
    '基斯诺斯',                                   # 11 Kithnos
    '基万瓜',                                     # 12 Kiwangwa
    '基辅斯科耶',                                 # 13 Kiyevskoye
    '基济尔塔什斯基潟湖',                         # 14 Kiziltashskiy Liman
    '基佐梅斯',                                   # 15 Kizomys
    '克拉格斯港',                                 # 16 Klagshamn
    '克拉克斯维克',                               # 17 Klaksvig
    '克拉维尼',                                   # 18 Klavini
    '小拉德',                                     # 19 Klein Rade
    '小海',                                       # 20 Kleines Meer
    '克莱马蒂纳',                                 # 21 Klematina
    '克莱尼诺',                                   # 22 Klenino
    '克莱诺沃',                                   # 23 Klenovo
    '克莱辛',                                     # 24 Klessin
    '克莱茨科-波奇托夫斯基',                     # 25 Kletsko-Pochtovskiy
    '克列万',                                     # 26 Klevan'
    '克莱文',                                     # 27 Kleven
    '克利斯托',                                   # 28 Kliestow
    '克利门蒂',                                   # 29 Klimenti
    '克利莫沃',                                   # 30 Klimovo
    '克林齐',                                     # 31 Klinci
    '克洛诺',                                     # 32 Klonno
    '克洛斯',                                     # 33 Klos
    '克林基内',                                   # 34 Klynkyne
    '克涅维齐',                                   # 35 Knevitsy
    '克涅沃 (克涅文布鲁赫)',                      # 36 Kniewo (Kniewenbruch)
    '诺克拉哈',                                   # 37 Knockraha
    '诺克斯特深水湾',                             # 38 Knockster Tief
    '克尼亚泽沃',                                 # 39 Knyazevo
    '克尼亚日奇',                                 # 40 Knyazhichi
    '克尼亚日耶谢洛',                             # 41 Knyazhye Selo
    '克海吉 (228 米) [高地]',                     # 42 Ko-hegy (228 m)[HILL]
    '科巴琴科',                                   # 43 Kobacenko
    '科比亚克',                                   # 44 Kobylak
    '科布扎尔齐',                                 # 45 Kobzartsi
    '科贾代雷',                                   # 46 Kocadere
    '科切万',                                     # 47 Kochevan
    '科奇米茹夫',                                 # 48 Kocmyrzow
    '科格尔尼克河',                               # 49 Kogelnik River
    '科洛',                                       # 50 Kohlow
    '科尔沙伊德',                                 # 51 Kohlscheid
    '科赫特拉',                                   # 52 Kohtla
    '科科兹卡河',                                 # 53 Kokkozka River
    '科科角',                                     # 54 Koko Head
    '科科什基 (科科申肯)',                        # 55 Kokoszki (Kokoschken)
    '科克特贝尔 (普拉涅尔斯科耶)',                # 56 Koktebel (Planerskoye)
    '科拉罗夫卡',                                 # 57 Kolarovka
    '集体农庄克雷普',                             # 58 Kolchos Krep
    '科莱奇科沃 (科莱茨考)',                      # 59 Koleczkowo (Kolletzkau)
    '科列季诺',                                   # 60 Koledino
    '科列斯诺耶',                                 # 61 Kolesnoye
    '科林比亚',                                   # 62 Kolimbia
    '集体农庄阿赫图巴',                           # 63 Kolkhoznaya Akhtuba
    '集体农庄镇',                                 # 64 Kolkhoznyy
    '科勒峡湾',                                   # 65 Kollefjord
    '科洛杰济',                                   # 66 Kolodezi
    '科洛格里沃',                                 # 67 Kologrivo
    '科洛马克',                                   # 68 Kolomak
    '科洛马克河',                                 # 69 Kolomak River
    '科洛尼亚',                                   # 70 Kolonia
    '科尔皮诺',                                   # 71 Kolpino
    '科尔平斯卡亚',                               # 72 Kolpinskaya
    '科尔塔',                                     # 73 Kolta
    '科马里丘',                                   # 74 Komarichu
    '科马罗沃',                                   # 75 Komarovo
    '科姆科沃',                                   # 76 Komkovo
    '卡昂城防司令部',                             # 77 Kommandantur Caen
    '司令部/第164轻装航空师',                     # 78 Kommando/164. leADiv
    '司令部/第21装甲师',                          # 79 Kommando/21. PzDiv
    '司令部/第90轻装航空师',                      # 80 Kommando/90. leADiv
    '司令部/第8装甲团/第15装甲师',                # 81 Kommando/PzReg 8/15. PzD
    '共青城',                                     # 82 Komsomolskoye
    '科米沙内',                                   # 83 Komyshany
    '孔德拉特',                                   # 84 Kondraty
    '科涅茨博尔',                                 # 85 Konetsbor
    '科涅茨德沃里耶',                             # 86 Konetsdvorye
    '康斯巴克',                                   # 87 Kongsbak
    '孔卡河',                                     # 88 Konka River
    '孔科夫',                                     # 89 Konkov
    '孔科沃',                                     # 90 Konkovo
    '孔诺沃',                                     # 91 Konnovo
    '科诺普良卡',                                 # 92 Konoplianka
    '孔希诺',                                     # 93 Konshchino
    '康韦耶尔',                                   # 94 Konveyyer
    '科帕尼',                                     # 95 Kopani
    '科潘斯科耶湖',                               # 96 Kopanskoye Ozero
    '科普诺瓦托',                                 # 97 Kopnovato
    '科波里耶湾',                                 # 98 Koporye Bay
    '科普捷沃',                                   # 99 Koptevo
    '科尔布斯',                                   # 100 Korbous
    '科尔奇内',                                   # 101 Korchyne
    '科尔达绍夫卡',                               # 102 Kordashovka
    '科尔东',                                     # 103 Kordon
    '科尔福斯',                                   # 104 Korfos
    '科林斯湾 (科林斯湾)',                        # 105 Korinthiakos Kolpos (Gulf of Corinth)
    '科尔涅沃',                                   # 106 Kornevo
    '科尔宁',                                     # 107 Kornin
    '科罗巴诺沃',                                 # 108 Korobanovo
    '科罗别茨',                                   # 109 Korobets
    '科罗达',                                     # 110 Koroda
    '科罗皮',                                     # 111 Koropi
    '科罗斯特舍夫',                               # 112 Korostyshev
    '科罗蒂奇',                                   # 113 Korotich
    '科罗特诺',                                   # 114 Korotno
    '科罗夫金斯卡亚',                             # 115 Korovkinskaya
    '科罗夫尼基',                                 # 116 Korovniki
    '科尔萨克河',                                 # 117 Korsak River
    '科尔孙-舍甫琴基夫斯基',                      # 118 Korsun-Shevchenkivskyi
    '科尔特文',                                   # 119 Korteven
    '科雷托夫卡',                                 # 120 Korytovka
    '别格利茨卡亚沙嘴',                           # 121 Kosa Beglitskaya
    '克里瓦亚沙嘴',                               # 122 Kosa Krivaya
    '奥比托奇纳亚沙嘴',                           # 123 Kosa Obitochnaya
    '科萨科沃 (科萨考)',                          # 124 Kosakowo (Kossakau)
    '科沙雷',                                     # 125 Koshary
    '科舍瓦河',                                   # 126 Kosheva River
    '科斯科洛沃',                                 # 127 Koskolovo
    '科斯坚基',                                   # 128 Kostenki
    '科斯佳尼夫卡 (康斯坦丁诺夫卡)',              # 129 Kostiantynivka (Konstantinovka)
    '科斯托赫里佐韦',                             # 130 Kostohryzove
    '科斯特罗沃',                                 # 131 Kostrovo
    '科斯佳尼夫卡',                               # 132 Kostyantynivka
    '科斯佳尼夫卡 (康斯坦丁诺夫卡)',              # 133 Kostyantynivka (Konstantinovka)
    '科斯蒂奇',                                   # 134 Kostychi
    '科斯秋基',                                   # 135 Kostyuki
    '科希采',                                     # 136 Koszyce
    '科捷尔尼科沃',                               # 137 Kotelnikowo
    '科滕',                                       # 138 Kothen
    '科特林岛',                                   # 139 Kotlin Island
    '科特卢班',                                   # 140 Kotluban
    '科特雷',                                     # 141 Kotly
    '科特利亚雷韦',                               # 142 Kotlyareve
    '科托夫斯基',                                 # 143 Kotovskiy
    '科特拉诺夫斯基',                             # 144 Kotranovskiy
    '科秋扎内',                                   # 145 Kotyuzhany
    '昆杜罗斯',                                   # 146 Koundouros
    '库措波迪',                                   # 147 Koutsopodi
    '科瓦连科',                                   # 148 Kovalenko
    '科瓦列夫卡',                                 # 149 Kovalevka
    '科瓦利夫卡',                                 # 150 Kovalivka
    '科夫赖',                                     # 151 Kovray
    '科夫斯克 (科夫斯基)',                        # 152 Kovske (Kovskiy)
    '科维亚吉',                                   # 153 Kovyagi
    '科伊苏格',                                   # 154 Koysug
    '科伊苏格河',                                 # 155 Koysug River
    '科茹霍夫卡',                                 # 156 Kozhukhovka
    '科兹洛夫斯基',                               # 157 Kozlovskiy
    '科济尔卡',                                   # 158 Kozyrka
    '摩托化步兵营 第20/第21装甲师',               # 159 KradSchtzBat 20/21. PzDiv
    '克拉科利耶',                                 # 160 Krakolye
    '克拉科夫',                                   # 161 Krakow
    '克拉科维茨',                                 # 162 Krakowiec
    '救护车队 第533/第5轻装师',                   # 163 Krankenkraftwagenzug 533/5. leD
    '红近卫军斯科耶 (尼古拉耶夫斯科耶)',          # 164 Krashogvardeyskoye (Nikolayevskoye)
    '克拉西洛夫卡',                               # 165 Krasilovka
    '红斯洛博达',                                 # 166 Krasnaja Sloboda
    '红戈尔卡',                                   # 167 Krasnaya Gorka
    '红斯洛博达',                                 # 168 Krasnaya Sloboda
    '红斯洛博达 (切尔沃纳斯洛博达)',              # 169 Krasnaya Sloboda (Chervona Sloboda)
    '红乌克兰卡',                                 # 170 Krasnaya Ukrainka
    '克拉斯诺兹纳缅斯基',                         # 171 Krasno-Znamenskiy
    '红军村',                                     # 172 Krasnoarmeyskaya
    '克拉斯诺达尔机场 (帕什科夫斯基机场)',        # 173 Krasnodar Airport (Pashkovsky Airport)
    '克拉斯诺达尔-斯大林格勒',                    # 174 Krasnodar-Stalingrad
    '克拉斯诺亚尔斯克',                           # 175 Krasnojarsk
    '克拉斯诺库茨卡亚',                           # 176 Krasnokutskaya
    '克拉斯诺佩列科普斯克',                       # 177 Krasnoperekopsk
    '克拉斯诺波利耶',                             # 178 Krasnopolye
    '克拉斯诺耶',                                 # 179 Krasnoye
    '红谢洛',                                     # 180 Krasnoye Selo
    '红博尔',                                     # 181 Krasny Bor
    '红岛',                                       # 182 Krasny Ostrov
    '红色登陆场 (赫里斯托福罗夫卡)',              # 183 Krasnyi Desant (Khristo-Forovka)
    '红克里米亚',                                 # 184 Krasnyi Krym
    '克拉斯内',                                   # 185 Krasnyy
    '红克里米亚',                                 # 186 Krasnyy Krym
    '红罂粟',                                     # 187 Krasnyy Mak
    '红隼 (阿拉科普拉)',                          # 188 Krasnyy Sokol (Alakopra)
    '红斯坦基',                                   # 189 Krasnyye Stanki
    '克拉修科夫斯卡亚',                           # 190 Krasyukovskaya
    '克拉蒂',                                     # 191 Krathi
    '克赖尔',                                     # 192 Kreir
    '克雷马斯蒂',                                 # 193 Kremasti
    '克列缅丘格第二',                             # 194 Kremenchuk Vtoroy
    '克雷门',                                     # 195 Kremmen
    '克列普卡亚河',                               # 196 Krepkaya River
    '克列夏蒂克',                                 # 197 Kreshchatik
    '克列斯季谢',                                 # 198 Krestishche
    '克列斯托沃',                                 # 199 Krestovo
    '克列斯托维',                                 # 200 Krestovyy
    '克列斯齐',                                   # 201 Krestzy
    '野战医院 (摩托化) 667 /非洲装甲战斗群',      # 202 Kriegslazarett (mot) 667 /PzGr Afrika
    '海军情报司令部',                             # 203 Kriegsmarine Intel HQ
    '克里亚诺夫卡',                               # 204 Krijanovka
    '克里穆尔达',                                 # 205 Krimulda
    '克林格莱米尔',                               # 206 Kringlemyr
    '克林卡',                                     # 207 Krinka
    '克林卡河',                                   # 208 Krinka River
    '克里皮奇诺耶',                               # 209 Kripichnoye
    '克里普',                                     # 210 Kripp
    '克里瓦亚河',                                 # 211 Krivaya River
    '克里维扬斯卡亚',                             # 212 Krivyanskaya
    '克尔克',                                     # 213 Krk
    '克罗恩',                                     # 214 Kroen
    '克罗莱韦茨',                                 # 215 Krolevec
    '喀琅施塔得',                                 # 216 Kronstadt
    '喀琅施塔得要塞',                             # 217 Kronstadt Fortification
    '喀琅施塔得炮台',                             # 218 Kronstadt Forts
    '克罗波特基诺 (库尔德扎奈)',                  # 219 Kropotkino (Kul'dzhanay)
    '克罗希琴科',                                 # 220 Kroscienko
    '克罗什尼亚',                                 # 221 Kroshnya
    '克罗托沃',                                   # 222 Krotovo
    '克鲁格洛耶',                                 # 223 Krugloye
    '克鲁赫雷克 (克鲁格利克)',                    # 224 Kruhlyk (Kruglik)
    '克吕斯阿贝勒 (克吕斯)',                      # 225 Kruisse Abeele (Kruise)
    '克鲁耶',                                     # 226 Kruje
    '克鲁米尼',                                   # 227 Krumini
    '克鲁坚基',                                   # 228 Krutenkiy
    '克鲁托夫斯基',                               # 229 Krutovskiy
    '克鲁托亚尔斯基',                             # 230 Krutoyarskiy
    '克鲁特亚尔',                                 # 231 Krutyi Yar
    '克鲁日林',                                   # 232 Kruzhilin
    '克里米亚',                                   # 233 Krym
    '克雷姆斯克',                                 # 234 Krymsk
    '克雷姆斯克空军基地',                         # 235 Krymsk Air Base
    '克里尼奇基 (克里尼奇基)',                    # 236 Krynychky (Krinichki)
    '克廖科沃',                                   # 237 Kryokovo
    '克雷西诺',                                   # 238 Krysino
    '克留科夫希纳',                               # 239 Kryukovshchina
    '克留科夫斯基潟湖',                           # 240 Kryukovskiy Liman
    '克日兹诺沃洛加',                             # 241 Kryznowloga
    '克热希采 (克里施特)',                        # 242 Krzeszyce (Kriescht)
    '克萨尔塞吉尔',                               # 243 Ksar es Seghir
    '库阿帕池',                                   # 244 Kuapa Pond
    '库班桥头堡',                                 # 245 Kuban-Bridgehead
    '库班卡',                                     # 246 Kubanka
    '库班斯卡亚',                                 # 247 Kubanskaya
    '库切罗沃',                                   # 248 Kucherovo
    '库丘古雷',                                   # 249 Kuchugury
    '库丘尔甘河',                                 # 250 Kuchurgan River
    '库达希夫卡 (库达舍夫卡)',                    # 251 Kudashivka (Kudashevka)
    '库德马',                                     # 252 Kudma
    '库德里诺',                                   # 253 Kudrino
    '库德里内 (舒雷)',                            # 254 Kudryne (Shury)
    '屈斯特林',                                   # 255 Kuestrin
    '屈斯特林-基茨',                              # 256 Kuestrin-Kietz
    '库富尔加卜',                                 # 257 Kufur el-Ghab
    '库盖伊',                                     # 258 Kugey
    '库亚尔尼克潟湖',                             # 259 Kujalnik Liman
    '库克鲁塞',                                   # 260 Kukruse
    '库尔巴科沃 (亚西诺夫斯基)',                  # 261 Kulbakovo (Yasinovskiy)
    '库尔巴基内',                                 # 262 Kulbakyne
    '库尔巴基内空军基地',                         # 263 Kulbakyne Air Base
    '库列绍夫卡',                                 # 264 Kuleshovka
    '库利耶夫卡',                                 # 265 Kulievka
    '库利希 (库利沙)',                            # 266 Kulishi (Kulisha)
    '库马乔韦 (波克罗沃-基列耶沃)',               # 267 Kumachove (Pokrovo-Kireyevo)
    '库姆布里',                                   # 268 Kumbri
    '库梅基',                                     # 269 Kumeyki
    '金桂里',                                     # 270 Kumgye-ri
    '库姆卡莱',                                   # 271 Kumkale
    '库莫韦 (旧基济尔拜)',                        # 272 Kumove (Stary Kizil-Bay)
    '库姆沙茨基',                                 # 273 Kumshatskiy
    '昆杜奇',                                     # 274 Kunduchi
    '昆山',                                       # 275 Kunshan
    '屈讷',                                       # 276 Kunö
    '库帕萨里',                                   # 277 Kupasaari
    '库佩尔亚诺夫营',                             # 278 Kuperjanov Battalion
    '库波罗诺耶',                                 # 279 Kuporosnoje
    '库拉耶夫卡',                                 # 280 Kurayevka
    '库尔昌斯卡亚',                               # 281 Kurchanskaya
    '库尔昌斯基潟湖',                             # 282 Kurchanskiy Liman
    '库尔格利亚科沃',                             # 283 Kurgljakowo
    '库尔戈洛沃',                                 # 284 Kurgolovo
    '库里茨科',                                   # 285 Kuritsko
    '库尔拉茨基 (库尔利亚茨科耶)',                # 286 Kurlatzki (Kurlyatskoye)
    '库尔莫亚尔斯克',                             # 287 Kurmojarsk
    '库罗尔特诺耶',                               # 288 Kurortnoye
    '库罗萨尼河',                                 # 289 Kurosani River
    '库罗维采',                                   # 290 Kurovicy
    '库里亚克萨',                                 # 291 Kuryaksa
    '库里利夫卡 (基里洛夫卡)',                    # 292 Kurylivka (Kirilovka)
    '库斯',                                       # 293 Kus
    '库舍拉',                                     # 294 Kushela
    '库舍韦雷',                                   # 295 Kushevery
    '库什库沙拉',                                 # 296 Kushkushara
    '库塔伊西',                                   # 297 Kutais
    '库捷尔马',                                   # 298 Kuter'ma
    '库捷伊尼科沃',                               # 299 Kuteynikovo
    '库伊贝舍沃',                                 # 300 Kuybyshevo
    '库伊贝舍沃 (比尔马克)',                      # 301 Kuybyshevo (Bilmak)
    '库伊贝舍沃机场',                             # 302 Kuybyshevo Airfield
    '库兹米诺',                                   # 303 Kuz'mino
    '库兹-列卡',                                  # 304 Kuz-Reka
    '库若尔斯卡亚',                               # 305 Kuzhorskaya
    '库济诺',                                     # 306 Kuzino
    '库兹米奇',                                   # 307 Kuzmichi
    '库兹米诺',                                   # 308 Kuzmino
    '库兹涅奇哈',                                 # 309 Kuznechikha
    '库兹涅佐夫卡',                               # 310 Kuznetsovka
    '库兹涅佐沃-米哈伊洛夫卡',                    # 311 Kuznetsovo-Mikhaylovka
    '库兹尼察 (库斯费尔德)',                      # 312 Kuznica (Kussfeld)
    '克瓦尔维克',                                 # 313 Kvalvig
    '克韦尔德哈根农庄',                           # 314 Kveldhagen Farm
    '克韦尔纳',                                   # 315 Kverna
    '克韦恩维肯',                                 # 316 Kvernviken
    '夸姆西西',                                   # 317 Kwamsisi
    '克瓦拉扎',                                   # 318 Kwaraza
    '基亚米希河',                                 # 319 Kyamishi River
    '基亚罗斯特罗夫',                             # 320 Kyarostrov
    '基里利夫卡 (基里洛夫卡)',                    # 321 Kyrylivka (Kirilovka)
    '基谢利夫卡',                                 # 322 Kyselivka
    '基谢利夫卡 (切霍维德希站)',                  # 323 Kyselivka (Stantsiya Chekhovidhi)
    '洛姆',                                       # 324 L'Homme
    '利沃夫卡',                                   # 325 L'vovka
    '利沃夫斯科耶',                               # 326 L'vovskoye
    'LRDG',                                       # 327 LRDG（未知缩写，保留原文）
    '第76军',                                     # 328 LXXVI Army Corps
    '拉阿尔卡伊德萨',                             # 329 La Alcaidesa
    '拉阿尔莫赖马',                               # 330 La Almoraima
    '拉巴佐日',                                   # 331 La Bazoge
    '拉卡拉德米哈斯',                             # 332 La Cala de Mijas
    '拉费泰苏茹阿尔',                             # 333 La Ferté-sous-Jouarre
    '拉方丹',                                     # 334 La Fontaine
    '拉格莱兹',                                   # 335 La Gleize
    '拉瓜迪亚机场',                               # 336 La Guardia Airport
    '拉利内阿',                                   # 337 La Linea
    '拉利内阿-德拉康塞普西翁',                    # 338 La Linea de la Concepcion
    '拉马尔萨',                                   # 339 La Marsa
    '拉默兹',                                     # 340 La Meuse
    '拉莫尔纳吉亚',                               # 341 La Mornaghia
    '拉罗什',                                     # 342 La Roche
    '拉特里尼泰',                                 # 343 La Trinite
    '拉万策瑙',                                   # 344 La Wantzenau
    '拉艾迪皮',                                   # 345 La-Haye-du-Puits
    '拉尔布鲁赫机场',                             # 346 Laarbruch Airport
    '拉巴',                                       # 347 Laba
    '拉贝格特',                                   # 348 Laberget
    '拉克',                                       # 349 Lac
    '比特根巴赫湖',                               # 350 Lac de Butgenbach
    '拉茨科',                                     # 351 Lacko
    '拉德',                                       # 352 Lade
    '拉德斯湖',                                   # 353 Lades Ezers
    '拉多日斯卡亚',                               # 354 Ladozhskaya
    '拉多加湖',                                   # 355 Ladozhskoye Ozero
    '拉多加湖 (拉多加湖)',                        # 356 Ladozhskoye Ozero (Lake Ladoga)
    '莱加斯万',                                   # 357 Laeigasvann
    '莱尔马',                                     # 358 Laerma
    '莱西希',                                     # 359 Laessig
    '拉贾和雷',                                   # 360 Lagja e Re
    '镜中维纳斯湖',                               # 361 Lago Specchio di Venere
    '富恩特德彼德拉潟湖',                         # 362 Laguna de Fuente de Piedra
    '卡拉瓦斯塔潟湖',                             # 363 Laguna e Karavastase
    '帕托库特潟湖',                               # 364 Laguna e Patokut
    '拉古特尼克',                                 # 365 Lagutnik
    '拉哈尼亚',                                   # 366 Lahania
    '拉日什',                                     # 367 Lajes
    '湖 (无法通行)',                              # 368 Lake (Impass)
    '加尔梅尔赫湖',                               # 369 Lake Ghar el Melh
    '伊德库湖',                                   # 370 Lake Idku
    '伊利基湖',                                   # 371 Lake Iliki
    '吉贾湖',                                     # 372 Lake Jija
    '库丘尔甘湖',                                 # 373 Lake Kuchurgan
    '曼扎拉湖',                                   # 374 Lake Manzala
    '马里乌特湖',                                 # 375 Lake Maryut
    '帕拉利姆尼湖',                               # 376 Lake Paralimni
    '佩普西湖',                                   # 377 Lake Peipus
    '龙康科马湖',                                 # 378 Lake Ronkonkoma
    '提姆萨赫湖',                                 # 379 Lake Timsah
    '突尼斯湖',                                   # 380 Lake Tunis
    '伊利基湖',                                   # 381 Lake Yliki
    '拉克杰莫诺夫卡',                             # 382 Lakedemonovka
    '拉赫塔',                                     # 383 Lakhta
    '拉赫塔机场 (霍尔姆机场)',                    # 384 Lakhta Airfield (Kholm Airfield)
    '拉科伊',                                     # 385 Lakkoi
    '拉克塞尔瓦',                                 # 386 Lakselva
    '兰贝岛',                                     # 387 Lambay Island
    '兰佩杜萨遭到攻击！',                         # 388 Lamberdusa under attack!
    '兰莫维戈尔基',                               # 389 Lamovy Gorki
    '兰佩杜萨',                                   # 390 Lampedusa
    '兰佩尼斯',                                   # 391 Lampernisse
    '朗德勒-库皮尼',                             # 392 Landelles-et-Coupigny
    '海峡群岛登陆',                               # 393 Landing at Channel Islands
    '戈佐岛登陆',                                 # 394 Landing at Gozo
    '兰斯克鲁纳',                                 # 395 Landskrona
    '亚琛地方军',                                 # 396 Landwehr Aachen
    '朗厄莱德',                                   # 397 Langeleed
    '朗厄利尼 (港)',                              # 398 Langelinie (PORT)
    '朗根萨尔察',                                 # 399 Langensalza
    '朗格奥格',                                   # 400 Langeoog
]


def main():
    raw = open(SRC, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), 'BOM in source'
    src = raw.decode('utf-8').split('\r\n')
    assert src[-1] == '', 'source should end with CRLF'
    src = src[:-1]

    assert len(src) == 400, 'src lines %d' % len(src)
    assert len(ZH) == 400, 'zh lines %d' % len(ZH)

    # 输入以 CRLF 结尾（末行为空），输出同样以 CRLF 结尾
    out = ''.join('%s\t%s\r\n' % (s, z) for s, z in zip(src, ZH))
    with open(DST, 'wb') as f:
        f.write(out.encode('utf-8'))
    print('written', DST)


if __name__ == '__main__':
    main()
