# -*- coding: utf-8 -*-
r"""
全库 .pgeqp 部署：只改每行 col1（Name），其余列逐字节保留。

译文：work\eqp-all\zh\z*.jsonl  {"md5":.., "zh":..}   （id 也可，脚本查表补全）
映射：work\eqp-all\paths.json   md5 -> {"text":.., "locs":[[rel,line,col],...]}

⚠️ pgeqp 只在 col1 放名称；Class 是编号（引擎查 OpenIcons.csv），**绝不能动**。
--apply 落盘，默认 DRY-RUN。
"""
import json, os, glob, sys, shutil

ROOT = r'D:\PGForever1.021'
WORK = r'D:\DSH\军事游戏汉化\pgforever\work\eqp-all'
BACKUP = r'D:\DSH\军事游戏汉化\pgforever\backup\eqpall-origin'
APPLY = '--apply' in sys.argv

idmap = {}
for f in glob.glob(os.path.join(WORK, 'src*.json')):
    for it in json.load(open(f, encoding='utf-8')):
        idmap[it['id']] = it['md5']

tr = {}
conf = []
for f in sorted(glob.glob(os.path.join(WORK, 'zh', 'z*.jsonl'))):
    for line in open(f, encoding='utf-8'):
        s = line.strip()
        if not s:
            continue
        it = json.loads(s)
        m = it.get('md5') or idmap.get(it.get('id', ''))
        if not m:
            print('!! 无法解析', f, it.get('id')); continue
        zh = it.get('zh', '')
        if m in tr and tr[m] != zh:
            conf.append((m, tr[m], zh))
        tr[m] = zh

paths = json.load(open(os.path.join(WORK, 'paths.json'), encoding='utf-8'))
print('译文 %d 条（冲突 %d）| 映射 %d 组' % (len(tr), len(conf), len(paths)))

# 纯型号（译名 == 原名）视为"保留原文"，允许不写入；但若译名含中文则必须覆盖
import re
CJK = re.compile(r'[\u4e00-\u9fff]')
nofound, banned, unchanged = [], [], 0
for m, zh in tr.items():
    if m not in paths:
        nofound.append((m, zh[:20])); continue
    if not zh.strip():
        continue
    for b in ['支那', '鬼子', '伪军', '共匪', '毛子']:
        if b in zh:
            banned.append((m, b))
    if not CJK.search(zh):
        unchanged += 1
print('映射缺失 %d %s' % (len(nofound), nofound[:5]))
print('禁用词 %d %s' % (len(banned), banned[:5]))
print('纯保留原文（无中文）%d 条' % unchanged)

plan = {}
for m, zh in tr.items():
    ent = paths.get(m)
    if not ent or not zh.strip():
        continue
    if zh == ent['text']:
        continue
    for rel, li, col in ent['locs']:
        plan.setdefault(rel, {}).setdefault(li, {})[col] = (m, zh)
print('涉及 %d 个文件' % len(plan))

done = miss = already = 0
if APPLY:
    for rel, linemap in plan.items():
        dst = os.path.join(ROOT, rel)
        raw = open(dst, 'rb').read()
        if raw[:2] != b'\xff\xfe':
            print('!! 非 UTF-16LE', rel); miss += 1; continue
        lines = raw.decode('utf-16').split('\r\n')
        ok = True
        touched = 0
        for li, colmap in linemap.items():
            if li >= len(lines):
                print('!! 行号越界', rel, li); ok = False; break
            cols = lines[li].split('\t')
            local_ok = True
            for col, (m, zh) in colmap.items():
                if col >= len(cols):
                    print('!! 列号越界', rel, li, col); local_ok = False; break
                cur = cols[col]
                if cur == zh:
                    # 已应用（幂等）
                    continue
                if cur != paths[m]['text']:
                    print('!! 原文不符 %s L%d C%d\n   实际 %r\n   期望 %r'
                          % (rel, li, col, cur[:50], paths[m]['text'][:50]))
                    local_ok = False; break
                cols[col] = zh
                touched += 1
            if not local_ok:
                ok = False; break
            lines[li] = '\t'.join(cols)
        if not ok:
            miss += 1; continue
        if touched == 0:
            already += 1; continue
        out = ('\ufeff' + '\r\n'.join(lines)).encode('utf-16-le')
        bk = os.path.join(BACKUP, rel)
        if not os.path.exists(bk):
            os.makedirs(os.path.dirname(bk), exist_ok=True)
            shutil.copy2(dst, bk)
        open(dst, 'wb').write(out)
        done += 1
    print('已部署 %d 个文件（失败 %d，本次无需改动 %d）' % (done, miss, already))
else:
    print('[DRY-RUN] 未落盘。')
