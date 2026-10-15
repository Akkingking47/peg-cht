# -*- coding: utf-8 -*-
"""标准译名库 · 权威译名核对审计器

对齐「通行的权威译名」，对 glossary/standard-glossary.tsv 做六类核对：

  A 未译残留    —— LOCKED 条目译文里仍夹着可译英文词
  B 内部不一致  —— 同一原文出现多个不同中文译名
  C 编码乱码    —— 原文列/译文列的 cp1252→GBK mojibake
  D 编制用语    —— 同一英文缩写有的译、有的留（口径不统一）
  E 标点规范    —— 分层内的括号全/半角混用、异常空格
  F 权威偏离    —— 著名人物/地名/术语与通行译名基准表不符

输出 glossary/glossary-authority-review.tsv（UTF-8 BOM / CRLF）。
"""
import collections
import csv
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GLOSS = os.path.join(ROOT, 'glossary', 'standard-glossary.tsv')
BASE = os.path.join(HERE, 'authority-baseline.tsv')
OUT = os.path.join(ROOT, 'glossary', 'glossary-authority-review.tsv')

CJK = re.compile(r'[\u4e00-\u9fff]')
LAT = re.compile(r'[A-Za-z]')
ROMAN = re.compile(r'^[IVXLCDM]+$')
# cp1252 单字节被 GBK 误读后最常出现的"假汉字"（实测归纳：áéèëíóöü 等衍生）
MOJI_CHARS = '閑馻鑢黦黣頠銆鈥锛黷鯾黶雗鰊鰎'

# 政策保留：长度 <=5 的全大写 token 视为缩写，不计入"未译残留"
ALLOW_UPPER = {
    'AT', 'BB', 'ZOC', 'LOS', 'LOF', 'VH', 'AAR', 'BV', 'UN', 'US', 'UK', 'AA', 'MG',
    'HQ', 'POW', 'RA', 'AR', 'IR', 'RCT', 'RTR', 'CTV', 'BLM', 'DLC', 'RDP', 'RC',
    'GRCA', 'GRDI', 'GRCA', 'DIM', 'DI', 'DLM', 'DLC', 'BC', 'CA', 'AK', 'AOK', 'SS',
    'HMS', 'HMAS', 'HMNZS', 'USS', 'KMS', 'RM', 'RN', 'LW', 'OKH', 'OKW', 'AFV',
}

# 计量单位/量纲符号：翻译中按惯例保留，不计入"未译残留"
UNITS = {
    'mm', 'cm', 'm', 'km', 'in', 'inch', 'inches', 'ft', 'yd', 'kg', 't', 'ton', 'tons',
    'lb', 'lbs', 'pdr', 'pound', 'pounder', 'cal', 'x', 'mph', 'kph', 'cmh', 'hp',
    'mg', 'g', 'l', 'ml', 'sec', 'min', 'hr', 'no', 'nos', 'mk', 'type', 'mod',
}

# 通用英文词：出现在译文列即为"该译而未译"（精准打击，避免误报）
EN_WORDS = {
    'not', 'used', 'open', 'general', 'class', 'early', 'late', 'field', 'heavy',
    'light', 'mobile', 'static', 'motor', 'motorised', 'motorized', 'mechanized',
    'mechanised', 'armored', 'armoured', 'infantry', 'cavalry', 'artillery', 'engineer',
    'signal', 'recon', 'reconnaissance', 'mountain', 'marine', 'militia', 'reserve',
    'battalion', 'company', 'platoon', 'regiment', 'brigade', 'division', 'corps',
    'army', 'group', 'force', 'forces', 'task', 'supply', 'transport', 'transportation',
    'bridging', 'bunker', 'airfield', 'beach', 'fort', 'fortress', 'railway', 'bridge',
    'canal', 'river', 'port', 'road', 'depot', 'hospital', 'prison', 'camp', 'nest',
    'line', 'frontier', 'border', 'north', 'south', 'east', 'west', 'northern',
    'southern', 'eastern', 'western', 'command', 'staff', 'headquarters', 'section',
    'garrison', 'pioneer', 'parachute', 'airborne', 'guards', 'front', 'sector',
    'position', 'defence', 'defense', 'attack', 'withdrawal', 'island', 'harbour',
    'harbor', 'valley', 'village', 'town', 'city', 'hill', 'wood', 'forest', 'ridge',
}

