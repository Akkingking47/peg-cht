# -*- coding: utf-8 -*-
"""chunk-03 -> part-03.tsv 汉化脚本（严格按 POLICY.md）。

输入：work/atomic/chunks/chunk-03.tsv   （400 行，单列地名/机构名）
输出：work/atomic/zh/part-03.tsv         （原文<TAB>译文，UTF-8 无 BOM，CRLF）

本片特点：绝大多数为地名（A/B 开头），末尾 40 行为 Battle of … 剧本名。

口径（与 part-01/02/04/05 保持一致）：
  - 地名：通行中文名优先，否则音译 + 通名后缀
    River→河  Creek→河  Stream→河  Bay→湾  Gulf→湾  Lake→湖  Sea→海  Ocean→洋
    Canal→运河  Airfield/Airport/Airstrip→机场（不加空格）  Air Base→空军基地
    Station→车站  Fjord→峡湾  Strait→海峡  Island→岛  Mountain→山  Forest→森林
    Port→港  Bridge→桥  Estuary→河口  ezers/Ozero→湖  Moore→海  sø→湖
  - Batteria/Batterie→炮兵连（保留其专名部分）
  - 标点、括号、空格逐字保留
  - 拿不准/未知项 → 保留原文（并在报告中点名）
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'chunks', 'chunk-03.tsv')
DST = os.path.join(HERE, 'part-03.tsv')

# 逐行译文（顺序与输入严格一致，共 400 条）
ZH = [
    '阿利泰尔梅',                               # 1 Aliterme
    '阿尔卡利亚河',                             # 2 Alkaliya River
    '阿尔科梅奈',                               # 3 Alkomenai
    '阿尔克斯尼',                               # 4 Alksni
    '阿拉齐',                                   # 5 Allazi
    '阿勒芒',                                   # 6 Allemant
    '阿伦代尔',                                 # 7 Allendale
    '奥勒洛斯',                                 # 8 Allhallows
    '阿尔内斯',                                 # 9 Alness
    '阿尔内斯湾',                               # 10 Alness Bay
    '阿罗哈珍珠港',                             # 11 Aloha Pearl Habor
    '圣安东尼奥山',                             # 12 Alpe Sant Antonio
    '阿尔芬',                                   # 13 Alphen
    '下卡托',                                   # 14 Alsókátó
    '旧鲁平',                                   # 15 Alt Ruppin
    '阿尔塔马哈河',                             # 16 Altamaha River
    '阿尔塔维拉',                               # 17 Altavilla
    '老劳特',                                   # 18 Alte Lauter
    '阿尔特瑙',                                 # 19 Altenau
    '阿尔托利亚',                               # 20 Altolia
    '阿卢克斯塔湖',                             # 21 Aluksta ezers
    '阿尔弗林厄姆 (阿尔弗林厄姆)',              # 22 Alveringhem (Alveringem)
    '阿尔弗纳',                                 # 23 Alverna
    '阿尔维尼亚诺',                             # 24 Alvignano
    '阿利基',                                   # 25 Alyki
    '昂布莱沃',                                 # 26 Ambleve
    '安布尔斯科耶',                             # 27 Amburskoye
    '阿默龙恩',                                 # 28 Amerongen
    '阿默斯福特',                               # 29 Amersfoort
    '阿米丰泰讷',                               # 30 Amifontaine
    '阿米格达洛凯法利',                         # 31 Amigdalokefali
    '阿米蒂维尔',                               # 32 Amityville
    '阿莫雷',                                   # 33 Amore
    '阿纳尼',                                   # 34 Anagni
    '阿纳帕',                                   # 35 Anapa
    '阿纳普斯卡亚',                             # 36 Anapskaya
    '阿纳斯塔西耶夫卡',                         # 37 Anastasiyevka
    '阿纳斯塔西耶夫斯卡亚',                     # 38 Anastasiyevskaya
    '阿纳托利耶夫卡',                           # 39 Anatolyevka
    '安德拉奇',                                 # 40 Andratx
    '安德烈耶沃',                               # 41 Andrejevo
    '安德尔',                                   # 42 Andres
    '安德烈耶沃-梅连季耶夫斯基',                # 43 Andreyevo-Melentyevskiy
    '安德烈伊科沃',                             # 44 Andreykovo
    '安德罗夫卡',                               # 45 Androvka
    '安德鲁舍夫卡',                             # 46 Andrushevka
    '安格蒙德',                                 # 47 Angermund
    '英苏入侵',                                 # 48 Anglo-Soviet Invasion
    '英雄港',                                   # 49 Angra do Heroismo
    '阿尼亚河',                                 # 50 Ania River
    '阿讷博',                                   # 51 Annebault
    '安诺-奥潘林卡',                            # 52 Anno-Opanlinka
    '安诺洛沃',                                 # 53 Annolovo
    '安诺夫卡',                                 # 54 Annovka
    '上阿莱波霍里',                             # 55 Ano Alepochori
    '上利奥夏',                                 # 56 Ano Liosia
    '安特克拉',                                 # 57 Antequera
    '安蒂特姆',                                 # 58 Antietam
    '安蒂特姆河',                               # 59 Antietam Creek
    '反坦克运河',                               # 60 Antitankgracht
    '安东尼夫卡',                               # 61 Antonivka
    '安东诺-科迪切沃',                          # 62 Antono-Codicevo
    '安东诺沃',                                 # 63 Antonovo
    '安特罗普希诺',                             # 64 Antropshino
    '安特卫普',                                 # 65 Antwerpen
    '安特卫普,  安特卫普',                      # 66 Antwerpen,  Antwerpia
    '安特卫普运河',                             # 67 Antwerpen-Kanaal
    '阿乌斯贾',                                 # 68 Aousdja
    '阿波拉基亚',                               # 69 Apolakkia
    '阿波尔达',                                 # 70 Apolda
    '阿波洛纳',                                 # 71 Apollona
    '阿波洛尼夫卡 (阿波洛诺夫卡)',              # 72 Apollonivka (Appolonovka)
    '阿波马托克斯河',                           # 73 Appomattox River
    '阿普拉尼',                                 # 74 Aprani
    '阿普里利亚 (工厂)',                        # 75 Aprilia (The Factory)
    '阿普歇伦斯克',                             # 76 Apsheronsk
    '阿普歇伦斯基港',                           # 77 Apsheronskiy Port
    '阿拉布卡',                                 # 78 Arabka
    '阿拉霍瓦',                                 # 79 Arakhova
    '阿兰奇',                                   # 80 Aranchi
    '阿尔森',                                   # 81 Arcen
    '古科林斯',                                 # 82 Archaia Korinthos
    '阿奇多纳',                                 # 83 Archidona
    '阿尔西勒蓬萨尔',                           # 84 Arcis-le-Ponsart
    '菲利尼凯旋门 (大理石拱门)',                # 85 Arco dei Fileni (Marble Arch)
    '阿尔代亚',                                 # 86 Ardea
    '阿登攻势',                                 # 87 Ardennenoffensive
    '阿德纳格拉斯克',                           # 88 Ardnagrask
    '阿伦东克',                                 # 89 Arendonk
    '阿戈利克湾',                               # 90 Argolic Gulf
    '阿尔戈斯机场',                             # 91 Argos Airfield
    '阿尔格农河',                               # 92 Arguenon River
    '阿尔汉格尔斯克',                           # 93 Arkhangelsk
    '阿尔希波-奥西波夫卡',                      # 94 Arkhipo-Osipovka
    '法国空军',                                 # 95 Armee de l`Air
    '第1装甲列车 "伊尔夫上尉"',                 # 96 Armoured Train No 1 "Kpt. Irv"
    '阿尔米扬斯克',                             # 97 Armyansk
    '阿纳尔斯塔皮',                             # 98 Arnarstapi
    '阿尔内斯',                                 # 99 Arnes
    '阿尔诺河',                                 # 100 Arno River
    '阿罗马特',                                 # 101 Aromat
    '阿尔帕钦',                                 # 102 Arpachin
    '阿勒瑟湖',                                 # 103 Arresø
    '阿罗内河',                                 # 104 Arrone River
    '布雷尼亚山谷溪',                           # 105 Arroyo de la Brena O del Valle
    '阿尔申采沃',                               # 106 Arshintsevo
    '阿尔西达',                                 # 107 Arsida
    '炮兵/第11步兵旅',                          # 108 Art/11thInfBrig.
    '炮兵/IT-苏佩尔加',                         # 109 Art/IT-Superga
    '第190炮兵团/第90轻装航空师',               # 110 ArtReg 190/90. leADiv
    '炮兵团/冯布罗伊希师',                      # 111 ArtReg/Div.vonBroich
    '阿尔塔',                                   # 112 Arta
    '阿塔内',                                   # 113 Artane
    '阿尔忒弥达 (卢萨)',                        # 114 Artemida (Loutsa)
    '阿尔捷莫夫斯基',                           # 115 Artemovskiy
    '阿尔捷沙',                                 # 116 Artesha
    '第621炮兵团部',                            # 117 Artillerie-Regimentsstab 621
    '阿尔乔莫沃',                               # 118 Artyomovo
    '阿尔扎诺夫斯基',                           # 119 Arzhanovskiy
    '下厄克奇拉尔',                             # 120 Asagi Okcular
    '阿舍尔斯莱本',                             # 121 Aschersleben
    '阿什本',                                   # 122 Ashbourne
    '阿什福德',                                 # 123 Ashford
    '阿什福德 (巴利马卡哈拉)',                  # 124 Ashford (Ballymacahara)
    '阿什顿因梅克菲尔德',                       # 125 Ashton-in-Makerfield
    '阿斯基利皮奥',                             # 126 Asklipio
    '阿斯克伦',                                 # 127 Asklund
    '阿索皮亚',                                 # 128 Asopia
    '阿斯普拉斯皮蒂亚',                         # 129 Aspra Spitia
    '阿斯普拉斯皮蒂亚 (帕拉利亚迪斯托穆)',      # 130 Aspra Spitia (Paralia Distomou)
    '阿斯普里利亚 (工厂)',                      # 131 Asprilia (The Factory)
    '阿斯普罗皮戈斯',                           # 132 Aspropyrgos
    '阿森',                                     # 133 Assen
    '阿索科莱',                                 # 134 Assokolay
    '阿斯塔霍夫卡',                             # 135 Astakhovka
    '阿森斯防空河',                             # 136 Astense AA stream
    '阿斯特拉罕卡',                             # 137 Astrakhanka
    '阿斯特拉河',                               # 138 Astura River
    '阿塔马诺夫卡',                             # 139 Atamanovka
    '阿瑟顿',                                   # 140 Atherton
    '阿蒂基亚',                                 # 141 Athikia
    '大西洋滩',                                 # 142 Atlantic Beach
    '大西洋高地',                               # 143 Atlantic Highlands
    '大西洋',                                   # 144 Atlantic Ocean
    '大西洋壁垒',                               # 145 Atlantic Wall
    '大西洋壁垒防空',                           # 146 Atlantic Wall Air Defense
    '大西洋壁垒',                               # 147 Atlantikwall
    '阿特马奈 (共产党人)',                      # 148 Atmanai (Kommunist)
    '冰岛之战',                                 # 149 Attack on Iceland
    '里加之战',                                 # 150 Attack on Riga
    '欧谢勒',                                   # 151 Auchel
    '奥金吉尔',                                 # 152 Auckingill
    '奥德维尔',                                 # 153 Auderville
    '奥德勒塞勒',                               # 154 Audresselles
    '奥埃湖',                                   # 155 Auesee
    '第3侦察营/第21装甲师',                     # 156 AufklAbt 3/21. PzDiv
    '第3侦察营/第5轻装师',                      # 157 AufklAbt 3/5. leD
    '奥古斯塔',                                 # 158 Augusta
    '奥古斯托夫卡',                             # 159 Augustovka
    '奥尔德恩',                                 # 160 Auldearn
    '奥利',                                     # 161 Auly
    '奥奈叙尔奥东',                             # 162 Aunay-sur-Odon
    '奥尼尼',                                   # 163 Aunini
    '奥里希',                                   # 164 Aurich
    '奥森特河',                                 # 165 Ausente River
    '奥斯基里',                                 # 166 Auskerry
    '奥蒂河',                                   # 167 Authie River
    '装甲汽车/指挥/第27"布雷西亚"',            # 168 Autoblido/Comando/27ª "Brescia"
    '奥韦雷',                                   # 169 Auvere
    '辅助机场',                                 # 170 Auxiliary Airfield
    '辅助机场',                                 # 171 Auxiliary Airstrip
    '阿弗卡佩勒 (阿弗卡佩勒)',                  # 172 Avecappelle (Avekapelle)
    '阿弗内勒',                                 # 173 Avenelles
    '阿夫克谢尼夫卡 (新阿克肖诺夫卡)',          # 174 Avksenivka (Novo-Aksemovka)
    '阿夫洛纳',                                 # 175 Avlona
    '阿夫涅波罗格',                             # 176 Avneporog
    '阿冯贝格河',                               # 177 Avonbeg River
    '阿冯莫尔',                                 # 178 Avonmore
    '阿夫罗瓦 (塔特什孔拉特)',                  # 179 Avrova (Tatysh Konrat)
    '阿伊河',                                   # 180 Ay River
    '圣安娜',                                   # 181 Ayia Anna
    '艾尔斯厄姆',                               # 182 Aylesham
    '艾因加扎拉',                               # 183 Ayn Al Gazalah
    '艾因加扎拉机场',                           # 184 Ayn Al Gazalah airport
    '阿泽维尔',                                 # 185 Azeville
    '亚速',                                     # 186 Azov
    '亚速海 (亚速海)',                          # 187 Azovske More (Sea of Azov)
    '亚速海',                                   # 188 Azovskoye More
    '亚速海',                                   # 189 Azovskoye more
    'B/第17枪骑兵团/BLADE',                     # 190 B/17thLancer/BLADE
    'B/第21枪骑兵团/BLADE',                     # 191 B/21stLancer/BLADE
    'B/第571美国空降',                          # 192 B/571stUS-Airborne
    'BT 2',                                     # 193 BT 2
    'BT 3',                                     # 194 BT 3
    '巴勒纳绍',                                 # 195 Baarle-Nassau
    '巴比耶多利 (赫克森格伦德)',                # 196 Babie Doly (Hexengrund)
    '巴宾斯科耶湖',                             # 197 Babinskoye Ozero
    '巴比特斯 (巴吉尔) 湖 (无法通行)',          # 198 Babites (Bagil) Lake (Impass)
    '巴克乌',                                   # 199 Bacau
    '巴乔伊',                                   # 200 Bacioi
    '巴卡兰',                                   # 201 Backaland
    '巴斯卡伊尔',                               # 202 Backaskaill
    '巴琴',                                     # 203 Baczyn
    '巴特贝德凯萨',                             # 204 Bad Bederkesa
    '巴特比布拉',                               # 205 Bad Bibra
    '巴特博登多夫',                             # 206 Bad Bodendorf
    '巴特弗兰肯豪森',                           # 207 Bad Frankenhausen
    '巴特弗赖恩瓦尔德',                         # 208 Bad Freienwalde
    '巴特哈尔茨堡',                             # 209 Bad Harzburg
    '巴特茨维申安',                             # 210 Bad Zwischenahn
    '阿尔库迪亚湾',                             # 211 Badia d' Alcudia
    '帕尔马湾',                                 # 212 Badia de Palma
    '波连萨湾',                                 # 213 Badia de Pollenca
    '巴加拉',                                   # 214 Bagalla
    '巴加莫约',                                 # 215 Bagamoyo
    '巴加耶夫斯卡亚',                           # 216 Bagayevskaya
    '巴格罗沃',                                 # 217 Bagerovo
    '巴格罗沃空军基地',                         # 218 Bagerovo Air Base
    '巴盖里亚',                                 # 219 Bagheria
    '巴尼亚拉',                                 # 220 Bagnara
    '里波利巴尼奥',                             # 221 Bagno a Ripoli
    '巴希丁',                                   # 222 Bahey El Din
    '巴希格',                                   # 223 Bahig
    '巴赫卢伊河',                               # 224 Bahlui River
    '铁路护卫支队',                             # 225 Bahnschutz Detachement
    '博赛湾',                                   # 226 Baie de Beaussais
    '塞纳湾',                                   # 227 Baie de Seine
    '韦斯湾',                                   # 228 Baie des Veys
    '圣米歇尔山海湾',                           # 229 Baie du Mont St Michel
    '贝马奥',                                   # 230 Baie-Mahault
    '巴约勒',                                   # 231 Bailleul
    '班察甘山',                                 # 232 Bain-Tsagan mountain
    '巴克顿',                                   # 233 Bakerton
    '巴赫奇萨赖',                               # 234 Bakhchisaray
    '巴赫穆特金',                               # 235 Bakhmutkin
    '巴金斯卡亚',                               # 236 Bakinskaya
    '巴基哈诺夫 (斯捷潘拉津)',                  # 237 Bakixanov (Stepana Razina)
    '巴肯',                                     # 238 Bakken
    '巴库机场',                                 # 239 Baku Airport
    '巴库卡拉空军基地',                         # 240 Baku Kala Air Base
    '巴莱亚',                                   # 241 Balaia
    '巴拉蒂纳',                                 # 242 Balatina
    '巴拉顿奥卡罗蒂亚',                         # 243 Balatonakarattya
    '巴拉顿博若克',                             # 244 Balatonbozsok
    '巴拉顿菲兹弗',                             # 245 Balatonfüzfö
    '巴拉顿萨尔索',                             # 246 Balatonszárszó
    '巴尔科姆',                                 # 247 Balcombe
    '巴尔多内 (弗里德里希施塔特)',              # 248 Baldone (Friederichstadt)
    '鲍尔多伊尔',                               # 249 Baldoyle
    '鲍尔多伊尔河口',                           # 250 Baldoyle Estuary
    '巴莱',                                     # 251 Bale
    '奥蒂湾',                                   # 252 Bale de l'Authie
    '巴尔弗',                                   # 253 Balfour
    '巴利采机场',                               # 254 Balice Airport
    '巴林托尔',                                 # 255 Balintore
    '巴利夫卡 (波波娃-巴洛夫卡)',               # 256 Balivka (Popova-Balovka)
    '科帕尼沟 (科帕尼溪)',                      # 257 Balka Kopani (Kopani Stream)
    '皮丘加沟',                                 # 258 Balka Pichuga
    '苏哈亚梅切特卡沟',                         # 259 Balka Sukhaya Mechetka
    '塔拉诺娃沟',                               # 260 Balka Taranova
    '巴朗恩',                                   # 261 Ballangen
    '巴朗恩峡湾',                               # 262 Ballangen Fjord
    '巴尔赫拉根',                               # 263 Ballchraggan
    '巴勒鲁普',                                 # 264 Ballerup
    '巴林科利格',                               # 265 Ballincollig
    '巴林哈西格',                               # 266 Ballinhassig
    '巴林斯皮特尔',                             # 267 Ballinspittle
    '巴尔斯塔',                                 # 268 Ballstad
    '巴利博哈尔',                               # 269 Ballyboughal
    '巴利布拉西尔',                             # 270 Ballybrassil
    '巴利科顿',                                 # 271 Ballycotton
    '巴利科顿湾',                               # 272 Ballycotton Bay
    '巴利科顿岛',                               # 273 Ballycotton Island
    '巴利弗莫特',                               # 274 Ballyfermot
    '巴利加文',                                 # 275 Ballygarvan
    '巴利格里桑',                               # 276 Ballygrissane
    '巴利马科达',                               # 277 Ballymacoda
    '巴利莫尔尤斯塔斯',                         # 278 Ballymore Eustace
    '巴洛蒂纳',                                 # 279 Balotina
    '巴洛夫内',                                 # 280 Balovne
    '巴洛齐',                                   # 281 Balozi
    '巴尔斯',                                   # 282 Bals
    '巴尔斯内斯',                               # 283 Balsnes
    '巴尔斯塔',                                 # 284 Balstad
    '巴尔塔桑德',                               # 285 Baltasound
    '巴尔塔桑德机场',                           # 286 Baltasound Airstrip
    '伯尔齐 (贝尔齐)',                          # 287 Balti (Beltsy)
    '波罗的海',                                 # 288 Baltic Sea
    '波罗的海地方军',                           # 289 Baltic Territorial Army
    '巴尔季耶茨 (维拉约基)',                    # 290 Baltiyets (Vilajoki)
    '巴尔图蒂诺',                               # 291 Baltutino
    '班巴',                                     # 292 Bamba
    '班清',                                     # 293 Ban Ching
    '班希姆林',                                 # 294 Ban Him Lam
    '班洪贡',                                   # 295 Ban Hong Cum
    '班乔',                                     # 296 Ban Keo
    '班凯派',                                   # 297 Ban Khe Phai
    '班科洛伊',                                 # 298 Ban Kho Loi
    '班纳洛伊',                                 # 299 Ban Na Loi
    '班翁勒贡',                                 # 300 Ban Ong Lech Cong
    '班翁佩',                                   # 301 Ban Ong Pet
    '班帕莱',                                   # 302 Ban Palech
    '班丹',                                     # 303 Ban Ten
    '班登河',                                   # 304 Bandon River
    '巴尼诺 (巴宁)',                            # 305 Banino (Banin)
    '巴诺夫卡',                                 # 306 Banovka
    '宝山',                                     # 307 Baoshan
    '巴奇纳机场',                               # 308 Baqqinah Airfield
    '巴拉宾',                                   # 309 Barabin
    '巴拉蒂夫卡',                               # 310 Barativka
    '巴尔贝里诺',                               # 311 Barberino
    '巴尔比',                                   # 312 Barby
    '巴登贝格',                                 # 313 Bardenberg
    '巴尔弗勒尔',                               # 314 Barfleur
    '巴尔加',                                   # 315 Barga
    '巴勒姆',                                   # 316 Barham
    '巴里洛-克列平斯卡亚',                      # 317 Barilo-Krepinskaya
    '巴金',                                     # 318 Barking
    '巴拉德河',                                 # 319 Barlad River
    '巴林机场',                                 # 320 Barling Airstrip
    '巴讷费尔德',                               # 321 Barneveld
    '巴讷维尔-卡特雷',                          # 322 Barneville-Carteret
    '滨海巴讷维尔',                             # 323 Barneville-Sur-Mer
    '巴龙',                                     # 324 Baron
    '巴罗尼西',                                 # 325 Baronissi
    '营房与飞行学校',                           # 326 Barracks and Flightschool
    '乌德梅尔水坝',                             # 327 Barrage Oued Rmel
    '巴罗克',                                   # 328 Barrock
    '巴尔苏基',                                 # 329 Barsuki
    '巴尔塔 (巴尔陶)',                          # 330 Barta (Bartau)
    '巴尔维克',                                 # 331 Barwik
    '巴雷比诺',                                 # 332 Barybino
    '巴桑斯基',                                 # 333 Basanskiy
    '巴萨尔吉诺机场',                           # 334 Basargino Airfield
    '巴什马奇卡',                               # 335 Bashmachka
    '巴斯卡科沃',                               # 336 Baskakovo
    '巴斯马诺沃',                               # 337 Basmanovo
    '巴斯特尔',                                 # 338 Basse-Terre
    '巴苏姆',                                   # 339 Bassum
    '巴斯特鲁普湖',                             # 340 Bastrup sø
    '巴达维亚石油公司',                         # 341 BataafsePetroleumMa.
    '巴泰诺耶',                                 # 342 Batainoye
    '巴泰斯克',                                 # 343 Bataysk
    '巴捷茨基',                                 # 344 Batetskiy
    '巴季谢沃',                                 # 345 Batishchevo
    '第120/53 MILMART炮兵连',                   # 346 Batteria 120/53 MILMART
    '阿戈斯蒂诺斯特拉夏炮台 (152/45)',          # 347 Batteria Agostino Strascia (152/45)
    '卡拉弗兰切塞炮台',                         # 348 Batteria Cala Francese
    '朱塞佩卡米尼塔炮台 (152/45)',              # 349 Batteria Giuseppe Caminita (152/45)
    'MILMART炮兵连',                            # 350 Batteria MILMART
    '保罗罗切拉炮台 (152/45)',                  # 351 Batteria Paolo Roccella (152/45)
    '蓬塔帕里诺炮台',                           # 352 Batteria Punta Parrino
    '阿里亚罗萨炮台',                           # 353 Batteria di Aria Rosa
    '卡萨加里托炮台',                           # 354 Batteria di Casa Garito
    '蓬塔阿莱莫炮台',                           # 355 Batteria di Punta Alaimo
    '奥尔巴赫炮兵连',                           # 356 Batterie Auerbach
    '齐默尔曼炮兵连',                           # 357 Batterie Zimmermann
    '巴特斯敦',                                 # 358 Batterstown
    '巴蒂帕利亚',                               # 359 Battipaglia
    '冯泰陶战斗群',                             # 360 Battle Group von Tettau
    '哈拉哈河之战',                             # 361 Battle at the Chalchin Gol
    '米什科瓦河之战',                           # 362 Battle at the Myschkowa
    '鲁尔之战',                                 # 363 Battle at the Ruhr
    '阿登之战',                                 # 364 Battle in the Ardennes
    '亚琛之战',                                 # 365 Battle of Aachen
    '亚历山大之战',                             # 366 Battle of Alexandria
    '阿尔汉格尔斯克之战',                       # 367 Battle of Arkhangelsk
    '雅典之战 1',                               # 368 Battle of Athens I
    '雅典之战 2',                               # 369 Battle of Athens II
    '巴库之战',                                 # 370 Battle of Baku
    '柏林之战',                                 # 371 Battle of Berlin
    '卡昂之战',                                 # 372 Battle of Caen
    '瑟堡之战',                                 # 373 Battle of Cherbourg
    '第聂伯罗彼得罗夫斯克之战',                 # 374 Battle of Dnipropetrovsk
    '东弗里西亚之战',                           # 375 Battle of East Friesland
    '阿拉曼之战',                               # 376 Battle of El Alamein
    '法国之战',                                 # 377 Battle of France
    '赫尔之战 1939',                            # 378 Battle of Hel '39
    '赫尔之战 1944',                            # 379 Battle of Hel '44
    '伦敦之战',                                 # 380 Battle of London
    '马略卡之战',                               # 381 Battle of Mallorca
    '纳尔瓦之战',                               # 382 Battle of Narva
    '纳尔维克之战 1',                           # 383 Battle of Narvik I
    '纳尔维克之战 2',                           # 384 Battle of Narvik II
    '诺夫哥罗德之战 1941',                      # 385 Battle of Novgorod '41
    '诺夫哥罗德之战 1943',                      # 386 Battle of Novgorod '43
    '敖德萨之战',                               # 387 Battle of Odessa
    '布拉格之战',                               # 388 Battle of Prague
    '罗得岛之战',                               # 389 Battle of Rhodes
    '罗马尼亚之战',                             # 390 Battle of Romania
    '罗斯托夫之战',                             # 391 Battle of Rostov
    '上海之战',                                 # 392 Battle of Shanghai
    '西里西亚之战',                             # 393 Battle of Silesia
    '锡瓦绿洲之战',                             # 394 Battle of Siwa Oasis
    '斯大林格勒之战 1',                         # 395 Battle of Stalingrad I
    '斯大林格勒之战 2',                         # 396 Battle of Stalingrad II
    '斯大林格勒之战 3',                         # 397 Battle of Stalingrad III
    '苏奥穆斯萨尔米之战',                       # 398 Battle of Suomussalmi
    '塔甘罗格之战',                             # 399 Battle of Taganrog
    '坦噶尼喀之战 1',                           # 400 Battle of Tanganyika I
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
