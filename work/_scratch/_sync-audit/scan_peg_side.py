#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG / PeG-WW2 侧「定名残留」扫描器（**只读**）。

目的：`docs\\51` 的定名（`work/_sync-audit/naming.tsv`）已落 OLGWW2 成品与真源；
      本脚本查 **PeG（`peg/research` ＋ `D:\\Program Files\\PeG` ＋ `EFILE_OPENPEG`）与
      PeG-WW2（`pegww2/research` ＋ `EFILE_OLGWW2`）** 里还有哪些地方同一英文仍残留在**中文侧**。

判据：规则命中**且**该单元格含 CJK ⇒ 「中文侧残留」（要改的目标）。
      命中但无 CJK ⇒ 「英文侧命中」（只统计，**不动**）。

`.xscn` 走 `apply_residual.parse()` 逐槽取值后再套规则（文本域与 `.txt` 同一套判据）。

输出：`work/_sync-audit/peg-side-hits.tsv`
      列 `范围 · 文件 · 位置 · 列/槽 · 残留英文 · old · new · 片段`
用法: python scan_peg_side.py
"""
import io
import os
import re
import sys
import collections

ROOT = r'D:\DSH\军事游戏汉化'
sys.path.insert(0, os.path.join(ROOT, 'work', 'efile-nashornpbem'))
from apply_residual import parse  # noqa: E402

NAMING = os.path.join(ROOT, 'work', '_sync-audit', 'naming.tsv')
OUT = os.path.join(ROOT, 'work', '_sync-audit', 'peg-side-hits.tsv')

ROOTS = [
    ('peg.research',    os.path.join(ROOT, 'peg', 'research')),
    ('pegww2.research', os.path.join(ROOT, 'pegww2', 'research')),
    ('peg.game.scn',    r'D:\Program Files\PeG\Scenario'),
    ('peg.game.usr',    r'D:\Program Files\PeG\Userscen'),
    ('peg.game.root',   r'D:\Program Files\PeG'),
    ('efile.OPENPEG',   r'D:\OpenPG2\EFILE_OPENPEG'),
    ('efile.OLGWW2',    r'D:\OpenPG2\EFILE_OLGWW2'),
]
TEXT_EXT = ('.tsv', '.txt', '.md', '.json', '.xml', '.cfg', '.csv')
SKIP_DIR_PARTS = ('\\evidence\\', '\\__pycache__\\', '\\out\\', '\\backup\\',
                  '\\cine\\', '\\Docs\\', '\\MAP\\', '\\SAVE\\')
NOISE = re.compile(r'(\.dat|\.dll|\.exe|\.csv|OpenIcons|\.bin)$', re.I)
CJK = re.compile(r'[\u4e00-\u9fff]')


def load_rules():
    rules = []
    with io.open(NAMING, encoding='utf-8-sig', newline='') as f:
        text = f.read().replace('\r\n', '\n')
    head = None
    for ln in text.split('\n'):
        if not ln.strip():
            continue
        c = ln.split('\t')
        if head is None:
            head = c
            continue
        if len(c) >= 3:
            rules.append((c[0].strip(), c[1], c[2], c[3] if len(c) > 3 else ''))
    rules.sort(key=lambda x: -len(x[1]))
    return rules


def read_text(path):
    raw = open(path, 'rb').read()
    for enc in ('utf-8-sig', 'gbk'):
        try:
            return raw.decode(enc)
        except Exception:
            pass
    return raw.decode('latin-1')


def check(cell, rules, rows, tag, rel, loc, ci):
    """对单个中文侧值套规则；返回 (命中数, 已改数)。"""
    n = n_done = 0
    if not cell or not CJK.search(cell):
        return 0, 0
    for key, old, new, why in rules:
        if old and old in cell:
            if new in cell:
                n_done += 1
                continue
            rows.append((tag, rel.replace('\\', '/'), loc, ci, key, old, new, cell.strip()[:110]))
            n += 1
            break
    return n, n_done


def main():
    rules = load_rules()
    print('规则行 %d 条（最长 old %d 字符）' % (len(rules), len(rules[0][1])))

    rows = []
    stat = collections.Counter()
    per_root = collections.Counter()
    files = 0
    for tag, base in ROOTS:
        if not os.path.isdir(base):
            print('  [缺] %s' % base)
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            if any(p in dirpath + '\\' for p in SKIP_DIR_PARTS):
                continue
            if tag == 'efile.OLGWW2' and '\\SCENARIO' not in dirpath and '\\TEXT-ZH' not in dirpath:
                continue
            if tag == 'efile.OPENPEG' and os.path.basename(dirpath) == '' and filenames:
                pass
            for fn in sorted(filenames):
                low = fn.lower()
                path = os.path.join(dirpath, fn)
                rel = os.path.relpath(path, base)
                if NOISE.search(fn):
                    continue
                if low.endswith('.xscn'):
                    try:
                        data, items, meta = parse(path)
                    except Exception:
                        stat['xscn 解析失败'] += 1
                        continue
                    files += 1
                    for g, k, off, ln in items:
                        v = data[off + 2:off + 2 + ln].decode('gbk', 'replace')
                        n, nd = check(v, rules, rows, tag, rel, 'g%d#%d' % (g, k), '-')
                        stat['中文侧残留'] += n
                        stat['已改'] += nd
                        per_root[tag] += n
                    if meta and meta[0] is not None:
                        v = data[meta[0] + 2:meta[0] + 2 + meta[1]].decode('gbk', 'replace')
                        n, nd = check(v, rules, rows, tag, rel, 'title', '-')
                        stat['中文侧残留'] += n
                        stat['已改'] += nd
                        per_root[tag] += n
                    continue
                if not low.endswith(TEXT_EXT):
                    continue
                try:
                    text = read_text(path)
                except Exception:
                    stat['读失败'] += 1
                    continue
                files += 1
                for i, ln in enumerate(text.replace('\r\n', '\n').replace('\r', '\n').split('\n'), 1):
                    if not ln.strip():
                        continue
                    cells = ln.split('\t')
                    for ci, cell in enumerate(cells):
                        if not cell:
                            continue
                        hit_cjk = bool(CJK.search(cell))
                        matched = False
                        for key, old, new, why in rules:
                            if old and old in cell:
                                matched = True
                                if hit_cjk:
                                    if new in cell:
                                        stat['已改'] += 1
                                        break
                                    rows.append((tag, rel.replace('\\', '/'), 'L%d' % i, ci, key, old, new,
                                                 cell.strip()[:110]))
                                    stat['中文侧残留'] += 1
                                    per_root[tag] += 1
                                else:
                                    stat['英文侧命中'] += 1
                                break
                        del matched
    with io.open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('范围\t文件\t位置\t列/槽\t残留英文\told\tnew\t片段\n')
        for r in rows:
            f.write('\t'.join(str(x) for x in r) + '\n')
    print('扫描文件 %d 个 · 统计 %s' % (files, dict(stat)))
    print('按范围中文侧残留：%s' % dict(per_root))
    print('明细 → %s（%d 行）' % (OUT, len(rows)))
    for title, ctr in (('命中文件', collections.Counter(r[0] + '/' + r[1] for r in rows)),
                       ('命中键', collections.Counter(r[4] for r in rows))):
        print('\n--- %s Top 25 ---' % title)
        for k, v in ctr.most_common(25):
            print('  %5d  %s' % (v, k))


if __name__ == '__main__':
    main()
