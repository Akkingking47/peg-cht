# -*- coding: utf-8 -*-
"""equip-03: translate generic/category unit names, keep type designations verbatim."""
import io, sys

d = {}

def add(src, dst):
    assert src not in d, src
    d[src] = dst

# ---- generic ground units: <thing> <year> ----
for y in ['18','35','36','38','40','41','42','43','44','45','48','54','90','91']:
    pass

# Infantry-family, all year variants -> 步兵
for y in ['1935','1936','1938','1941','1942','1943','1945','1946','1947','1948',
          '1950','1951','1954','1955','1956','1958','1960','1963','1964','1965',
          '1966','1967','1968','1969','1970','1973','1974','1975','1979','1980',
          '1983','1984','1985','1990','1991','1992','1995','2000','2003','2004',
          '2005','2006','2008','2010','2012','2013','2015','35','48','91']:
    add('Infantry ' + y, '步兵 ' + y)
for y in ['1936','1942','1944','1948','1955','1963','1970','1977']:
    add('Infanteri ' + y, '步兵 ' + y)
for y in ['18','1936','1943','1945','1948','1956','1962','1964','1967','1969',
          '1971','1973','1980','1985','1986','1987','1990','1991','2000','2010']:
    add('Infanterie ' + y, '步兵 ' + y)
add('Infanterie', '步兵')
add('Infantry', '步兵')

# light infantry
for y in ['1980','1985','1990','2000','2010','2015']:
    add('Light Inf.' + y, '轻步兵 ' + y)
for y in ['2000','2004','2010']:
    add('Light Infantry ' + y, '轻步兵 ' + y)
add('Light Infantry', '轻步兵')

# armoured infantry
for y in ['1948','1954','1968','1975','1980','1985','1990','2000','2010','2015','48','54']:
    add('IDF Engineers ' + y, '以军工兵 ' + y)
for y in ['1948','1954','1968','1975','1980','1985','1990','2000','2010','2015','48','54']:
    add('IDF Infantry ' + y, '以军步兵 ' + y)
for y in ['1955','1968','1975','1980','1985','1990','2000','2010','2015']:
    add('IDF Paratroopers ' + y, '以军伞兵 ' + y)
    add('IDF Special Forces ' + y, '以军特种部队 ' + y)
for y in ['1990','2000','2010','2015']:
    add('IDF Light Inf.' + y, '以军轻步兵 ' + y)
for y in ['1948','1954','1968','1975','1980','1990','2000','2010','2015']:
    add('IDF Bridging ' + y, '以军架桥队 ' + y)
add('IDF Special Forces', '以军特种部队')
add('IDF Engineers', '以军工兵')
add('IDF Infantry', '以军步兵')
add('IDF Bridging', '以军架桥队')

# JSDF
for y in ['1954','1965','1973','1980','1990','2000','2010','2015']:
    add('JSDF Eng. ' + y, '自卫队工兵 ' + y)
    add('JSDF Inf. ' + y, '自卫队步兵 ' + y)

# Marines
for y in ['1980','1984','1990','1992','2000']:
    add('Marines ' + y, '海军陆战队 ' + y)
add('Marines 05', '海军陆战队 05')
add('Marines', '海军陆战队')

# Mercenaries
for y in ['1944','1950','1961','1970','1980','1990','2000']:
    add('Mercenaries ' + y, '雇佣兵 ' + y)

# Komandosi
for y in ['1990','2000','2010','45','48','54']:
    add('Komandosi ' + y, '突击队 ' + y)

# Marine Eng / Marine Inf (German naval)
for y in ['1941','1944','1950','1951','1958','1963','1966','1973','1980','1985','1990','2000','2010']:
    add('Marine Eng. ' + y, '海军陆战队工兵 ' + y)
for y in ['1935','1942','1943','1944','1950','1951','1958','1963','1966','1973','1980','1985','1990','2000','2010']:
    add('Marine Inf. ' + y, '海军陆战队步兵 ' + y)

