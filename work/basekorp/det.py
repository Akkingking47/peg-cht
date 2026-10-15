# -*- coding: utf-8 -*-
"""BASEKORP `.xscn` 番号串 —— 确定性翻译引擎（不吃 LLM 的那一层）。

处理顺序：
  1. 保护 `[...]` 方括号标记（按 BRACKET 词典译；纯番号罗马/阿拉伯原样保留）
  2. 保护 `'Nickname` 引号昵称（单独走音译/译名）
  3. 罗马数字 -> 阿拉伯数字
  4. 序数 `236th` -> `第236`
  5. 数字 + 后缀型编制（`236D`）-> `第236师`
  6. 独立 token（`Rifle` / `Division` / `Pz`）-> 中文
  7. 段首纯数字 / 罗马 -> `第N`
  8. 剩余未译 ASCII 成分 -> 原样保留（交给 LLM 层）

产出：对每个唯一串给出 (zh, resid) —— resid = 仍未汉化的 ASCII 成分集合，
供统计与后续 LLM 分块使用。

用法：python det.py           # 跑全量，输出 _det-out.tsv + 覆盖率报告
      python det.py --peek N  # 抽看 N 条
"""
import io, os, re, sys, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
from tokdict import WORD, SUF, BRACKET

ROMV = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
ROMRE = re.compile(r'M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})')


def rom2int(s):
    t = 0
    for i, c in enumerate(s):
        v = ROMV[c]
        t += -v if i + 1 < len(s) and v < ROMV[s[i + 1]] else v
    return t


def is_roman(s):
    return bool(s) and ROMRE.fullmatch(s) is not None


HAN = re.compile(r'[一-鿿]')


def has_han(s):
    return HAN.search(s) is not None


# ---------------- 方括号 ----------------
def tr_bracket(inner):
    if inner in BRACKET:
        v = BRACKET[inner]
        return v if v else inner
    if is_roman(inner):
        return inner                      # 纯罗马番号：保留
    if re.fullmatch(r'\d+', inner):
        return inner                      # 纯数字：保留
    if re.fullmatch(r'\d+[A-Za-z\.]*', inner):
        return inner                      # 数字+后缀：保留（如 [51A] [6A]）
    parts = re.split(r'(\s+)', inner)
    out = []
    for p in parts:
        if p.strip() in BRACKET:
            out.append(BRACKET[p.strip()] or p)
        elif p.strip() in WORD:
            out.append(WORD[p.strip()])
        else:
            out.append(p)
    return ''.join(out)


BRACKET_RE = re.compile(r'\[([^\]]*)\]')


def protect_brackets(s):
    hold = []

    def rep(m):
        hold.append(m.group(0))
        return '\x01%s\x02' % chr(0xE000 + len(hold) - 1)
    return BRACKET_RE.sub(rep, s), hold


def restore_brackets(s, hold):
    def rep(m):
        i = ord(m.group(1)) - 0xE000
        return '[' + tr_bracket(hold[i][1:-1]) + ']'
    return re.sub('\x01([\ue000-\uf8ff])\x02', rep, s)


# ---------------- 引号昵称 ----------------
QUOT = re.compile(r"['’]([A-Za-z][A-Za-z0-9\-'’\.]*)")


def protect_quot(s):
    hold = []

    def rep(m):
        hold.append(m.group(1))
        return '\x03%s\x02' % chr(0xE000 + len(hold) - 1)
    return QUOT.sub(rep, s), hold


def restore_quot(s, hold):
    def rep(m):
        return "'" + hold[ord(m.group(1)) - 0xE000]
    return re.sub('\x03([\ue000-\uf8ff])\x02', rep, s)


# ---------------- 主翻译 ----------------
ORD = re.compile(r'\b(\d+)(th|st|nd|rd)\b(?!\s*[\u4e00-\u9fff])')
NUM_SUF = re.compile(r'(?<![\w])(\d+)([A-Za-z][A-Za-z\.]*)(?![\w])')


def _suf_zh(suf):
    return SUF.get(suf) or SUF.get(suf.rstrip('.')) or SUF.get(suf + '.')


