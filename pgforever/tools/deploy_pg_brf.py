# -*- coding: utf-8 -*-
r"""
校验并部署 PG 战役简报译文：
- 汇总 batch1..6.zh.json，与原文逐条比对（file 必须一一对应）
- 校验：条数、file、含 <p>、长度 ≤ 原文 70%、无残留英文句子
- 写回 D:\PGForever1.021\PG\Scenario\<file>，UTF-8 无 BOM（原文件风格）
"""
import json
import os
import re

SRC = r'D:\DSH\军事游戏汉化\pgforever\backup\origin\PG\Scenario'
BRFDIR = r'D:\DSH\军事游戏汉化\pgforever\work\pg\brf'
DST = r'D:\PGForever1.021\PG\Scenario'
REPORT = r'D:\DSH\军事游戏汉化\pgforever\work\pg\brf\deploy-report.txt'

# 汇总译文
zh_map = {}
dups = []
for n in range(1, 7):
    p = os.path.join(BRFDIR, 'batch%d.zh.json' % n)
    if not os.path.exists(p):
        print('!! 缺 %s' % p)
        continue
    for it in json.load(open(p, encoding='utf-8')):
        f = it.get('file')
        z = (it.get('zh') or '').strip()
        if f in zh_map and zh_map[f] != z:
            dups.append(f)
        zh_map[f] = z
print('汇总译文 %d 条（重复定义 %d）' % (len(zh_map), len(dups)))

src_files = sorted(f for f in os.listdir(SRC) if f.lower().endswith('.pgbrf'))
print('原文 %d 个' % len(src_files))

missing = [f for f in src_files if f not in zh_map or not zh_map[f]]
print('未译 / 空译文: %d %s' % (len(missing), missing[:8]))

# 禁用词
BAN = ['支那', '鬼子', '伪军', '共匪', '毛子']

over, bad_tag, residual, banned = [], [], [], []
for f in src_files:
    if f not in zh_map or not zh_map[f]:
        continue
    en = open(os.path.join(SRC, f), 'rb').read().decode('utf-8', 'replace')
    zh = zh_map[f]
    # 长度
    if len(zh) > len(en) * 0.70:
        over.append((f, len(zh), len(en), round(len(zh) / len(en), 2)))
    # 标签
    if ('<p>' in en) and ('<p>' not in zh):
        bad_tag.append(f)
    # 禁用词
    for b in BAN:
        if b in zh:
            banned.append((f, b))
    # 残留英文句子：去掉标签/型号/已知保留项后仍含 3 个以上连续英文单词
    z2 = re.sub(r'<[^>]+>', ' ', zh)
    z2 = re.sub(r'[A-Za-z0-9\-/\.\(\)\"]+', ' ', z2)
    if re.search(r'\b[A-Za-z]{3,}\s+[A-Za-z]{3,}\s+[A-Za-z]{3,}', z2):
        residual.append(f)

print()
print('超长(>70%%): %d %s' % (len(over), over[:6]))
print('缺 <p>: %d %s' % (len(bad_tag), bad_tag[:6]))
print('禁用词: %d %s' % (len(banned), banned[:6]))
print('可疑残留英文: %d %s' % (len(residual), residual[:6]))

# 部署
done = 0
for f in src_files:
    z = zh_map.get(f)
    if not z:
        continue
    out = z
    if not out.endswith('\n'):
        out += '\r\n'
    open(os.path.join(DST, f), 'wb').write(out.encode('utf-8'))    # UTF-8 无 BOM
    done += 1
print()
print('已部署 %d / %d 个简报' % (done, len(src_files)))

with open(REPORT, 'w', encoding='utf-8') as fp:
    fp.write('简报部署校验报告\n')
    fp.write('译文 %d 条 / 原文 %d 个 / 已部署 %d\n\n' % (len(zh_map), len(src_files), done))
    fp.write('未译: %s\n' % missing)
    fp.write('超长(>70%%): %s\n' % over)
    fp.write('缺<p>: %s\n' % bad_tag)
    fp.write('禁用词: %s\n' % banned)
    fp.write('可疑残留英文: %s\n' % residual)
print('报告 -> %s' % REPORT)

print()
print('=== 抽查 3 条 ===')
for f in src_files[:2] + src_files[100:101]:
    if f in zh_map:
        print('--- %s' % f)
        print('  原文: %s' % open(os.path.join(SRC, f), 'rb').read().decode('utf-8', 'replace')[:100])
        print('  译文: %s' % zh_map[f][:100])
