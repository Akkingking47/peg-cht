# -*- coding: utf-8 -*-
"""OLGWW2 .xscn 组1 番号串「N Arm / N Inf / N Cav」——**只修同文件内自相矛盾**的。

依据（用户裁定）：纯「数字+兵种缩写」位于父位时是**师级**，判据
`4 RTR/4 Bde/7 Arm/[XIII]`（4皇家坦克团/第4旅/第7装甲师/第13军）—— 番号串顺序是
`本单位/上级/再上级`，故 `N Arm` = 装甲师、`N Inf` = 步兵师。
但**不做全局加「师」**：只在该文件自己出现两种写法（如 `第7装甲` 与 `第7装甲师` 并存）时才统一，
以免把跨场景可能指不同部队的写法一并改掉。

原始语言硬桥：与 backup\\ORIGINAL-EFILE_OLGWW2\\SCENARIO 同 (gi,idx) 对齐，逐 '/' 段比对。

用法： python fix_arm_inf.py            # dry-run
       python fix_arm_inf.py --apply    # 写盘（备份 backup/olgww2-arminf-before/）
"""
import os, sys, glob, re, shutil, collections

sys.path.insert(0, r'D:\DSH\军事游戏汉化\work\efile-nashornpbem')
from apply_residual import parse

OR = r'D:\DSH\军事游戏汉化\backup\ORIGINAL-EFILE_OLGWW2\SCENARIO'
NN = r'D:\OpenPG2\EFILE_OLGWW2\SCENARIO'
BK = r'D:\DSH\军事游戏汉化\backup\olgww2-arminf-before'

ARM = re.compile(r'^(\d+)\s*Arm\s*\.?$', re.I)
INF = re.compile(r'^(\d+)\s*Inf\s*\.?$', re.I)
CAV = re.compile(r'^(\d+)\s*Cav\s*\.?$', re.I)


def desired(o_seg):
    m = ARM.match(o_seg)
    if m:
        return '第%s装甲师' % m.group(1)
    m = INF.match(o_seg)
    if m:
        return '第%s步兵师' % m.group(1)
    m = CAV.match(o_seg)
    if m:
        return '第%s骑兵' % m.group(1)
    return None


def load(pairs):
    """返回 [(fn, key, o_seg, zh_seg, off, oldlen_wo_len)]，只保留段数齐的条目。"""
    out = []
    for po in sorted(glob.glob(os.path.join(OR, '*.xscn'))):
        fn = os.path.basename(po)
        pn = os.path.join(NN, fn)
        if not os.path.exists(pn):
            continue
        do, io_, _ = parse(po)
        dn, inn, _ = parse(pn)
        om = {(g, i): (o, l) for g, i, o, l in io_}
        nm = {(g, i): (o, l) for g, i, o, l in inn}
        for key in sorted(set(om) & set(nm)):
            if key[0] < 1:
                # 组0 是**镜像 .txt 名字清单**的地名/单位项（docs19 已定 .txt 为规范本地化）
                # ⇒ 不能按 g1 的番号规则改，否则立刻造出 .xscn↔.txt 不一致（实测 DAK5 g0#5）。
                continue
            oo, ol = om[key]
            no, nl = nm[key]
            so = do[oo + 2:oo + 2 + ol].decode('cp1252', 'replace')
            sn = dn[no + 2:no + 2 + nl].decode('gbk', 'replace')
            ao, an = so.split('/'), sn.split('/')
            if len(ao) != len(an):
                continue
            for k, (a, b) in enumerate(zip(ao, an)):
                if desired(a.strip()) is not None:
                    out.append((fn, key, k, a.strip(), b.strip(), so, sn, no, nl))
    return out


def kind_of(seg):
    for tag, rx in (('ARM', ARM), ('INF', INF), ('CAV', CAV)):
        m = rx.match(seg)
        if m:
            return (m.group(1), tag)
    return None


recs = load(None)
# 第一遍：找同文件内的矛盾键
byf = collections.defaultdict(lambda: collections.defaultdict(set))
for fn, key, k, a, b, so, sn, no, nl in recs:
    byf[fn][kind_of(a)].add(b)
bad = {fn: {kk for kk, v in d.items() if len(v) > 1} for fn, d in byf.items()}
bad = {fn: v for fn, v in bad.items() if v}

# 第二遍：对矛盾文件里**该键的全部段**统一定值。
# 注意同一条目可能有多段命中 ⇒ 必须按 (fn,key) 累积，否则多段会互相覆盖。
stats = collections.Counter()
samples = []
edit = collections.defaultdict(dict)          # (fn, key) -> {seg_index: want}
raw = {}
for fn, key, k, a, b, so, sn, no, nl in recs:
    if fn not in bad:
        continue
    kk = kind_of(a)
    if kk not in bad[fn]:
        continue
    want = desired(a)
    raw[(fn, key)] = (fn, key, no, nl, so, sn)
    if b == want:
        stats['已合规'] += 1
        continue
    edit[(fn, key)][k] = want
    stats['待改段'] += 1
    if len(samples) < 200:
        samples.append((fn, key[0], key[1], so, sn, want))

print('=== 同文件内矛盾的键 ===')
for fn in sorted(bad):
    print('  %-16s %s' % (fn, sorted(bad[fn])))
print('\n=== 待改明细（前 30 例）===')
for fn, g, i, so, sn, want in samples:
    print('   %-16s g%d#%-4d  %-34s | %-30s -> %s' % (fn, g, i, so, sn, want))

plan = collections.defaultdict(list)          # fn -> [(off, len, newbytes)]
for (fn, key), segs in edit.items():
    _, _, no, nl, so, sn = raw[(fn, key)]
    na = sn.split('/')
    if len(na) != len(so.split('/')):
        continue
    for k, want in segs.items():
        na[k] = want
    plan[fn].append((no, 2 + nl, '/'.join(na).encode('gbk')))

print('\n统计：', dict(stats), ' 涉及文件', len(plan), ' 涉及条目', len(edit),
      ' 替换段', sum(len(v) for v in edit.values()))

apply = '--apply' in sys.argv
if not apply:
    print('\n（dry-run，未写盘）')
    sys.exit()

os.makedirs(BK, exist_ok=True)
n = 0
for fn, lst in sorted(plan.items()):
    pn = os.path.join(NN, fn)
    dn = open(pn, 'rb').read()
    dst = os.path.join(BK, fn)
    if not os.path.exists(dst):
        shutil.copy2(pn, dst)
    buf = bytearray()
    last = 0
    for off, oldlen, nb in sorted(lst, key=lambda x: x[0]):
        buf += dn[last:off] + len(nb).to_bytes(2, 'little') + nb
        last = off + oldlen
    buf += dn[last:]
    tmp = pn + '.new'
    open(tmp, 'wb').write(bytes(buf))
    assert open(tmp, 'rb').read() == bytes(buf)
    os.replace(tmp, pn)
    n += 1
print('已写回 %d 文件，备份 %s' % (n, BK))
