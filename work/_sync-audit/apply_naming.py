# -*- coding: utf-8 -*-
"""「定名补进词库」执行器：把 95 条残留专名的中文定名写回**真源**。

规则表：work/_sync-audit/naming.tsv（残留英文 · old · new · 依据）
目标集：work/_sync-audit/residual-names-todo.tsv（en · 残留英文 · …）
出现表：glossary/glossary-occ.tsv（en zh cat scope src loc）

改写对象（只有这三类）：
  · .txt  → <efile>/SCENARIO/ + <efile>/TEXT-ZH/SCENARIO/（两层恒等，都改）
  · .xscn → <efile>/SCENARIO/<fn>（字节级定点，长度字段同步）
  · work/efile-nashornpbem/olgww2-glossary.tsv（PRI 0 真源）的 dst 列

规则按 old 长度倒序套用（先长后短，避免 N.Auckland 被 Auckland 抢先）。
默认 dry-run，--apply 才写盘；写前备份到 backup/before-naming/，写 .new 后回读校验再替换。

用法： python apply_naming.py [--apply]
"""
import os, io, re, sys, shutil, collections

sys.path.insert(0, os.path.join(r'D:\DSH\军事游戏汉化\work', 'efile-nashornpbem'))
from apply_residual import parse

GAME = r'D:\OpenPG2'
ROOT = r'D:\DSH\军事游戏汉化'
TODO = os.path.join(ROOT, 'work', '_sync-audit', 'residual-names-todo.tsv')
NAMING = os.path.join(ROOT, 'work', '_sync-audit', 'naming.tsv')
OCC = os.path.join(ROOT, 'glossary', 'glossary-occ.tsv')
TRUTH = os.path.join(ROOT, 'work', 'efile-nashornpbem', 'olgww2-glossary.tsv')
BK = os.path.join(ROOT, 'backup', 'before-naming')
EFILES = ['EFILE_OLGWW2', 'EFILE_OPENPG', 'EFILE_NASHORNPBEM']


def load(path):
    out, head = [], None
    with io.open(path, encoding='utf-8-sig', newline='') as f:
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


def apply_rules(value, rules):
    """按规则表依次做子串替换，返回 (新值, [(old,new), …])。"""
    hits = []
    for old, new in rules:
        if old and old in value:
            value = value.replace(old, new)
            hits.append((old, new))
    return value, hits