# 装备/技术缩写白名单（按口径保留原文）
TECH_ABBR = {
    'flak', 'pak', 'pzgren', 'gren', 'how', 'sub', 'mob', 'stat', 'hv', 'lt', 'med',
    'hy', 'auto', 'kfz', 'pkw', 'lkw', 'zug', 'sd', 'sf', 'ausf', 'kwk', 'stuk',
    'stuh', 'nebel', 'wurf', 'werfer', 'abt', 'btl', 'komp', 'battr', 'kol', 'schw',
    'grp', 'bat', 'port', 'pont', 'tac', 'strat', 'gpt', 'agrp', 'cie', 'esc', 'cha',
    'dcha', 'bda', 'bie', 'aty', 'rdiv', 'ccy', 'usa', 'brit', 'aust', 'wdd', 'sef',
    'rattt', 'rdp', 'rct', 'ir', 'ra', 'ar', 'hms', 'uss', 'kms',
}


def core_chars(s):
    """取译名中的实义汉字（去掉通用编制/结构字）。"""
    junk = set('第师团旅营连军群队部的与和之型号级次新旧前后第')
    return set(c for c in (s or '') if CJK.match(c)) - junk

# 编制缩写 → 期望中文（用于 D 类一致性统计）
ABBR_ZH = {
    'INF': '步兵', 'INF.': '步兵', 'PZ': '装甲', 'PZ.': '装甲', 'CAV': '骑兵',
    'ART': '炮兵', 'ARTY': '炮兵', 'ENG': '工兵', 'SIG': '通信', 'RECCE': '侦察',
    'RECO': '侦察', 'PARA': '伞兵', 'MTN': '山地', 'GEB': '山地', 'MECH': '机械化',
    'MOT': '摩托化', 'MOT.': '摩托化', 'RES': '预备役', 'GDE': '卫队',
}


def load_glossary():
    """与 glossary.py / check_glossary.py 保持一致：裸 TSV，split('\\t') 取位。
    （不能用 csv.DictReader —— 值以 '"' 开头时会被当成引号字段而错位。）"""
    out, head = [], None
    with io.open(GLOSS, encoding='utf-8-sig', newline='') as f:
        text = f.read().replace('\r\n', '\n')
    for ln in text.split('\n'):
        if not ln.strip():
            continue
        c = ln.split('\t')
        if head is None:
            head = c
            continue
        out.append({head[k]: (c[k] if k < len(c) else '') for k in range(len(head))})
    return out


