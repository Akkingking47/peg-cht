# -*- coding: utf-8 -*-
"""
chunk-01.tsv -> zh/part-01.tsv
按 POLICY.md 翻译 400 行。第一列逐字节保留原文，脚本自检后写出。

翻译模型
--------
1. `/` 是层级分隔符，逐段处理（苏/德编制链），分隔符与空格原样保留。
2. 段内先做「长词短语」替换（Divisione costiera -> 海岸师）。
3. 段内数字序号：去掉英文序数后缀 th/st/nd/rd/第·ª·º，罗马数字转阿拉伯，
   译作「第N」。数字绑定：a) 紧随其后的词（1. Panzer-Division）
   b) 天干序号罗马数字（IX AK / AOK 6 / XX），c) 否则该段「名词词」。
4. 未知缩写一律原样保留，不猜。
"""
import io, os, re

BASE = r'd:\DSH\军事游戏汉化\work\atomic'
IN   = os.path.join(BASE, 'chunks', 'chunk-01.tsv')
OUT  = os.path.join(BASE, 'zh', 'part-01.tsv')

# ============================================================ 短语词表
# 长串必须排在短串之前
PHRASE = [
    # ---------------- 意大利语
    ('Divisione costiera',             '海岸师'),
    ('Divisione Assietta',             '阿西耶塔师'),
    ('132a Divisione "Ariete"',        '第132"公羊"师'),
    ('Batteria MILMART',               'MILMART炮兵连'),
    ('Squadriglia',                    '飞行中队'),
    ('Carabinieri',                    '宪兵'),
    ('Genio',                          '工兵'),
    ('Lancieri di Novara',             '诺瓦拉枪骑兵团'),
    # ---------------- 德语
    ('Krankentransport-Kompanie',      '伤病运送连'),
    ('Krankentrans.-Komp',             '伤病运送连'),
    ('Volksgrenadier-Division',        '国民掷弹兵师'),
    ('Volksgrenadier Division',        '国民掷弹兵师'),
    ('Panzergrenadier-Division',       '装甲掷弹兵师'),
    ('Infanterie-Division',            '步兵师'),
    ('Panzer-Division',                '装甲师'),
    ('Feld-Division',                  '野战师'),
    ('Flak-Division',                  '高射炮师'),
    ('Festungs-Battalion',             '要塞营'),
    ('Festungs-Battailon',             '要塞营'),
    ('Flammpanzer-Kompanie',           '喷火坦克连'),
    ('MG-Battalion',                   '机枪营'),
    ('Divisionskommando',              '师部'),
    ('Divisionsstab',                  '师部'),
    ('Deutsch-Balt. Batterie',         '波罗的海德意志人炮兵连'),
    # ---------------- 英语
    ('Royal Engineers',                '皇家工兵'),
    ('Bridging Platoon',               '架桥排'),
    ('Coastal Infantry Regiment',      '海岸步兵团'),
    ('Coastal Brigade',                '海岸旅'),
    ('Engineer Regiment',              '工兵团'),
    ('Heavy Weapon Regiment',          '重武器团'),
    ('Infantry Division',              '步兵师'),
    ('Armoured Division',              '装甲师'),
    ('Armored Division',               '装甲师'),
    ('Airborne Division',              '空降师'),
    ('Parachute Division',             '伞兵师'),
    ('Tank Brigade',                   '战车旅'),
    ('Armoured Brigade',               '装甲旅'),
    ('Parachute Brigade',              '伞兵旅'),
    ('Panzer Division',                '装甲师'),
    ('Battlegroup',                    '战斗群'),
    ('Mobile Group',                   '机动群'),
    ('Harbour Garrison',               '港口守备部队'),
    ('Armoured Lorry',                 '装甲卡车'),
    ('Armoured Car',                   '装甲车'),
    ('Airborne Eng. Bn.',              '空降工兵营'),
    ('Airborne Eng.Bn.',               '空降工兵营'),
    ('Assault Unit',                   '突击队'),
    ('Field Hospital',                 '野战医院'),
    ('Canadian Armoured Brigade',      '加拿大装甲旅'),
    ('South African Division',         '南非师'),
    ('New Zealand Division',           '新西兰师'),
    ('Belorussian Front',              '白俄罗斯方面军'),
    ('Canadian Army',                  '加拿大集团军'),
    ('Canadian Corps',                 '加拿大军'),
    ('Canadian',                       '加拿大'),
    ('Independent Parachute Brigade',  '独立伞兵旅'),
    ('Czechoslovak Armoured Brigade',  '捷克斯洛伐克装甲旅'),
    ('Independent Parachute Brigade',  '独立伞兵旅'),
    ('Polish Armored Division',        '波兰装甲师'),
    ('Heavy Anti-aircraft',            '重型高射炮'),
    ('Heavy Anti-Aircraft',            '重型高射炮'),
    ('Airborne Eng. Bn',               '空降工兵营'),
    ('Infantry Regiment',              '步兵团'),
    ('Armoured',                       '装甲'),
    ('Armored',                        '装甲'),
    ('Commandos',                      '突击队'),
    ('Engineers',                      '工兵'),
    ('Corps',                          '军'),
    ('Army',                           '集团军'),
    ('Front',                          '方面军'),
    ('Hill',                           '高地'),
    # ---------------- 意大利语编制名词（跟在 "N.Art" / "N.Inf" 之后）
    ('Art',                            '炮兵'),
    ('Inf',                            '步兵'),
    ('Legion',                         '军团'),
    # ---------------- 拉丁/英语缩合
    ('Parachute',                      '伞兵'),
    ('BomberSqdr.',                    '轰炸机中队'),
    ('BomberSqdr',                     '轰炸机中队'),
    ('MTB',                            '鱼雷艇'),
    ('flotilla',                       '分队'),
    ('Regia Aero',                     '皇家空军'),
    ('Jagd',                           '战斗机'),
    ('Cmdo.',                          '突击队'),
    ('ParaReg.',                       '伞兵团'),
    ('Camicie Nere',                   '黑衫军'),
    ('Grenadier Guards',               '掷弹兵卫队'),
    ('Irish Guards',                   '爱尔兰卫队'),
    ('Scots Guards',                   '苏格兰卫队'),
    ('Bridging',                       '架桥'),
    ('Czechoslovak',                   '捷克斯洛伐克'),
    ('Independent',                    '独立'),
    ('Polish',                         '波兰'),
]

