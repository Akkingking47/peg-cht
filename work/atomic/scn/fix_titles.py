# -*- coding: utf-8 -*-
"""
修正 ATOMIC 场景标题行的 "Battle of X" 译法，对齐已交付 efile 口径：
  Battle of/at/in X  ->  X之战
  YYYY Battle of X   ->  YYYY年X之战   (年份与名称之间不留空格)
  Operation X        ->  X行动        (已是正确，无需改)
仅改「段首行（标题行）」；正文里的"战役"（普指战役/会战）不动。
"""
import glob, os, sys

# name -> 期望的完整标题行（校正后）
FIX = {
    'Forward1i.txt':          '苏奥穆斯萨尔米之战',
    '1919_rigai.txt':         '1919年里加之战',
    '1942_tunisi.txt':        '1942年突尼斯之战',
    'Forward41i.txt':         '罗马尼亚之战',
    '1943_rhodesi.txt':       '1943年罗得岛之战',
    'Forward43i.txt':         '布拉格之战',
    '1954_dienbienphui.txt':  '1954年奠边府之战',
    'Forward25i.txt':         '西里西亚之战',
    'Forward4i.txt':          '敖德萨之战：',
    'Forward27i.txt':         '柏林之战',
    'Forward31i.txt':         '阿登之战',
    '1943_prokhorovkai.txt':  '1941年普罗霍罗夫卡之战',
    '1919_cesisi.txt':        '1919年采西斯之战',
    'Forward0i.txt':          '哈拉哈河之战',
    'Forward29i.txt':         '东弗里斯兰之战',
    'Forward19i.txt':         '维普里之战',
}

def split_files(raw):
    parts = []
    idx = 0
    while True:
        j = raw.find(b'@@FILE\t', idx)
        if j < 0:
            break
        k = raw.find(b'\n', j)
        nxt = raw.find(b'@@FILE\t', k)
        head = raw[j:k]
        body = raw[k+1:] if nxt < 0 else raw[k+1:nxt]
        parts.append((head, body))
        if nxt < 0:
            break
        idx = nxt
    return parts

total = 0
for f in sorted(glob.glob('work/atomic/scn/out-*.txt')):
    raw = open(f, 'rb').read()
    parts = split_files(raw)
    changed = False
    newparts = []
    for head, body in parts:
        name = head.split(b'\t')[1].decode('utf-8', errors='replace')
        if name in FIX:
            lines = body.split(b'\n')
            if lines:
                # 首行（可能带 \r）
                first = lines[0]
                cr = first.endswith(b'\r')
                cur = first[:-1].decode('utf-8', errors='replace') if cr else first.decode('utf-8', errors='replace')
                want = FIX[name]
                if cur.strip() != want:
                    print(f"{os.path.basename(f)}  {name}\n    旧: {cur!r}\n    新: {want!r}")
                    nl = want.encode('utf-8') + (b'\r' if cr else b'')
                    lines[0] = nl
                    body = b'\n'.join(lines)
                    changed = True
                    total += 1
        newparts.append((head, body))
    if changed:
        out = b''.join(h + b'\n' + b for h, b in newparts)
        open(f, 'wb').write(out)

print(f"\n共修正 {total} 处标题行。")
