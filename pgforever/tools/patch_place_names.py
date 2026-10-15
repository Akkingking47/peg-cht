# -*- coding: utf-8 -*-
"""MAPNAMES.STR 地名（城市名）汉化 —— 全部 38 个文件、记录 14+

★ 三种文件格式并存，逐一探测（详见 work/mapnames/place_tools.py）

  头部：2 字节小端计数 N；主体：N × 20 字节定长记录
  记录 0..13 = 通用地形名（已汉化，本脚本跳过）；14+ = 河流名 / 地名 / 区域名

  格式 A（36 个 file）—— **NUL 终止 + NUL 补满**
      记录 = 名称 + '\x00' + 若干 NUL 补满 20B
      取名称：blk.split(b'\x00')[0]；上限 19B（6 汉字）

  格式 B（0 个，历史误判，保留探测逻辑）—— 空格补位 + 3 字节排序键

  格式 D（Cyber General，1 个）—— **20B 定长记录槽**（含一处 +17 偏移）
      与格式 A 同为定长记录，差别仅在槽起点网格：
        k <= 95 : 20*k ;  k >= 96 : 1937 + 20*(k-96)
      （记录 95 'Proz' 被原作者写成 37B，其后整体后移 17B）
      槽内左对齐 + 空格补满；上限 19B（6 汉字）
      ⚠️ 曾误判为「连续名称缓冲区」，已由网格法 1700/1700 命中推翻

写入编码
--------
  **UTF-8**（不是 GBK）。该进程 exe 内嵌 manifest 设了 activeCodePage=UTF-8，
  引擎按 CP_ACP=65001 解析这些单字节串。写 GBK 会显示为方框。

长度约束
--------
  统一 ≤ 19 字节（最多 6 汉字 = 18B），三种格式均安全。
  超长条目只报告不写入（其原文保持英文）。

用法
----
  python patch_place_names.py           # DRY-RUN，只报告
  python patch_place_names.py --apply   # 落盘
"""

import glob
import os
import struct
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), 'work', 'mapnames'))

from river_zh import RIVER, KEEP          # noqa: E402
import cyber_names as CYBER               # noqa: E402

REC = 20
FIRST_CUSTOM = 14          # 0..13 是通用地形名
ROOT = r'D:\PGForever1.021'
LIMIT = 19                 # 名称 UTF-8 字节上限（6 汉字）

FMT_A = 'A(NUL补满)'
FMT_B = 'B(空格+键)'
FMT_D = 'D(连续流)'


def load_place_table():
    """汇总 place_*.py 的全部译表"""
    tbl = {}
    here = os.path.join(os.path.dirname(_HERE), 'work', 'mapnames')
    for f in sorted(glob.glob(os.path.join(here, 'place_*.py'))):
        base = os.path.basename(f)
        if base in ('place_tools.py', 'place_mojibake.py'):
            continue
        ns = {}
        exec(open(f, encoding='utf-8').read(), ns)
        for k, v in ns.items():
            if k.isupper() and isinstance(v, dict):
                tbl.update(v)
    return tbl


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
    """→ FMT_A / FMT_B / FMT_D"""
    # 格式 D 判据：按「20B 严格网格」抽取时，中部会出现大量「左对齐但含内部
    # 长空格」的残片（源自 +17 偏移），而格式 A 不会。
    fake = 0
    for i in range(FIRST_CUSTOM, min(n, FIRST_CUSTOM + probe)):
        off = 2 + i * REC
        if off + REC > len(raw):
            break
        blk = bytes(raw[off:off + REC])
        if b'\x00' in blk:
            continue
        s = blk.rstrip(b' ')
        if b'  ' in s and s[-1:].isalpha():
            fake += 1
    if fake > 50:
        return FMT_D

    sp = nul = 0
    for i in range(FIRST_CUSTOM, min(n, FIRST_CUSTOM + probe)):
        off = 2 + i * REC
        if off + REC > len(raw):
            break
        blk = bytes(raw[off:off + REC])
        body = blk.replace(b'\x00', b'')
        if b'  ' in body:
            sp += 1
        if blk[-1] == 0 and blk[-2] == 0:
            nul += 1
    return FMT_B if sp > nul else FMT_A