# ============================================================ 层级与序数
# 德/苏编制链的罗马数字后缀：III=团, II=营, I=连, X=军, XX=师, XXX=军, XXXX=集团军
ECHELON = {'I': '连', 'II': '营', 'III': '团',
           'X': '军', 'XX': '师', 'XXX': '军', 'XXXX': '集团军'}

# 意大利/德语师名等专名
PROPER = {
    'Littorio': '利托里奥', 'Folgore': '闪电', 'Bologna': '博洛尼亚',
    'Trento': '特伦托', 'Brescia': '布雷西亚', 'Trieste': '的里雅斯特',
    'Superga': '苏佩尔加', 'Ariete': '公羊', 'Aosta': '奥斯塔',
    'Assietta': '阿西耶塔', 'Novara': '诺瓦拉', 'Po': '波',
    'Maczuga': '马丘加', 'Toonela': '图奥内拉', 'Vanapagan': '瓦纳帕甘',
    'Zenker': '岑克尔', 'Wolfgang': '沃尔夫冈',
    'Tunis': '突尼斯', 'Riga': '里加', 'Cesis': '切西斯',
    'Rhodes': '罗得岛', 'Perekop': '佩列科普',
    'Palemo': '巴勒莫', 'Warwickshire': '沃里克郡',
    'Worcestershire': '伍斯特郡', 'Marche': '马尔凯',
}

# 整行覆盖
FULL = {
    '"Lancieri di Novara"/133ª "Littorio"' : '"诺瓦拉枪骑兵团"/第133"利托里奥"',
    '"Maczuga" Hill'                       : '"马丘加"高地',
    '"Toonela" Armoured Lorry'             : '"图奥内拉"装甲卡车',
    '"Trois Ponts"'                        : '"特鲁瓦蓬"',
    '"Vanapagan" Armoured Car'             : '"瓦纳帕甘"装甲车',
    '"Wolfgang Zenker"'                    : '"沃尔夫冈·岑克尔"',
    "'s Grandeel"                          : "'s 赫兰德",
    "'s-Hertogenbosch"                     : "'s-海尔托亨博斯",
    "'s-Hertogengoch"                      : "'s-海尔托亨戈赫",
    '1919 BATTLE OF CESIS'                 : '1919 切西斯战役',
    '1919 BATTLE OF RIGA'                  : '1919 里加战役',
    '1920 SIEGE OF PEREKOP'                : '1920 佩列科普围城战',
    '1941 OPERATION SONNENBLUME'           : '1941 向日葵行动',
    '1942 BATTLE OF TUNIS (PBEM)'          : '1942 突尼斯战役 (PBEM)',
    '1943 BATTLE OF PROKHOROVKA (PBEM)'    : '1943 普罗霍罗夫卡战役 (PBEM)',
    '1943 BATTLE OF RHODES'                : '1943 罗得岛战役',
    '1954 BATTLE OF DIEN BIEN PHU'         : '1954 奠边府战役',
    '2nd El Alamein: Allied Attack'        : '第二次阿拉曼：盟军进攻',
    '2nd El Alamein: Counterattack'        : '第二次阿拉曼：反击',
    '128 m [ROUGH]'                        : '128米 [崎岖地形]',
    '159 m [ROUGH]'                        : '159米 [崎岖地形]',
    '183 m [ROUGH]'                        : '183米 [崎岖地形]',
    '193 m [ROUGH]'                        : '193米 [崎岖地形]',
    '204 m [ROUGH]'                        : '204米 [崎岖地形]',
    '226 m [HILL]'                         : '226米 [高地]',
    '234 m [HILL]'                         : '234米 [高地]',
    '257 m [HILL]'                         : '257米 [高地]',
}

