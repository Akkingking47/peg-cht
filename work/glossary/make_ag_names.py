# -*- coding: utf-8 -*-
r"""
EFILE_AG\names.txt 汉化生成器。

口径（用户裁定：全部音译，层内一律中文、不得中英混排）：
  * Classified* 是 mod 作者的**占位标记**（1085 行 / 34 个唯一值），不是人名 ⇒ 保留原文
  * 其余按 ag-names-map.tsv 音译：
      - 知名古人用通行译名（汉尼拔/亚历山大/大流士/薛西斯/维钦托利/汉谟拉比…）
      - 中国年号/帝名用汉字本体（永和/元嘉/建宁/刘宏/刘协…），不音译
      - 皮克特 "X mac Y"（mac=…之子）、罗马三名法按词整体定名
  * 出稿 GBK / 无 BOM / CRLF；逐行对齐；未命中必须报错
用法：python make_ag_names.py [--apply]
"""
import os, io, sys, shutil, collections

GAME = r'D:\OpenPG2'
SRC = os.path.join(GAME, 'EFILE_AG')
DST = os.path.join(SRC, 'TEXT-ZH')
BK = r'D:\DSH\军事游戏汉化\backup\ag-names-before'
MAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ag-names-map.tsv')


def load_map():
    d = {}
    # utf-8-sig：写入工具可能带上 BOM，用 -sig 自动剥离，否则首行键会变成 '\ufeffAbalabius'
    with io.open(MAP, encoding='utf-8-sig', newline='') as f:
        for ln in f:
            parts = ln.rstrip('\r\n').split('\t')
            if len(parts) < 2:
                continue
            k, v = parts[0].strip(), parts[1].strip()
            if k:
                d[k] = v
    return d


def main():
    apply_ = '--apply' in sys.argv
    table = load_map()
    print('映射表 %d 条' % len(table))

    raw = open(os.path.join(SRC, 'names.txt'), 'rb').read()
    lines = raw.decode('cp1252').replace('\r\n', '\n').split('\n')
    out = []
    miss = collections.Counter()
    kept = collections.Counter()
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith('*'):
            out.append(ln)
            continue
        if s.startswith('Classified'):
            # 占位标记 ⇒ 保留原文
            out.append(ln)
            kept[s] += 1
            continue
        z = table.get(s)
        if z is None:
            out.append(ln)
            miss[s] += 1
        else:
            out.append(ln.replace(s, z))

    print('names.txt %d 行  占位保留 %d 行/%d 种  未命中 %d 种/%d 处'
          % (len(out), sum(kept.values()), len(kept), len(miss), sum(miss.values())))
    for k, v in miss.most_common(60):
        print('    x%-4d %s' % (v, k))
    if miss:
        print('\n* 存在未命中，未写盘')
        return
    if not apply_:
        print('\n（dry-run，未写盘）')
        return

    os.makedirs(BK, exist_ok=True)
    os.makedirs(DST, exist_ok=True)
    data = '\r\n'.join(out).encode('gbk')
    tmp = os.path.join(DST, 'names.txt.new')
    open(tmp, 'wb').write(data)
    assert open(tmp, 'rb').read() == data, '回读不一致'
    dst = os.path.join(DST, 'names.txt')
    if os.path.exists(dst) and not os.path.exists(os.path.join(BK, 'names.txt')):
        shutil.copy2(dst, os.path.join(BK, 'names.txt'))
    os.replace(tmp, dst)
    print('已写出 names.txt  %d B  CRLF=%d' % (len(data), data.count(b'\r\n')))


if __name__ == '__main__':
    main()
