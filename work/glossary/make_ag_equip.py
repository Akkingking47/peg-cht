# -*- coding: utf-8 -*-
r"""
EFILE_AG\equip.txt 汉化生成器（211 个唯一词 / 734 行）。

纪律：只写 <efile>\TEXT-ZH\equip.txt，绝不动原文；GBK / 无 BOM / CRLF；逐行对齐；
       未命中必须报错（不许静默漏译）。
用法：python make_ag_equip.py [--apply]
"""
import os, io, sys, shutil, collections

GAME = r'D:\OpenPG2'
SRC = os.path.join(GAME, 'EFILE_AG')
DST = os.path.join(SRC, 'TEXT-ZH')
BK = r'D:\DSH\军事游戏汉化\backup\ag-equip-before'

# ---------------------------------------------------------------- 城墙/木栅：规则生成
# 方位是图形方向代码，保留语义译法；括号按 equip 层约定用**半角**。
DIR = {
    'E': '东', 'W': '西', 'N': '北', 'S': '南',
    'NE': '东北', 'NW': '西北', 'SE': '东南', 'SW': '西南',
    'N-S': '南北', 'W-E': '东西', 'NE-S': '东北-南', 'NE-SW': '东北-西南',
    'NW-S': '西北-南', 'NW-SE': '西北-东南', 'SE-N': '东南-北', 'SW-N': '西南-北',
    'N (i)': '北（内）', 'N (o)': '北（外）', 'S (i)': '南（内）', 'S (o)': '南（外）',
    'N-S (l)': '南北（左）', 'N-S (r)': '南北（右）',
    'l d': '左下', 'l u': '左上', 'r d': '右下', 'r u': '右上',
}
WALL_BASE = {'palisade': '木栅', 'stonewall': '石墙'}


def wall(name):
    """'palisade NE + Tower' -> '木栅 东北 + 塔楼'"""
    base, rest = name.split(' ', 1)
    zh = WALL_BASE[base]
    suf = ''
    if ' + Tower' in rest:
        suf = ' + 塔楼'
        rest = rest.replace(' + Tower', '')
    if ' + Gate' in rest:
        suf += ' + 城门'
        rest = rest.replace(' + Gate', '')
    rest = rest.strip()
    return '%s %s%s' % (zh, DIR.get(rest, rest), suf)