def main():
    apply = '--apply' in sys.argv

    rules_by_key = collections.defaultdict(list)
    for d in load(NAMING):
        rules_by_key[d['残留英文'].strip()].append((d['old'], d['new'], d['依据']))
    for k in rules_by_key:
        rules_by_key[k].sort(key=lambda x: -len(x[0]))
    print('规则键 %d 个 · 规则行 %d 条' % (len(rules_by_key), sum(len(v) for v in rules_by_key.values())))

    keys_by_en = collections.defaultdict(set)
    for d in load(TODO):
        keys_by_en[d['en'].strip()].add(d['残留英文'].strip())
    print('目标原文 %d 条' % len(keys_by_en))

    txt_changes = collections.defaultdict(list)      # (efile, fn) -> [(line, old, new)]
    xscn_changes = collections.defaultdict(list)     # (efile, fn) -> [(g, k, old, new)]
    truth_changes = collections.defaultdict(list)    # en -> [(old, new)]
    skip = collections.Counter()
    n_chg = 0
    for r in load(OCC):
        en = r['en'].strip()
        if en not in keys_by_en:
            continue
        rules = []
        for k in sorted(keys_by_en[en]):
            rules += [(o, n) for o, n, _ in rules_by_key.get(k, [])]
        cur = r['zh']
        if not cur:
            continue
        new, hits = apply_rules(cur, rules)
        if not hits or new == cur:
            continue
        scope, src, loc = r['scope'], r['src'], r['loc']
        if src == 'glossary':
            truth_changes[en] += hits
            n_chg += 1
            continue
        if scope not in EFILES:
            skip['非目标范围'] += 1
            continue
        if src == 'xscn':
            m = re.match(r'SCENARIO/(.+):g(\d+)#(\d+)$', loc)
            if m:
                xscn_changes[(scope, m.group(1))].append((int(m.group(2)), int(m.group(3)), cur, new))
            elif re.match(r'SCENARIO/(.+):title$', loc):
                xscn_changes[(scope, re.match(r'SCENARIO/(.+):title$', loc).group(1))].append((-1, 0, cur, new))
            else:
                skip['xscn 位置无法解析'] += 1
                continue
        elif src == 'txt':
            m = re.match(r'(.*?):(\d+)$', loc)
            if not m:
                skip['文本位置无法解析'] += 1
                continue
            txt_changes[(scope, m.group(1))].append((int(m.group(2)), cur, new))
        else:
            skip['其它 src(%s)' % src] += 1
            continue
        n_chg += 1

    print('待改出现 %d 处；跳过 %s' % (n_chg, dict(skip)))
    print('  txt 文件 %d 个 · xscn %d 个 · 真源表 %d 条' %
          (len(txt_changes), len(xscn_changes), len(truth_changes)))

    print('\n--- txt 改动明细 ---')
    for (efile, fn), chs in sorted(txt_changes.items()):
        for ln, old, new in chs:
            print('  [txt] %s/SCENARIO/%s:%d\n        %s\n     -> %s' % (efile, fn, ln, old, new))
    print('\n--- xscn 改动明细 ---')
    for (efile, fn), chs in sorted(xscn_changes.items()):
        for g, k, old, new in chs:
            print('  [xscn] %s/%s g%d#%d\n        %s\n     -> %s' % (efile, fn, g, k, old, new))
    print('\n--- 真源表 (olgww2-glossary.tsv) 改动明细 ---')
    for en, hits in sorted(truth_changes.items()):
        print('  %s  %s' % (en, '; '.join('%s→%s' % h for h in hits)))

    done = []

    # ---- txt ----
    for (efile, fn), chs in sorted(txt_changes.items()):
        for path in [os.path.join(GAME, efile, 'SCENARIO', fn),
                     os.path.join(GAME, efile, 'TEXT-ZH', 'SCENARIO', fn)]:
            if not os.path.exists(path):
                continue
            raw = open(path, 'rb').read()
            lines = raw.decode('gbk').split('\n')
            byline = collections.defaultdict(list)
            for ln, old, new in chs:
                byline[ln].append((old, new))
            n_ok = 0
            for ln, pairs in byline.items():
                if ln - 1 >= len(lines):
                    continue
                v = lines[ln - 1]
                for old, new in pairs:
                    if old in v:
                        v = v.replace(old, new)
                        n_ok += 1
                lines[ln - 1] = v
            if n_ok == 0:
                print('  [txt!] %s/%s 0 处命中（槽值可能不一致）' % (efile, fn))
                continue
            nd = '\n'.join(lines).encode('gbk')
            print('  [txt] %s/%s %d/%d 处  %d->%d B' %
                  (efile, os.path.relpath(path, os.path.join(GAME, efile)), n_ok, len(chs), len(raw), len(nd)))
            if apply:
                os.makedirs(BK, exist_ok=True)
                dst = os.path.join(BK, efile + '__' + os.path.relpath(path, os.path.join(GAME, efile)).replace('\\', '_'))
                if not os.path.exists(dst):
                    shutil.copy2(path, dst)
                tmp = path + '.new'
                open(tmp, 'wb').write(nd)
                assert open(tmp, 'rb').read() == nd
                os.replace(tmp, path)
                done.append(path)

    # ---- xscn ----
    for (efile, fn), chs in sorted(xscn_changes.items()):
        path = os.path.join(GAME, efile, 'SCENARIO', fn)
        if not os.path.exists(path):
            continue
        data, items, meta = parse(path)
        if not items:
            continue
        bykey = collections.defaultdict(list)
        for g, k, old, new in chs:
            bykey[(g, k)].append((old, new))
        table = {(g, k): (off, ln) for g, k, off, ln in items}
        if meta and meta[0] is not None:
            table[(-1, 0)] = (meta[0], meta[1])
        repl = []
        n_ok = 0
        for (g, k), pairs in bykey.items():
            if (g, k) not in table:
                print('  [xscn!] %s/%s g%d#%d 槽不存在' % (efile, fn, g, k))
                continue
            off, ln = table[(g, k)]
            v = data[off + 2:off + 2 + ln].decode('gbk', 'replace')
            v0 = v
            for old, new in pairs:
                if old in v:
                    v = v.replace(old, new)
                    n_ok += 1
            if v != v0:
                nb = v.encode('gbk')
                repl.append((off, 2 + ln, len(nb).to_bytes(2, 'little') + nb))
        if not repl:
            print('  [xscn!] %s/%s 0 处命中' % (efile, fn))
            continue
        print('  [xscn] %s/%s %d 处' % (efile, fn, n_ok))
        if apply:
            os.makedirs(BK, exist_ok=True)
            dst = os.path.join(BK, efile + '__SCENARIO_' + fn)
            if not os.path.exists(dst):
                shutil.copy2(path, dst)
            buf = bytearray()
            last = 0
            for off, oldlen, newbytes in sorted(repl, key=lambda x: x[0]):
                buf += data[last:off] + newbytes
                last = off + oldlen
            buf += data[last:]
            tmp = path + '.new'
            open(tmp, 'wb').write(bytes(buf))
            assert open(tmp, 'rb').read() == bytes(buf)
            os.replace(tmp, path)
            done.append(path)

    # ---- 真源表 ----
    if truth_changes and apply:
        raw = io.open(TRUTH, encoding='utf-8-sig', newline='').read()
        nl = '\r\n' if '\r\n' in raw else '\n'
        lines = raw.replace('\r\n', '\n').split('\n')
        n_ok = 0
        for i, ln in enumerate(lines):
            c = ln.split('\t')
            if len(c) < 2 or c[0].strip() not in truth_changes:
                continue
            v = c[1]
            for old, new in truth_changes[c[0].strip()]:
                if old in v:
                    v = v.replace(old, new)
                    n_ok += 1
            c[1] = v
            lines[i] = '\t'.join(c)
        os.makedirs(BK, exist_ok=True)
        dst = os.path.join(BK, 'olgww2-glossary.tsv')
        if not os.path.exists(dst):
            shutil.copy2(TRUTH, dst)
        nd = nl.join(lines).encode('utf-8-sig')
        tmp = TRUTH + '.new'
        open(tmp, 'wb').write(nd)
        assert open(tmp, 'rb').read() == nd
        os.replace(tmp, TRUTH)
        print('  [真源] olgww2-glossary.tsv %d 处' % n_ok)
        done.append(TRUTH)

    print('\n%s（改动文件 %d）' % ('已写盘，备份 ' + BK if apply else '（dry-run，未写盘）', len(done)))


if __name__ == '__main__':
    main()
