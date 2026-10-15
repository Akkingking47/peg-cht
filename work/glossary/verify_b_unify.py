# -*- coding: utf-8 -*-
"""B 类统一的**重建复核**：拿 backup/olgww2-b-unify2-before 与现值逐行比对，
列出全部改动记录（去重），并扫描「落败变体是否仍以复合名形式残留」。

用法： C:\\Python314\\python.exe verify_b_unify.py
"""
import io, os, re, collections

ROOT = r'D:\DSH\军事游戏汉化'
GAME = r'D:\OpenPG2'
BK = os.path.join(ROOT, 'backup', 'olgww2-b-unify2-before')


def rd(p):
    return io.open(p, encoding='gbk', errors='replace', newline='').read().replace('\r\n', '\n').split('\n')


def locate(ef, rel):
    """备份名把路径分隔符换成了 '_'（而真实文件名本身也可能含 '_'，如 strings_efile.txt）
    ⇒ 不能反向 replace，只能正向枚举比对。"""
    root = os.path.join(GAME, ef)
    for dp, dn, fns in os.walk(root):
        for fn in fns:
            p = os.path.join(dp, fn)
            if os.path.relpath(p, root).replace('\\', '_') == rel:
                return p
    return None


pairs = collections.Counter()
bad = []
for b in sorted(os.listdir(BK)):
    m = re.match(r'^(EFILE_[A-Z0-9]+)__(.+)$', b)
    if not m:
        bad.append(('命名无法解析', b))
        continue
    ef, rel = m.group(1), m.group(2)
    cur = locate(ef, rel)
    if cur is None:
        bad.append(('定位失败', b))
        continue
    a, z = rd(os.path.join(BK, b)), rd(cur)
    for i in range(max(len(a), len(z))):
        x = a[i] if i < len(a) else ''
        y = z[i] if i < len(z) else ''
        if x != y:
            pairs[(ef, os.path.relpath(cur, GAME), x.strip(), y.strip())] += 1

print('备份文件 %d 个；定位/解析异常 %d 个' % (len(os.listdir(BK)), len(bad)))
for t in bad:
    print('   ', t)
print('改动记录（去重）%d 条：' % len(pairs))
for (ef, fn, x, y), n in sorted(pairs.items()):
    print('  %-16s %-26s %-26s -> %-20s x%d' % (ef[6:], fn, x[:26], y[:20], n))

# ---- 落败变体是否以复合名残留 ----
lose = {}
for (ef, fn, x, y), n in pairs.items():
    for part in re.split(r'[/|]', x):
        part = part.strip()
        if part and part != y and re.search(r'[\u4e00-\u9fff]', part):
            lose.setdefault(part, set()).add((ef, fn))
print('\n--- 落败变体全库残留扫描（含复合名/子串）---')
res = 0
for p in [os.path.join(GAME, e, fn) for e in ('EFILE_OPENPG', 'EFILE_OLGWW2', 'EFILE_NASHORNPBEM')
          for fn in ('TEXT-ZH\\equip.txt', 'TEXT-ZH\\names.txt', 'TEXT-ZH\\strings_efile.txt', 'TEXT-ZH\\nations.txt')]:
    if not os.path.exists(p):
        continue
    for i, line in enumerate(rd(p)):
        for v in lose:
            if v in line:
                res += 1
                print('  %-46s :%-5d %s   [旧值 %s]' % (os.path.relpath(p, GAME), i + 1, line.strip()[:40], v))
print('残留 %d 处' % res)