# ---------------------------------------------------------------- 手工定名
EQ = {
    # —— 版本标识行：引擎可能解析，保留原文
    'VERSION: Antique General Efile 3.4."Britannia"': 'VERSION: Antique General Efile 3.4."Britannia"',

    # —— 罗马军团兵种（通行军制译名）
    'Hastati': '青年兵', 'Principes': '壮年兵', 'Triarii': '后备兵',
    'praet.Triarii': '禁卫后备兵', 'praet. Triarii': '禁卫后备兵',
    'Velites': '轻装标枪兵', 'Manipularii': '支队兵', 'Praetoriani': '禁卫军',
    'Praet.Archers': '禁卫弓箭手', 'Vigiles': '城防军', 'Benefitiari': '特许兵',
    'Limitanei': '边防军', 'Foederati': '同盟军', 'Ferentarii': '轻装兵',
    'Signifer': '旗手', 'Gladiatores': '角斗士', 'Romani': '罗马人',
    'Scolae Palatinae': '宫廷卫队',
    'Comitatenses Cavalry': '野战军骑兵', 'Comitatenses Infantry': '野战军步兵',
    'lght.Auxiliares': '轻装辅助军', 'med. Auxiliares': '中型辅助军',
    'lght.Auxiliares w. rom. Officer': '轻装辅助军（罗马军官）',
    'deserted german Legionaires': '逃亡的日耳曼军团兵',
    'SPQR - Senatus PopulusQue Romanus': 'SPQR - 元老院与罗马人民',

    # —— 蛮族 / 通用兵种
    'Warriors': '战士', 'young Warriors': '青年战士', 'gentry Warriors': '贵族战士',
    'early Warriors': '早期战士',
    'Guards-of-the-Tribe': '部落卫队', 'Guards of the Tribe': '部落卫队',
    'gentry Guards-of-the-Tribe': '贵族部落卫队',
    'exp.Guards-of-the-Tribe': '精锐部落卫队',
    'early Guards-of-the-Tribe': '早期部落卫队',
    'Haeuptling': '首领', 'Doppelkaempfer': '决斗士', 'Plänkler': '散兵',
    'Skirmishers': '散兵', 'Sappers': '工兵', 'Veteran Sappers': '老兵工兵',
    'early Sappers': '早期工兵', 'Slingers': '投石兵', 'bal.Slingers': '巴利阿里投石兵',
    'Axe-Men': '斧兵', 'Axefighters': '斧斗士', 'early Axefighters': '早期斧斗士',
    'Clubfighters': '棍棒兵', 'early Clubfighters': '早期棍棒兵',
    'Spearmen': '长矛兵', 'early Spearmen': '早期长矛兵',
    'Archers': '弓箭手', 'Veteran Archers': '老兵弓箭手',
    'Archers w.comp.Bows': '复合弓弓箭手',
    'Archers w.comp.Bows&posn.Arrw.': '复合弓毒箭弓箭手',
    'Archers w.poisn.Arrows': '毒箭弓箭手',
    'Veteran Archers w.poisn.Arrows': '老兵毒箭弓箭手',
    'Archers w.Hastati': '青年兵弓箭手',
    'young Tusci': '青年伊特鲁里亚人', 'Veteran Tusci': '老兵伊特鲁里亚人',

    # —— 侦察 / 特种
    'Scout': '侦察兵', 'armed Scout': '武装侦察兵', 'Cavalry Scout': '骑兵侦察兵',
    'Spy': '间谍', 'Spy-Cave': '间谍藏身处',
    'Assassin': '刺客', 'exp.Assassin': '精锐刺客',
    'Assassin w.poisn.Blade': '毒刃刺客',
    'exp.Assassin w.poisn.Blade': '精锐毒刃刺客',
    'Saboteur': '破坏者', 'Saboteurs': '破坏者',
    'Wizard': '巫师', 'King': '国王', 'General': '将军',
    'Guards': '卫队', 'Veteran Guards': '老兵卫队',
    'Slave-Guards': '奴隶卫队', 'Elite Slave-Guards': '精锐奴隶卫队',
    'armed Slaves': '武装奴隶', 'Elite armed Slaves': '精锐武装奴隶',
    'armed Servants': '武装侍从',
    'Pirates': '海盗', 'Veteran Pirates': '老兵海盗',
    'barbarian migration': '蛮族迁徙',

    # —— 骑兵 / 步兵
    'Cavalry': '骑兵', 'light Cavalry': '轻骑兵', 'heavy Cavalry': '重骑兵',
    'early Cavalry': '早期骑兵', 'gentry Cavalry': '贵族骑兵',
    'lght.numid.Cavalry': '轻努米底亚骑兵',
    'Cavalry Trnsprt': '骑兵运输', 'Cavalry Transport': '骑兵运输',
    'armed Cav. Trnsprt': '武装骑兵运输',
    'Infantry': '步兵', 'light Infantry': '轻步兵',
    'Ind. Infantry1': '印度步兵1', 'Ind. Infantry2': '印度步兵2',
    'Ind. Infantry3': '印度步兵3', 'Ind. Infantry4': '印度步兵4',
    'Ind. Infantry5': '印度步兵5', 'Ind. Infantry6': '印度步兵6',
    'Elephant': '战象', 'Chariot': '战车',

    # —— 舰船
    'Battleship': '战舰', 'northern Battleship': '北方战舰',
    'Transportship': '运输船', 'Carrier': '运载船',
    'Longboat': '长船', 'Longboat black': '长船（黑）', 'Longboat blue': '长船（蓝）',
    'Longboat brown': '长船（棕）', 'Longboat green': '长船（绿）',
    'Longboat grey': '长船（灰）', 'Longboat yellow': '长船（黄）',
    'Heptera': '七列桨战舰', 'Liburna': '利布尔尼亚快船',
    'light Liburna': '轻型利布尔尼亚快船', 'Pentecontera': '五十桨船',
    'Tricontera': '三十桨船', 'Trirema': '三列桨战舰', 'Rammer': '撞角舰',
    'phoenician Wargalley': '腓尼基战桨船',

    # —— 攻城器械 / 工事
    'hvy. Ballista': '重型弩炮', 'Cart Ballista': '车载弩炮',
    'hvy. Catapult': '重型投石机', 'med. Catapult': '中型投石机',
    'heavy catapult': '重型投石机', 'Scorpion': '蝎弩',
    'praet.Scorpion': '禁卫蝎弩', 'Scorpion w.Hastati': '青年兵蝎弩',
    'Siege Tower': '攻城塔', 'Spear Trap': '尖刺陷阱',
    'temporary bridge': '临时桥', 'Brigde': '桥',

    # —— 建筑
    'wooden Tower': '木塔', 'wodden Tower': '木塔', 'Wodden Tower': '木塔',
    'Stone-Tower': '石塔', 'Battle Tower': '战斗塔楼',
    'Fortress': '堡垒', 'Wodden Fortress': '木堡垒',
    'wooden fortress wall': '木堡垒墙', 'stone-fortress wall': '石堡垒墙',
    'stone-fortress gate': '石堡垒门',
    'Castell': '城堡', 'Burgus': '堡塔', 'Circus': '竞技场',
    'Pyramids': '金字塔', 'House': '房屋', 'Town': '城镇',
    'cottages': '村舍', 'armed cottages': '武装村舍', 'Tipi cottages': '帐篷村舍',
    'Corral': '畜栏', 'Big Corall': '大畜栏', 'Iceberg': '冰山',

    # —— 运输工具
    'dog sled': '狗拉雪橇', 'Reindeer Transport': '驯鹿运输',
    'Kameltransport': '骆驼运输', 'Ox Cart': '牛车',
    'Wagon': '马车', 'wagon': '马车',
    'l. Wagon': '轻马车', 'l. wagon': '轻马车',
    'hvy. Wagon': '重马车', 'h. wagon': '重马车',
    'Mountain Trnsprt': '山地运输',
    '..None': '无',
}