# Polish infantry
for y in ['1935','1938','1943','1945','1950','1955','1958','1965','1971','1979','1988','1991','1995','2000','2010']:
    add('Inzyniernyje ' + y, '工兵 ' + y)
for y in ['1943','1944','1945']:
    add('Inzenyr ' + y, '工兵 ' + y)

# ---- explicit generic/category terms ----
T = {
 'Horses': '马匹',
 'Horska 1943': '山地步兵 1943',
 'Hovercraft': '气垫船',
 'HQ Unit': '司令部',
 'Ice patrol vessel': '冰区巡逻舰',
 'Icebreaker': '破冰船',
 'Industrial Complex': '工业区',
 'Inf. de fortresse': '要塞步兵',
 'Infantry Target': '步兵靶标',
 'Internal Troops': '内务部队',
 'Jungle Inf. 1980': '丛林步兵 1980',
 'Jungle Infantry': '丛林步兵',
 'Katapultschiff': '弹射起飞舰',
 'Kavallerie Aufklarer': '骑兵侦察',
 'Kawaleria dywizyjna': '师属骑兵',
 'Kawaleria Motorowa': '摩托化骑兵',
 'Kawaleria Pancerna': '装甲骑兵',
 'Kawaleria Powietrzna': '空降骑兵',
 'Kawaleria Powietrzna 54': '空降骑兵 54',
 'Kawaleria Zmot.': '摩托化骑兵',
 'Kawalierija': '骑兵',
 'Kawalierija 1935': '骑兵 1935',
 'Kawalierija 1938': '骑兵 1938',
 'Kedo': '凯多',
 'Kedyw': '凯迪夫',
 'Kempeitai Gendarmerie': '宪兵队',
 'Khasan monitor': '哈桑号浅水重炮舰',
 'Ko Hyoteki': '甲标的袖珍潜艇',
 'Kolarze': '自行车兵',
 'Kolo': '轮式',
 'Komandosi': '突击队',
 'Kompania Desantowa': '登陆连',
 'Kompania Motocyklowa': '摩托车连',
 'Kompania Spadochronowa': '伞兵连',
 'Konnaja': '骑兵',
 'Konnyje Strelkovy': '骑乘步兵',
 'Kosaken': '哥萨克',
 'Kradschutzen': '摩托车步兵',
 'Kradschutzen 43': '摩托车步兵 43',
 'Krasnaja Gvardija': '红近卫军',
 'Kremlowskij Polk': '克里姆林宫团',
 'Kuomintang Elite': '国民党精锐',
 'Kurassiere': '胸甲骑兵',
 'Kustenjager': '海岸猎兵',
 'Kustenjager 40': '海岸猎兵 40',
 'Kustenjager 43': '海岸猎兵 43',
 'Kuter Szturmowy [W]': '突击艇 [W]',
 'Kuter Torpedowy': '鱼雷艇',
 'Landesschutzen': '国土防卫军',
 'Landing Craft [W]': '登陆艇 [W]',
 'Landing Ship': '登陆舰',
 'Lastbil (Volvo)': '卡车（沃尔沃）',
 'Lastwagen': '卡车',
 'Legion': '军团',
 'Legion Etrangere': '外国军团',
 'Legion Etrangere 1948': '外国军团 1948',
 'Leib Gvardija': '近卫军',
 'Leichte Inf. 16': '轻步兵 16',
 'Light AA': '轻型高射炮',
 'Light AA entr.': '轻型高射炮（装甲）',
 'Light Fieldworks': '轻型野战工事',
 'Light Reaction Reg.': '轻装快速反应团',
 'Liner': '班轮',
 'LIV (SO)': 'LIV（特种作战）',
 'Long Range Desert Patrol': '远程沙漠巡逻队',
 'Long Range Recce Patrol': '远程侦察巡逻队',
 'Loshadi': '马匹',
 'Luftlande': '空降兵',
 'Luftw. Sturmpion.': '空军突击工兵',
 'Luftw. Sturmpion. 44': '空军突击工兵 44',
 'Luftwaffe 44': '空军 44',
 'Luftwaffe Gren.': '空军掷弹兵',
 'Luftwaffe PzGr 43': '空军装甲掷弹兵 43',
 'Luftwaffe PzGr 43 (gep.)': '空军装甲掷弹兵 43（装甲）',
 'Luftwaffe PzGr 44': '空军装甲掷弹兵 44',
 'Luftwaffe PzGr 44 (gep.)': '空军装甲掷弹兵 44（装甲）',
 'Lyzhny': '滑雪兵',
 'Marine': '海军陆战队',
 'Marine 2010': '海军陆战队 2010',
 'Marine Commando': '海军陆战队突击队',
 'Marine Festung Inf.': '海军陆战队要塞步兵',
 'Marine Grenadiere': '海军陆战队掷弹兵',
 'Marine Inf.': '海军陆战队步兵',
 'Marine Pioniere 38': '海军陆战队工兵 38',
 'Marine Pioniere 41': '海军陆战队工兵 41',
 'Marine Pioniere 44': '海军陆战队工兵 44',
 'Marine Raiders': '海军陆战队突击队',
 'Marine Schutzen 38': '海军陆战队步兵 38',
 'Marine Schutzen 41': '海军陆战队步兵 41',
 'Marine Schutzen 44': '海军陆战队步兵 44',
 'Mech. Infantry': '机械化步兵',
 'Mercenaries': '雇佣兵',
 'MG (entr.)': '机枪（装甲）',
 'MG (VDV)': '机枪（空降兵）',
 'MG Entr.': '机枪（装甲）',
 'MG Schutzen': '机枪步兵',
 'Militia': '民兵',
 'Mozdzierz': '迫击炮',
 'NLF': '民族解放阵线',
 'Naval Transport': '海军运输船',
 'None': '无',
 'Obrona Narodowa': '国民防卫队',
 'Oplot': None,
 'Piechota': '步兵',
 'Piechota 35': '步兵 35',
 'Piechota 40': '步兵 40',
 'Piechota Gorska 35': '山地步兵 35',
 'Piechota Legionowa': '军团步兵',
 'Pionier': '工兵',
 'Pioniere': '工兵',
 'Pioneer': '工兵',
 'Pontonniers': '架桥工兵',
 'RSI Fanteria': '意大利社会共和国步兵',
 'RSI Guardia Nazionale': 'RSI 国民警卫队',
 'Reassign Unit': '重新指派',
 'Recce': '侦察',
 'Recon': '侦察',
 'Regular': '正规步兵',
 'Resistance': '抵抗军',
 'Rowery': '自行车',
 'Royal Engineers': '皇家工兵',
 'Royal Guards': '皇家卫队',
 'SA': '南非',
 'SNLF': '海军特别陆战队',
 'SS Grenadiere': '党卫军掷弹兵',
 'SS Kavallerie': '党卫军骑兵',
 'SS Kavallerie 42': 'SS 骑兵 42',
 'SS Pioniere': '党卫军工兵',
 'SS Polizei': '党卫军警察',
 'SS Sturmpioniere': '党卫军突击工兵',
 'Saperzy': '工兵',
 'Sapper': '工兵',
 'Sappers': '工兵',
 'Scout': '侦察兵',
 'Scout Car': '侦察车',
 'Sea Transport': '运输船',
 'Security': '警备部队',
 'Security Force': '守备部队',
 'Select Air defense': '选择防空',
 'Select Anti Tank': '选择 AT',
 'Select Artillery': '选择炮兵',
 'Select Auxiliary Ship': '选择辅助舰',
 'Select Battleship': '选择 BB',
 'Select Carrier': '选择航空母舰',
 'Select Cruiser': '选择巡洋舰',
 'Select Destroyer': '选择驱逐舰',
 'Select Fighters': '选择战斗机',
 'Select Fortification': '选择要塞',
 'Select Infantry': '选择步兵',
 'Select Level Bombers': '选择重型轰炸机',
 'Select Recon': '选择侦察',
 'Select Submarine': '选择潜艇',
 'Select Tactical Bombers': '选择战术轰炸机',
 'Select Tanks': '选择坦克',
 'Sissi': '游击队',
 'Ski': '滑雪兵',
 'Sniper': '狙击手',
 'Spad.': '伞降',
 'Spadochroniarze': '伞兵',
 'Strzelcy Konni': '骑乘射手',
 'Strzelcy Pieszy': '徒步射手',
 'Strongpoint': '支撑点',
 'Supply Depot': '补给站',
 'Taczanka': '机枪车',
 'Tank': '坦克',
 'Tank Hunter': '反坦克歼击车',
 'Tankhunter': '反坦克歼击车',
 'Tankbuster': '反坦克歼击车',
 'Towed': '牵引',
 'Tracked': '履带式',
 'Tractor': '牵引车',
 'Train': '列车',
 'Tren': '列车',
 'Troops': '部队',
 'Truck': '卡车',
 'Vonat': '列车',
 'Wagon': '马车',
 'Wheeled': '轮式',
 'Winter War': '冬季战争',
 'Zandarmeria': '宪兵',
}