def tr_segment(seg):
    """翻译一个 '/' 分段（不含括号）。返回 (文本, 未译成分集合)."""
    resid = set()
    s = seg.strip()
    if not s:
        return seg, resid
    if s == '-':
        return s, resid

    # 段首罗马数字
    m = re.fullmatch(r'([IVXLCDM]+)(?![A-Za-z0-9])(.*)', s)
    # ⚠️ 单字母段：只把 I/V/X 当罗马数字；C(连) D(师) M/L 是编制或标记，不能当 100/500/1000
    if m and len(m.group(1)) == 1 and m.group(1) not in ('I', 'V', 'X'):
        m = None
    if m and is_roman(m.group(1)):
        rest = m.group(2)
        if not rest:
            return '第%d' % rom2int(m.group(1)), resid
        r2, rs = tr_segment(rest)
        return '第%d%s' % (rom2int(m.group(1)), r2), rs

    # 纯数字段
    if re.fullmatch(r'\d+', s):
        return '第' + s, resid

    # 序数 236th
    def ordrep(m):
        return '第' + m.group(1)
    s2 = ORD.sub(ordrep, s)

    # 数字+后缀：236D / 82ABD
    def nsrep(m):
        num, suf = m.group(1), m.group(2)
        zh = _suf_zh(suf)
        if zh:
            return '第%s%s' % (num, zh)
        resid.add(suf)
        return '%s%s' % (num, suf)
    s2 = NUM_SUF.sub(nsrep, s2)

    # 独立 token
    def wrep(m):
        t = m.group(0)
        if t in WORD:
            return WORD[t]
        t2 = t.rstrip('.')
        if t2 in WORD:
            return WORD[t2]
        resid.add(t)
        return t
    s2 = re.sub(r"[A-Za-z\u0080-\u00ff][A-Za-z0-9\u0080-\u00ff\.']*", wrep, s2)

    # 段首裸数字（前面没加第的）
    def bare(m):
        j = m.start()
        pre = s2[max(0, j - 4):j]
        if re.search(r'(?:No\.?|N[oO]\.?|no\.?)$', pre):
            return m.group(0)
        if j > 0 and s2[j - 1] in '.,':
            return m.group(0)
        return '第' + m.group(1)
    s2 = re.sub(r'(?<!第)(?<![\w\u4e00-\u9fff])(\d+)(?![\w])', bare, s2)
    # 「第N 中文」之间不要空格
    # 段内「数字+中文」补「第」（数字后缀未被词典命中的情况）
    s2 = re.sub(r'(?<![\w\u4e00-\u9fff第])(\d+)(?=[\u4e00-\u9fff])',
                lambda m: '第' + m.group(1), s2)
    s2 = re.sub(r'(第\d+)\s+(?=[\u4e00-\u9fff])', r'\1', s2)
    s2 = re.sub(r'\s*([\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', r'\1', s2)
    s2 = re.sub(r'\s{2,}', ' ', s2).strip()
    return s2, resid


def translate(s):
    """整串翻译。返回 (zh, resid_set)。"""
    s2, bh = protect_brackets(s)
    s2, qh = protect_quot(s2)
    resid = set()
    # 按 '/' 分段（保留分隔符与空段）
    parts = s2.split('/')
    outs = []
    for p in parts:
        if not p.strip():
            outs.append(p)
            continue
        # 段内可能带空格连接的多个词，也可能带 (...)
        def paren_rep(m):
            inner, rs = tr_segment(m.group(1))
            resid.update(rs)
            return '(' + inner + ')'
        pi = re.sub(r'\(([^)]*)\)', paren_rep, p)
        t, rs = tr_segment(pi)
        resid |= rs
        outs.append(t)
    out = '/'.join(outs)
    out = restore_quot(out, qh)
    out = restore_brackets(out, bh)
    return out, resid


def main():
    rows = [l.rstrip('\n').split('\t') for l in
            io.open(os.path.join(HERE, '_xscn-todo.tsv'), encoding='utf-8')][1:]
    srcs = [(r[0], int(r[1]), r[2]) for r in rows]
    out = []
    residc = collections.Counter()
    full = 0
    totfreq = sum(f for _, f, _ in srcs)
    fullfreq = 0
    for s, f, ex in srcs:
        zh, rs = translate(s)
        out.append((s, zh, f, ex, rs))
        for r in rs:
            residc[r] += f
        clean = not any(c.isalpha() and ord(c) < 128 for c in
                        re.sub(r'\[[^\]]*\]', '', zh))
        if clean:
            full += 1
            fullfreq += f
    print('唯一 %d  实例 %d' % (len(srcs), totfreq))
    print('确定性层「无残留 ASCII 词」：唯一 %d (%.1f%%)  实例 %d (%.1f%%)'
          % (full, 100.0 * full / len(srcs), fullfreq, 100.0 * fullfreq / totfreq))
    print()
    print('=== 残留未译 token TOP 60（按实例）===')
    for k, v in residc.most_common(60):
        print('  %7d  %s' % (v, k))
    with io.open(os.path.join(HERE, '_det-out.tsv'), 'w', encoding='utf-8', newline='') as fo:
        fo.write('src\tzh\tfreq\texample\tresid\r\n')
        for s, zh, f, ex, rs in out:
            fo.write('%s\t%s\t%d\t%s\t%s\r\n' % (s, zh, f, ex, ' '.join(sorted(rs))))
    with io.open(os.path.join(HERE, '_det-resid.tsv'), 'w', encoding='utf-8', newline='') as fo:
        fo.write('token\tfreq\r\n')
        for k, v in residc.most_common():
            fo.write('%s\t%d\r\n' % (k, v))
    print('\n-> _det-out.tsv / _det-resid.tsv')


def peek(n):
    rows = [l.rstrip('\n').split('\t') for l in
            io.open(os.path.join(HERE, '_det-out.tsv'), encoding='utf-8')][1:]
    for r in rows[:int(n)]:
        print('%-42s -> %-42s  %s' % (r[0][:42], r[1][:42], r[4]))


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--peek':
        peek(sys.argv[2])
    else:
        main()
