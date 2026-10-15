# -*- coding: utf-8 -*-
"""chunk-14 -> part-14.tsv 汉化脚本（严格按 work/xscn/POLICY.md）。

输入：work/atomic/chunks/chunk-14.tsv   （400 行，单列地名/机构名/番号）
输出：work/atomic/zh/part-14.tsv         （原文<TAB>译文，UTF-8 无 BOM，CRLF）

本片特点：O/P 开头地名为主。含大量挪威语峡湾名（Orkanger/Orkedalsfjord/Oyord）、
爱沙尼亚语（Piispajarvi/Pikjas）、希腊语（Palaia Epidavros/Peristeri）、
苏联地名（Ozero*/Ostrov*/Petrovskiy 系列，含别名括号）与少量德语部队番号。

口径（与 part-01..10 保持一致）：
  - 地名：通行中文名优先，否则音译 + 通名后缀
      River→河 Lake→湖 Bay→湾 Sea→海 Canal→运河 Airfield/Airport→机场
      Station→站 Hill/Mount/height→山 岛 Ostrov/Ostrov*/Island→岛
      Ozero→湖 Ostrova→群岛/岛群 Gora→山 Fjord→峡湾 Port→港
      height→高地(保留原文 height 时加注) 实际按 POLICY 通名表
  - 俄语 Ozero X → X湖；Ostrov X → X岛；Ostrov(a) 复数 → 岛群/群岛
  - 括号内别名逐字保留结构，译为中文
  - 装备/舰船/飞机型号、未知缩写、纯编号 → 保留原文
  - 方括号代号（[HILL]/[AIRFIELD]/[PORT]）按 part-10 口径译：HILL→高地，PORT→港
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'chunks', 'chunk-14.tsv')
DST = os.path.join(HERE, 'part-14.tsv')

# 逐行译文（顺序与输入严格一致，共 400 条）
ZH = [
    '奥里尔',                                     # 1 Oril
    '奥里尔 (奥里尔运河)',                        # 2 Oril (Oril Canal)
    '奥坎厄尔',                                   # 3 Orkanger
    '奥克达尔峡湾',                               # 4 Orkedalsfjord (挪)
    '奥克拉',                                     # 5 Orkla
    '奥勒 (沃尔勒)',                              # 6 Orle (Worle)
    '奥尔利诺耶',                                 # 7 Orlinoye
    '奥尔林斯基',                                 # 8 Orlinskiy
    '奥尔利夫卡 (奥尔洛夫卡)',                    # 9 Orlivka (Orlovka)
    '奥尔沃沃 (阿德勒斯霍斯特)',                  # 10 Orlowo (Adlershorst)
    '奥利',                                       # 11 Orly
    '奥尔利克 (奥尔利克)',                        # 12 Orlyk (Orlik)
    '奥姆斯柯克',                                 # 13 Ormskirk
    '奥恩湾灯塔',                                 # 14 Orne Bay Lighthouse
    '奥菲尔',                                     # 15 Orphir
    '奥尔沙',                                     # 16 Orsha
    '奥鲁',                                       # 17 Oru
    '奥西马河',                                   # 18 Os\'ma River
    '奥舍斯莱本',                                 # 19 Oschersleben
    '奥谢什奇莫',                                 # 20 Oseshchmo
    '奥西诺夫斯基',                               # 21 Osinovskiy
    '奥斯洛尼诺 (奥斯兰宁)',                      # 22 Oslonino (Oslanin)
    '奥斯马',                                     # 23 Osma
    '奥索科里夫卡',                               # 24 Osokorivka
    '奥索瓦 (埃斯彭克鲁格)',                      # 25 Osowa (Espenkrug)
    '奥西宁',                                     # 26 Ossining
    '奥斯特尔',                                   # 27 Ostel
    '奥斯坦德',                                   # 28 Ostende
    '奥斯坦德 (奥斯坦德)',                        # 29 Ostende (Oostende)
    '奥斯坦德-布鲁日机场',                        # 30 Ostende-Brugge-Airport
    '奥斯特埃姆斯',                               # 31 Osterems
    '奥斯特霍尔茨-沙姆贝克',                      # 32 Osterholz-Scharmbeck
    '奥斯特格罗塞芬',                             # 33 Ostgrossefehn
    '奥斯蒂亚',                                   # 34 Ostia
    '奥斯特里夫卡',                               # 35 Ostrivka
    '奥斯特罗索瓦茨',                             # 36 Ostrosovac
    '小岛 (佩尼-萨里)',                           # 37 Ostrov Malyy (Peni-Sari)
    '莫什奇内岛 (拉万-萨里)',                     # 38 Ostrov Moshchnyy (Lavan-Sari)
    '谢斯卡尔岛 (塞斯卡里)',                      # 39 Ostrov Seskar (Seyskari)
    '舒约斯特罗夫岛',                             # 40 Ostrov Shuyostrov
    '图米谢岛',                                   # 41 Ostrov Tumishche
    '萨雷-布拉特岛群',                           # 42 Ostrova Sary-Bulat
    '奥斯特罗夫斯凯',                             # 43 Ostrovske
    '奥苏加',                                     # 44 Osuga
    '奥西彭科 (新斯帕西夫卡)',                    # 45 Osypenko (Novospasivka)
    '奥塔克',                                     # 46 Otac
    '奥特福德',                                   # 47 Otford
    '奥特诺索沃',                                 # 48 Otnosovo
    '奥特拉德诺耶',                               # 49 Otradnoye
    '奥特拉德诺耶 (奥穆蒂)',                      # 50 Otradnoye (Omuti)
    '奥塔贝里',                                   # 51 Ottaberry
    '奥特沃茨克',                                 # 52 Otwock
    '奥齐亚斯',                                   # 53 Otzias
    '旧拜耶兰',                                   # 54 Oud Beijerland
    '旧埃姆斯',                                   # 55 Oude Ems
    '旧马斯',                                     # 56 Oude Maas
    '旧通厄',                                     # 57 Oude Tonge
    '奥登堡',                                     # 58 Oudenburg
    '乌特罗',                                     # 59 Outreau
    '奥维迪奥波尔',                               # 60 Ovidiopol
    '厄夫勒',                                     # 61 Ovre
    '奥夫西谢 (马洛耶)',                          # 62 Ovsishche (Maloye)
    '欧文纳布',                                   # 63 Owenabue
    '欧文纳库拉河',                               # 64 Owenacurra River
    '奥克斯泰德',                                 # 65 Oxted
    '厄扬根',                                     # 66 Oyangen
    '厄约尔',                                     # 67 Oyord
    '奥伊斯特湾',                                 # 68 Oyster Bay
    '奥伊斯特湾港',                               # 69 Oyster Bay Harbor
    '奥伊斯特黑文',                               # 70 Oyster Haven
    '奥泽里',                                     # 71 Ozeri
    '奥泽里谢',                                   # 72 Ozerishche
    '奥泽尔基 (佩里亚屈利亚)',                    # 73 Ozerki (Peryakyulya)
    '奥焦尔纳亚',                                 # 74 Ozernaya
    '奥泽尔内 (奥焦尔诺耶)',                      # 75 Ozerne (Ozernoye)
    '艾古利湖 (艾古利斯科耶湖)',                  # 76 Ozero Ajgul\'skoe (Ozero Aygul\'skoye)
    '安古尔湖 (扬古尔湖)',                        # 77 Ozero Angul (Ozero Yangul)
    '别洛耶湖',                                   # 78 Ozero Beloye
    '杰希诺湖',                                   # 79 Ozero Dekhino
    '多尔日诺湖',                                 # 80 Ozero Dolzhino
    '格卢博科耶湖',                               # 81 Ozero Glubokoye
    '伊尔门湖',                                   # 82 Ozero Ilmen
    '伊日莫泽罗湖',                               # 83 Ozero Izhmozero
    '哈博洛沃湖',                                 # 84 Ozero Khabolovo
    '基亚特斯科耶湖 (基亚茨科耶湖)',              # 85 Ozero Kiatskoe (Ozero Kiyatskoye)
    '基尔莱乌茨科耶湖',                           # 86 Ozero Kirleutskoye
    '红湖 (克拉斯诺耶湖)',                        # 87 Ozero Krasnoe (Ozero Krasnoye)
    '库德莫泽罗湖',                               # 88 Ozero Kudmozero
    '莱贝尔湖',                                   # 89 Ozero Leber
    '列希湖',                                     # 90 Ozero Leshiy
    '梅尔科耶湖',                                 # 91 Ozero Melkoye
    '佩尔托泽罗湖',                               # 92 Ozero Pertozero
    '里戈瓦罗克斯科耶湖',                         # 93 Ozero Rigovarokskoye
    '萨洛泽罗湖',                                 # 94 Ozero Salozero
    '萨姆罗湖',                                   # 95 Ozero Samro
    '舒耶泽罗湖',                                 # 96 Ozero Shuyezero
    '锡瓦什湖',                                   # 97 Ozero Sivash
    '旧湖 (斯塔罗耶湖)',                          # 98 Ozero Staroe (Ozero Staroye)
    '斯托亚切耶湖',                               # 99 Ozero Stoyacheye
    '苏达奇耶湖',                                 # 100 Ozero Sudachye
    '托别奇克斯科耶湖',                           # 101 Ozero Tobechikskoye
    '奥泽维尔',                                   # 102 Ozeville
    '奥若金',                                     # 103 Ozhogin
    '奥兹纳科沃',                                 # 104 Oznakovo
    '奥佐尔涅基',                                 # 105 Ozolnieki
    '帕恰列夫卡',                                 # 106 Pacharevka
    '帕多克伍德',                                 # 107 Paddock Wood
    '帕多内',                                     # 108 Padone
    '帕德龙',                                     # 109 Padron
    '帕格',                                       # 110 Pag
    '帕加里',                                     # 111 Pagari
    '帕亚尼亚',                                   # 112 Paiania
    '帕热',                                       # 113 Paje
    'Pak/IT-苏佩尔加',                            # 114 Pak/IT-Superga
    '帕基特尼亚',                                 # 115 Pakitnya
    '旧埃皮达夫罗斯',                             # 116 Palaia Epidavros
    '旧法利罗',                                   # 117 Palaio Faliro
    '帕兰卡',                                     # 118 Palanka
    '帕莱奥霍拉',                                 # 119 Paleochora
    '帕莱奥霍里',                                 # 120 Paleochori
    '帕莱茨 (富伊) 高地',                         # 121 Palets (Fui) height
    '帕利塞兹帕克',                               # 122 Palisades Park
    '马略卡岛帕尔马',                             # 123 Palma de Mallorca
    '帕尔马霍尔',                                 # 124 Palmajor
    '帕尔马诺瓦',                                 # 125 Palmanova
    '帕洛迪纳山',                                 # 126 Palodina Mount
    '帕卢基亚',                                   # 127 Paloukia
    '帕尔采沃 (塔利)',                            # 128 Paltsevo (Tali)
    '帕米亚特尼克 (帕米亚特尼克)',                # 129 Pamiatnyk (Pamyatnik)
    '帕蒙村',                                     # 130 Pammunjeon
    '帕纳罗河',                                   # 131 Panaro River
    '帕尼亚塞卡山',                               # 132 Pania Secca Mount
    '潘基夫卡 (潘科夫卡)',                        # 133 Pankivka (Pankovka)
    '帕诺沃',                                     # 134 Panovo
    '潘申卡',                                     # 135 Panshinka
    '潘希诺',                                     # 136 Panshino
    '潘泰莱里亚',                                 # 137 Pantelleria
    '第107装甲旅',                                # 138 Panzer Brigade 107
    '装甲军',                                     # 139 Panzer Corps
    '装甲教导师',                                 # 140 Panzer Lehr Division
    '第100装甲营',                                # 141 Panzer-Abteilung 100
    '第206装甲营',                                # 142 Panzer-Abteilung 206
    '第"弗伦茨贝格"装甲师',                       # 143 Panzer-Division "Frundsberg"
    '装甲教导师',                                 # 144 Panzer-Lehr-Division
    '装甲封锁线',                                 # 145 Panzersperre
    '利耶帕亚军车营',                             # 146 Panzerwagen-Abt. Libau
    '保拉',                                       # 147 Paola
    '帕彭堡',                                     # 148 Papenburg
    '造纸厂',                                     # 149 Paper Factory
    '帕普林',                                     # 150 Paplin
    '帕拉斯科瓦亚',                               # 151 Paraskovaya
    '帕尔尼-菲兰',                                # 152 Pargny-Filain
    '帕尔戈洛沃',                                 # 153 Pargolovo
    '帕林恰',                                     # 154 Parincea
    '帕里斯岛机场/佩奇机场',                      # 155 Parris Island Airfield/Page Field
    '帕尔蒂尼科',                                 # 156 Partinico
    '帕尔蒂赞斯凯',                               # 157 Partyzanske
    '帕鲁巴尼克',                                 # 158 Parubanik
    '帕鲁蒂内',                                   # 159 Parutyne
    '帕斯卡乌齐',                                 # 160 Pascauti
    '帕希诺',                                     # 161 Pashino
    '帕什科夫斯卡亚',                             # 162 Pashkovskaya
    '帕西奇韦斯特',                               # 163 Passage West
    '帕塞伊克',                                   # 164 Passaic
    '帕塞伊克河',                                 # 165 Passaic River
    '帕斯尚尔-敦刻尔克运河',                      # 166 Passchendaele-Dunkirk Canal
    '帕斯尚尔-尼乌波特运河',                      # 167 Passchendaele-Nieuport Canal
    '帕乔格',                                     # 168 Patchogue
    '帕泰尔诺',                                   # 169 Paterno
    '帕特森',                                     # 170 Paterson
    '帕特卡',                                     # 171 Patka
    '帕特拉基耶夫斯科耶',                         # 172 Patrakeyevskoye
    '帕特拉乌利',                                 # 173 Patrauli
    '帕特罗克洛斯 (盖杜罗尼西)',                  # 174 Patroklos (Gaidouronisi)
    '帕蒂',                                       # 175 Patti
    '帕维洛斯塔 (保尔港)',                        # 176 Pavilosta (Paulshafen)
    '帕夫林卡',                                   # 177 Pavlinka
    '帕夫利夫卡 (帕夫洛夫卡)',                    # 178 Pavlivka (Pavlovka)
    '帕夫洛-赫里霍里夫卡 (帕夫洛-格里戈里耶夫卡)',  # 179 Pavlo-Hryhorivka (Pavlo-Grigoryevka)
    '帕夫洛-奥恰科沃',                            # 180 Pavlo-Ochakovo
    '帕夫洛夫卡',                                 # 181 Pavlovka
    '帕尤索夫卡',                                 # 182 Payusovka
    '帕扎尔利',                                   # 183 Pazarli
    '珍珠城',                                     # 184 Pearl City
    '珍珠港',                                     # 185 Pearl Harbor
    '珍珠港海军造船厂',                           # 186 Pearl Harbor Naval Shipyard
    '佩科尼克河',                                 # 187 Peconic River
    '佩德罗瓦连特',                               # 188 Pedro Valiente
    '佩高',                                       # 189 Pegau
    '佩格韦尔湾',                                 # 190 Pegwell Bay
    '派内',                                       # 191 Peine
    '佩利尼亚',                                   # 192 Pelinia
    '德里尼河三角洲',                             # 193 Pellgu i Drinit
    '佩尔泰斯 (希亚岑堡)',                        # 194 Peltes (Hiazenburg)
    '彭布罗克',                                   # 195 Pembroke
    '彭克思',                                     # 196 Penketh
    '新佩佩尼',                                   # 197 Pepenii Noi
    '佩钦',                                       # 198 Peqin
    '佩拉霍拉',                                   # 199 Perachora
    '佩拉马',                                     # 200 Perama
    '珀西',                                       # 201 Percy
    '佩尔迪卡',                                   # 202 Perdika
    '佩列杰尔尼基',                               # 203 Peredelniki
    '佩列多沃耶',                                 # 204 Peredovoye
    '佩列亚斯拉夫-赫梅利尼茨基',                   # 205 Pereiaslav-Khmelnytskyi
    '佩列科普',                                   # 206 Perekop
    '佩列拉佐夫斯基',                             # 207 Perelazovsky
    '佩列萨迪夫卡',                               # 208 Peresadivka
    '佩列谢奇纳亚',                               # 209 Peresechnaya
    '佩雷塞奇纳',                                 # 210 Peresecina
    '佩列沃兹纳亚瓦拉卡',                         # 211 Perevoznaya Varaka
    '佩列沃兹诺耶 (库考皮)',                      # 212 Perevoznoye (Kukauppi)
    '佩里亚纳',                                   # 213 Periana
    '佩里斯特里',                                 # 214 Peristeri
    '佩里斯特里亚',                               # 215 Peristeria
    '佩里沃利',                                   # 216 Perivoli
    '佩里沃利亚',                                 # 217 Perivolia
    '佩尔莱夫卡',                                 # 218 Perlewka
    '佩尔讷',                                     # 219 Pernes
    '佩尔萨诺',                                   # 220 Persano
    '五一村',                                     # 221 Pershe Travnya
    '第一康斯坦丁诺夫卡 (佩尔沃-康斯坦丁诺夫卡)',  # 222 Pershokostiantynivka (Pervo-Konstantinovka)
    '五一村 (五一日)',                             # 223 Pershotravenka (Pervoye Maya)
    '五一镇',                                     # 224 Pershotravneve
    '佩尔斯坚基',                                 # 225 Perstenki
    '佩尔托泽罗',                                 # 226 Pertozero
    '佩伦',                                       # 227 Perun
    '五一村',                                     # 228 Pervomaiske
    '五一村 (基文纳帕)',                          # 229 Pervomayskoye (Kivennapa)
    '佩尔维泽 (佩尔韦泽)',                        # 230 Pervyser (Pervijze)
    '佩萨河',                                     # 231 Pesa River
    '佩夏纳亚高地',                               # 232 Peschanaya height
    '佩尚卡',                                     # 233 Peschanka
    '佩夏内',                                     # 234 Peschanyy
    '佩希纳',                                     # 235 Pescina
    '佩什科沃',                                   # 236 Peshkovo
    '佩斯基 (皮耶斯蒂)',                          # 237 Peski (Pjesti)
    '佩索钦',                                     # 238 Pesochin
    '佩斯 (祖格洛)',                              # 239 Pest (Zugló)
    '佩塔利奥伊湾',                               # 240 Petalioi Gulf
    '佩捷利诺',                                   # 241 Petelino
    '彼得斯堡',                                   # 242 Petersburg
    '彼得斯堡要塞',                               # 243 Petersburg Fortifications
    '彼得斯堡坦克战',                             # 244 Petersburg Tank Battle
    '彼得斯维尔',                                 # 245 Petersville
    '小堡',                                       # 246 Petit-Bourg
    '小苏勒夫尔河',                               # 247 Petite Souleuvre River
    '佩特里尼亚',                                 # 248 Petrinja
    '彼得里夫卡',                                 # 249 Petrivka
    '彼得里夫卡 (彼得罗夫卡)',                    # 250 Petrivka (Petrovka)
    '彼得罗-格奥尔基耶夫斯克',                    # 251 Petro-Georgiyevsk
    '彼得罗-米哈伊利夫卡 (彼得罗-米哈伊洛夫卡)',   # 252 Petro-Mykhailivka (Petro-Mykhaylovka)
    '彼得罗奇纳',                                 # 253 Petrochina
    '彼得宫 (彼得霍夫)',                          # 254 Petrodvorets (Peterhof)
    '彼得要塞 (什利谢尔堡)',                      # 255 Petrokrepost (Shlisselburg)
    '炼油厂与储油罐区',                           # 256 Petroleum Refinery and Storage Tanks
    '彼得罗洛沃',                                 # 257 Petrolovo
    '彼得罗马古拉',                               # 258 Petromagoula
    '彼得罗巴甫洛夫斯卡亚',                       # 259 Petropavlovskaya
    '彼得罗皮尔 (彼得罗波尔)',                    # 260 Petropil (Petropol)
    '彼得罗萨河',                                 # 261 Petrosa River
    '彼得罗斯拉维扬卡',                           # 262 Petroslavyanka
    '彼得罗夫卡',                                 # 263 Petrovka
    '彼得罗沃',                                   # 264 Petrovo
    '彼得罗夫斯卡亚',                             # 265 Petrovskaya
    '彼得罗夫斯基',                               # 266 Petrovskii
    '彼得罗夫斯基',                               # 267 Petrovskiy
    '彼得罗夫斯科耶',                             # 268 Petrovskoye
    '彼得鲁希诺',                                 # 269 Petrushino
    '彼得里亚尼诺',                               # 270 Petryanino
    '彼得里基夫卡 (彼得里科夫卡)',                # 271 Petrykivka (Petrikowka)
    '佩滕德',                                     # 272 Pettend
    '佩泽和沃格尔',                               # 273 Peze e Vogel
    '法拉萨尔纳',                                 # 274 Phalasarna
    '菲利普斯堡',                                 # 275 Philippsbourg
    '第220(摩托化)工兵营/第164轻装航空师',        # 276 PiBat 220 (mot)/164. leADiv
    '第200特别用途工兵营/第5轻装师',              # 277 PiBtl z.b.V 200/5. leD
    '科里利亚平原',                               # 278 Piano di Coriglia
    '皮亚诺罗',                                   # 279 Pianoro
    '皮亚诺萨',                                   # 280 Pianosa
    '皮亚塞奇诺',                                 # 281 Piaseczno
    '皮亚斯尼察 (皮亚斯尼茨)',                    # 282 Piasnica (Piasnitz)
    '皮亚特拉尼亚姆茨',                           # 283 Piatra Neamt
    '皮恰内 (佩夏诺耶)',                          # 284 Pichane (Peschanoye)
    '皮丘加',                                     # 285 Pichuga
    '皮库',                                       # 286 Pico
    '皮德希尔内 (波德戈尔内)',                    # 287 Pidhirne (Podgorny)
    '皮德霍罗德内 (波德戈罗德诺耶)',              # 288 Pidhorodne (Podgorodnoye)
    '皮德卢日亚',                                 # 289 Pidluzhzhya
    '皮德斯特普内',                               # 290 Pidstepne
    '皮耶迪蒙特马西卡诺',                         # 291 Piedimonte Massicano
    '皮耶迪蒙特马泰塞',                           # 292 Piedimonte Matese
    '皮耶莱谢沃 (佩尔曹)',                        # 293 Pieleszewo (Pelzau)
    '皮耶罗沃尔',                                 # 294 Pierowall
    '皮耶维卡斯',                                 # 295 Pievikas
    '皮加迪亚',                                   # 296 Pigadia
    '皮古利诺',                                   # 297 Pigulino
    '皮伊斯帕耶尔维',                             # 298 Piispajarvi
    '皮克萨斯',                                   # 299 Piksas
    '皮纳',                                       # 300 Pina
    '皮纳尔',                                     # 301 Pinar
    '派尼朗',                                     # 302 Piney Run
    '平瓦尔湖',                                   # 303 Pingvallavatn
    '皮翁比诺 (意大利本土)',                      # 304 Piombino (Italian mainland)
    '皮翁比诺 (意大利本土) : 港',                 # 305 Piombino (Italian mainland) : PORT
    '施特龙贝格工兵营',                           # 306 Pionier-Abt. Stromberg
    '皮拉拉希 (阿尔乔姆)',                        # 307 Pirallahi (Artyom)
    '比雷埃夫斯',                                 # 308 Pireas
    '皮尔焦蒂卡',                                 # 309 Pirgiotika
    '皮尔戈斯',                                   # 310 Pirgos
    '皮尔波利',                                   # 311 Pirpoli
    '皮尔萨吉 (皮尔沙吉)',                        # 312 Pirsagi (Pirshagi)
    '皮什昌卡 (佩尚卡)',                          # 313 Pishchanka (Peschanka)
    '皮斯卡列沃',                                 # 314 Piskarevo
    '皮斯科希内 (佩斯科希诺)',                    # 315 Piskoshyne (Peskoshino)
    '皮斯基',                                     # 316 Pisky
    '皮斯托亚',                                   # 317 Pistoia
    '皮托姆尼克',                                 # 318 Pitomnik
    '皮托姆尼克机场',                             # 319 Pitomnik Airfield
    '南湾',                                       # 320 Pivdenna Bay
    '南布格河',                                   # 321 Pivdennyi Buh River
    '皮日马',                                     # 322 Pizhma
    '普拉卡',                                     # 323 Plaka
    '普拉尼',                                     # 324 Plani
    '普拉森代尔 (普拉森代尔)',                    # 325 Plasschendaele (Plassendale)
    '普拉斯托沃',                                 # 326 Plastovo
    '普拉斯图诺夫斯卡亚',                         # 327 Plastunovskaya
    '普拉塔尼',                                   # 328 Platani
    '普拉塔尼亚',                                 # 329 Platania
    '普拉塔尼亚斯',                               # 330 Platanias
    '普拉托诺-彼得罗夫卡',                        # 331 Platono-Petrovka
    '普拉托沃-伊万诺夫斯基',                      # 332 Platovo-Ivanovskiy
    '普拉托沃-希亚泽夫斯基',                      # 333 Platovo-Khyazevskiy
    '普拉韦什奇纳 (波洛韦什奇纳)',                # 334 Plaveshchyna (Poloveshchina)
    '普列西斯托夫斯基',                           # 335 Plesistovskiy
    '普莱斯兰',                                   # 336 Pleslin
    '普勒蒂伊',                                   # 337 Pleurtuit
    '普利米里',                                   # 338 Plimiri
    '普拉内',                                     # 339 Pllane
    '普洛多罗德内 (赖兴费尔德)',                  # 340 Plodorodne (Raykhenfeld)
    '普洛斯卡奥索科里夫卡',                       # 341 Ploska Osokorivka
    '普拉克利',                                   # 342 Pluckley
    '普卢特尼察 (普卢特尼茨)',                    # 343 Plutnica (Plutnitz)
    '普柳萨河',                                   # 344 Plyussa River
    '普涅沃',                                     # 345 Pnevo
    '波别达 (坎内利亚尔维)',                      # 346 Pobeda (Kannelyarvi)
    '波别达 (叶卡捷里诺沃-哈普罗沃)',             # 347 Pobyeda (Yekaterinovo-Khaprovo)
    '波奇托维',                                   # 348 Pochtovyy
    '波奇托伊亚尔',                               # 349 Pochtoyy Yar
    '布良斯克包围圈',                             # 350 Pocket of Brjansk
    '基辅包围圈',                                 # 351 Pocket of Kiew
    '明斯克包围圈',                               # 352 Pocket of Minsk
    '波德别列济耶',                               # 353 Podberez\'ye
    '波德别列济耶',                               # 354 Podberezye
    '波德博里耶',                                 # 355 Podborye
    '波德尔齐希',                                 # 356 Podelzig
    '波德戈尔诺耶',                               # 357 Podgornoje
    '波德戈尔内',                                 # 358 Podgornyy
    '波德戈尔齐',                                 # 359 Podgortsy
    '波德克列特尼耶',                             # 360 Podkletnije
    '波多利耶',                                   # 361 Podolye
    '波德佩申斯基',                               # 362 Podpeshinskiy
    '波德斯波里耶',                               # 363 Podsporie
    '波加尼',                                     # 364 Pogani
    '波加尼科 (241 米) [高地]',                   # 365 Pogany-ko (241 m) [HILL]
    '波加尔',                                     # 366 Pogar
    '波格列比',                                   # 367 Pogreby
    '波格罗比',                                   # 368 Pogroby
    '沙托角',                                     # 369 Point des Chateaux
    '皮特尔角',                                   # 370 Pointe-a-Pitre
    '波克罗夫',                                   # 371 Pokrov
    '波克罗夫斯科耶',                             # 372 Pokrovskoye
    '波拉诺维采 (尼米奇)',                        # 373 Polanowice (Niemitzsch)
    '波列沃耶',                                   # 374 Polevoye
    '波利比诺',                                   # 375 Polibino
    '波利约瓦',                                   # 376 Polijova
    '波兰军事转运站',                             # 377 Polish Military Transit Depot
    '波兰邮政局',                                 # 378 Polish Postal Office
    '波利托特杰利斯科耶',                         # 379 Politotdel\'skoye
    '波利托特杰利斯科耶',                         # 380 Politotdelskoye
    '警察',                                       # 381 Polizei
    '波连萨',                                     # 382 Pollenca
    '波洛梅季河',                                 # 383 Polomet\' River
    '波卢尼诺',                                   # 384 Polunino
    '波利亚科夫卡',                               # 385 Polyakovka
    '波利亚纳 (奥克佳布里斯基)',                  # 386 Polyana (Oktyabrisky)
    '波利亚诺沃',                                 # 387 Polyanovo
    '波利亚内 (乌西基尔科)',                      # 388 Polyany (Usikirkko)
    '波利登德里',                                 # 389 Polydendri
    '波利瓦尼夫卡 (波利万诺夫卡)',                # 390 Polyvanivka (Polivanovka)
    '波梅齐亚',                                   # 391 Pomezia
    '庞贝',                                       # 392 Pompei
    '庞德斯恩德',                                 # 393 Ponders End
    '波涅茹凯',                                   # 394 Ponezhukay
    '蓬塔西耶韦',                                 # 395 Pontassieve
    '蓬塔韦尔',                                   # 396 Pontavert
    '萨莫贾桥',                                   # 397 Ponte Samoggia
    '蓬',                                         # 398 Ponts
    '波尼亚蒂夫卡 (奥尔洛娃)',                    # 399 Ponyativka (Orlova)
    '波尼亚托夫卡',                               # 400 Ponyatovka
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