for k, v in T.items():
    if v is not None:
        add(k, v)

# ---- ship-type suffix: translate the generic type word only ----
SUFFIX = [
 ('-class missile boat', '级导弹艇'),
 ('-class patrol boat', '级巡逻艇'),
 ('-class gunboat', '级炮艇'),
 ('-class corvette', '级护卫舰'),
 ('-class frigate', '级护卫舰'),
 ('-class destroyer', '级驱逐舰'),
 ('-class cruiser', '级巡洋舰'),
 ('-class carrier', '级航空母舰'),
 ('-class battleship', '级战列舰'),
 ('-class submarine', '级潜艇'),
 ('-class SS', '级潜艇'),
 ('-class SSBN', '级弹道导弹核潜艇'),
 ('-class SSGN', '级巡航导弹核潜艇'),
 ('-class SSN', '级攻击核潜艇'),
 ('-class LPH', '级直升机登陆舰'),
 ('-class', '级'),
 (' missile boat', '导弹艇'),
 (' patrol boat', '巡逻艇'),
 (' patrol vessel', '巡逻舰'),
 (' gunboat', '炮艇'),
 (' corvette', '护卫舰'),
 (' frigate', '护卫舰'),
 (' destroyer', '驱逐舰'),
 (' minelayer', '布雷舰'),
 (' minesweeper', '扫雷舰'),
 (' monitor', '浅水重炮舰'),
 (' sub-chaser', '猎潜艇'),
]

def suffix_map(s):
    for suf, zh in SUFFIX:
        if s.endswith(suf):
            return s[:-len(suf)] + zh
    return None

rows = [l for l in io.open(sys.argv[1], encoding='utf-8').read().split('\n')[1:] if l != '']
out = []
kept = 0
translated = 0
unknown = []
for r in rows:
    src = r.split('\t')[0]
    if src in d:
        dst = d[src]
    else:
        dst = suffix_map(src)
        if dst is None:
            dst = src
    if dst == src:
        kept += 1
    else:
        translated += 1
    out.append(src + '\t' + dst)

with io.open(sys.argv[2], 'w', encoding='utf-8', newline='\n') as f:
    f.write('src\tdst\n')
    for l in out:
        f.write(l + '\n')

print('rows', len(rows))
print('translated', translated)
print('kept', kept)
# report dictionary entries that never matched (typos)
unused = [k for k in d if not any(l.split('\t')[0] == k for l in rows)]
print('unused dict keys', len(unused))
for k in unused:
    print('  UNUSED', repr(k))
