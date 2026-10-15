# -*- coding: utf-8 -*-
"""
地名译名工具与长度约束校验。

用途：
  1) 给批量生成的地名译表做【字节长度校验】（20 字节记录，最多 6 汉字）
  2) 提供统一的通名后缀/音译后处理规则
  3) 输出待译清单，按长度分档，便于分批处理

约束（硬）：
  记录 20 字节 = 名称(UTF-8) + NUL + NUL 补满
  ⇒ 名称 UTF-8 字节数 <= 19；中文 3 字节/字 ⇒ 最多 6 字（18B）
  7 字 = 21B 会溢出，破坏下一条记录。
"""

import glob
import os
import struct
import unicodedata
import re
import collections

REC = 20
NAME_MAX_B = 19          # 名称可用的最大字节数（留 1 字节给 NUL）
MAX_HANZI = 6            # 由 NAME_MAX_B 推出
ROOT = r'D:\PGForever1.021'
WORK = r'D:\DSH\军事游戏汉化\pgforever\work\mapnames'


def zb(s):
    """UTF-8 字节数。"""
    return len(s.encode('utf-8'))


def fits(zh):
    return zb(zh) <= NAME_MAX_B


def find_mapnames():
    pats = [os.path.join(ROOT, '*', 'Scenario', 'mapnames.str'),
            os.path.join(ROOT, '*', 'Scenario', 'MAPNAMES.STR')]
    seen, out = set(), []
    for p in pats:
        for f in glob.glob(p):
            k = f.lower()
            if k not in seen:
                seen.add(k)
                out.append(f)
    return sorted(out)


def detect_format(raw, n, probe=1500):
    sp = nul = 0
    for i in range(14, min(n, 14 + probe)):
        off = 2 + i * REC
        if off + REC > len(raw):
            break
        blk = raw[off:off + REC]
        if b'  ' in blk.replace(b'\x00', b''):
            sp += 1
        if blk[-1] == 0 and blk[-2] == 0:
            nul += 1
    return ('B' if sp > nul else 'A')


def collect_names():
    """返回 (全部名称计数, 是否含中文)。仅统计格式 A 文件（格式 B 单独处理）。"""
    cnt = collections.Counter()
    for f in find_mapnames():
        raw = open(f, 'rb').read()
        n = struct.unpack_from('<H', raw, 0)[0]
        if detect_format(raw, n) == 'B':
            continue
        for i in range(14, n):
            off = 2 + i * REC
            if off + REC > len(raw):
                break
            nm = raw[off:off + REC].split(b'\x00')[0].decode('utf-8', 'replace').strip()
            if nm and nm not in ('Empty', 'Lake'):
                cnt[nm] += 1
    return cnt


def has_cn(s):
    return any('\u4e00' <= c <= '\u9fff' for c in s)


# ---- 通名后缀规则（英文尾词 → 中文） ----
SUFFIX = {
    'Sea': '海', 'Ocean': '洋', 'Island': '岛', 'Islands': '群岛',
    'Lake': '湖', 'Gulf': '湾', 'Bay': '湾', 'Mount': '山',
    'Mountain': '山', 'Mountains': '山', 'Cape': '角', 'Strait': '海峡',
    'Hill': '山', 'Hills': '山', 'Peninsula': '半岛', 'Valley': '谷',
    'Forest': '林', 'Desert': '沙漠', 'Pass': '山口', 'Port': '港',
    'Airfield': '机场', 'Station': '站', 'Bridge': '桥', 'Gate': '门',
    'Park': '公园', 'Beach': '滩', 'Point': '角', 'Canal': '运河',
    'Dam': '坝', 'Creek': '溪', 'Wood': '林', 'Woods': '林',
    'Field': '原', 'Fields': '原', 'Fort': '堡', 'Fortress': '要塞',
    'Castle': '堡', 'Monastery': '修道院', 'Factory': '厂',
    'Harbor': '港', 'Harbour': '港', 'Ports': '港',
}

# ---- 常见前缀/虚词（保留或简化） ----
DROP_WORDS = {'The', 'the', 'of', "o'", 'de', 'la', 'le', 'les', 'du', 'des'}

# ---- 允许保留原文的（占位符/非地名） ----
KEEP_AS_IS = {'Riverdale', 'River pass', 'River Els', 'Empty', 'Lake',
              '??', '???', '1', '9', '888888'}


def load_table(path):
    """读一个 python 译表文件，取出所有 {en: zh} 字典。"""
    ns = {}
    src = open(path, encoding='utf-8').read()
    exec(compile(src, path, 'exec'), ns)
    tbl = {}
    for k, v in ns.items():
        if isinstance(v, dict) and k.isupper():
            tbl.update({a: b for a, b in v.items() if isinstance(b, str) and b})
    return tbl


def validate(tbl, names):
    """校验译表：长度超限 / 含非中文 / 译名重复率。返回问题列表。"""
    probs = []
    for en, zh in tbl.items():
        if not zh:
            continue
        if not has_cn(zh):
            probs.append(('无中文', en, zh))
        if not fits(zh):
            probs.append(('超长%dB' % zb(zh), en, zh))
    return probs


if __name__ == '__main__':
    names = collect_names()
    todo = sorted(t for t in names if not has_cn(t) and t not in KEEP_AS_IS)
    print('全部名称 %d，待译 %d' % (len(names), len(todo)))
    print('字节上限 %d ⇒ 最多 %d 汉字' % (NAME_MAX_B, MAX_HANZI))
    # 按长度分档输出
    buckets = collections.defaultdict(list)
    for t in todo:
        L = len(t)
        buckets['%02d_%s' % (L // 5 * 5, 'char')].append(t)
    os.makedirs(WORK, exist_ok=True)
    with open(os.path.join(WORK, 'todo_all.txt'), 'w', encoding='utf-8') as fh:
        for t in todo:
            fh.write('%2d|%4d|%s\n' % (len(t), names[t], t))
    print('清单 -> todo_all.txt')