def load_baseline():
    out = []
    with io.open(BASE, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r.get('en'):
                out.append(r)
    return out


def norm(s):
    return re.sub(r'[\s\.\-]', '', s or '').lower()


def seg_split(s):
    """按 / 与 - 拆段，保留空段以维持位置对应。"""
    return re.split(r'(?<=/)|(?=/)', s or '')


def audit(rows, base):
    issues = []

    def add(kind, sev, r, expected='', note=''):
        issues.append(dict(kind=kind, sev=sev, cat=r['cat'], scope=r['scope'],
                           en=r['en'], zh=r['zh'], expected=expected, note=note))

    locked = [r for r in rows if r['status'] == 'LOCKED' and CJK.search(r['zh'] or '')]

    # ---------- A 未译残留 ----------
    for r in locked:
        zh = r['zh']
        for m in re.finditer(r"(?<![A-Za-z])[A-Za-z][A-Za-z'\-\.]{1,}(?![A-Za-z])", zh):
            w = m.group(0)
            core = w.strip('.\'-').lower()
            if not core or any(ch in MOJI_CHARS for ch in w):
                continue
            if core in EN_WORDS:
                add('A未译残留', 'HIGH', r, note=w)
                break
            if len(core) > 6 and not core.isupper() and core not in TECH_ABBR:
                add('A未译残留', 'MID', r, note=w)
                break

    # ---------- B 内部不一致 ----------
    byen = collections.defaultdict(set)
    scope_of = collections.defaultdict(set)
    for r in locked:
        byen[(r['en'].strip(), r['cat'])].add(r['zh'].strip())
        scope_of[(r['en'].strip(), r['cat'])].add(r['scope'])
    for (en, cat), zhs in byen.items():
        if len(zhs) > 1:
            same = len(scope_of[(en, cat)]) == 1
            for z in sorted(zhs):
                r = next(x for x in locked if x['en'].strip() == en and x['zh'].strip() == z)
                add('B内部不一致', 'HIGH' if same else 'MID', r,
                    expected=' | '.join(sorted(zhs)),
                    note='同 efile 内不一致（必须统一）' if same else '跨 efile 表述差异')

    # ---------- C 编码乱码 ----------
    for r in rows:
        if CJK.search(r['en'] or ''):
            add('C乱码', 'HIGH', r, note='原文列 mojibake')
    for r in rows:
        if any(ch in (r['zh'] or '') for ch in MOJI_CHARS):
            add('C乱码', 'HIGH', r, note='译文列 mojibake')

    # ---------- D 编制用语不统一 ----------
    stance = collections.defaultdict(lambda: collections.Counter())
    for r in locked:
        if r['cat'] not in ('UNIT', 'PLACE'):
            continue
        en, zh = r['en'], r['zh']
        for m in re.finditer(r"(?<![A-Za-z])([A-Z][A-Za-z]{1,6})\.?(?![A-Za-z])", en):
            tok = m.group(1).upper()
            if tok not in ABBR_ZH:
                continue
            if tok == 'PZ':
                # `Pz IVH` / `Pz 38(t)` / `Pz II` 中的 Pz 是**型号前缀**，不是编制缩写
                tail = en[m.end():].lstrip()
                if tail[:1].isdigit() or tail[:1] in 'IVXLCDM':
                    continue
            exp = ABBR_ZH[tok]
            if exp in zh:
                stance[tok]['译'] += 1
            elif re.search(r'(?<![A-Za-z])' + re.escape(m.group(1)) + r'\.?(?![A-Za-z])', zh):
                stance[tok]['留'] += 1
    for tok, c in sorted(stance.items()):
        if c['译'] and c['留']:
            r = next(x for x in locked if re.search(r'(?<![A-Za-z])' + tok + r'\.?(?![A-Za-z])', x['en'] or '', re.I))
            add('D编制用语', 'MID', r, expected=ABBR_ZH[tok],
                note='%s 译%d次/留%d次' % (tok, c['译'], c['留']))

    # ---------- E 标点规范 ----------
    for r in locked:
        zh = r['zh']
        has_fw = bool(re.search(r'[（）]', zh))
        has_hw = bool(re.search(r'[()]', zh))
        if has_fw and has_hw:
            add('E标点规范', 'HIGH', r, note='全角/半角括号混用')
            continue
        lay = 'txt' if r['cat'] in ('PLACE', 'TEXT') else 'xscn'
        if lay == 'txt' and has_hw:
            add('E标点规范', 'LOW', r, note='.txt 层用半角括号')
        if lay == 'xscn' and has_fw:
            add('E标点规范', 'LOW', r, note='.xscn 层用全角括号')
        if re.search(r'[\u4e00-\u9fff] +[\u4e00-\u9fff]', zh):
            add('E标点规范', 'MID', r, note='汉字间多余空格')

    # ---------- F 权威偏离（限人名/地名：术语一致性另由 B/D 类覆盖） ----------
    for b in base:
        key, want, cat = b['en'], b['zh'], b['cat']
        if cat not in ('LEADER', 'PLACE'):
            continue
        pat = re.compile(r'(?<![A-Za-z])' + re.escape(key) + r'(?![A-Za-z])', re.I)
        rank = re.compile(r'\b(Gen|Col|Maj|Capt|Lt|Sgt|Cmdt|Cdt|QG|EM|Cmd)\b|\bGen\.|\bCol\.', re.I)
        for r in locked:
            if r['cat'] != cat or not pat.search(r['en']):
                continue
            if rank.search(r['en']):
                continue  # 含军衔/职务词 -> 是人名，不是该地名
            zh = r['zh']
            alts = [want] + [a for a in (b.get('alt') or '').split('|') if a]
            if any(a in zh or norm(a) == norm(zh) for a in alts):
                continue
            if any(core_chars(a) & core_chars(zh) for a in alts):
                continue  # 与期望译名有共同实义字 → 视为可接受的同义/近译
            add('F权威偏离', 'MID', r, expected=want, note='基准 %s' % cat)

    return issues


def main():
    rows = load_glossary()
    base = load_baseline()
    issues = audit(rows, base)

    order = ['A未译残留', 'C乱码', 'F权威偏离', 'B内部不一致', 'D编制用语', 'E标点规范']
    issues.sort(key=lambda x: (order.index(x['kind']) if x['kind'] in order else 9, x['cat'], x['en']))

    with io.open(OUT, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['kind', 'sev', 'cat', 'scope', 'en', 'zh', 'expected', 'note'],
                           delimiter='\t', quoting=csv.QUOTE_ALL)
        w.writeheader()
        for it in issues:
            w.writerow(it)

    print('库条目 %d | 基准 %d | 问题 %d' % (len(rows), len(base), len(issues)))
    print('-' * 62)
    c = collections.Counter(i['kind'] for i in issues)
    for k in order:
        if c[k]:
            print('  %-10s %4d' % (k, c[k]))
    print('-' * 62)
    for k in order:
        sub = [i for i in issues if i['kind'] == k]
        if not sub:
            continue
        print('\n### %s (%d) 样例:' % (k, len(sub)))
        for i in sub[:12]:
            print('   [%s] %-40s => %-26s %s' % (i['cat'], i['en'][:40], i['zh'][:26], i['note'][:34]))
    print('\n明细 -> %s' % OUT)


if __name__ == '__main__':
    main()
