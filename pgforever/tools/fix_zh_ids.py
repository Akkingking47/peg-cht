# -*- coding: utf-8 -*-
r"""按 id（md5 前 10 位）解析译文 → 补全完整 md5。就地重写 jsonl。"""
import json, glob, os, re, sys

WORK = r'D:\DSH\军事游戏汉化\pgforever\work\brf-all'
# id → 完整 md5
idmap = {}
for f in glob.glob(os.path.join(WORK, 'src*.json')):
    for it in json.load(open(f, encoding='utf-8')):
        idmap[it['id']] = it['md5']

fixed = bad = 0
for f in sorted(glob.glob(os.path.join(WORK, 'zh', 'z*.jsonl'))):
    out, ch = [], False
    for line in open(f, encoding='utf-8'):
        s = line.strip()
        if not s:
            continue
        it = json.loads(s)
        m = it.get('md5', '')
        if m not in idmap.values():
            i = it.get('id') or m[:10]
            if i in idmap:
                it['md5'] = idmap[i]
                it.pop('id', None)
                ch = True; fixed += 1
            else:
                print('  !! 无法解析', f, i); bad += 1
        else:
            it.pop('id', None)
        out.append(json.dumps(it, ensure_ascii=False))
    if ch:
        open(f, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
        print('修正', os.path.basename(f))
print('修复 %d 条，失败 %d 条' % (fixed, bad))