def name_of(blk, fmt):
    if fmt == FMT_A:
        return blk.split(b'\x00')[0], b''
    return blk[:REC - 3].rstrip(b' '), blk[REC - 3:]


def patch_a_b(raw, table, fmt, dry):
    """格式 A / B：逐 20B 记录替换"""
    n = struct.unpack_from('<H', raw, 0)[0]
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
        if len(enc) > LIMIT:
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
    return hits, longs


def patch_d(raw, table, dry):
    """格式 D（Cyber General）：**20B 定长记录槽**，按槽逐条改写

    槽起点网格见 cyber_names.rec_start()：
        k <= 95  : 20*k
        k >= 96  : 1937 + 20*(k-96)      （唯一 +17 偏移，源自记录 95 'Proz' 占 37B）

    每条槽内左对齐放名称、空格补满。中文 ≤19B 即可安全写入，
    **不需要**与英文等长（此前用「等长替换」是误把该文件当成连续缓冲区）。
    """
    hits, longs = [], []
    for k, off, en in CYBER.slots(raw, first=FIRST_CUSTOM):
        if en in KEEP or len(en) < 2:
            continue
        zh = table.get(en)
        if not zh:
            continue
        enc = zh.encode('utf-8')
        slen = CYBER.slot_len(k)
        if len(enc) > LIMIT or len(enc) + 1 > slen:
            longs.append((en, zh, len(enc)))
            continue
        blk = bytes(raw[off:off + REC])
        cur = blk.split(b'\x00')[0].rstrip(b' ')
        if cur != en.encode('latin1', 'ignore'):
            continue                     # 实读名称与预期不符 → 不动
        newblk = enc + b' ' * (REC - len(enc))
        if blk == newblk:
            continue
        hits.append((en, zh))
        if not dry:
            raw[off:off + REC] = newblk
    return hits, longs


def patch_file(path, table, dry=True):
    raw = bytearray(open(path, 'rb').read())
    size0 = len(raw)
    n = struct.unpack_from('<H', raw, 0)[0]
    fmt = detect_format(raw, n)

    if fmt == FMT_D:
        hits, longs = patch_d(raw, table, dry)
    else:
        hits, longs = patch_a_b(raw, table, fmt, dry)

    if not dry and hits:
        assert len(raw) == size0, '文件大小变化！'
        open(path, 'wb').write(bytes(raw))

    return size0, len(raw), fmt, hits, longs

def main():
    dry = '--apply' not in sys.argv
    table = load_place_table()
    table.update(RIVER)                       # 河流名并入（同属记录 14+）
    files = find_files()
    print('目标 %d 个文件 | %s | 译表 %d 条\n'
          % (len(files), 'DRY-RUN（不改盘）' if dry else '★ APPLY（写盘）', len(table)))

    tot_hit = tot_long = 0
    for f in files:
        game = os.path.basename(os.path.dirname(os.path.dirname(f)))
        s0, s1, fmt, hits, longs = patch_file(f, table, dry=dry)
        tot_hit += len(hits)
        tot_long += len(longs)
        if not hits and not longs:
            continue
        sizeok = 'OK ' if s0 == s1 else 'SIZE!'
        print('%-6s %-34s %-12s 改 %4d  超长 %2d'
              % (sizeok, game, fmt, len(hits), len(longs)))
        for en, zh, ln in longs[:5]:
            print('        ⚠️ 超长: %-22s -> %s (%dB)' % (en, zh, ln))

    print('\n合计：替换 %d 处，超长 %d 处' % (tot_hit, tot_long))
    if dry:
        print('（DRY-RUN，未写盘；加 --apply 落盘）')


if __name__ == '__main__':
    main()
