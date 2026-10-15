# -*- coding: utf-8 -*-
r"""
提取 PG 的 equipment.pgeqp 中需要翻译的 Name 列。
输出 work\pg\equip-names.json：[{id, name, cls, n}]（按名称去重，n 为出现次数）
"""
import json
import os

SRC = r'D:\DSH\军事游戏汉化\pgforever\backup\origin\PG\Scenario\equipment.pgeqp'
OUTDIR = r'D:\DSH\军事游戏汉化\pgforever\work\pg'
os.makedirs(OUTDIR, exist_ok=True)

text = open(SRC, 'rb').read().decode('utf-16')
lines = text.split('\r\n')

# Class 代码 -> 类别（依据 UI 类别顺序推断，仅作翻译参考，不写入文件）
CLASS_HINT = {
    0: '步兵', 1: '坦克', 2: '侦察', 3: 'AT', 4: '炮兵', 5: '高射炮', 6: '防空',
    7: '要塞', 8: '战斗机', 9: '战术轰炸机', 10: '重型轰炸机', 11: '潜艇',
    12: '驱逐舰', 13: '主力舰', 14: '航空母舰', 15: '地面运输', 16: '运输机',
}

rows = []
for i, l in enumerate(lines):
    if i < 2:
        continue
    if not l.strip():
        continue
    c = l.split('\t')
    rows.append((c[0], c[1], c[2]))

print('装备条目 %d 条' % len(rows))
uniq = {}
for idx, name, cls in rows:
    if name in uniq:
        uniq[name]['n'] += 1
    else:
        try:
            ci = int(cls)
        except Exception:
            ci = -1
        uniq[name] = {'id': idx, 'name': name, 'cls': ci, 'hint': CLASS_HINT.get(ci, ''), 'n': 1}

items = sorted(uniq.values(), key=lambda x: int(x['id']))
json.dump(items, open(os.path.join(OUTDIR, 'equip-names.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('唯一名称 %d 条 -> %s' % (len(items), os.path.join(OUTDIR, 'equip-names.json')))
print()
for it in items:
    print('%4s | %-32s | %-8s | x%d' % (it['id'], it['name'], it['hint'], it['n']))
