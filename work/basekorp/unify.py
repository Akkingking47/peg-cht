# -*- coding: utf-8 -*-
"""BASEKORP `.xscn` 映射表 —— 跨批次一致化后处理。

修的是「同一英文成分在不同批次被译成不同中文」这类问题（跨批次一致性铁律），
以及确定性/LLM 两层混用产生的格式毛刺。全部为**幂等**的字符串级修正。

用法：python unify.py           # 默认干跑，打印改动数
      python unify.py --apply   # 写回 bk-xscn-map.tsv
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAP = os.path.join(HERE, 'bk-xscn-map.tsv')

ROMV = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
ROMRE = re.compile(r'M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})')


def rom2int(s):
    t = 0
    for i, c in enumerate(s):
        v = ROMV[c]
        t += -v if i + 1 < len(s) and v < ROMV[s[i + 1]] else v
    return t


ROMTOK = re.compile(r'\b[IVXLCDM]{1,7}\b')


def sub_rom(text):
    """只把「完整且合法」的罗马数字 token 换成 第N。
    ⚠️ 直接对整串跑 ROMRE 会匹配空串（D 在 "Diego" 里被当 500），必须先按 token 切。"""
    return ROMTOK.sub(lambda x: ('第%d' % rom2int(x.group(0)))
                      if ROMRE.fullmatch(x.group(0)) else x.group(0), text)


def int2rom(n):
    if not (0 < n < 4000):
        return None
    vals = ((1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),
            (50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I'))
    out = ''
    for v, ch in vals:
        while n >= v:
            out += ch; n -= v
    return out


def fix_bracket(m):
    """括号内按既有先例**保留罗马番号**：把「第N」还原成罗马数字。"""
    inner = re.sub(r'第(\d+)',
                   lambda x: int2rom(int(x.group(1))) or x.group(0), m.group(1))
    return '%s%s%s' % (m.group(0)[0], inner, m.group(0)[-1])


# 尾部「汉字+第N」（第N 后面可能还挂着未闭合的绰号串，如 `'Kappa`）
TAILNUM = re.compile(r"([一-鿿]+(?:-[一-鿿]+)*)第(\d+)(\s*'[^']*)?$")

# 编制词尾：只有以它结尾的汉字串才允许被「第N」前置
TYPE_END = re.compile(r'(?:高射炮团|战斗机群|轰炸机群|驱逐机联队|战斗机联队|轰炸机大队'
                      r'|摩托化师|装甲师|步兵师|空降旅|山地师|骑兵师|坦克师|近卫师'
                      r'|方面军|集团军|航空队|装甲旅|步兵旅|炮兵团|步兵团|装甲团'
                      r'|掷弹兵团|工兵营|机枪营|侦察营|反坦克营|支队|分队|纵队'
                      r'|中队|大队|联队|农庄|炮兵|骑兵|步兵|工兵|坦克|装甲'
                      r'|师|团|旅|军|营|连|群|队)$')

# 国名 / 军种名：不是编制词，禁止移动（否则 `法国第42` 会被毁成 `第42法国`）
NONTYPE = {'法国', '英国', '德国', '苏联', '美国', '意大利', '日本', '波兰', '罗马尼亚',
           '匈牙利', '芬兰', '南非', '加拿大', '澳大利亚', '新西兰', '印度', '中国',
           '挪威', '荷兰', '比利时', '希腊', '南斯拉夫', '保加利亚', '奥地利', '西班牙',
           '瑞典', '瑞士', '丹麦', '空军', '海军', '陆军', '近卫', '党卫军', '皇家空军'}


def fix_tailnum(m):
    """尾部「汉字+第N」归位。

    先例（20,606 条已交付译文）中该形态 **0 例**，且一律第N前置
    （`Grenadier-Regiment 1057` -> `第1057掷弹兵团`、`JG 27/ L 2` -> `第27战斗机联队`）。

    护栏：汉字串必须以编制词结尾、且不能是纯国名/军种名 —— 否则不动
    （`法国第42 'Weydehr` 保持原样，不能变成 `第42法国`）。

    分两支：
      A 前面没有紧邻「第M」—— N 是番号 => 前置：`高射炮团第4` -> `第4高射炮团`
      B 前面已有「第M」—— N 是计数器序号，不是番号 => 去掉「第」：
        `第6近卫师第87` -> `第6近卫师 87`
        （实证：ssbdm_25.xscn 中 `6th Guards dv` 有 27 个离散尾号 7..87，
          而 `6th Guards Kav` 仅 1..4 —— 尾号是同族计数器的流水号）
    """
    run, num, tail = m.group(1), m.group(2), m.group(3) or ''
    if run in NONTYPE or not TYPE_END.search(run):
        return m.group(0)
    # ⚠️ re.sub 只替换 group(0)；返回值里不能再带前缀，否则前缀被复制一遍
    pre = m.string[:m.start(1)]
    if re.search(r'第\d+$', pre):          # B：已是「第M…」，尾部为序号
        return '%s %s%s' % (run, num, tail)
    return '第%s%s%s' % (num, run, tail)   # A：番号前置


def _idempotent_guard():
    """自检：规则 10 必须 (1) 幂等 (2) 不吞前缀 (3) 不动国名。"""
    cases = {
        '高射炮团第4': '第4高射炮团',
        '第6近卫师第87': '第6近卫师 87',
        '第1/高射炮-团第49': '第1/第49高射炮-团',
        '第7印度坦克第30': '第7印度坦克 30',
        '南非空军战斗机群第20': '第20南非空军战斗机群',
        '党卫军第11军': '党卫军第11军',
        "党卫军/BdM 战斗机联队第43 'Sarrenna": "党卫军/BdM 第43战斗机联队 'Sarrenna",
        "法国第42 'Weydehr": "法国第42 'Weydehr",        # 国名：不动
        "空军第1 'Goerings 大队": "空军第1 'Goerings 大队",  # 军种名：不动
    }
    for src, want in cases.items():
        a = re.sub(TAILNUM.pattern, fix_tailnum, src)
        assert a == want, (src, a, want)
        assert re.sub(TAILNUM.pattern, fix_tailnum, a) == a, ('非幂等', src)


def fix_hill(m):
    """`Hill 195` -> `195高地`（先例 `Pt 187` -> `187高地`：裸编号在前）。"""
    return '%s高地%s' % (m.group(1), m.group(2) or '')


def fix_post(m):
    """`Post 31` -> `第31哨所`。"""
    return '第%s哨所%s' % (m.group(1), m.group(2) or '')


def fix_serial(m):
    """规则 10 没接住的「汉字+第N」：汉字串非编制词 => N 是流水号，去「第」留裸号。"""
    run, num, tail = m.group(1), m.group(2), m.group(3) or ''
    if run in NONTYPE:                      # 国名/军种名绝不动
        return m.group(0)
    return '%s %s%s' % (run, num, tail)


# (正则, 替换, 说明)
RULES = [
    # 1. 方括号 / 圆括号内罗马数字 -> 第N（与既有 efile 先例一致）
    (r'\[([IVXLCDM]{1,7}[^\]]*)\]', fix_bracket, '括号内罗马数字规范化'),
    (r'\(([IVXLCDM]{1,7}[^)]*)\)', fix_bracket, '圆括号内罗马数字规范化'),

    # 2. BdM 是不明场景标记，不该译成「德国少女联盟」
    (r'德国少女联盟', 'BdM', 'BdM 还原为标记'),
    (r'(?<!德国)少女联盟', 'BdM', 'BdM 还原为标记'),

    # 3. Elms = Elements（…的一部），不是「榆树」
    (r'榆树', '分队', 'Elms 改译“分队”'),

    # 4. 单字母 C 被当罗马数字 100
    (r'第100(?=[/（(\s]|$)', '连', '单字母 C 还原为“连”'),

    # 5. Arm K / SS Korps 双重军级词
    (r'第(\d+)集团军军', r'第\1军', 'Armee-Korps 去重'),
    (r'第(\d+)党卫军军', r'党卫军第\1军', 'SS-Korps 语序'),
    (r'党卫军军', '党卫军军', '占位'),

    # 6. FAF 统一为法国空军
    (r'(?<![一-鿿/A-Za-z])FAF(?![a-z])', '法国空军', 'FAF 统一'),

    # 7. 德式「第2.」去掉多余句点
    (r'第(\d+)\.(?![^\s/]*[一-鿿])', r'第\1', '去掉“第N.”句点'),

    # 8. 「第N 中文」不留空格（层级拼接）
    (r'第(\d+)\s+(?=[一-鿿])', r'第\1', '去掉第N后空格'),

    # 9. 连写装甲群/战斗群等时去掉多余空格
    (r'\s{2,}', ' ', '合并多空格'),

    # 10. 尾部「汉字+第N」：第N 必须前置（先例 20,606 条中 0 例后置）
    #     10a 番号：X第N -> 第NX      （JG 27 -> 第27战斗机联队）
    #     10b 序号：第M…X第N -> 第M…X N（6th Guards dv 87 的 87 是计数器序号，非番号）
    (TAILNUM.pattern, fix_tailnum, '尾部第N归位'),

    # 11. 规则 10 放行后的残留：地图要素按先例（Pt 187 -> 187高地）裸编号前置
    (r"高地第(\d+)(\s*'[^']*)?$", fix_hill, '高地编号前置'),
    (r"哨所第(\d+)(\s*'[^']*)?$", fix_post, '哨所编号前置'),

    # 12. 其余残留：汉字串不是编制词 => 尾号是流水号，去掉「第」留裸号
    #     （`44th Army AT/m 26` -> `第44集团军反坦克/迫击炮 26`）
    (TAILNUM.pattern, fix_serial, '尾部流水号去第'),
]


def apply_one(dst):
    n = 0
    for pat, rep, _ in RULES:
        new = re.sub(pat, rep, dst)
        if new != dst:
            n += 1
        dst = new
    return dst.strip(), n


def main():
    do = '--apply' in sys.argv
    rows = [l.rstrip('\n').split('\t') for l in io.open(MAP, encoding='utf-8-sig')][1:]
    changed = 0
    out = []
    samples = []
    for s, d, note in rows:
        nd, n = apply_one(d)
        if nd != d:
            changed += 1
            if len(samples) < 12:
                samples.append((s, d, nd))
        out.append((s, nd, note))
    print('映射 %d 条，改 %d 条' % (len(out), changed))
    for s, a, b in samples:
        print('  %-36s %-40s -> %s' % (s[:36], a[:40], b[:40]))
    if do:
        with io.open(MAP, 'w', encoding='utf-8-sig', newline='') as f:
            f.write('src\tdst\tnote\r\n')
            for s, d, n in out:
                f.write('%s\t%s\t%s\r\n' % (s, d, n))
        print('已写回 %s' % MAP)
    else:
        print('（干跑，未写入；加 --apply 落盘）')


if __name__ == '__main__':
    main()
