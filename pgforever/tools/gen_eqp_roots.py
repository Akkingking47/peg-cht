# -*- coding: utf-8 -*-
r"""
按词根生成 .pgeqp 装备名译文（补齐子代理未覆盖的分片）。

策略：与既定口径一致 ——
  · 装备型号 / 舰名 / 飞机型号 / 武器型号 → 保留原文
  · 兵种 / 编制 / 后勤 / 工事 / 武器类别 / 舰船类别词 → 译中文
  · 国别短码后缀 → 译中文（Hu→匈牙利、Po→波兰…），前缀缩写保留（US/GB/AU/RA/RN…）

只输出"确实发生变化"的条目；纯型号条目省略（部署时无需改动）。
"""
import glob, json, os, re, sys

WORK = r'D:\DSH\军事游戏汉化\pgforever\work\eqp-all'
OUT = os.path.join(WORK, 'zh')
GROUPS = sys.argv[1:] or ['05', '09', '10', '17', '20']

# ---------- 多词短语（最长优先，先替换） ----------
PHRASES = [
    ('Pocket Battleship', '袖珍战列舰'),
    ('Sandbag Bunker', '沙袋地堡'),
    ('Barbed Wire', '铁丝网'),
    ('National Guard', '国民卫队'),
    ('Border Guard', '边防军'),
    ('Light Tank', '轻型坦克'),
    ('Medium Tank', '中型坦克'),
    ('Heavy Tank', '重型坦克'),
    ('Sea Plane', '水上飞机母舰'),
    ('Draft Horse', '驮马'),
    ('Pontoon Bridge', '浮桥'),
    ('Pontoon Brdge', '浮桥'),
    ('Pontoon Bdge', '浮桥'),
    ('Bridge Engr', '架桥工兵'),
    ('Bridge Eng', '架桥工兵'),
    ('Bridge En', '架桥工兵'),
    ('Army Engr', '陆军工兵'),
    ('Army Eng', '陆军工兵'),
    ('Army Inf', '陆军步兵'),
    ('Inf HW', '重武器步兵'),
    ('HW Inf', '重武器步兵'),
    ('Mnt Infantry', '山地步兵'),
    ('Mountain Inf', '山地步兵'),
    ('Marine MG', '陆战队机枪'),
    ('Marine Rgt', '陆战团'),
    ('MC Rockets', '陆战队火箭炮'),
    ('Scout Car', '侦察车'),
    ('Scout Gr', '侦察组'),
    ('Recon Cav', '侦察骑兵'),
    ('Recon', '侦察'),
    ('Recce', '侦察'),
    ('Rcn', '侦察'),
    ('Air Transport', '空运'),
    ('Radar Station', '雷达站'),
    ('Radar', '雷达站'),
    ('Field Works', '野战工事'),
    ('Field Fortification', '野战工事'),
    ('Strong Point', '据点'),
    ('Strongpoint', '据点'),
    ('Pill Box', '碉堡'),
    ('Block House', '碉楼'),
    ('Tank Trap', '反坦克桩'),
    ('Tank Trap', '反坦克桩'),
    ('Coastal Battery', '海岸炮台'),
    ('Battery', '炮台'),
    ('Fortress', '要塞'),
    ('Casemate', '炮廓'),
    ('Bunker', '地堡'),
    ('Fort', '要塞'),
    ('Anti-Tank Gun', '反坦克炮'),
    ('Antitank Rifles', '反坦克枪'),
    ('Antitank Rifle', '反坦克枪'),
    ('MG Rgt', '机枪团'),
    ('MG Inf', '机枪步兵'),
    ('Machine Gun', '机枪'),
    ('Mtn Gun', '山炮'),
    ('Mont Gun', '山炮'),
    ('Mountain Gun', '山炮'),
    ('Field Gun', '野战炮'),
    ('Field Art', '野战炮'),
    ('Light Artillery', '轻型火炮'),
    ('Garrison', '守备队'),
    ('Bridge', '架桥'),
    ('Engineers', '工兵'),
    ('Engineer', '工兵'),
    ('Bridgers', '架桥工兵'),
    ('Pioneers', '工兵'),
    ('Pioniere', '工兵'),
    ('Seabees', '海蜂工兵'),
    ('Seebees', '海蜂工兵'),
    ('Paratroopers', '伞兵'),
    ('Paratroops', '伞兵'),
    ('Paramarines', '伞降陆战队'),
    ('Paraengineers', '伞降工兵'),
    ('Paratroops', '伞兵'),
    ('Commandos', '突击队'),
    ('Commando', '突击队'),
    ('Rangers', '游骑兵'),
    ('Cossacks', '哥萨克'),
    ('Partisans', '游击队'),
    ('Partisians', '游击队'),
    ('Partisan', '游击队'),
    ('Irregulars', '非正规军'),
    ('Internationals', '国际纵队'),
    ('Legionnaires', '外籍军团兵'),
    ('Legionnaire', '外籍军团兵'),
    ('Legion', '军团'),
    ('Reserves', '预备队'),
    ('Regulars', '正规军'),
    ('Conscripts', '新兵'),
    ('Conscript', '新兵'),
    ('Volunteers', '志愿兵'),
    ('Cadets', '士官生'),
    ('Militia', '民兵'),
    ('Guards', '近卫军'),
    ('Guard', '近卫'),
    ('Special Forces', '特种部队'),
    ('Sailors', '水兵'),
    ('Marines', '陆战队'),
    ('Marine', '陆战队'),
    ('Cavalry', '骑兵'),
    ('Cav', '骑兵'),
    ('Bicycle', '自行车步兵'),
    ('Motorcycle', '摩托车'),
    ('Armored Infantry', '装甲步兵'),
    ('ArmoredInfantry', '装甲步兵'),
    ('Panzergrenadier', '装甲掷弹兵'),
    ('Flammenwerfer', '火焰喷射器'),
    ('Flammpanzer', '喷火坦克'),
    ('Flamm', '喷火'),
    ('Truck', '卡车'),
    ('Wagon', '马车'),
    ('Camion', '卡车'),
    ('Horse', '马匹'),
    ('Mule', '骡马'),
    ('Pack', '驮运'),
    ('Limber', '前车'),
    ('Carrier', '运输车'),
    ('Halftrk', '半履带车'),
    ('Hftrk', '半履带车'),
    ('Halftrack', '半履带车'),
    ('Jeep', '吉普车'),
    ('Tractor', '牵引车'),
    ('Transport Ship', '运输舰'),
    ('Transport', '运输'),
    ('Supply', '补给'),
    ('Merchant', '商船'),
    ('Battleship', '战列舰'),
    ('BB', '战列舰'),
    ('Heavy Cruiser', '重巡洋舰'),
    ('Light Cruiser', '轻巡洋舰'),
    ('Cruiser', '巡洋舰'),
    ('LtCruiser', '轻巡洋舰'),
    ('HvyCruiser', '重巡洋舰'),
    ('LtCr', '轻巡洋舰'),
    ('Destroyer', '驱逐舰'),
    ('Destr', '驱逐舰'),
    ('Niszczyciel', '驱逐舰'),
    ('Submarine', '潜艇'),
    ('Sub', '潜艇'),
    ('Flotilla', '分舰队'),
    ('Monitor', '浅水重炮舰'),
    ('Mines', '水雷'),
    ('Howitzer', '榴弹炮'),
    ('Mortar', '迫击炮'),
    ('Rockets', '火箭炮'),
    ('Rocket', '火箭炮'),
    ('Katyusha', '喀秋莎'),
    ('Nebelwerfer', '喷烟者'),
    ('Artillery', '火炮'),
    ('Arty', '火炮'),
    ('Art', '火炮'),
    ('ATG', '反坦克炮'),
    ('FlaK', '高射炮'),
    ('Flak', '高射炮'),
    ('AA', '高射炮'),
    ('AD', '防空炮'),
    ('MG', '机枪'),
    ('Gun', '炮'),
    ('Ship', '舰船'),
    ('Jager', '猎兵'),
    ('Jaeger', '猎兵'),
    ('Alpini', '山地兵'),
    ('Bersaglieri', '狙击兵'),
    ('Piechota', '步兵'),
    ('Infanterie', '步兵'),
    ('Infantery', '步兵'),
    ('Infantry', '步兵'),
    ('Inf', '步兵'),
    ('Mounted', '乘马'),
    ('Capital', '主力舰'),
    ('Coastal', '海岸'),
    ('Army', '陆军'),
    ('Corps', '军'),
    ('Division', '师'),
    ('Brigade', '旅'),
    ('Regiment', '团'),
    ('Battalion', '营'),
    ('Company', '连'),
    ('Squadron', '中队'),
    ('Squad', '班'),
    ('Sqd', '班'),
    ('Section', '分队'),
    ('Armored', '装甲'),
    ('Light', '轻型'),
    ('Heavy', '重型'),
    ('Hvy', '重型'),
    ('Field', '野战'),
    ('Royal', '皇家'),
    ('Colonial', '殖民'),
    ('Enemy', '敌方'),
    ('Axis', '轴心'),
    ('Allied', '盟军'),
    ('Mountain', '山地'),
    ('Mnt', '山地'),
    ('Airborne', '空降'),
    ('Air', '空中'),
    ('Naval', '海军'),
    ('HQ', '司令部'),
    ('Communication', '通信'),
    ('Observation', '观测'),
    ('Car', '汽车'),
    ('Indian', '印度'),
    ('Italian', '意大利'),
    ('Kriegs Marine', '德国海军'),
    ('Kav', '骑兵'),
    ('Mg', '机枪'),
    ('HW', '重武器'),
    ('Helicopter', '直升机'),
    # 日军兵种/编制
    ('Kyoka Hohei', '强化步兵'),
    ('Jitensha Butai', '自行车部队'),
    ('Kutei Butai', '海军陆战队'),
    ('Konkyochitai', '根据地队'),
    ('Konoe Shidan', '近卫师团'),
    ('Ko-Gata Sensha', '甲型坦克'),
    ('Rikusentai', '海军陆战队'),
    ('Kempeitai', '宪兵队'),
    ('Teishin Shudan', '挺进团'),
    ('Teishin Dan', '挺进团'),
    ('Hohei', '步兵'),
    ('Kohei', '工兵'),
    ('Kairyu', '海龙'),
    ('Kaiten', '回天'),
    ('Ohka', '樱花'),
    # 其他语言兵种
    ('Piechota', '步兵'),
    ('Ciezka', '重型'),
    ('Huszar', '骠骑兵'),
    ('Husaren', '骠骑兵'),
    ('Honved', '匈牙利国防军'),
    ('Landwehr', '地方防卫军'),
    ('Landesschutzen', '地方步兵'),
    ('Prezidento', '总统号'),
    ('Marinestosstruppen', '海军突击队'),
    ('Marine-Infanterie', '海军步兵'),
    ('Marine Inf.', '海军步兵'),
    ('NavalInfantry', '海军步兵'),
    ('Naval Infantry', '海军步兵'),
    ('Naval', '海军'),
    ('Marine', '陆战队'),
    ('Mountain', '山地兵'),
    ('Militia', '民兵'),
    ('Mortar Inf.', '迫击炮步兵'),
    ('Field HQ', '野战司令部'),
    ('Guard Tower', '哨塔'),
    ('ArmorCav', '装甲骑兵'),
    ('ArmCav', '装甲骑兵'),
    ('Autopropulsada', '自行火炮'),
    ('Bridgelayer', '架桥车'),
    ('Merchant Ship', '商船'),
    ('Pontoon', '浮桥'),
    ('Recon', '侦察'),
    ('Scouts', '侦察兵'),
    ('Scout', '侦察'),
    ('Squad', '班'),
    ('Train', '辎重队'),
    ('Rail', '铁道'),
    ('Staff', '参谋部'),
    ('T-Boat', '鱼雷艇'),
    ('Tank', '坦克'),
    ('Tower', '塔'),
    ('Fort', '要塞'),
    ('Garn', '守备队'),
    ('Soldaten', '士兵'),
    ('Schutzen', '步兵'),
    ('Destructor', '驱逐舰'),
    ('Infanteria', '步兵'),
    ('Para', '伞兵'),
    ('4xMG', '4x机枪'),
]