# ============================================================ 序号处理
ROMAN = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
ORDSUF = re.compile(r'(?<=\d)(st|nd|rd|th)\b', re.I)     # 100th -> 100
ITALORD = re.compile(r'(?<=[0-9])\s*[ºª°]')               # 133ª -> 133

# 已经译成中文的名词（供「第N+名词」绑定）
ZH_NOUN = re.compile(r'[\u4e00-\u9fff]')
# 未译的未知缩写 token（保持原样）
UNK = re.compile(r'^[A-Za-z][A-Za-z0-9.\-]*$')


def roman_int(s):
    t = 0
    for i, c in enumerate(s):
        v = ROMAN.get(c, 0)
        t += -v if i + 1 < len(s) and ROMAN.get(s[i + 1], 0) > v else v
    return t


# ============================================================ 段翻译
def tr_seg(seg):
    """翻译一个 `/` 段，保留前后空白。"""
    m = re.fullmatch(r'(\s*)(.*?)(\s*)', seg, re.S)
    lead, core, trail = m.groups()
    if core.strip() == '':
        return lead + core + trail

    # ---- 1) 英文序数 + 缩写词 → 第N+中文名词（须在去后缀之前）
    core = re.sub(r'(?<![\dA-Za-z\u7b2c])(\d{1,4})(?:st|nd|rd|th)ParaReg\.',
                  lambda m: '第%s伞兵团' % m.group(1), core)
    core = re.sub(r'(?<![\dA-Za-z\u7b2c])(\d{1,4})(?:st|nd|rd|th)Div\.',
                  lambda m: '第%s师' % m.group(1), core)
    core = re.sub(r'(?<![\dA-Za-z\u7b2c])(\d{1,4})(?:st|nd|rd|th)BomberSqdr\.',
                  lambda m: '第%s轰炸机中队' % m.group(1), core)

    # ---- 1b) 去序数后缀 / 意式序数符号
    core = ORDSUF.sub('', core)
    core = ITALORD.sub('', core)

    # ---- 2) 长词短语替换（PHRASE 已按长→短排序）
    #        以英文/数字边界为界，避免 "Art" 命中 "ArtReg" 这类词内子串
    for a, b in PHRASE:
        core = re.sub(r'(?<![A-Za-z0-9])%s(?![A-Za-z0-9])' % re.escape(a), b, core)

    # ---- 3) 专名裸词
    for a, b in PROPER.items():
        core = re.sub(r'(?<![A-Za-z\u4e00-\u9fff])%s(?![A-Za-z\u4e00-\u9fff])'
                      % re.escape(a), b, core)

    # ---- 4) 编制链层级：NN.XX / NN.III / NN.I  数字+罗马层级 → 第N+层级名
    def echelon(mm):
        num, r = mm.group(1), mm.group(2)
        lvl = ECHELON.get(r)
        return '第%s%s' % (num, lvl) if lvl else mm.group(0)

    core = re.sub(r'(?<![\dA-Za-z\u4e00-\u9fff])(\d{1,4})\.(XXXX|XXX|XX|X|III|II|I)(?![A-Za-z])',
                  echelon, core)

    # ---- 5) 数字 + 已译中文名词 → 第N+名词
    #        先屏蔽已经带「第」的，避免二次加前缀
    core = re.sub(r'(?<![\dA-Za-z\u4e00-\u9fff\u7b2c])(\d{1,4})\s*\.?\s*([\u4e00-\u9fff][\u4e00-\u9fff]*)',
                  lambda m: '第%s%s' % (m.group(1), m.group(2)), core)

    # ---- 6) 未译的英文序数 (ParaReg./Div./Cmdo. 等)：数字 + 英文缩写词
    #        仅当该段不是纯编号时，加「第」并去点
    core = re.sub(r'(?<![\dA-Za-z\u4e00-\u9fff\u7b2c])(\d{1,4})(st|nd|rd|th)(?=[A-Z])',
                  lambda m: '第%s' % m.group(1), core)

    # ---- 7) 意式 "Nª Divisione 名称" → "第N名称师"
    core = re.sub(r'(?<![\dA-Za-z\u7b2c])(\d{1,3})\s*Divisione\s+(\S+)',
                  lambda m: '第%s%s师' % (m.group(1), m.group(2)), core)
    core = re.sub(r'(?<![\dA-Za-z\u7b2c])(\d{1,3})\s*Divisione(?![A-Za-z])',
                  lambda m: '第%s师' % m.group(1), core)
    # 意式序数后缀贴在数字后：132a Divisione -> 132a 已在上一步未匹配，这里补
    core = re.sub(r'(?<![\dA-Za-z\u7b2c])(\d{1,3})a\s+Divisione(?![A-Za-z])',
                  lambda m: '第%s师' % m.group(1), core)

    return lead + core + trail


