# -*- coding: utf-8 -*-
"""chunk-16 -> part-16.tsv 汉化脚本（严格按 work/xscn/POLICY.md）。

输入：work/atomic/chunks/chunk-16.tsv   （400 行，单列地名/机构名/番号）
输出：work/atomic/zh/part-16.tsv         （原文<TAB>译文，UTF-8 无 BOM，CRLF）

本片特点：R/S 开头地名为主，含大量 `River X` 格式（→ X河）与少量
德国空军联队番号（Schlachtgeschwader / Schnellkampfgeschwader）、
英军机构名（Royal Air Force / Royal Navy Commandos）、
战役场景名（Second Italo-Senussi War / Seoul Final Battle / Rzhew Meat Grinder）
与别名括号地名。

口径（与 part-01..15 保持一致）：
  - 地名：通行中文名优先，否则音译 + 通名后缀
      River→河 Canal→运河 Bay→湾 Sea→海 Lake→湖 Station→站
      Airport/Airbase/Air Base→机场 Airfield→机场 Hill/Heights→高地/山
      Estuary→河口 Inlet→湾 Fjord→峡湾 Gulf→湾 Pocket→包围圈/口袋
      Island→岛 Cove→湾/科夫 Works→厂 Bridge→桥 Settlement→聚落
  - `River X` → `X河`（先例 Bel'bek River→别利别克河 / River Dee→迪河）
  - 括号内别名逐字保留结构，内部专名音译
  - 德语 Schlachtgeschwader→强击航空团，Schnellkampfgeschwader→快速战斗航空团
  - 未知缩写/纯编号 → 保留原文
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'chunks', 'chunk-16.tsv')
DST = os.path.join(HERE, 'part-16.tsv')

# 逐行译文（顺序与输入严格一致，共 400 条）
ZH = [
    '格拉冯河',                                   # 1 River Glavon
    '戈维河',                                     # 2 River Gowy
    '利河',                                       # 3 River Lee
    '利菲河',                                     # 4 River Liffey
    '梅德韦河',                                   # 5 River Medway
    '默西河',                                     # 6 River Mersey
    '奈恩河',                                     # 7 River Nairn
    '纳雷夫河',                                   # 8 River Narew
    '尼斯河',                                     # 9 River Ness
    '奥东河',                                     # 10 River Odon
    '奥卡河',                                     # 11 River Oka
    '奥林河',                                     # 12 River Orrin
    '乌斯河',                                     # 13 River Ouse
    '皮利茨河',                                   # 14 River Pilicc
    '罗奇河',                                     # 15 River Roach
    '罗瑟河',                                     # 16 River Rother
    '索斯纳河',                                   # 17 River Sosna
    '斯蒂克河',                                   # 18 River Stick
    '斯蒂夫基河',                                 # 19 River Stiffkey
    '泰晤士河',                                   # 20 River Thames
    '图克河',                                     # 21 River Touques
    '韦弗河',                                     # 22 River Weaver
    '维普日河',                                   # 23 River Wieprz
    '弗克拉河',                                   # 24 River Wkra
    '里弗黑德',                                   # 25 Riverhead
    '里弗斯蒂克',                                 # 26 Riverstick
    '里弗斯敦',                                   # 27 Riverstown
    '罗比亚河',                                   # 28 Rob'ya River
    '罗伯特湾',                                   # 29 Robert's Cove
    '罗卡卢梅拉',                                 # 30 Roccalumera
    '罗卡蒙菲纳',                                 # 31 Roccamonfina
    '罗卡拉文多拉',                               # 32 Roccaravindolla
    '罗卡罗马纳',                                 # 33 Roccaromana
    '罗切斯特机场',                               # 34 Rochester Airport
    '罗克炮台',                                   # 35 Rock Battery
    '罗克费里',                                   # 36 Rock Ferry
    '罗卡韦湾',                                   # 37 Rockaway Inlet
    '罗克维尔森特',                               # 38 Rockville Centre
    '罗库尔-圣马丁',                              # 39 Rocourt-Saint-Martin
    '罗登基兴',                                   # 40 Rodenkirchen
    '罗季奥诺沃-涅斯韦泰斯科耶',                  # 41 Rodionovo-Nesvetayskoye
    '罗德诺耶',                                   # 42 Rodnoye
    '罗杰斯敦河口',                               # 43 Rogerstown Estuary
    '罗戈日基诺',                                 # 44 Rogozhkino
    '罗勒斯维尔',                                 # 45 Rohrersville
    '罗克索拉内',                                 # 46 Roksolany
    '罗克索良内',                                 # 47 Roksolyany
    '罗曼科夫',                                   # 48 Romankov
    '罗曼诺沃',                                   # 49 Romanovo
    '罗姆巴克站',                                 # 50 Rombak Station
    '罗姆巴克斯博滕',                             # 51 Rombaksbotn
    '朗康科马',                                   # 52 Ronkonkoma
    '罗森达尔',                                   # 53 Roosendaal
    '罗帕日 (罗登波伊斯城堡)',                    # 54 Ropazi (Schloss Rodenpois)
    '罗斯河',                                     # 55 Ros River
    '罗索',                                       # 56 Roseau
    '罗希诺',                                     # 57 Roshchino
    '罗西亚湾',                                   # 58 Rosia Bay
    '罗斯基勒',                                   # 59 Roskilde
    '罗斯基勒峡湾',                               # 60 Roskilde Fjord
    '罗斯马伦',                                   # 61 Rosmalen
    '罗索纳河',                                   # 62 Rosona River
    '罗萨瓦河',                                   # 63 Rossava River
    '罗瑟姆',                                     # 64 Rossum
    '罗斯塔尼',                                   # 65 Rostani
    '罗斯托夫-纳-东河',                           # 66 Rostov-Na-Donu
    '罗斯托夫-纳-东河',                           # 67 Rostov-na-Donu
    '罗斯托夫-斯大林格勒',                        # 68 Rostow-Stalingrad
    '罗特巴赫',                                   # 69 Rothbach
    '罗特埃尔德',                                 # 70 Rothe Erde
    '罗特讷夫',                                   # 71 Rotheneuf
    '鹿特丹',                                     # 72 Rotterdam
    '鹿特丹桥梁',                                 # 73 Rotterdam bridges
    '朗德伍德',                                   # 74 Roundwood
    '罗维亚伊',                                   # 75 Roviai
    '罗夫诺',                                     # 76 Rovno
    '罗尔斯敦',                                   # 77 Rowlestown
    '皇家空军',                                   # 78 Royal Air Force
    '皇家炮台',                                   # 79 Royal Battery
    '皇家埃及空军',                               # 80 Royal Egyptian Air Force
    '皇家海军',                                   # 81 Royal Navy
    '皇家海军突击队',                             # 82 Royal Navy Commandos
    '皇家滕布里奇韦尔斯',                         # 83 Royal Tunbridge Wells
    '罗扎',                                       # 84 Roza
    '罗曾达尔',                                   # 85 Rozendaal
    '罗日杰斯特沃',                               # 86 Rozhdestvo
    '罗热夫卡',                                   # 87 Rozhevka
    '罗兹基什内',                                 # 88 Rozkishne
    '罗祖拉',                                     # 89 Rozula
    '罗戈日讷',                                   # 90 Rrogozhine
    '鲁巴什金',                                   # 91 Rubashkin
    '鲁贝内',                                     # 92 Rubene
    '鲁别日内',                                   # 93 Rubezhnyy
    '鲁奇伊',                                     # 94 Ruch'i
    '鲁德涅沃',                                   # 95 Rudnevo
    '鲁多伊拜拉克',                               # 96 Rudoi Bairak
    '鲁尔',                                       # 97 Ruhr
    '鲁尔包围圈',                                 # 98 Ruhr Pocket
    '吕梅尼勒',                                   # 99 Rumesnil
    '鲁米亚 (拉梅尔)',                            # 100 Rumia (Rahmel)
    '朗科恩',                                     # 101 Runcorn
    '拉什',                                       # 102 Rush
    '俄罗斯洛佐瓦亚',                             # 103 Russkaya Lozovaya
    '俄罗斯波利亚纳',                             # 104 Russkaya Polyana
    '俄罗斯科洛杰茨',                             # 105 Russkiy Kolodets
    '拉瑟福德',                                   # 106 Rutherford
    '鲁维亚诺',                                   # 107 Ruviano
    '鲁武河',                                     # 108 Ruvu River
    '里瓦奇河',                                   # 109 Rvach River
    '里亚宾基',                                   # 110 Ryabinki
    '里亚斯纳河',                                 # 111 Ryasna River
    '里亚斯内 (里亚斯诺耶)',                      # 112 Ryasnyy (Ryasnoye)
    '里亚赞斯卡亚',                               # 113 Ryazanskaya
    '里亚热纳亚',                                 # 114 Ryazhenaya
    '雷巴切',                                     # 115 Rybache
    '雷巴科夫卡',                                 # 116 Rybakovka
    '雷巴尔切',                                   # 117 Rybalche
    '雷巴茨科耶',                                 # 118 Rybatskoye
    '拉伊',                                       # 119 Rye
    '拉伊水',                                     # 120 Rye Water
    '雷诺克',                                     # 121 Rynok
    '留霍沃',                                     # 122 Ryukhovo
    '热平 (雷彭)',                                # 123 Rzepin (Reppen)
    '勒扎韦茨',                                   # 124 Rzhavets
    '勒热夫空军基地',                             # 125 Rzhev Air Base
    '勒热夫绞肉机',                               # 126 Rzhew Meat Grinder
    '圣阿加托米利泰洛',                           # 127 S. Agato Militello
    '圣克罗切卡梅里纳',                           # 128 S. Croce Camerina
    '圣罗伯托',                                   # 129 S. Roberto
    'SS 劳顿·B·埃文斯',                          # 130 SS Lawton B. Evans
    '萨德拉戈内拉',                               # 131 Sa Dragonera
    '萨波布拉',                                   # 132 Sa Pobla
    '萨拉皮塔',                                   # 133 Sa Rapita
    '萨勒',                                       # 134 Saale
    '萨勒河',                                     # 135 Saale River
    '萨本朱',                                     # 136 Sabuncu
    '萨塞',                                       # 137 Sacey
    '萨孔河',                                     # 138 Sachon River
    '萨达尼',                                     # 139 Sadani
    '萨德基',                                     # 140 Sadki
    '萨多罗耶',                                   # 141 Sadoroye
    '萨多瓦',                                     # 142 Sadova
    '萨多韦',                                     # 143 Sadove
    '萨德普里东亚',                               # 144 Sady Pridonya
    '塞生市场',                                   # 145 Saegaengsijang
    '塞普齐希',                                   # 146 Saepzig
    '萨格特',                                     # 147 Saggart
    '萨格特埃姆斯',                               # 148 Sagter Ems
    '萨希尔',                                     # 149 Sahil
    '萨希 (卡拉比)',                              # 150 Sahy (Karaby)
    '圣赫利尔',                                   # 151 Saint Helier
    '圣约瑟夫',                                   # 152 Saint Joseph
    '圣朗贝尔',                                   # 153 Saint Lambert
    '圣安妮',                                     # 154 Saint-Anne
    '圣埃尔姆-乌特尔-拉姆库尔',                   # 155 Saint-Erme-Outre-et-Ramecourt
    '圣雅克',                                     # 156 Saint-Jacques
    '圣路易',                                     # 157 Saint-Louis
    '圣马丁德瓦勒维尔',                           # 158 Saint-Martin-de-Varreville
    '圣波勒泰努瓦兹',                             # 159 Saint-Pol-sur-Ternoise
    '圣罗斯',                                     # 160 Saint-Rose
    '圣索沃尔勒维孔特',                           # 161 Saint-Sauveur-le-Vicomte
    '圣西尔万',                                   # 162 Saint-Sylvain
    '圣蒂博',                                     # 163 Saint-Thibaut
    '圣蒂埃里',                                   # 164 Saint-Thierry
    '萨卡尔卡',                                   # 165 Sakarka
    '萨哈尔内',                                   # 166 Sakharnyy
    '萨克斯维克',                                 # 167 Saksvik
    '樱花',                                       # 168 Sakura
    '萨拉',                                       # 169 Sala
    '萨拉科斯',                                   # 170 Salakos
    '萨拉米纳',                                   # 171 Salamina
    '萨拉米纳湾',                                 # 172 Salamina Bay
    '萨拉米斯海军基地',                           # 173 Salamis Naval Base
    '萨拉蒙',                                     # 174 Salamun
    '萨拉尔',                                     # 175 Salar
    '萨尔杜斯 (弗劳恩堡)',                        # 176 Saldus (Frauenburg)
    '萨莱米',                                     # 177 Salemi
    '萨利内约尼凯',                               # 178 Saline Joniche
    '萨林斯',                                     # 179 Sallins
    '萨尔姆巴赫',                                 # 180 Salmbach
    '萨尔纳沃洛克',                               # 181 Salnavolok
    '萨尔特霍尔姆',                               # 182 Saltholm
    '萨尔特湖',                                   # 183 Saltvatnet
    '萨尔瓦托山',                                 # 184 Salvatorberg
    '萨尔茨吉特',                                 # 185 Salzgitter
    '萨尔茨吉特钢铁厂',                           # 186 Salzgitter Steel Works
    '萨马拉',                                     # 187 Samara
    '萨马尔斯科耶',                               # 188 Samarskoye
    '桑别克',                                     # 189 Sambek
    '桑别克河',                                   # 190 Sambek River
    '萨莫法洛夫卡',                               # 191 Samofalovka
    '萨莫贾河',                                   # 192 Samoggia River
    '萨莫特坎',                                   # 193 Samotkan
    '萨姆罗河',                                   # 194 Samro River
    '萨穆尔斯基',                                 # 195 Samurskiy
    '圣比亚焦',                                   # 196 San Biagio
    '圣卡夏诺',                                   # 197 San Casciano
    '萨恩费利切苏尔帕纳罗',                       # 198 San Felice Sul Panaro
    '利里河畔圣乔治',                             # 199 San Giorgio a Liri
    '圣乔瓦尼',                                   # 200 San Giovanni
    '圣格雷戈里奥马泰塞',                         # 201 San Gregorio Matese
    '圣瓜恩',                                     # 202 San Gwann
    '圣路易斯德萨维尼利亚斯',                     # 203 San Luis de Sabinillas
    '圣米尼亚托',                                 # 204 San Miniato
    '圣尼科洛',                                   # 205 San Nicolo
    '卡萨莱圣彼得罗',                             # 206 San Pietro In Casale
    '圣彼得罗泰尔梅',                             # 207 San Pietro Terme
    '圣罗曼诺',                                   # 208 San Romano
    '圣罗克-拉利内阿',                            # 209 San Roque-La Linea
    '圣塞韦里诺',                                 # 210 San Severino
    '圣维托',                                     # 211 San Vito
    '桑德',                                       # 212 Sand
    '桑德岛',                                     # 213 Sand Island
    '桑迪机场',                                   # 214 Sanday Airport
    '桑登',                                       # 215 Sanden
    '桑德斯特德',                                 # 216 Sanderstead
    '桑德内斯',                                   # 217 Sandness
    '桑德维格',                                   # 218 Sandvig
    '桑威克',                                     # 219 Sandwick
    '桑迪胡克',                                   # 220 Sandy Hook
    '萨纳卡 (萨纳查尔)',                          # 221 Sangacal (Sangachal)
    '萨纳查尔空军基地',                           # 222 Sangachal Air Base
    '桑加哈',                                     # 223 Sangaha
    '桑加特',                                     # 224 Sangatte
    '桑格豪森',                                   # 225 Sangerhausen
    '桑纳特',                                     # 226 Sannat
    '圣阿戈斯蒂诺',                               # 227 Sant Agostino
    '圣阿古斯提',                                 # 228 Sant Agusti
    '圣埃利亚',                                   # 229 Sant Elia
    '圣安布罗焦',                                 # 230 Sant\'Ambrogio
    '圣安杰洛',                                   # 231 Sant\'Angelo
    '圣阿波利纳雷',                               # 232 Sant\'Apollinare
    '圣埃利亚',                                   # 233 Sant\'Elia
    '圣巴巴拉',                                   # 234 Santa Barbara
    '圣克罗切卡梅里纳',                           # 235 Santa Croce Camerina
    '圣玛尔加莉达',                               # 236 Santa Margalida
    '圣玛格丽塔',                                 # 237 Santa Margherita
    '圣玛丽亚德尔卡米',                           # 238 Santa Maria del Cami
    '圣庞萨',                                     # 239 Santa Ponca
    '桑塔尼',                                     # 240 Santanyi
    '桑泰尔诺河',                                 # 241 Santerno River
    '桑特里',                                     # 242 Santry
    '圣巴托洛梅乌德雷加托斯',                     # 243 Sao Bartolomeu de Regatos
    '萨佩吉诺',                                   # 244 Sapegino
    '萨蓬高地',                                   # 245 Sapun Heights
    '萨拉塔-加尔贝纳',                            # 246 Sarata-Galbena
    '萨拉托夫斯卡亚',                             # 247 Saratovskaya
    '萨莱',                                       # 248 Saray
    '沙尔凯西',                                   # 249 Sarkeszi
    '萨尔马特斯卡亚河',                           # 250 Sarmatskaya River
    '萨罗尼克湾',                                 # 251 Saronic Gulf
    '萨尔森特米哈伊',                             # 252 Sarszentmihaly
    '萨希诺',                                     # 253 Sashino
    '萨西',                                       # 254 Sassi
    '萨索马可尼',                                 # 255 Sasso Marconi
    '萨西',                                       # 256 Sassy
    '萨蒂拉河',                                   # 257 Satilla River
    '萨瓦特卡',                                   # 258 Savatka
    '萨韦纳河',                                   # 259 Savena River
    '萨韦尼',                                     # 260 Saveni
    '萨沃内河',                                   # 261 Savone River
    '萨克斯林厄姆',                               # 262 Saxlingham
    '塞维尔',                                     # 263 Sayville
    '斯卡洛韦',                                   # 264 Scalloway
    '斯卡帕',                                     # 265 Scapa
    '斯卡帕湾',                                   # 266 Scapa Bay
    '斯卡帕湾',                                   # 267 Scapa Flow
    '斯卡帕湾 45',                                # 268 Scapa Flow '45
    '斯卡夫',                                     # 269 Scarff
    '斯卡尔佩里亚',                               # 270 Scarperia
    '斯卡斯代尔',                                 # 271 Scarsdale
    '斯卡茨塔机场',                               # 272 Scatsta Airport
    '斯考里',                                     # 273 Scauri
    '舍费赖',                                     # 274 Schaeferei
    '绍姆堡',                                     # 275 Schaumburg
    '沙伊本哈德',                                 # 276 Scheibenhard
    '斯海尔德',                                   # 277 Schelde
    '舍尔诺夫',                                   # 278 Schernow
    '斯海恩德尔',                                 # 279 Schijndel
    '希马塔里',                                   # 280 Schimatari
    '第2强击航空团',                              # 281 Schlachtgeschwader 2
    '第2强击航空团第1大队',                       # 282 Schlachtgeschwader 2.I
    '第2强击航空团第2大队',                       # 283 Schlachtgeschwader 2.II
    '施拉登',                                     # 284 Schladen
    '施莱塔尔',                                   # 285 Schleithal
    '第10快速战斗航空团',                         # 286 Schnellkampfgeschwader 10
    '斯洪霍芬',                                   # 287 Schoonhoven
    '斯霍尔巴克',                                 # 288 Schoorbakke
    '斯霍勒 (斯霍勒)',                            # 289 Schoore (Schore)
    '绍尔滕斯',                                   # 290 Schortens
    '第104摩托化步兵团/第21装甲师',               # 291 SchtzReg 104/21. PzDiv
    '施韦特',                                     # 292 Schwedt
    '施魏格霍芬',                                 # 293 Schweighofen
    '施韦尼茨',                                   # 294 Schweinitz
    '第101重型装甲营',                            # 295 Schwere Panzerabteilung 101
    '第504重型装甲营/非洲军',                     # 296 Schwere-PzAbt 504/DAK
    '施维洛赫湖',                                 # 297 Schwielochsee
    '西皮奥内·阿夫里卡诺',                        # 298 Scipione Africano
    '斯库莱尼',                                   # 299 Sculeni
    '斯卡尔索普机场',                             # 300 Sculthorpe Airbase
    '斯昆皮亚',                                   # 301 Scumpia
    '西耶河',                                     # 302 Scye River
    '锡克利夫',                                   # 303 Sea Cliff
    '锡福德',                                     # 304 Seaford
    '谢尔盖·埃内斯库',                            # 305 Searge Enescu
    '塞贝雷哈河',                                 # 306 Sebereha River
    '塞比内',                                     # 307 Sebyne
    '塞基亚河',                                   # 308 Secchia River
    '第二次意塞努西战争',                         # 309 Second Italo-Senussi War
    '西班牙秘密任务：马拉加',                     # 310 Secret mission in Spain: Malaga
    '西班牙秘密任务：马略卡',                     # 311 Secret mission in Spain: Mallorca
    '塞德尔斯贝格',                               # 312 Sedelsberg
    '塞杰纳纳河',                                 # 313 Sedjenana River
    '塞费尔德',                                   # 314 Seefeld
    '塞豪森',                                     # 315 Seehausen
    '塞森',                                       # 316 Seesen
    '塞格河',                                     # 317 Sege River
    '塞格尔内斯',                                 # 318 Segelnes
    '塞尔登',                                     # 319 Selden
    '塞莱河',                                     # 320 Sele River
    '塞莱梅特',                                   # 321 Selemet
    '塞列什尼亚',                                 # 322 Seleshnya
    '谢列茨科耶',                                 # 323 Seletskoye
    '塞利尼亚',                                   # 324 Selinia
    '谢利瓦诺夫卡',                               # 325 Selivanovka
    '谢利瓦诺沃',                                 # 326 Selivanovo
    '塞尔内斯',                                   # 327 Selnes
    '塞尔蒂亚尔纳内斯',                           # 328 Seltjarnarnes
    '塞尔茨',                                     # 329 Seltz
    '谢梅尼夫卡 (谢苗诺夫卡)',                   # 330 Semenivka (Semenovka)
    '谢米巴尔卡',                                 # 331 Semibalka
    '谢米卢克斯基耶维谢尔基',                     # 332 Semilukskije Wyselki
    '谢涅什科夫库特',                             # 333 Seneshkov Kut
    '森格莱阿',                                   # 334 Senglea
    '塞尼奥河',                                   # 335 Senio River
    '先克维切夫卡',                               # 336 Senkevichevka
    '先诺伊',                                     # 337 Sennoy
    '塞努西雇佣兵',                               # 338 Senussi Paid Regulars
    '塞努西部族战士',                             # 339 Senussi Tribal Fighters
    '首尔决战',                                   # 340 Seoul Final Battle
    '谢拉菲莫夫',                                 # 341 Serafimov
    '谢拉菲莫维奇 (谢拉菲莫夫)',                  # 342 Serafimovich (Serafimov)
    '塞拉波',                                     # 343 Serapo
    '塞尔基奥河',                                 # 344 Serchio River
    '谢列布里扬斯基',                             # 345 Serebryanskiy
    '谢列季纳-布达',                              # 346 Seredina-Buda
    '谢列济诺',                                   # 347 Serezino
    '谢尔盖耶夫卡',                               # 348 Sergeyevka
    '谢尔吉耶夫斯科耶',                           # 349 Sergiyevskoye
    '谢尔戈-伊万诺夫斯科耶',                      # 350 Sergo-Ivanovskoye
    '谢尔希伊夫卡 (谢尔盖耶夫卡)',                # 351 Serhiivka (Sergeyevka)
    '塞里福普拉',                                 # 352 Serifopoula
    '塞尔拉塞尔扎诺',                             # 353 Serra Serzano
    '圣巴巴拉山',                                 # 354 Serra de Santa Barbara
    '塞雷塔',                                     # 355 Serreta
    '塞斯萨利内斯',                               # 356 Ses Salines
    '塞萨奥伦卡',                                 # 357 Sessa Aurunca
    '塞萨诺',                                     # 358 Sessano
    '塞斯托菲奥伦蒂诺',                           # 359 Sesto Fiorentino
    '谢斯特罗列茨基拉兹利夫',                     # 360 Sestroretskiy Razliv
    '塞特',                                       # 361 Setter
    '“街垒”聚落',                                # 362 Settlement "Barrikady"
    '“红色十月”聚落',                            # 363 Settlement "Red October"
    '谢通河',                                     # 364 Setun River
    '塞瓦斯托波尔湾 (北湾)',                      # 365 Sevastopol Bay (Severnaya Bay)
    '谢瓦斯季亚诺夫',                             # 366 Sevastyanov
    '塞文欧克斯',                                 # 367 Sevenoaks
    '谢韦里诺夫卡',                               # 368 Severinovka
    '北德维纳',                                   # 369 Severnaya Dvina
    '西北滨海区',                                 # 370 Severo-Primorskaya Part
    '北德文斯克 (莫洛托夫斯克)',                  # 371 Severodvinsk (Molotovsk)
    '谢韦尔斯卡亚',                               # 372 Severskaya
    '北顿涅茨河',                                 # 373 Severskii Donets River
    '谢夫斯克',                                   # 374 Sevsk
    '塞扎',                                       # 375 Sezha
    '斯菲纳里',                                   # 376 Sfinari
    '斯加里 (扎尔)',                              # 377 Sgari (Zhar)
    '沙布雷基诺',                                 # 378 Shablykino
    '沙赫特',                                     # 379 Shakhty
    '上海先',                                     # 380 Shanghaisien
    '尚基尔河',                                   # 381 Shankhill River
    '尚基尔',                                     # 382 Shankill
    '绍基',                                       # 383 Shaoki
    '沙皮诺',                                     # 384 Shapino
    '沙罗夫卡',                                   # 385 Sharovka
    '夏普斯堡',                                   # 386 Sharpsburg
    '沙特河',                                     # 387 Shat River
    '绍米扬',                                     # 388 Shaumyan
    '谢格洛夫卡',                                 # 389 Shcheglovka
    '谢普金',                                     # 390 Shchepkin
    '谢尔班卡',                                   # 391 Shcherbanka
    '谢尔奇耶',                                   # 392 Shchuchye
    '谢尔登',                                     # 393 Shelden
    '谢南多厄枢纽站',                             # 394 Shenandoah Junction
    '谢南多厄河',                                 # 395 Shenandoah River
    '谢纳夫拉什',                                 # 396 Shenavlash
    '申吉伊',                                     # 397 Shendzhiy
    '谢泼兹敦',                                   # 398 Shepherdstown
    '谢普韦',                                     # 399 Shepway
    '舍夫琴卡 (舍甫琴科)',                        # 400 Shevchenka (Shevchenko)
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
