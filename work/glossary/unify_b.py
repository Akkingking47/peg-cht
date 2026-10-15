# -*- coding: utf-8 -*-
"""按 glossary-b-class-decide.tsv 的目标值，把**同一原文**在全库统一为一种译名。

数据来源：glossary/glossary-occ.tsv（逐处出现：en zh cat scope src loc）
目标来源：glossary/glossary-b-class-decide.tsv（cat en variants 分布 建议 理由）

只动 3 个已汉化 efile 的生效文件；
  · .txt  → <efile>/SCENARIO/ + <efile>/TEXT-ZH/SCENARIO/（两层恒等，都改）
  · 根文件 → <efile>/TEXT-ZH/<fn>
  · .xscn → <efile>/SCENARIO/<fn>（字节级定点）
替换按「名单项」粒度（以 '/' 分段整段相等才换），避免误伤子串。

用法： python unify_b.py [--apply]
"""
import os, io, re, sys, shutil, collections

sys.path.insert(0, os.path.join(r'D:\DSH\军事游戏汉化\work', 'efile-nashornpbem'))
from apply_residual import parse

GAME = r'D:\OpenPG2'
ROOT = r'D:\DSH\军事游戏汉化'
DEC = os.path.join(ROOT, 'glossary', 'glossary-b-class-decide.tsv')
OCC = os.path.join(ROOT, 'glossary', 'glossary-occ.tsv')
BK = os.path.join(ROOT, 'backup', 'olgww2-b-unify2-before')
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


def repl_parts(value, old, new):
    """按 '/' 分段：整段相等才替换。返回 (新值, 是否改)。"""
    if value.strip() == old:
        lead = value[:len(value) - len(value.lstrip())]
        trail = value[len(value.rstrip()):]
        return lead + new + trail, True
    if '/' not in value:
        return value, False
    parts = value.split('/')
    hit = False
    for i, p in enumerate(parts):
        if p.strip() == old:
            lead = p[:len(p) - len(p.lstrip())]
            trail = p[len(p.rstrip()):]
            parts[i] = lead + new + trail
            hit = True
    return ('/'.join(parts), True) if hit else (value, False)


def main():
    apply = '--apply' in sys.argv
    # 键必须带 cat：同一原文在不同 cat 下的正确译法**本就不同**
    #（Cossack→哥萨克[UNIT]/哥萨克号[PLACE 舰船]；Carrier→航空母舰[舰种]/运输车[陆上单位]）
    # 只按 en 建键会被后来者覆盖，造成跨类别误改。
    tgt = {}
    for d in load(DEC):
        tgt[(d['en'].strip(), d['cat'].strip())] = d['建议'].strip()
    print('目标组数 %d' % len(tgt))

    # ---- 归类改动 ----
    txt_changes = collections.defaultdict(list)    # (efile, src, fn) -> [(line, old, new)]
    xscn_changes = collections.defaultdict(list)   # (efile, fn) -> [(g, k, old, new)]
    skip = collections.Counter()
    n_chg = 0
    for r in load(OCC):
        en = r['en'].strip()
        key = (en, r['cat'].strip())
        if key not in tgt:
            continue
        want = tgt[key]
        cur = r['zh'].strip()
        if cur == want:
            continue
        # 只统一「已是中文」的变体；未译原文 / 政策保留（舰名、型号）不动
        if not re.search(r'[\u4e00-\u9fff]', cur):
            skip['未译原文/政策保留'] += 1
            continue
        scope, src, loc = r['scope'], r['src'], r['loc']
        if scope not in EFILES or src == 'glossary':
            skip['非目标范围'] += 1
            continue
        if src == 'xscn':
            m = re.match(r'SCENARIO/(.+):g(\d+)#(\d+)$', loc)
            if m:
                xscn_changes[(scope, m.group(1))].append((int(m.group(2)), int(m.group(3)), cur, want))
            elif re.match(r'SCENARIO/(.+):title$', loc):
                xscn_changes[(scope, re.match(r'SCENARIO/(.+):title$', loc).group(1))].append((-1, 0, cur, want))
            else:
                skip['xscn 位置无法解析'] += 1
                continue
        else:
            m = re.match(r'(.*?):(\d+)$', loc)
            if not m:
                skip['文本位置无法解析'] += 1
                continue
            txt_changes[(scope, src, m.group(1))].append((int(m.group(2)), cur, want))
        n_chg += 1
    print('待改出现 %d 处；跳过 %s' % (n_chg, dict(skip)))
    print('  文本文件 %d 个；xscn %d 个' % (len(txt_changes), len(xscn_changes)))
    print('\n--- 抽样 30 条 ---')
    shown = 0
    for (efile, src, fn), chs in sorted(txt_changes.items()):
        for ln, old, new in chs:
            if shown >= 30:
                break
            print('  %-6s %-16s %-22s %s -> %s' % (src, efile[6:], '%s:%d' % (fn, ln), old, new))
            shown += 1
        if shown >= 30:
            break

    # ---- 文本文件 ----
    done_files = []
    for (efile, src, fn), chs in sorted(txt_changes.items()):
        bases = []
        if src == 'txt':
            bases = [os.path.join(GAME, efile, 'SCENARIO', fn),
                     os.path.join(GAME, efile, 'TEXT-ZH', 'SCENARIO', fn)]
        else:
            p1 = os.path.join(GAME, efile, 'TEXT-ZH', fn)
            p2 = os.path.join(GAME, efile, fn)
            bases = [p1 if os.path.exists(p1) else p2]
        for path in bases:
            if not os.path.exists(path):
                continue
            raw = open(path, 'rb').read()
            text = raw.decode('gbk')
            lines = text.split('\n')
            byline = collections.defaultdict(list)
            for ln, old, new in chs:
                byline[ln].append((old, new))
            n_ok = 0
            for ln, pairs in byline.items():
                if ln - 1 >= len(lines):
                    continue
                v = lines[ln - 1]
                for old, new in pairs:
                    v2, hit = repl_parts(v, old, new)
                    if hit:
                        v = v2
                        n_ok += 1
                lines[ln - 1] = v
            if n_ok == 0:
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
                done_files.append(path)

    # ---- .xscn ----
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
                continue
            off, ln = table[(g, k)]
            v = data[off + 2:off + 2 + ln].decode('gbk', 'replace')
            for old, new in pairs:
                v2, hit = repl_parts(v, old, new)
                if hit:
                    v = v2
                    n_ok += 1
            if n_ok:
                nb = v.encode('gbk')
                repl.append((off, 2 + ln, len(nb).to_bytes(2, 'little') + nb))
        if not repl:
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
            done_files.append(path)

    print('\n%s（改动文件 %d）' % ('已写盘，备份 ' + BK if apply else '（dry-run，未写盘）', len(done_files)))


if __name__ == '__main__':
    main()
