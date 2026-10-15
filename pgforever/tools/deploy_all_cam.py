# -*- coding: utf-8 -*-
r"""
全库 .pgcam 部署（v2）。

⚠️ 与 pgscn 部署不同：pgcam 同一行可能有多个可译列（Entry points 行 = col0 name + col2 desc），
   所以必须**按行处理、按列装配**，不能逐条字符串替换（否则同行的 name 替换会破坏 desc 的列索引）。

译文来源：work\cam-all\zh\z*.jsonl  {"id"/"md5":.., "kind":.., "zh":..}
映射来源：work\cam-all\paths.json   md5 -> {"kind":.., "locs":[[rel, line_idx, col], ...]}

做法：
  1) 扫全部待改文件，收集 (rel, line_idx, col) -> 译文
  2) 逐文件按行重组：line = '\t'.join(cols)，只替换命中的列
  3) 重编码 UTF-16LE + BOM 写回；首写备份到 backup\camall-origin\

--apply 落盘，默认 DRY-RUN。
"""
import json, os, glob, sys, shutil

ROOT = r'D:\PGForever1.021'
WORK = r'D:\DSH\军事游戏汉化\pgforever\work\cam-all'
BACKUP = r'D:\DSH\军事游戏汉化\pgforever\backup\camall-origin'
APPLY = '--apply' in sys.argv

# id -> md5
idmap = {}
for f in glob.glob(os.path.join(WORK, 'src*.json')):
    for it in json.load(open(f, encoding='utf-8')):
        idmap[it['id']] = it['md5']

# md5 -> zh
tr = {}
dups = []
for f in sorted(glob.glob(os.path.join(WORK, 'zh', 'z*.jsonl'))):
    for line in open(f, encoding='utf-8'):
        s = line.strip()
        if not s:
            continue
        it = json.loads(s)
        m = it.get('md5') or idmap.get(it.get('id', ''))
        if not m:
            print('!! 无法解析', f, it.get('id')); continue
        if m in tr and tr[m] != it['zh']:
            dups.append(m)
        tr[m] = it['zh']
print('译文 %d 条（冲突 %d）' % (len(tr), len(dups)))

paths = json.load(open(os.path.join(WORK, 'paths.json'), encoding='utf-8'))
print('映射 %d 组' % len(paths))

# 源文本表（用于校验）
src = {}
for f in glob.glob(os.path.join(WORK, 'src*.json')):
    for it in json.load(open(f, encoding='utf-8')):
        src[it['md5']] = it['text']

BAN = ['支那', '鬼子', '伪军', '共匪', '毛子']
nofound, banned = [], []
for m, zh in tr.items():
    if m not in paths:
        nofound.append(m); continue
    for b in BAN:
        if b in zh:
            banned.append((m, b))
print('映射缺失 %d %s' % (len(nofound), nofound[:5]))
print('禁用词 %d %s' % (len(banned), banned[:5]))

# 组装：rel -> {line_idx: {col: zh}}
plan = {}
for m, zh in tr.items():
    ent = paths.get(m)
    if not ent:
        continue
    for rel, li, col in ent['locs']:
        plan.setdefault(rel, {}).setdefault(li, {})[col] = (m, zh)

print('涉及 %d 个文件' % len(plan))

done = miss = 0
if APPLY:
    for rel, linemap in plan.items():
        dst = os.path.join(ROOT, rel)
        raw = open(dst, 'rb').read()
        if raw[:2] != b'\xff\xfe':
            print('!! 非 UTF-16LE', rel); miss += 1; continue
        lines = raw.decode('utf-16').split('\r\n')
        ok = True
        for li, colmap in linemap.items():
            if li >= len(lines):
                print('!! 行号越界', rel, li); ok = False; break
            cols = lines[li].split('\t')
            for col, (m, zh) in colmap.items():
                if col >= len(cols):
                    print('!! 列号越界', rel, li, col); ok = False; break
                if cols[col].strip() != src[m]:
                    print('!! 原文不符 %s L%d C%d\n   实际 %r\n   期望 %r'
                          % (rel, li, col, cols[col][:60], src[m][:60]))
                    ok = False; break
                cols[col] = zh
            if not ok:
                break
            lines[li] = '\t'.join(cols)
        if not ok:
            miss += 1; continue
        out = ('\ufeff' + '\r\n'.join(lines)).encode('utf-16-le')
        bk = os.path.join(BACKUP, rel)
        if not os.path.exists(bk):
            os.makedirs(os.path.dirname(bk), exist_ok=True)
            shutil.copy2(dst, bk)
        open(dst, 'wb').write(out)
        done += 1
    print('已部署 %d 个文件（失败 %d）' % (done, miss))
else:
    print('[DRY-RUN] 未落盘。')
