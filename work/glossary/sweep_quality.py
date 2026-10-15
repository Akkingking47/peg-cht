# -*- coding: utf-8 -*-
"""梳理：用「新规则」体检现有译文（视角混用 / 标点 / 空格 / 槽位）"""
import io, os, re, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
G = r'D:\Program Files\PeG-WW2'
CJK = re.compile(r'[\u4e00-\u9fff]')
# 视角标记（来自视角判定三层）
MARK = {
    '苏': ['将军同志', '同志', '红军'],
    '德': ['将军阁下', '阁下', '元首'],
    '盟': ['将军，', '长官', '指挥官，'],
}
WORLD = re.compile(r'[\u4e00-\u9fff][,;:!\?\(\)]|[,;:!\?\(\)][\u4e00-\u9fff]')
SPACE = re.compile(r'[\u4e00-\u9fff]  +[\u4e00-\u9fff]|\s+[\u4e00-\u9fff]\s*[，。！？；：]')
mix, punct, space = [], collections.Counter(), collections.Counter()
files = 0
for d in ('SCENARIO', 'USERSCEN'):
    p = os.path.join(G, d)
    if not os.path.isdir(p):
        continue
    for fn in os.listdir(p):
        if not fn.lower().endswith('.txt'):
            continue
        q = os.path.join(p, fn)
        try:
            t = io.open(q, encoding='gbk', errors='replace').read()
        except Exception:
            continue
        if not CJK.search(t):
            continue
        files += 1
        hit = {}
        for side, ms in MARK.items():
            n = sum(t.count(m) for m in ms)
            if n:
                hit[side] = n
        # 强标记（将军同志/将军阁下）互斥性
        strong = [s for s, ms in MARK.items() if any(t.count(m) for m in ms[:1])]
        if '苏' in strong and ('德' in strong or '盟' in strong):
            mix.append((fn, strong, hit))
        for m in WORLD.finditer(t):
            punct[m.group(0)] += 1
        for m in SPACE.finditer(t):
            space[m.group(0)[:12]] += 1
print('场景文本文件（含中文）: %d' % files)
print()
print('=== ① 同一文件内强视角标记混用（将军同志 vs 将军阁下）===')
print('   命中 %d 个文件' % len(mix))
for fn, s, hit in mix[:25]:
    print('   %-40s %s  %s' % (fn[:40], '+'.join(s), hit))
print()
print('=== ② 中文旁的半角标点（%d 处）===' % sum(punct.values()))
for k, v in punct.most_common(14):
    print('   %-8s %d' % (k, v))
print()
print('=== ③ 中文间多余空格（%d 处）===' % sum(space.values()))
for k, v in space.most_common(10):
    print('   %-16s %d' % (repr(k), v))
