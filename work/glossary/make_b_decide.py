# -*- coding: utf-8 -*-
"""把 B 类（同原文多译名）整理成**可裁定清单**：每组的候选、出现范围、建议取值、理由。
输出 glossary/glossary-b-class-decide.tsv
"""
import os, io, re, csv, collections, glob

ROOT = r'D:\DSH\军事游戏汉化'
GL = os.path.join(ROOT, 'glossary', 'standard-glossary.tsv')
REV = os.path.join(ROOT, 'glossary', 'glossary-authority-review.tsv')
BASE = os.path.join(ROOT, 'work', 'glossary', 'authority-baseline.tsv')
OUT = os.path.join(ROOT, 'glossary', 'glossary-b-class-decide.tsv')


def load(path):
    out, head = [], None
    with io.open(path, encoding='utf-8-sig', newline='') as f:
        text = f.read().replace('\r\n', '\n')
    for ln in text.split('\n'):
        if not ln.strip():
            continue
        c = ln.rstrip('\r').split('\t')
        if head is None:
            head = c
            continue
        out.append({head[k]: (c[k] if k < len(c) else '') for k in range(len(head))})
    return out


rows = load(GL)
with io.open(REV, encoding='utf-8-sig', newline='') as f:
    rev = [r for r in csv.DictReader(f, delimiter='\t') if (r.get('kind') or '') == 'B内部不一致']
base = {}
for b in load(BASE):
    if b.get('en'):
        base[b['en']] = b

# 权威基准按**姓氏**建键（Kluge / Manteuffel），而游戏里写的是 von Kluge / von Manteuffel
# ⇒ 必须先剥掉贵族介词再查，否则著名将领（冯·克鲁格、冯·曼陀菲尔…）一律漏过基准、
#   被普通投票改成少数派音译（实测会变成「冯·克卢格」「冯·曼托伊费尔」）。
PARTICLES = ('von ', 'van ', 'de la ', 'de ', 'del ', 'della ', 'di ', 'da ', 'le ')


def base_lookup(en, cat):
    cands = [en]
    low = en.lower()
    for p in PARTICLES:
        if low.startswith(p):
            cands.append(en[len(p):])
    for k in cands:
        b = base.get(k)
        if b and (b.get('cat') or '') == cat:
            return b
    return None

byen = collections.defaultdict(list)
for r in rows:
    if not re.search(r'[\u4e00-\u9fff]', r['zh'] or ''):
        continue
    byen[(r['en'].strip(), r['cat'])].append(r)

# 投票排除的 efile：EFILE_NASHORNPBEM 是本工程的 POC，其 TEXT-ZH 根文件取自 OPENPG
# （实测 names.txt 588 个同名里 560 个译文完全一致 = 95%）。把它计入「多数票」等于给
# OPENPG 重复计票，会让「一对一」对决伪造成 2:1 的"多数"，使真正的平票裁决规则失效。
VOTE_EXCLUDE = {'EFILE_NASHORNPBEM'}
REAL = [e for e in ('EFILE_OPENPG', 'EFILE_OLGWW2')]

# docs19 已确立：OLGWW2 的 .txt 场景名清单＝**规范本地化**（.xscn 早期误用罗马字音译，已统一回 .txt）。
# 故凡候选值出现在该清单中，即视为项目已确定的规范名，优先于平票取向。
# 反例代价实测：Viipuri 会由 维堡（jh3viip42.txt）退成 维普里、Georgetown 由 乔治市（rsmal01.txt）退成 乔治敦，
# 而 维普里/乔治敦 在 OLGWW2 全库 0 处出现。
GAME = r'D:\OpenPG2'


def build_norm():
    s = set()
    for p in glob.glob(os.path.join(GAME, 'EFILE_OLGWW2', 'SCENARIO', '*.txt')):
        try:
            txt = io.open(p, encoding='gbk', errors='replace', newline='').read()
        except Exception:
            continue
        for line in txt.replace('\r\n', '\n').split('\n'):
            for tok in line.split('/'):
                t = re.sub(r'\([^)]*\)', '', re.sub(r'\[[^\]]*\]', '', tok)).strip()
                if t:
                    s.add(t)
    return s


NORM = build_norm()

