# -*- coding: utf-8 -*-
r"""
全库 .pgscn 场景文件盘点 + 待译字段导出。

结构（UTF-16LE + BOM，CRLF 分隔）：
    Name\t<场景名>
    Description\t<描述（可能是多段，含 \n 转义）>
其余为纯数值/座标配置，绝不改动。

输出：
    work/scn-all/index.json   每个文件的 name/desc/en
    work/scn-all/src*.json    分批待译
    work/scn-all/paths.json   唯一内容 → 文件路径列表
"""
import os, json, hashlib, collections

ROOT = r'D:\PGForever1.021'
OUT = r'D:\DSH\军事游戏汉化\pgforever\work\scn-all'
os.makedirs(OUT, exist_ok=True)

files = []
for dp, dn, fn in os.walk(ROOT):
    for f in fn:
        if f.lower().endswith('.pgscn'):
            files.append(os.path.join(dp, f))
files.sort()
print('共 %d 个 .pgscn' % len(files))

recs = []
bad = []
for p in files:
    raw = open(p, 'rb').read()
    if raw[:2] != b'\xff\xfe':
        bad.append((p, 'no-BOM')); continue
    t = raw.decode('utf-16')
    name = desc = None
    for line in t.split('\r\n'):
        if line.startswith('Name\t') and name is None:
            name = line.split('\t', 1)[1]
        elif line.startswith('Description\t') and desc is None:
            desc = line.split('\t', 1)[1]
    if name is None:
        bad.append((p, 'no-Name')); continue
    recs.append({'path': os.path.relpath(p, ROOT), 'raw': raw,
                 'name': name, 'desc': desc or ''})
print('有效 %d，异常 %d %s' % (len(recs), len(bad), [b[1] for b in bad][:6]))

# 已汉化判定（Name 含中文）
def zh(s):
    return any('\u4e00' <= c <= '\u9fff' for c in s)
done = [r for r in recs if zh(r['name'])]
todo = [r for r in recs if not zh(r['name'])]
print('已汉化 %d / 待汉化 %d' % (len(done), len(todo)))

# 按 (name,desc) 去重
h2 = {}
order = []
for r in todo:
    key = (r['name'], r['desc'])
    h = hashlib.md5(('\x00'.join(key)).encode('utf-8')).hexdigest()
    if h not in h2:
        h2[h] = {'md5': h, 'name': r['name'], 'desc': r['desc'],
                 'first': r['path'], 'paths': []}
        order.append(h)
    h2[h]['paths'].append(r['path'])

print('待译唯一内容 %d 条，覆盖 %d 个文件'
      % (len(order), sum(len(h2[h]['paths']) for h in order)))

# 导出
B = 100
nb = 0
for i in range(0, len(order), B):
    nb += 1
    chunk = order[i:i+B]
    json.dump([{'id': h[:10], 'md5': h, 'src': h2[h]['first'],
                'name': h2[h]['name'], 'desc': h2[h]['desc']} for h in chunk],
              open(os.path.join(OUT, 'src%02d.json' % nb), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
json.dump({h: h2[h]['paths'] for h in order},
          open(os.path.join(OUT, 'paths.json'), 'w', encoding='utf-8'),
          ensure_ascii=False)
print('→ %d 批，paths.json' % nb)

# 样本
print('\n=== 样本（前 5 条待译）===')
for h in order[:5]:
    print('\n-- %s' % h2[h]['first'])
    print('   Name: %s' % h2[h]['name'])
    print('   Desc: %s' % h2[h]['desc'][:220])