# ---------- 完整名称覆盖表（优先于词根，用于消歧） ----------
OVERRIDE = {
    'Ro.37': 'Ro.37',
    'MR Be1': 'MR Be1',
    'Inf. Mora': 'Inf. Mora',
    'Princes Royal': 'Princes Royal',
    'Ocean Mines': 'Ocean 水雷舰',
    'Cruiser IV': '巡航坦克 IV',
    'SF AD Ship': 'SF 防空舰',
    'US AD Ship': 'US 防空舰',
    'Int. Brigade': '国际旅',
    'MN Inf.Marina': 'MN 海军陆战队',
    'MR Inf. Naval': 'MR 海军陆战队',
    'MR Grd. Naval': 'MR 海军警卫',
    'Itl Draft Horse': 'Itl 驮马',
    'Indian Legion': '印度军团',
    'Italian Cav': '意大利骑兵',
    'Italian MG Inf': '意大利机枪步兵',
    'K.u.k. Kav': '奥匈骑兵',
    'K.u.k. Mg Inf': '奥匈机枪步兵',
    'Kriegs Marine': '德国海军',
    'LW Inf.': 'LW 步兵',
    'I Flotilla': '第1分舰队',
    'II Flotilla': '第2分舰队',
    'III Flotilla': '第3分舰队',
    'IX Flotilla': '第9分舰队',
    'II Scout Gr': '第2侦察组',
    'IV Scout Gr': '第4侦察组',
    'Rus 47mm G': '苏联 47mm 炮',
    'Rus 57mm G': '苏联 57mm 炮',
    'Rus 76mm G': '苏联 76mm 炮',
    'Armored Car': '装甲汽车',
    'US Marine B': 'US 陆战队 B',
    '8,8 Flak18': '8,8 高射炮 18',
    'Po Bleriot': '波兰 Bleriot',
    'Ital 105/ Art': '意大利 105mm 火炮',
    'Ital 155/Art': '意大利 155mm 火炮',
    'Ocean Mines': 'Ocean 水雷舰',
}