# ============================================================ 主翻译
def tr_quote(m):
    """引号内文本：专名整词替换，未识别则原样（含引号）。"""
    inner = m.group(1)
    def rep(mm):
        w = mm.group(0)
        return PROPER.get(w, w)
    return '"%s"' % re.sub(r'[A-Za-z][A-Za-z\'-]*', rep, inner)


def translate(s):
    if s in FULL:
        return FULL[s]

    keep = []

    def hold(t):
        keep.append(t)
        return '\x00%d\x00' % (len(keep) - 1)

    # --- 0) 保护：装备/型号 (BA-10, M4A1, A-5) —— 必须在序数处理前
    t = re.sub(r'(?<![A-Za-z0-9])(?:[A-Z]{1,3}|[A-Z][a-z]?)-?\d{1,3}[A-Za-z0-9-]*(?![A-Za-z0-9])',
               lambda m: hold(m.group(0)), s)

    # --- 1) 去英文序数后缀 / 意式序数符号
    t = ORDSUF.sub('', t)
    t = ITALORD.sub('', t)

    # --- 2) 保护并翻译引号内专名
    t = re.sub(r'"([^"]*)"', lambda m: hold(tr_quote(m)), t)

    # --- 3) 保护：纯编号 (777/6, 1462/462)
    t = re.sub(r'(?<![\dA-Za-z])\d+(?:/\d+)+(?![\dA-Za-z])',
               lambda m: hold(m.group(0)), t)

    # --- 4) 逐 `/` 段处理
    t = '/'.join(tr_seg(seg) for seg in t.split('/'))

    # --- 5) 还原
    t = re.sub(r'\x00(\d+)\x00', lambda m: keep[int(m.group(1))], t)

    # --- 6) 英文缩写 + 序数 → 第N + 中文名词
    t = re.sub(r'(?<![\dA-Za-z\u7b2c])(\d{1,4})(st|nd|rd|th)ParaReg\.', r'第\1伞兵团', t)
    t = re.sub(r'(?<![\dA-Za-z\u7b2c])(\d{1,4})(st|nd|rd|th)Div\.',     r'第\1师', t)
    t = re.sub(r'(?<![\dA-Za-z\u7b2c])(\d{1,4})(st|nd|rd|th)BomberSqdr\.', r'第\1轰炸机中队', t)
    return t


# ============================================================ IO
def read_lines(path):
    raw = io.open(path, 'rb').read()
    try:
        txt = raw.decode('utf-8')
    except UnicodeDecodeError:
        txt = raw.decode('latin-1')
    if txt.startswith('\ufeff'):
        txt = txt[1:]
    lines = txt.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    while lines and lines[-1] == '':
        lines.pop()
    return lines


def main():
    src = read_lines(IN)
    print('input lines =', len(src))
    zh = [translate(s) for s in src]

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, 'w', encoding='utf-8', newline='') as f:
        for a, b in zip(src, zh):
            f.write('%s\t%s\r\n' % (a, b))

    raw = io.open(OUT, 'rb').read()
    assert raw[:3] != b'\xef\xbb\xbf', 'BOM!'
    txt = raw.decode('utf-8')
    lines = txt.split('\r\n')
    assert lines[-1] == '', 'must end with CRLF'
    lines.pop()
    assert len(lines) == len(src) == 400, 'lines=%d' % len(lines)
    for i, (ln, a) in enumerate(zip(lines, src), 1):
        assert ln.count('\t') == 1, 'line %d tab=%d' % (i, ln.count('\t'))
        p = ln.split('\t')
        assert p[0] == a, 'line %d col1 mismatch' % i
        for ch in '/[]()':
            assert p[0].count(ch) == p[1].count(ch), \
                'sep %r line %d: %r -> %r' % (ch, i, p[0], p[1])
    print('SELF-CHECK OK: 400 lines, 2 cols, no BOM, CRLF')


if __name__ == '__main__':
    main()