# 手工例外：**语义性错误**（不是风格选择），逐条给语源依据。仅此一条。
EXC = {
    ('Tienraivaaja', 'EQUIP'): ('道路工兵',
        '手工例外：芬兰语 tie=道路 / raivaaja=清障开路人 ⇒ 筑路清障兵；OPENPG 的「架桥工兵」把兵种弄错'),
}

def key_of(s):
    # 归一化：去「第」、去空格、去标点，取实义字集合大小
    return re.sub(r'[\s·・\-.,（）()]', '', s)

out = []
for (en, cat), items in sorted(byen.items()):
    zhs = collections.Counter(i['zh'].strip() for i in items)
    if len(zhs) < 2:
        continue
    zhv = collections.Counter(i['zh'].strip() for i in items if i['scope'] not in VOTE_EXCLUDE)
    if not zhv:
        continue
    # 分布（按 efile；属 POC 的来源标 *，仅供显示，不参与投票）
    dist = collections.defaultdict(set)
    for i in items:
        dist[i['zh'].strip()].add(i['scope'])
    dstr = '; '.join('%s:%d%s' % (z, n, '[' + ','.join(sorted(s[6:] + ('*' if s in VOTE_EXCLUDE else '')
                                                                  for s in dist[z])) + ']')
                     for z, n in zhs.most_common())
    # 建议
    rec, why = '', ''
    if len(zhv) == 1:
        rec = next(iter(zhv))
        why = '剔除 POC 重复票后唯一译法'
    b = base_lookup(en, cat)
    if not rec and b:
        want = b['zh']
        alts = [want] + [a for a in (b.get('alt') or '').split('|') if a]
        for a in alts:
            for z in zhv:
                if z == a or a in z:
                    rec, why = z, '权威基准「%s」' % want
                    break
            if rec:
                break
    if not rec:
        def score(z):
            vef = dist[z] - VOTE_EXCLUDE
            # 平票时以 OPENPG 为准（用户裁定）：实测其内部一致性最高
            #（同文件内多译法 3/969 = 0.3%，OLGWW2 54/1776 = 3.0%），且为 OpenGen 官方默认 efile。
            pref = 0 if 'EFILE_OPENPG' in vef else (1 if 'EFILE_OLGWW2' in vef else 2)
            # 注意 max() 逐元素**升序**比较 ⇒ 位次越靠前、数值越大者胜。
            # 规范清单优惠**只给 OLGWW2 那一侧**：因为 .txt 清单是 OLGWW2 的，别处候选撞上清单里
            # 无关词条（如 Lake→湖 撞上某个含「湖」的名字）属误命中，不能算数。
            norm_bonus = 1 if ('EFILE_OLGWW2' in vef and z in NORM) else 0
            return (zhv[z], norm_bonus, -pref, len(z))
        rec = max(zhv, key=score)
        why = ('项目规范名清单优先（docs19）'
               if (rec in NORM and 'EFILE_OLGWW2' in (dist[rec] - VOTE_EXCLUDE))
               else '库内多数（%d/%d，OPENPG 优先）' % (zhv[rec], sum(zhv.values())))
    if (en, cat) in EXC:
        rec, why = EXC[(en, cat)]
    out.append((cat, en, len(zhs), dstr, rec, why))

with io.open(OUT, 'w', encoding='utf-8-sig', newline='\r\n') as f:
    f.write('cat\ten\tvariants\t分布(译名:次数[efile])\t建议\t理由\n')
    for c, en, n, d, r, w in out:
        f.write('%s\t%s\t%d\t%s\t%s\t%s\n' % (c, en, n, d, r, w))

print('B 类组数 %d -> %s' % (len(out), OUT))
print('投票源: %s（* 标记的 efile 为 POC 派生，只作对齐目标、不参与投票）' % ' + '.join(REAL))
print('规则栈: 权威基准 > OLGWW2 规范名清单（%d token，docs19） > 平票取向 OPENPG > 手工例外 %d 条'
      % (len(NORM), len(EXC)))
print('按类别:', dict(collections.Counter(o[0] for o in out)))
print('按候选数:', dict(collections.Counter(o[2] for o in out)))
print('建议依据:', dict(collections.Counter(o[5].split('（')[0] for o in out)))
print()
for o in out[:30]:
    print('  [%-6s] %-28s %d 种 -> 建议 %-12s (%s)' % (o[0], o[1][:28], o[2], o[4][:12], o[5][:22]))