# ---------- 国别短码（后缀，译中文） ----------
COUNTRY = {
    'Hu': '匈牙利', 'Po': '波兰', 'Bu': '保加利亚', 'Bg': '保加利亚', 'Ro': '罗马尼亚',
    'Ru': '苏联', 'Rus': '苏联', 'Fr': '法国', 'Ge': '德国', 'Ger': '德国',
    'Gr': '希腊', 'Yu': '南斯拉夫', 'Fi': '芬兰', 'No': '挪威', 'Ne': '荷兰',
    'It': '意大利', 'Ital': '意大利', 'Be': '比利时', 'Sw': '瑞典', 'Turk': '土耳其',
    'Serb': '塞尔维亚', 'Cz': '捷克', 'Czech': '捷克', 'Slavic': '斯拉夫',
    'Polish': '波兰', 'Prussian': '普鲁士', 'Magyar': '匈牙利', 'Montenegrin': '黑山',
    'Portugal': '葡萄牙', 'Br': '英国', 'Serbian': '塞尔维亚', 'Russian': '苏联', 'K.u.k.': '奥匈',
}

# ---------- 绝不替换（型号/舰名/机构代号） ----------
PROTECT = re.compile(r'^(US|GB|AU|RA|RN|REP|FJ|AF|CCP|CHN|PO|SF|NTRK|VM|LSF|ODS|GRA|KXI|KXIV|II|III|IV|IX|V|VI|B|a|b|SB|MC|NG)$')


