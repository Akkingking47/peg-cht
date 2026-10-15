# -*- coding: utf-8 -*-
"""Generate part-13.tsv per POLICY.md (chunk-13: place names + Spanish/Basque unit designations)."""
import io, sys

SRC = r'D:\DSH\军事游戏汉化\work\xscn\chunks\chunk-13.tsv'
DST = r'D:\DSH\军事游戏汉化\work\xscn\zh\part-13.tsv'

# Column-1 must equal the input bytes verbatim -> read as latin-1 so the mojibake
# lines (43/166) round-trip exactly on write.
src = io.open(SRC, encoding='latin-1', newline='').read().split('\r\n')
assert src and src[-1] == '', 'unexpected trailing content'
src.pop()

zh = [
 '阿尔塔富利亚',                                                   # 1 Altafulla
 '老奥得河',                                                       # 2 Alte Oder
 '老奥得河',                                                       # 3 Alte Oder River
 '阿尔维塞·达莫斯托',                                             # 4 Alvise da Mosto
 '阿利图斯',                                                       # 5 Alytus
 '阿迈乌尔 No.19/1旅/第1师',                                       # 6 Amaiur No.19/1 Bda./1.Div.
 '阿马尔河',                                                       # 7 Amal River
 '天津',                                                           # 8 Amatsu
 '安伯卢普',                                                       # 9 Amberloop
 '阿姆菲克利亞',                                                   # 10 Amfiklia
 '阿莫雷别塔',                                                     # 11 Amorebieta
 '圆形剧场',                                                       # 12 Amphiteatre
 '阿姆斯特丹-莱茵运河',                                            # 13 Amsterdam-Rhine canal
 '阿姆蒂萨',                                                       # 14 Amtissa
 '阿穆阿特吉 No.35/6旅/第2师',                                     # 15 Amuategi No.35/6 Bda./2 Div.
 '阿穆尔河',                                                       # 16 Amur
 '安边',                                                           # 17 Anbyon
 '安德烈亚·多里亚',                                               # 18 Andrea Doria
 '安德烈耶沃',                                                     # 19 Andreevo
 '安德烈谢尼',                                                     # 20 Andrieseni
 '安德鲁什基',                                                     # 21 Andruschki
 '安法',                                                           # 22 Anfa
 '安加特河',                                                       # 23 Angat River
 '阿涅林',                                                         # 24 Anielin
 '安州',                                                           # 25 Anju
 '安克内斯',                                                       # 26 Ankenes
 '安陆',                                                           # 27 Anlu
 '安娜马约尔',                                                     # 28 Annamajor
 '阿诺',                                                           # 29 Ano
 '安松',                                                           # 30 Ansong
 '安泰拉特',                                                       # 31 Antelat
 '安东尼奥·皮加费塔',                                             # 32 Antonio Pigafetta
 '安东尼奥托·乌索迪马雷',                                         # 33 Antoniotto Usodimare
 '安东诺夫卡',                                                     # 34 Antonovka
 '安特卫普 [港口]',                                                # 35 Antwerp [PORT]
 '安特卫普 [火车站]',                                              # 36 Antwerp [R.R. Station]
 '安特卫普大道',                                                   # 37 Antwerpse Steenweg
 'ANV 第2 No.23/1旅/第1师',                                        # 38 ANV 2 No.23/1 Bda./1 Div.
 'ANV 第3 No.68/10旅/第3师',                                       # 39 ANV 3 No.68/10 Bda./3 Div.
 'ANV No.6/13旅/第2师',                                            # 40 ANV No.6/13 Bda./2 Div.
 'ANV No.6/2纵队',                                                 # 41 ANV No.6/2 Col.
 '安阳',                                                           # 42 Anyang
 '乐化',                                                           # 43 ÀÖ»¯ (GBK mojibake recovery)
 '青岛',                                                           # 44 Aohima
 'APG',                                                            # 45 APG
 '奥波什塔格',                                                     # 46 Apostag
 '阿波斯托洛韦',                                                   # 47 Apostolove
 '阿克运河',                                                       # 48 Aq Canal
 '阿克河',                                                         # 49 Aq River
 '阿奎拉',                                                         # 50 Aquila
 '第29(摩托化)炮兵团 / 第29(摩托化)步兵师 / 第41军 / 第4集团军',   # 51 AR (mot.) 29 / 29 (mot.) ID / XLI AK / AOK 4
 '第1/第58(摩托化)炮兵团 / 第20(摩托化)步兵师 / 第14(摩托化)军 / 第4集团军',  # 52 AR (mot.) I./58 / 20 (mot.) ID / XIV (mot.) AK / AOK 4
 '第185炮兵团/第185福尔戈雷师/[X]',                                # 53 AR 185/185 Folgore/[X]
 '第190炮兵团/第90轻装师/[非洲军]',                                # 54 AR 190/90 LD/[DAK]
 '第617炮兵团',                                                    # 55 AR 617
 '第782炮兵团 / - / 第14摩托化军 / 第4集团军',                     # 56 AR 782 / - / XIV (Mot.) AK / AOK 4
 '拉马迪',                                                         # 57 Ar Ramadi
 '鲁特拜',                                                         # 58 Ar Rutbah
 '炮兵营/-/[2A]',                                                  # 59 AR.Btn./-/[2A]
 '炮兵营/第10朝鲜人民军师/[2A]',                                   # 60 AR.Btn./10 KPA Div./[2A]
 '炮兵团/-/[39A]',                                                 # 61 AR/-/[39A]
 '炮兵团/-/[42A]',                                                 # 62 AR/-/[42A]
 '炮兵团/-/[50A]',                                                 # 63 AR/-/[50A]
 '炮兵团/-/[66A]',                                                 # 64 AR/-/[66A]
 '炮兵团/第164轻装师/[非洲军]',                                    # 65 AR/164 LD/[DAK]
 '炮兵团/第36步兵师/第5集团军',                                    # 66 AR/36 ID/V Army
 '炮兵团/第4步兵师/第5集团军',                                     # 67 AR/4 ID/V Army
 '阿拉伯军团摩托化团',                                             # 68 Arab Legion Mechanised Regiment
 '阿拉瓦 No.14/5旅/第4师',                                         # 69 Araba No.14/5 Bda./4 Div.
 '阿拉迈奥',                                                       # 70 Aramaio
 '阿拉纳戈伊里 No.39/11旅/第2师',                                  # 71 Arana Goiri No.39/11 Bda./2 Div.
 '岚',                                                             # 72 Arashi
 '阿尔巴',                                                         # 73 Arba
 '阿尔汉格洛夫卡',                                                 # 74 Archangelowka
 '阿尔奇利亚',                                                     # 75 Archilla
 '阿尔西涅加',                                                     # 76 Arciniega
 '阿登 (K集群)',                                                   # 77 Ardennes (Groupement K)
 '阿德利',                                                         # 78 Ardleigh
 '阿雷塔',                                                         # 79 Areta
 '阿尔赫西利亚',                                                   # 80 Argecilla
 '阿林盖',                                                         # 81 Aringay
 '阿尔基-埃尔多 (森林)',                                           # 82 Arki-erdo (FOREST)
 '武装警察',                                                       # 83 Armed Police
 '阿尔芒蒂耶尔',                                                   # 84 Armentieres
 '阿尔内克',                                                       # 85 Arneke
 '阿拉苏阿',                                                       # 86 Arrazua
 '阿里翁达斯',                                                     # 87 Arriondas
 '阿罗芒什莱班',                                                   # 88 Arromanches-les-Bains
 '阿尔谢尼耶夫斯基',                                               # 89 Arsen'evskii
 '炮兵营/第17旅/第11集团军',                                       # 90 Art Bn/17 Br/11 Army
 '炮兵营/第3步兵师/第1韩国师',                                     # 91 Art Bn/3 ID/1 ROK
 '炮兵团/第114解放军师/[38A]',                                     # 92 Art R/114 PLA Div./[38A]
 '第422炮兵营 / 第4军 / 第6集团军',                                # 93 Art.-Abt. 422 / IV AK / AOK 6
 '第616炮兵营 / 第19摩托化军 / 克莱斯特集群',                      # 94 Art.-Abt. 616 / XIX (mot.) AK / Gr. Kleist
 '第731炮兵营 / 第4军 / 第6集团军',                                # 95 Art.-Abt. 731 / IV AK / AOK 6
 '第2/第46炮兵营 / 第11军 / 第6集团军',                            # 96 Art.-Abt. II./46 / XI AK / AOK 6
 '炮兵群/''A''师/[XIV]',                                           # 97 Art.Grp./''A'' Div./[XIV]
 '炮兵群/''B''师/[XIV]',                                           # 98 Art.Grp./''B'' Div./[XIV]
 '第255炮兵团 / 第255步兵师 / 第11军 / 第6集团军',                 # 99 Art.-Reg. 255 / 255 ID / XI AK / AOK 6
 '第30炮兵团 / 第30步兵师 / 第11军 / 第6集团军',                   # 100 Art.-Reg. 30 / 30 ID / XI AK / AOK 6
 '第103炮兵团 / 第4装甲师 / 第4军 / 第6集团军',                    # 101 Art.-Rgt. 103 / 4 Pz.Div. / IV AK / AOK 6
 '第109炮兵团 (第2营) / 第3军 / 第12集团军',                       # 102 Art.-Rgt. 109 (II.) / III AK / AOK 12 
 '第14炮兵团 / 第14步兵师 / 第11军 / 第6集团军',                   # 103 Art.-Rgt. 14 / 14 ID / XI AK / AOK 6
 '第19炮兵团 / 第19步兵师 / 第11军 / 第6集团军',                   # 104 Art.-Rgt. 19 / 19 ID / XI AK / AOK 6
 '第23炮兵团 / 第23步兵师 / 第3军 / 第12集团军',                   # 105 Art.-Rgt. 23 / 23 ID / III AK / AOK 12 
 '第24炮兵团 / 第24步兵师 / 第6军 / 第12集团军',                   # 106 Art.-Rgt. 24 / 24 ID / VI AK / 12 AOK 
 '第253炮兵团 (第4营) / 第3军 / 第12集团军',                       # 107 Art.-Rgt. 253 (IV.) / III AK / AOK 12 
 '第269炮兵团 / 第269步兵师 / 第27军 / 第6集团军',                 # 108 Art.-Rgt. 269 / 269 ID / XXVII AK / AOK 6
 '第3炮兵团 / 第3步兵师 / 第3军 / 第12集团军',                     # 109 Art.-Rgt. 3 / 3 ID / III AK / AOK 12 
 '第31炮兵团 / 第31步兵师 / 第11军 / 第6集团军',                   # 110 Art.-Rgt. 31 / 31 ID / XI AK / AOK 6
 '第32炮兵团 / 第32步兵师 / 第2军 / 第4集团军',                    # 111 Art.-Rgt. 32 / 32 ID / II AK / AOK 4 
 '第36炮兵团 / 第36步兵师 / 第7军 / 第16集团军',                   # 112 Art.-Rgt. 36 / 36 ID / VII AK / AOK 16 
 '第39炮兵团 (第1营) / 第3步兵师 / 第3军 / 第12集团军',            # 113 Art.-Rgt. 39 (I.) / 3 ID / III AK / AOK 12 
 '第59炮兵团 (第1营) / 第23步兵师 / 第3军 / 第12集团军',           # 114 Art.-Rgt. 59 (I.) / 23 ID / III AK / AOK 12 
 '第60炮兵团 (第1营) / 第24步兵师 / 第6军 / 第12集团军',           # 115 Art.-Rgt. 60(I.) / 24 ID / VI AK / 12 AOK 
 '第68炮兵团 (第1营) / 第32步兵师 / 第2军 / 第4集团军',            # 116 Art.-Rgt. 68 (I.) / 32 ID / II AK / AOK 4 
 '第72炮兵团 (第1营) / 第36步兵师 / 第7军 / 第16集团军',           # 117 Art.-Rgt. 72 (I.) / 36 ID / VII AK / AOK 16 
 '第72炮兵团 / 第35步兵师 / 第4军 / 第6集团军',                    # 118 Art.-Rgt. 72 / 35 ID / IV AK / AOK 6
 '第73炮兵团 / 第1装甲师 / 第19摩托化军 / 克莱斯特集群',           # 119 Art.-Rgt. 73 / 1 Pz.Div. / XIX (mot.) AK / Gr. Kleist
 '第74炮兵团 / 第2装甲师 / 第19摩托化军 / 克莱斯特集群',           # 120 Art.-Rgt. 74 / 2 Pz.Div. / XIX (mot.) AK / Gr. Kleist
 '第75炮兵团 / 第3装甲师 / 第16军 / 第6集团军',                    # 121 Art.-Rgt. 75 / 3 Pz.Div. / XVI AK / AOK 6
 '第78炮兵团 / 第7装甲师 / 第15摩托化军 / 第4集团军',              # 122 Art.-Rgt. 78 / 7 Pz.Div. / XV (mot.) AK / 4 AOK
 '第90炮兵团 / 第10装甲师 / 第19摩托化军 / 克莱斯特集群',          # 123 Art.-Rgt. 90 / 10 Pz.Div. / XIX (mot.) AK / Gr. Kleist
 '阿特米西奥',                                                     # 124 Artemissio
 '第102炮兵团 / 第9装甲师 / 第14摩托化军 / 第4集团军',             # 125 Artillerie-Regiment 102 / 9 Pz.Div. / XIV (mot.) AK / AOK 4
 '第103炮兵团 / 第4装甲师 / 第16摩托化军 / 第4集团军',             # 126 Artillerie-Regiment 103 / 4 Pz.Div. / XVI (Mot.) AK / AOK 4
 '第74炮兵团 / 第2装甲师 / 第19军 / 第12集团军',                   # 127 Artillerie-Regiment 74 / 2 Pz.Div. / XIX AK / AOK 12
 '第76炮兵团 / 第6装甲师 / 第41军 / 第4集团军',                    # 128 Artillerie-Regiment 76 / 6 Pz.Div. / XLI AK / AOK 4
 '第78炮兵团 / 第7装甲师 / 第15摩托化军 / 第4集团军',              # 129 Artillerie-Regiment 78 / 7 Pz.Div. / XV (Mot.) AK / 4 AOK
 '第80炮兵团 / 第8装甲师 / 第41军 / 第4集团军',                    # 130 Artillerie-Regiment 80 / 8 Pz.Div. / XLI AK / AOK 4
 '阿尔泽',                                                         # 131 Arzew
 '塞勒曼',                                                         # 132 As Salman
 '塞马沃',                                                         # 133 As Samawah
 '朝云/第9驱逐舰',                                                 # 134 Asagumo/9 DD
 '朝风',                                                           # 135 Asakaze
 '阿斯卡里',                                                       # 136 Ascari
 '阿西德拉',                                                       # 137 Ascidera
 '阿西德拉河',                                                     # 138 Ascidera River
 '阿什杜德',                                                       # 139 Asdod
 '阿什福德机场',                                                   # 140 Ashford Airport
 '阿欣登',                                                         # 141 Ashingdon
 '阿斯拉格岭',                                                     # 142 Aslag Ridge
 '阿斯佩内塞特',                                                   # 143 Aspeneset
 '塞勒特',                                                         # 144 AsSalt
 '阿斯特内',                                                       # 145 Astene
 '阿斯蒂加拉加',                                                   # 146 Astigarraga
 '阿斯图里亚斯',                                                   # 147 Asturias
 '阿苏阿',                                                         # 148 Asua
 'AT 1P',                                                          # 149 AT 1P
 '配属 B/第2印度步兵师',                                           # 150 at B/2 Indian ID
 '配属 营/第33步兵师/第15集团军',                                  # 151 at Bn/33 ID/15 Army
 '配属 营/第90解放军师/[20A]',                                     # 152 At Bn/90 PLA Div./[20A]
 '配属 营/Y部队',                                                  # 153 At Bn/Y Forces
 'AT 库内恩塞',                                                    # 154 AT Cuneense
 '炮兵 团/第1师/第2军',                                            # 155 At R/1  Div/2 Corps
 '炮兵 团/第10集团军',                                             # 156 At R/10 Army
 '配属 团/KAR',                                                    # 157 at R/KAR
 '反坦克/-/[9AG]',                                                 # 158 AT/-/[9AG]
 'AT/第9团',                                                       # 159 AT/9  R
 '反坦克/喀尔巴阡步枪旅/波兰',                                     # 160 AT/Carpathian Rifle Brigade/ Polish
 '阿塔兰迪',                                                       # 161 Atalandi
 '阿塔兰',                                                         # 162 Ataran
 '配属营/哈巴尼亚部队/阿拉伯军团',                                 # 163 atB/Habforce/Arab Legion
 '配属营/HG D',                                                    # 164 atB/HG D
 '配属营/撒哈拉集群',                                              # 165 atB/Saharian Grouping
 '罗家集',                                                         # 166 ÂÞ¼Ò¼¯ (GBK mojibake recovery)
 '阿提卡拉溪',                                                     # 167 Atikara Stream
 '炮兵 团/第10印度师',                                             # 168 atR/10 Indian Div
 '反坦克团/第36步兵师/第5集团军',                                  # 169 ATR/36 ID/V Army
 '反坦克团/第4步兵师/第5集团军',                                   # 170 ATR/4 ID/V Army
 '配属 FEF',                                                       # 171 Attached to FEF
 'Aty 1P',                                                         # 172 Aty 1P
 '炮兵营/第11步兵师(菲律宾)/USAFFE',                               # 173 Aty Bn/11 ID(PA)/USAFFE
 '炮兵营/第2朝鲜人民军师/[2A]',                                    # 174 Aty Bn/2 KPA Div./[2A]
 '炮兵群/第15集团军',                                              # 175 Aty G/15 Army
 '炮兵 团/第1师/第2军',                                            # 176 Aty R/1  Div/2 Corps
 '炮兵 团/第10军/第9战区',                                         # 177 Aty R/10 Corps/9 War Area
 '炮兵 团/第100军/汪精卫军',                                       # 178 Aty R/100 Corps/Wang Army
 '炮兵 团/第11步兵师/第1韩国师',                                   # 179 Aty R/11 ID/1 ROK
 '炮兵 团/第114步兵师/NCAC',                                       # 180 Aty R/114 ID/NCAC
 '炮兵 团/第152师',                                                # 181 Aty R/152 Div
 '炮兵 团/第18军',                                                 # 182 Aty R/18 Corps
 '炮兵 团/第18师/第18军',                                          # 183 Aty R/18 Div/18 Corps
 '炮兵 团/第199师/第18军',                                         # 184 Aty R/199 Div/18 Corps
 '炮兵 团/第21步兵师(菲律宾)/USAFFE',                              # 185 Aty R/21 ID(PA)/USAFFE
 '炮兵 团/第30步兵师/Y部队',                                       # 186 Aty R/30 ID/Y Force
 '炮兵 团/第31步兵师/第15集团军',                                  # 187 Aty R/31 ID/15 Army
 '炮兵 团/第33师/第2军',                                           # 188 Aty R/33 Div/2 Corps
 '炮兵 团/第36步兵师',                                             # 189 Aty R/36 ID
 '炮兵 团/第38步兵师/Y部队',                                       # 190 Aty R/38 ID/Y Force
 '炮兵 团/第39步兵师/Y部队',                                       # 191 Aty R/39 ID/Y Force
 '炮兵 团/第44军/第29集团军',                                      # 192 Aty R/44 Corps/29 Army
 '炮兵 团/第50步兵师/Y部队',                                       # 193 Aty R/50 ID/Y Force
 '炮兵 团/第51步兵师(菲律宾)/USAFFE',                              # 194 Aty R/51 ID(PA)/USAFFE
 '炮兵 团/第55师/第18军',                                          # 195 Aty R/55 Div/18 Corps
 '炮兵 团/第58军/第9战区',                                         # 196 Aty R/58 Corps/9 War Area
 '炮兵 团/第64步兵师/NCAC',                                        # 197 Aty R/64 ID/NCAC
 '炮兵 团/第65步兵师/NCAC',                                        # 198 Aty R/65 ID/NCAC
 '炮兵 团/第66军/第10集团军',                                      # 199 Aty R/66 Corps/10 Army
 '炮兵 团/第71步兵师(菲律宾)/USAFFE',                              # 200 Aty R/71 ID(PA)/USAFFE
 '炮兵 团/第72军/第9战区',                                         # 201 Aty R/72 Corps/9 War Area
 '炮兵 团/第73军/第29集团军',                                      # 202 Aty R/73 Corps/29 Army
 '炮兵 团/第74军/汪精卫军',                                        # 203 Aty R/74 Corps/Wang Army
 '炮兵 团/第76师/第2军',                                           # 204 Aty R/76 Div/2 Corps
 '炮兵 团/第77师/第18军',                                          # 205 Aty R/77 Div/18 Corps
 '炮兵 团/第79军/第10集团军',                                      # 206 Aty R/79 Corps/10 Army
 '炮兵 团/第91步兵师(菲律宾)/USAFFE',                              # 207 Aty R/91 ID(PA)/USAFFE
 '炮兵营/-/[2A]',                                                  # 208 Aty.Btn./-/[2A]
 '炮兵营/第10朝鲜人民军师/[2A]',                                   # 209 Aty.Btn./10 KPA Div./[2A]
 '炮兵营/第2朝鲜人民军师/[2A]',                                    # 210 Aty.Btn./2 KPA Div./[2A]
 '炮兵师/解放军 SC/[8A]',                                          # 211 Aty.Div./PLA SC/[8A]
 '炮兵/第53师/[V]',                                                # 212 Aty/53 Div./[V]
 '炮兵/喀尔巴阡步枪旅/波兰',                                       # 213 Aty/Carpathian Rifle Brigade/ Polish
 '炮兵/第5集团军',                                                 # 214 Aty/V Army
 '炮兵营/第3朝鲜人民军师/[5A]',                                    # 215 AtyBtm/3 KPA Div./[5A]
 '炮兵营/-/[5A]',                                                  # 216 AtyBtn/-/[5A]
 '炮兵营/第4朝鲜人民军师/[5A]',                                    # 217 AtyBtn/4 KPA Div./[5A]
 '炮兵营/第6骑兵师/[57SC]',                                        # 218 AtyBtn/6 Cav.Div./[57SC]
 '炮兵群/第13师/-/',                                               # 219 AtyGrp./13 Div./-/
 '炮兵群/第4师/[N]',                                               # 220 AtyGrp./4 Div./[N]
 '炮兵群/第40师/-/',                                               # 221 AtyGrp./40 Div./-/
 '炮兵群/第1师/[N]',                                               # 222 AtyGrp/1 Div./[N]
 '炮兵群/第11师/[V]',                                              # 223 AtyGrp/11 Div./[V]
 '炮兵群/第16师/[XII]',                                            # 224 AtyGrp/16 Div./[XII]
 '炮兵群/第27 BM/[XVIII]',                                         # 225 AtyGrp/27 BM/[XVIII]
 '炮兵群/第3师/[XV]',                                              # 226 AtyGrp/3 Div./[XV]
 '炮兵群/第35师/[XV]',                                             # 227 AtyGrp/35 Div./[XV]
 '炮兵群/第4师/[CTV]',                                             # 228 AtyGrp/4 Div./[CTV]
 '炮兵群/第42师/[XXIV]',                                           # 229 AtyGrp/42 Div./[XXIV]
 '炮兵群/第44师/[XII]',                                            # 230 AtyGrp/44 Div./[XII]
 '炮兵群/第45师/[V]',                                              # 231 AtyGrp/45 Div./[V]
 '炮兵群/第46师/[V]',                                              # 232 AtyGrp/46 Div./[V]
 '炮兵群/第50师/[CEM]',                                            # 233 AtyGrp/50 Div./[CEM]
 '炮兵群/第54师/[V]',                                              # 234 AtyGrp/54 Div./[V]
 '炮兵群/第56师/[XII]',                                            # 235 AtyGrp/56 Div./[XII]
 '炮兵群/第60师/[XVIII]',                                          # 236 AtyGrp/60 Div./[XVIII]
 '阿齐巴尔',                                                       # 237 Atzibar
 '奥克兰 MR/第1MR旅/[NMD]',                                        # 238 Auckland MR/1 MR Bde./[NMD]
 '奥德利恩德',                                                     # 239 Audley End
 '欧丹勒罗曼',                                                     # 240 Audun-le-Roman
 '第35侦察营 / 第35步兵师 / 第4军 / 第6集团军',                    # 241 Aufkl.-Abt 35 / 35 ID / IV AK / AOK 6
 '第1侦察营 / 第9军 / 第6集团军',                                  # 242 Aufkl.-Abt. 1 / IX AK / AOK 6
 '第14侦察营 / 第14步兵师 / 第11军 / 第6集团军',                   # 243 Aufkl.-Abt. 14 / 14 ID / XI AK / AOK 6
 '第19侦察营 / 第19步兵师 / 第11军 / 第6集团军',                   # 244 Aufkl.-Abt. 19 / 19 ID / XI AK / AOK 6
 '第20侦察营 / 第20摩托化步兵师 / 第14摩托化军 / 第4集团军',       # 245 Aufkl.-Abt. 20 / 20 (mot.) ID / XIV (mot.) AK / AOK 4
 '第208侦察营 / 第208步兵师 / 第26军 / 第18集团军',                # 246 Aufkl.-Abt. 208 / 208 ID / XXVI AK / AOK 18
 '第23侦察营 / 第23步兵师 / 第3军 / 第12集团军',                   # 247 Aufkl.-Abt. 23 / 23 ID / III AK / AOK 12 
 '第24侦察营 / 第24步兵师 / 第6军 / 第12集团军',                   # 248 Aufkl.-Abt. 24 / 24 ID / VI AK / 12 AOK 
 '第255侦察营 / 第255步兵师 / 第11军 / 第6集团军',                 # 249 Aufkl.-Abt. 255 / 255 ID / XI AK / AOK 6
 '第269侦察营 / 第269步兵师 / 第27军 / 第6集团军',                 # 250 Aufkl.-Abt. 269 / 269 ID / XXVII AK / AOK 6
 '第29侦察营 / 第29摩托化步兵师 / 第41军 / 第4集团军',             # 251 Aufkl.-Abt. 29 / 29 (mot.) ID / XLI AK / AOK 4
 '第3侦察营 / 第3步兵师 / 第3军 / 第12集团军',                     # 252 Aufkl.-Abt. 3 / 3 ID / III AK / AOK 12 
 '第3侦察营 / 第3装甲师 / 第16军 / 第6集团军',                     # 253 Aufkl.-Abt. 3 / 3 Pz.Div./ XVI AK / AOK 6
 '第30侦察营 / 第30步兵师 / 第11军 / 第6集团军',                   # 254 Aufkl.-Abt. 30 / 30 ID / XI AK / AOK 6
 '第31侦察营 / 第31 / 第11军 / 第6集团军',                         # 255 Aufkl.-Abt. 31 / 31 / XI AK / AOK 6
 '第31侦察营 / 第31步兵师 / 第11军 / 第6集团军',                   # 256 Aufkl.-Abt. 31 / 31 ID / XI AK / AOK 6
 '第32侦察营 / 第32步兵师 / 第2军 / 第4集团军',                    # 257 Aufkl.-Abt. 32 / 32 ID / II AK / AOK 4 
 '第36侦察营 / 第36步兵师 / 第7军 / 第16集团军',                   # 258 Aufkl.-Abt. 36 / 36 ID / VII AK / AOK 16 
 '第37侦察营 / 第7装甲师 / 第15摩托化军 / 第4集团军',              # 259 Aufkl.-Abt. 37 / 7 Pz.Div. / XV (mot.) AK / 4 AOK
 '第4侦察营 / 第1装甲师 / 第19摩托化军 / 克莱斯特集群',            # 260 Aufkl.-Abt. 4 / 1 Pz.Div. / XIX (mot.) AK / Gr. Kleist
 '第5侦察营 / 第2装甲师 / 第19摩托化军 / 克莱斯特集群',            # 261 Aufkl.-Abt. 5 / 2 Pz.Div. / XIX (mot.) AK / Gr. Kleist
 '第5侦察营 / 第2装甲师 / 第19军 / 第12集团军',                    # 262 Aufkl.-Abt. 5 / 2 Pz.Div. / XIX AK / AOK 12
 '第57侦察营 / 第6装甲师 / 第41军 / 第4集团军',                    # 263 Aufkl.-Abt. 57 / 6 Pz.Div. / XLI AK / AOK 4
 '第61侦察营 / 第61步兵师 / 第4军 / 第6集团军',                    # 264 Aufkl.-Abt. 61 / 61 ID / IV AK / AOK 6
 '第7侦察营 / 第4装甲师 / 第4军 / 第6集团军',                      # 265 Aufkl.-Abt. 7 / 4 Pz.Div. / IV AK / AOK 6
 '第7侦察营 / 第4装甲师 / 第16摩托化军 / 第4集团军',               # 266 Aufkl.-Abt. 7 / 4 Pz.Div. / XVI (Mot.) AK / AOK 4
 '第8侦察营 / 第5装甲师 / 第15摩托化军 / 第4集团军',               # 267 Aufkl.-Abt. 8 / 5 Pz.Div. / XV (mot.) AK / 4 AOK
 '第9侦察营 / - / 第9装甲师 / 第14摩托化军 / 第4集团军',            # 268 Aufkl.-Abt. 9 / - / 9 Pz.Div. / XIV (mot.) AK / AOK 4
 '第90侦察营 / 第10装甲师 / 第19摩托化军 / 克莱斯特集群',          # 269 Aufkl.-Abt. 90 / 10 Pz.Div. / XIX (mot.) AK / Gr. Kleist
 '党卫军特别机动师侦察营 / 党卫军特别机动师 (摩托化)',             # 270 Aufkl.-Abt. SS-V / SS-Verfügungs-Division (mot.)
 '奥雷河',                                                         # 271 Aure River
 '奥里特',                                                         # 272 Aurith
 'aux 利沃诺',                                                     # 273 aux Livorno
 '阿夫利',                                                         # 274 Aveley
 '阿韦利亚内达 No.38/12旅/第2师',                                  # 275 Avellaneda No.38/12 Bda./2 Div.
 '阿韦雷什蒂',                                                     # 276 Averesti
 '阿维耶雷',                                                       # 277 Aviere
 '阿沃拉',                                                         # 278 Avola
 '奥德格莱',                                                       # 279 Aw Dheegle
 '阿克塞尔',                                                       # 280 Axel
 '阿克塞尔溪',                                                     # 281 Axelse Kreek
 '轴心国补给点',                                                   # 282 Axis Supply Point
 '阿耶夫库尔',                                                     # 283 Ayevkur
 '圣康斯坦丁诺斯',                                                 # 284 Ayla Konstantinos
 '圣玛丽娜',                                                       # 285 Ayla Marina
 '圣特里亚斯',                                                     # 286 Ayla Trias
 '艾因塔亚',                                                       # 287 Ayn Taya
 '阿萨纳 No.7/5旅/第4师',                                          # 288 Azana No.7/5 Bda./4 Div.
 'B',                                                              # 289 B
 'B连/KAR',                                                        # 290 B Coy/KAR
 'B 梅利利亚/第4旅/[1Agrp.]',                                      # 291 B Melilla/4 Bda./[1Agrp.]
 'B.苏丹',                                                         # 292 B.Soltane
 'BA-10[1]',                                                       # 293 BA-10[1]
 'BA-64[4]',                                                       # 294 BA-64[4]
 '巴卜盖塔拉',                                                     # 295 Bab el Qattara
 '巴博尼迈杰尔',                                                   # 296 Babonymegyer
 '巴布',                                                           # 297 Babu
 '巴川',                                                           # 298 Bachuan
 '巴德戈斯基运河',                                                 # 299 Badgoski Canal
 '巴迪尔河',                                                       # 300 Badiel River
 '巴德卡河',                                                       # 301 Badka River
 '巴杜',                                                           # 302 Badu
 '贝伦塔尔',                                                       # 303 Baerenthal
 '巴加克',                                                         # 304 Bagac
 '巴加克河',                                                       # 305 Bagac River
 '巴戈山 (丘陵)',                                                  # 306 Bago-hegy (HILL)
 '巴赫卢伊',                                                       # 307 Bahlui
 '米勒赫湾',                                                       # 308 Bahr of Milh
 '圣米歇尔山海湾',                                                 # 309 Baie du Mont St. Michel
 '班察干山',                                                       # 310 Bain-Tsagan Mountain
 '白沙',                                                           # 311 Baisha
 '鲍科尼切尔涅',                                                   # 312 Bakonycsernye
 '鲍科尼沙尔卡尼',                                                 # 313 Bakonysarkany
 '鲍科尼圣基拉伊-切斯奈克',                                        # 314 Bakonyszentkiraly-Csesznek
 '鲍科尼松巴特海伊',                                               # 315 Bakonyszombathely
 '巴克里',                                                         # 316 Bakri
 '巴兰泰河',                                                       # 317 Balantay River
 '巴拉顿湖',                                                       # 318 Balaton
 '巴拉顿奥尔马迪',                                                 # 319 Balatonalmadi
 '巴拉顿弗尔德瓦尔',                                               # 320 Balatonfoldvar
 '巴拉顿菲赖德',                                                   # 321 Balatonfured
 '巴拉顿菲兹弗',                                                   # 322 Balatonfuzfo
 '巴拉顿凯奈谢',                                                   # 323 Balatonkenese
 '巴拉顿索巴迪',                                                   # 324 Balatonszabadi
 '巴拉顿萨尔索',                                                   # 325 Balatonszarszo
 '巴拉顿维拉戈什',                                                 # 326 Balatonvilagos
 '巴尔加德',                                                       # 327 Balcad
 '巴厘巴板船坞 (港)',                                              # 328 Balikpapan Docks (Port)
 '巴厘巴板部队',                                                   # 329 Balikpapan Force
 '巴利瓦格',                                                       # 330 Baliuag
 '巴雷卡',                                                         # 331 Balyka
 '班班',                                                           # 332 Bamban
 '班班河',                                                         # 333 Bamban River
 '邦卡尔瑟普拉',                                                   # 334 Bangkalsepula
 '巴尼苏海拉',                                                     # 335 Bani Suhaylah
 '巴尼亚',                                                         # 336 Bania
 '巴尼纳',                                                         # 337 Banina
 '巴尼诺',                                                         # 338 Banino
 '宝坻',                                                           # 339 Baodi
 '巴基奥',                                                         # 340 Baquio
 '巴尔河',                                                         # 341 Bar River
 '巴拉卡尔多',                                                     # 342 Baracaldo
 '巴劳奇考',                                                       # 343 Baracska
 '巴拉诺维切',                                                     # 344 Baranovicze
 '巴兰尼-切尔 (森林)',                                             # 345 Barany-cser (FOREST)
 '巴尔博埃尼',                                                     # 346 Barboeni
 '伯尔拉德',                                                       # 347 Barlad
 '贝尔诺瓦',                                                       # 348 Barnova
 '巴恩斯利',                                                       # 349 Barnsley
 '科安泰拦阻线 KW 防线',                                           # 350 Barrages Cointet Ligne KW
 '拜拉尼机场',                                                     # 351 Barrani airstrip
 '巴尔捷涅夫卡',                                                   # 352 Barten'evka
 '巴尔托洛梅奥·科莱奥尼',                                         # 353 Bartolomeo Colleoni
 '巴萨布阿',                                                       # 354 Basabua
 '巴苏',                                                           # 355 Basou
 '下科尔姆运河',                                                   # 356 Basse Colme Canal
 '下科姆运河',                                                     # 357 Basse Come Canal
 '巴桑日',                                                         # 358 Bassenge
 '拜斯塔特阿吉鲁德',                                               # 359 Bastat al Ajrud
 '巴什库夫',                                                       # 360 Baszkow
 '营/M/-/-/第6 DO/[奥尔蒂斯]',                                     # 361 Bat.M/-/-/6 DO/[Ortiz]
 '巴塔兰河',                                                       # 362 Batalan River
 '巴彻勒',                                                         # 363 Batchelor
 '巴瑟斯特岛传教站',                                               # 364 Bathhurst Island Mission
 '炮兵连守备部队',                                                 # 365 Battery Garrisons 
 '巴图法哈特',                                                     # 366 Batufahat
 '巴图贡',                                                         # 367 Batugon
 '巴图里诺',                                                       # 368 Baturino
 '巴亚姆布伊',                                                     # 369 Bayambuy
 '白云山',                                                         # 370 Bayiashan
 '巴伊拉克',                                                       # 371 Bayrak
 '巴扎尔',                                                         # 372 Bazar
 'BC',                                                             # 373 BC
 'BD',                                                             # 374 BD
 '志愿兵旅 桑坦德/[S.Esteban]',                                    # 375 Bda. Vol. Santander/[S.Esteban]
 '滩头',                                                           # 376 Beach
 '滩头阵地',                                                       # 377 Beach Head
 'beB/第50步兵师/第13军/第8军',                                    # 378 beB/50 ID/XIII/VIII
 'beB/第51步兵师/第30军/第8军',                                    # 379 beB/51 ID/XXX/VIII
 '贝达富姆',                                                       # 380 Beda Fomm
 '贝尔讷姆',                                                       # 381 Beernem
 '贝尔弗尔德',                                                     # 382 Beervelde
 '贝斯科',                                                         # 383 Beeskow
 '北京 - 武汉铁路',                                                # 384 Beijing - Wuhan R.R.
 '贝斯峡湾',                                                       # 385 Beisfjord
 '贝斯峡湾',                                                       # 386 Beisfjorden
 '别克托夫卡',                                                     # 387 Beketowka
 '别尔别克',                                                       # 388 Bel'bek
 '别尔别克河',                                                     # 389 Bel'bek River
 '贝尔切什蒂',                                                     # 390 Belcesti
 '别利杜吉诺',                                                     # 391 Bel'dugino
 '别列别尔卡',                                                     # 392 Belebelka
 '别列布济卡',                                                     # 393 Belebzika
 '贝尔瑟勒',                                                       # 394 Belsele
 '贝尔谢巴兰德',                                                   # 395 Belsobarand
 '别雷',                                                           # 396 Belyi
 '别雷拉斯特',                                                     # 397 Belyi Rast
 '本加尔德',                                                       # 398 Ben Gardane
 '本弗利特',                                                       # 399 Benfleet
 '班加西港',                                                       # 400 Benghazi harbour
]

assert len(src) == len(zh), 'line count mismatch: input=%d zh=%d' % (len(src), len(zh))

errs = []
for i, (a, b) in enumerate(zip(src, zh), 1):
    if '\t' in a or '\t' in b:
        errs.append('line %d: tab in source/translation' % i)
    if b.strip() == '':
        errs.append('line %d: empty translation' % i)
    for ch in '/[]()':
        if a.count(ch) != b.count(ch):
            errs.append('separator %r mismatch line %d: %r -> %r' % (ch, i, a, b))
    # column 1 must be byte-identical to the input line
    if a.encode('latin-1').decode('utf-8', 'replace') not in (a, '\ufffd'):
        pass
if errs:
    for e in errs:
        print(e)
    sys.exit(1)

out = ''.join('%s\t%s\r\n' % (a, b) for a, b in zip(src, zh))
with io.open(DST, 'w', encoding='utf-8', newline='') as f:
    f.write(out)
print('wrote %s (%d lines)' % (DST, len(zh)))
