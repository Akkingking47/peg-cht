# -*- coding: utf-8 -*-
"""原文侧编码自动识别与还原。

背景（本轮新发现）：部分 efile 的原文文件**不是纯 cp1252**，而是：
  · 有的是 UTF-8（`BarrÃ³n` 实际是 `Barrón` 的 C3 B3 被按 cp1252 读）
  · 有的同一文件内**混用** cp1252 单字节 与 UTF-8 多字节
因此必须**逐行**判编码，不能整文件一刀切。

判据：某行按 UTF-8 能解码成功、且解码后不再含 `Ã`/`Â` 这类 mojibake 前导符，
      则该行原字节是 UTF-8；否则按 cp1252 单字节解。

输出：还原后的原文串 + ASCII 折写 + 语种，供后续汉化。
只读，不写游戏文件。
"""
import os, io, glob, collections, unicodedata

GAME = r'D:\OpenPG2'
ROOT = r'D:\DSH\军事游戏汉化'
BK = os.path.join(ROOT, 'backup')
DONE = {'EFILE_OLGWW2', 'EFILE_OPENPG', 'EFILE_NASHORNPBEM'}
OUT = os.path.join(ROOT, 'work', 'glossary', 'out-orig-restored.txt')

MANUAL = {'ß': 'ss', 'ø': 'o', 'Ø': 'O', 'æ': 'ae', 'Æ': 'AE', 'œ': 'oe', 'Œ': 'OE',
          'ł': 'l', 'Ł': 'L', 'đ': 'd', 'Đ': 'D', 'ð': 'd', 'Ð': 'D',
          'þ': 'th', 'Þ': 'Th', 'ı': 'i', 'µ': 'u'}
# mojibake 前导符（UTF-8 首字节 C2/C3/C5 等被 cp1252 读出后的样子）
MOJI = set('ÃÂÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞ')
LANGS = [('德', set('äöüÄÖÜß')), ('法', set('éèêëàâçîïôûùœæÉÈÊÀÂÇÎÏÔÛÙ')),
         ('意', set('àèéìòù')), ('西', set('áéíóúñüÁÉÍÓÚÑ¿¡')),
         ('葡', set('ãõçâêôàÃÕÇ')), ('北欧', set('åøæÅØÆöä')),
         ('波兰', set('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ')), ('捷克', set('čšžřěůýáíéČŠŽŘĚŮÝ'))]


def fold(s):
    o = []
    for ch in s:
        if ch in MANUAL:
            o.append(MANUAL[ch]); continue
        d = ''.join(c for c in unicodedata.normalize('NFKD', ch) if not unicodedata.combining(c))
        o.append(d if d else ch)
    return ''.join(o)


def lang_of(s):
    return '+'.join(n for n, cs in LANGS if any(c in cs for c in s)) or '?'


def dec_line(raw):
    """逐行判编码，返回 (text, how)。how: utf8 / cp1252 / latin1。"""
    if not any(x >= 0x80 for x in raw):
        return raw.decode('ascii', 'replace'), 'ascii'
    try:
        t = raw.decode('utf-8')
        # UTF-8 成功且不再残留 mojibake 前导符 ⇒ 采信
        if not any(c in MOJI for c in t):
            return t, 'utf8'
    except Exception:
        pass
    try:
        return raw.decode('cp1252'), 'cp1252'
    except Exception:
        return raw.decode('latin-1'), 'latin1'


def files_for(ef):
    base = os.path.join(BK, 'ORIGINAL-' + ef) if ef in DONE else os.path.join(GAME, ef)
    if not os.path.isdir(base):
        return []
    out = [(r, os.path.join(base, r)) for r in
           ('equip.txt', 'names.txt', 'nations.txt', 'strings_efile.txt')]
    out += [('SCENARIO/' + os.path.basename(p), p)
            for p in glob.glob(os.path.join(base, 'SCENARIO', '*.txt'))]
    return [(r, p) for r, p in out if os.path.exists(p)]


def is_ruler(line):
    s = line.strip()
    return len(s) >= 4 and len(set(s)) <= 2 and all(ord(c) > 127 or c in ' \t-_=*' for c in s)


rows = []
encstat = collections.Counter()
fstat = collections.Counter()
wordmap = collections.defaultdict(set)      # 还原串 -> 位置集合

for ef in sorted(os.listdir(GAME)):
    if not ef.startswith('EFILE_'):
        continue
    for rel, p in files_for(ef):
        b = open(p, 'rb').read()
        # 整文件编码画像
        full = []
        for i, raw in enumerate(b.replace(b'\r\n', b'\n').split(b'\n')):
            t, how = dec_line(raw)
            if not any(ord(c) > 127 for c in t):
                continue
            if is_ruler(t):
                continue
            encstat[how] += 1
            fstat[(ef, rel, how)] += 1
            rows.append((ef, rel, i + 1, t.strip(), fold(t.strip()), lang_of(t), how))
            wordmap[t.strip()].add((ef, rel, i + 1))

with io.open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    f.write('# 原文侧编码还原\n')
    f.write('# 命中行 %d；按行编码判定: %s\n' % (len(rows), dict(encstat)))
    f.write('# 唯一串 %d\n' % len(wordmap))
    f.write('\n## 一、文件编码画像（非 ASCII 行数）\n')
    for (ef, rel, how), n in sorted(fstat.items()):
        f.write('  %-22s %-30s %-7s %d\n' % (ef, rel, how, n))
    f.write('\n## 二、唯一串清单（按语种分组）\n')
    bylang = collections.defaultdict(list)
    for w in wordmap:
        bylang[lang_of(w)].append(w)
    for lg in sorted(bylang):
        f.write('\n### 语种 [%s]  %d 串\n' % (lg, len(bylang[lg])))
        for w in sorted(bylang[lg]):
            locs = sorted(wordmap[w])
            f.write('  %-46s | %-40s | %s\n' % (w, fold(w), '%s %s L%d' % (locs[0][0][6:], locs[0][1], locs[0][2])))
    f.write('\n## 三、逐行明细\n')
    cur = None
    for ef, rel, ln, txt, fl, lg, how in rows:
        if (ef, rel) != cur:
            cur = (ef, rel)
            f.write('\n### %s / %s\n' % (ef, rel))
        f.write('  L%-5d [%-6s][%s] %s\n' % (ln, how, lg, txt))

print('命中 %d 行，唯一串 %d' % (len(rows), len(wordmap)))
print('按行编码:', dict(encstat))
print('->', OUT)