def translate(name):
    # 保留首尾空白（原文有的条目带尾随空格，必须原样保留以免产生无意义改动）
    m = re.match(r'^(\s*)(.*?)(\s*)$', name, re.S)
    pad_l, core, pad_r = m.group(1), m.group(2), m.group(3)
    s = core
    quoted = s.startswith('"') and s.endswith('"')
    if quoted:
        s = s[1:-1]

    key = s
    if key in OVERRIDE:
        out = OVERRIDE[key]
        out = ('"' + out + '"') if quoted else out
        return pad_l + out + pad_r

    def sub_phrases(t):
        for en, zh in sorted(PHRASES, key=lambda x: -len(x[0])):
            pat = re.compile(r'(?<![A-Za-z0-9])' + re.escape(en) + r'(?![A-Za-z0-9])')
            t = pat.sub(zh, t)
        return t

    out = sub_phrases(s)

    # 国别短码：左右都不得紧邻字母/数字（避免 Gr40 / MG42 等被误切）
    for k, v in COUNTRY.items():
        out = re.sub(r'(?<![A-Za-z0-9])' + re.escape(k) + r'(?![A-Za-z0-9])', v, out)

    # 清理：中文后紧跟 '.' 且无内容 → 去点
    out = re.sub(r'(?<=[\u4e00-\u9fff])\.\s*$', '', out)
    # 中文与后续数字间补空格
    out = re.sub(r'([\u4e00-\u9fff])(\d)', r'\1 \2', out)

    if quoted:
        out = '"' + out + '"'
    return pad_l + out + pad_r


def main():
    src = {}
    for f in sorted(glob.glob(os.path.join(WORK, 'src*.json'))):
        for it in json.load(open(f, encoding='utf-8')):
            src[it['md5']] = it['text']

    done = set()
    for f in sorted(glob.glob(os.path.join(OUT, 'z*.jsonl'))):
        for line in open(f, encoding='utf-8'):
            s = line.strip()
            if s:
                done.add(json.loads(s).get('md5', ''))

    CJK = re.compile(r'[\u4e00-\u9fff]')
    total_out = 0
    for g in GROUPS:
        p = os.path.join(WORK, 'src%s.json' % g)
        if not os.path.exists(p):
            continue
        recs = json.load(open(p, encoding='utf-8'))
        miss = [r for r in recs if r['md5'] not in done]
        lines = []
        for r in miss:
            zh = translate(r['text'])
            if zh and zh != r['text']:
                lines.append(json.dumps({'md5': r['md5'], 'zh': zh}, ensure_ascii=False))
        # 分块写，每块 90
        for i in range(0, len(lines), 90):
            op = os.path.join(OUT, 'z%sg%d.jsonl' % (g, i // 90 + 1))
            with open(op, 'w', encoding='utf-8') as w:
                w.write('\n'.join(lines[i:i + 90]) + '\n')
        total_out += len(lines)
        print('src%s: 缺 %d，生成译文 %d 条 → %d 个文件'
              % (g, len(miss), len(lines), (len(lines) + 89) // 90))
    print('合计新增译文 %d 条' % total_out)


if __name__ == '__main__':
    main()
