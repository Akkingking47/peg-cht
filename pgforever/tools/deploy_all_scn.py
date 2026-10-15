# -*- coding: utf-8 -*-
r"""
全库 .pgscn 部署：只改 Name / Description 两行，其余逐字节保留。
读 work\scn-all\zh\z*.jsonl（{"id":..,"zh_name":..,"zh_desc":..}）
映射取 work\scn-all\paths.json
--apply 落盘，默认 DRY-RUN。
"""
import json, os, glob, sys, shutil

ROOT = r'D:\PGForever1.021'
WORK = r'D:\DSH\军事游戏汉化\pgforever\work\scn-all'
BACKUP = r'D:\DSH\军事游戏汉化\pgforever\backup\scnall-origin'
APPLY = '--apply' in sys.argv

# id -> 完整 md5
idmap = {}
for f in glob.glob(os.path.join(WORK, 'src*.json')):
    for it in json.load(open(f, encoding='utf-8')):
        idmap[it['id']] = it['md5']

tr = {}
dups = []
for f in sorted(glob.glob(os.path.join(WORK, 'zh', 'z*.jsonl'))):
    for line in open(f, encoding='utf-8'):
        s = line.strip()
        if not s:
            continue
        it = json.loads(s)
        m = it.get('md5')
        if not m:
            m = idmap.get(it.get('id', ''))
        if not m:
            print('!! 无法解析', f, it.get('id')); continue
        if m in tr and tr[m] != (it['zh_name'], it['zh_desc']):
            dups.append(m)
        tr[m] = (it['zh_name'], it['zh_desc'])
print('译文 %d 条（重复 %d）' % (len(tr), len(dups)))

paths = json.load(open(os.path.join(WORK, 'paths.json'), encoding='utf-8'))
print('映射 %d 条，覆盖 %d 文件' % (len(paths), sum(len(v) for v in paths.values())))

BAN = ['支那', '鬼子', '伪军', '共匪', '毛子']
bad, banned, nofound = [], [], []
for m, (n, d) in tr.items():
    if m not in paths:
        nofound.append(m); continue
    if not n or not d:
        bad.append(m)
    for b in BAN:
        if b in n or b in d:
            banned.append((m, b))
print('空字段 %d %s' % (len(bad), bad[:5]))
print('禁用词 %d %s' % (len(banned), banned[:5]))

done = 0
if APPLY:
    for m, (n, d) in tr.items():
        if m not in paths:
            continue
        for rel in paths[m]:
            dst = os.path.join(ROOT, rel)
            raw = open(dst, 'rb').read()
            if raw[:2] != b'\xff\xfe':
                print('!! 非 UTF-16LE，跳过', rel); continue
            text = raw.decode('utf-16')
            lines = text.split('\r\n')
            hitn = hitd = False
            for i, line in enumerate(lines):
                if line.startswith('Name\t') and not hitn:
                    lines[i] = 'Name\t' + n; hitn = True
                elif line.startswith('Description\t') and not hitd:
                    lines[i] = 'Description\t' + d; hitd = True
            if not (hitn and hitd):
                print('!! 字段缺失', rel); continue
            out = ('\ufeff' + '\r\n'.join(lines)).encode('utf-16-le')
            bk = os.path.join(BACKUP, rel)
            if not os.path.exists(bk):
                os.makedirs(os.path.dirname(bk), exist_ok=True)
                shutil.copy2(dst, bk)
            open(dst, 'wb').write(out)
            done += 1
    print('已部署 %d 个文件' % done)
else:
    print('[DRY-RUN] 未落盘。')