def lookup(s):
    if s in EQ:
        return EQ[s]
    head = s.split(' ')[0]
    if head in WALL_BASE and len(s) > len(head):
        return wall(s)
    return None


def main():
    apply = '--apply' in sys.argv
    src = os.path.join(SRC, 'equip.txt')
    lines = open(src, 'rb').read().decode('cp1252').replace('\r\n', '\n').split('\n')
    out, miss = [], collections.Counter()
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith('*'):
            out.append(ln)
            continue
        z = lookup(s)
        if z is None:
            out.append(ln)
            miss[s] += 1
        else:
            out.append(ln.replace(s, z))
    print('equip.txt %d 行  唯一未命中 %d 种 / %d 处' % (len(out), len(miss), sum(miss.values())))
    for k, v in miss.most_common(40):
        print('    ×%-3d %s' % (v, k))
    if miss:
        print('\n★ 存在未命中，未写盘')
        return
    if not apply:
        print('\n（dry-run，未写盘）')
        return

    os.makedirs(BK, exist_ok=True)
    os.makedirs(DST, exist_ok=True)
    data = '\r\n'.join(out).encode('gbk')
    tmp = os.path.join(DST, 'equip.txt.new')
    open(tmp, 'wb').write(data)
    assert open(tmp, 'rb').read() == data, '回读不一致'
    dst = os.path.join(DST, 'equip.txt')
    if os.path.exists(dst) and not os.path.exists(os.path.join(BK, 'equip.txt')):
        shutil.copy2(dst, os.path.join(BK, 'equip.txt'))
    os.replace(tmp, dst)
    print('已写出 equip.txt  %d B  CRLF=%d' % (len(data), data.count(b'\r\n')))


if __name__ == '__main__':
    main()
