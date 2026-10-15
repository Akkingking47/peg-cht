# -*- coding: utf-8 -*-
r"""
全库简报（.pgbrf）部署工具
- 读取 work\brf-all\zh\z*.jsonl（每行 {"md5":..,"zh":..}）
- 与 work\brf-all\index.json 的 md5→paths 映射对照
- 写回 D:\PGForever1.021\<path>，UTF-8 无 BOM
- --apply 才落盘，默认 DRY-RUN
"""
import json, os, glob, sys, shutil, re

ROOT = r'D:\PGForever1.021'
WORK = r'D:\DSH\军事游戏汉化\pgforever\work\brf-all'
BACKUP = r'D:\DSH\军事游戏汉化\pgforever\backup\brfall-origin'
APPLY = '--apply' in sys.argv

# 1) 读译表
zh = {}
dups = []
for f in sorted(glob.glob(os.path.join(WORK, 'zh', 'z*.jsonl'))):
    for line in open(f, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        it = json.loads(line)
        m, z = it['md5'], it['zh']
        if m in zh and zh[m] != z:
            dups.append(m)
        zh[m] = z
print('读入译文 %d 条（重复 %d）' % (len(zh), len(dups)))

# 2) 读映射
paths = json.load(open(os.path.join(WORK, 'paths.json'), encoding='utf-8'))
print('映射条目 %d，覆盖文件 %d' % (len(paths), sum(len(v) for v in paths.values())))

# 3) 校验
BAN = ['支那', '鬼子', '伪军', '共匪', '毛子']
over, badtag, banned, nofound = [], [], [], []
ok = []
for m, z in zh.items():
    if m not in paths:
        nofound.append(m); continue
    if '<p>' in z and '</p>' not in z:
        badtag.append(m)
    for b in BAN:
        if b in z:
            banned.append((m, b))
    # 长度：按 UTF-8 字节数比较才公平（中文 1 字 = 3 字节）
    # 简报是独立文件，不像 MAPNAMES 有定长槽，理论上不限制；
    # 但简报框有 max-height，译文过长会被裁切，故仍设 1.05 倍字节上限警戒
    p0 = os.path.join(ROOT, paths[m][0])
    try:
        en = open(p0, 'rb').read()
        if len(z.encode('utf-8')) > len(en) * 1.05:
            over.append((m, len(z.encode('utf-8')), len(en),
                         round(len(z.encode('utf-8'))/max(1,len(en)), 2)))
    except Exception:
        nofound.append(m)

print('\n映射缺失: %d %s' % (len(nofound), nofound[:5]))
print('缺 </p>: %d %s' % (len(badtag), badtag[:5]))
print('禁用词: %d %s' % (len(banned), banned[:5]))
print('偏长(>95%%): %d %s' % (len(over), over[:5]))

# 4) 部署
donef = 0
if APPLY:
    os.makedirs(BACKUP, exist_ok=True)
    for m, z in zh.items():
        if m not in paths:
            continue
        out = z
        if not out.endswith('\n'):
            out += '\r\n'
        data = out.encode('utf-8')
        for rel in paths[m]:
            dst = os.path.join(ROOT, rel)
            # 备份（首次）
            bk = os.path.join(BACKUP, rel)
            if not os.path.exists(bk):
                os.makedirs(os.path.dirname(bk), exist_ok=True)
                shutil.copy2(dst, bk)
            open(dst, 'wb').write(data)
            donef += 1
    print('\n已部署 %d 个文件' % donef)
else:
    print('\n[DRY-RUN] 未落盘。加 --apply 执行。')
    for m, z in list(zh.items())[:2]:
        print('\n-- %s' % paths[m][0])
        print('  原文:', open(os.path.join(ROOT, paths[m][0]), 'rb').read().decode('utf-8','ignore')[:110])
        print('  译文:', z[:110])
