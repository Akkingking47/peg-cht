# -*- coding: utf-8 -*-
"""
MAPNAMES.STR 河流名汉化（记录 14+）

★ 文件结构（2026-09-21 完全破译，两种格式并存，必须先探测）

  头部：2 字节小端计数 N
  主体：N × 20 字节定长记录

  格式 A（绝大多数 game，36/38 个）—— **NUL 终止 + NUL 补满**
      记录 = 名称字节 + '\x00' + 若干 '\x00' 补满到 20 字节
      ⇒ 取名称：`blk.split(b'\x00')[0]`
      可容纳最多 19 字节名称。

  格式 B（仅 Cyber General）—— **空格补位 + 尾部 3 字节排序键**
      记录 = 名称 + 半角空格补位到 17 字节 + 3 字节排序键
      ⇒ 取名称：`blk[:17].rstrip(b' ')`
      可容纳最多 17 字节名称；后 3 字节**必须原样保留**。
      ⚠️ 用格式 A 的方法读它，会把排序键粘进名称，
         看出一堆假的"跨记录碎片"（'a River'、'e River' …）——
         那是排序键被误当名称的产物，不是原文真的被截断。

  判据：统计记录中"含连续空格"与"以 \\x00\\x00 结尾"的比例，谁多算谁。

  两种格式下，记录 0..13 均为通用地形名（已汉化）；14+ 混合河流名/地名/区域名。

写入编码
--------
  **UTF-8**（不是 GBK）。该进程 exe 内嵌 manifest 设了 activeCodePage=UTF-8，
  引擎按 CP_ACP=65001 解析这些单字节串。写 GBK 会显示为方框。

长度约束
--------
  格式 A：译名 UTF-8 字节数 <= 19（最多 6 汉字 = 18B）
  格式 B：译名 UTF-8 字节数 <= 17（最多 5 汉字 = 15B）—— 后 3 字节是排序键
  脚本按每个文件的实际格式分别校验，超长只报告不写入。
"""

import glob
import os
import struct
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), 'work', 'mapnames'))
from river_zh import RIVER, KEEP  # noqa: E402

REC = 20
FIRST_CUSTOM = 14          # 0..13 是通用地形名
ROOT = r'D:\PGForever1.021'

FMT_A, FMT_B = 'A(NUL补满)', 'B(空格+3字节键)'


def find_files():
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
    """按记录内容判断是格式 A 还是 B。"""
    sp = nul = 0
    for i in range(FIRST_CUSTOM, min(n, FIRST_CUSTOM + probe)):
        off = 2 + i * REC
        if off + REC > len(raw):
            break
        blk = raw[off:off + REC]
        body = blk.replace(b'\x00', b'')
        if b'  ' in body:
            sp += 1
        if blk[-1] == 0 and blk[-2] == 0:
            nul += 1
    return (FMT_B, sp) if sp > nul else (FMT_A, nul)


def name_of(blk, fmt):
    """取出记录的可见名称，以及（格式 B 的）3 字节排序键。"""
    if fmt == FMT_A:
        return blk.split(b'\x00')[0], b''
    return blk[:REC - 3].rstrip(b' '), blk[REC - 3:]


def maxlen_of(fmt):
    return (REC - 1) if fmt == FMT_A else (REC - 3)


def patch_file(path, table, dry=True):
    raw = bytearray(open(path, 'rb').read())
    size0 = len(raw)
    n = struct.unpack_from('<H', raw, 0)[0]
    fmt, score = detect_format(raw, n)
    limit = maxlen_of(fmt)

    hits, longs = [], []
    for i in range(FIRST_CUSTOM, n):
        off = 2 + i * REC
        if off + REC > len(raw):
            break
        blk = bytes(raw[off:off + REC])
        nm, key = name_of(blk, fmt)
        try:
            en = nm.decode('utf-8').strip()
        except UnicodeDecodeError:
            continue
        if not en or en in KEEP:
            continue
        zh = table.get(en)
        if not zh:
            continue

        enc = zh.encode('utf-8')
        if len(enc) > limit:
            longs.append((en, zh, len(enc)))
            continue

        if fmt == FMT_A:
            newblk = enc + b'\x00' * (REC - len(enc))
        else:
            newblk = enc + b' ' * (REC - 3 - len(enc)) + key
        if len(newblk) != REC:
            longs.append((en, zh, len(newblk)))
            continue

        if blk != newblk:
            hits.append((en, zh))
            raw[off:off + REC] = newblk

    if not dry and hits:
        assert len(raw) == size0, '文件大小变化！'
        open(path, 'wb').write(bytes(raw))

    return size0, len(raw), fmt, hits, longs


def main():
    dry = '--apply' not in sys.argv
    files = find_files()
    print('目标 %d 个文件 | %s | 译表 %d 条\n'
          % (len(files), 'DRY-RUN（不改盘）' if dry else '★ APPLY（写盘）', len(RIVER)))

    tot_hit = tot_long = 0
    for f in files:
        game = os.path.basename(os.path.dirname(os.path.dirname(f)))
        s0, s1, fmt, hits, longs = patch_file(f, RIVER, dry=dry)
        tot_hit += len(hits)
        tot_long += len(longs)
        if not hits and not longs:
            continue
        sizeok = 'OK ' if s0 == s1 else 'SIZE!'
        print('%-6s %-34s %-16s 改 %3d  超长 %2d'
              % (sizeok, game, fmt, len(hits), len(longs)))
        for en, zh, ln in longs[:6]:
            print('        ⚠️ 超长: %-22s -> %s (%dB)' % (en, zh, ln))

    print('\n合计：替换 %d 处，超长 %d 处' % (tot_hit, tot_long))
    if dry:
        print('（DRY-RUN，未写盘；加 --apply 落盘）')


if __name__ == '__main__':
    main()
