# -*- coding: utf-8 -*-
"""BASEKORP `.xsch`（分支选择屏）译文装配器。

src **一律从实盘解析导出**（不经手抄），dst 由下表给出。
换行在 TSV 里用 `<CRLF>` 承载 —— xsch.py 的 unesc() 第一优先把它还原为真实 CRLF，
比裸 `\n` 更不易被 Python 的通用换行模式吃掉。

★ 槽 A 原文尾部**自带 CRLF**（`Party in Berlin\r\n` / `Caucasus Winter Camp\r\n` …）：
  那是作者录入噪音，但字节上落在定长 104B 槽内 ⇒ 按铁律 1「只换人类可读文字」**原样保留**。

译名依据（真源 glossary/standard-glossary.tsv，LOCKED）：
  Georgetown -> 乔治市（OLGWW2 + OPENPG 双源）｜Newfoundland -> 纽芬兰｜Blitzkrieg -> 闪电战
  Caucasus -> 高加索（crossmap）｜Berlin -> 柏林
  St.John's -> 圣约翰斯（**区别于** crossmap 的 `St John`->圣约翰：那是另一座城市，英文成分不同）
  GHQ -> 总司令部（真源/crossmap 均无先例，本次新定）
"""
import os
import sys
import io

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'xsch'))
import xsch  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'basekorp-xsch.tsv')
BASE = os.path.join(xsch.GAME, 'EFILE_BASEKORP', 'SCENARIO')

YES_SPEC = '是的，我喜欢特别行动，我自愿报名！<CRLF>'
NO = '不，谢谢，我要享受应得的休整'      # 调用处自行补 '！'

# (file, idx) -> (槽A译文, 槽B译文)；None 表示该槽不译（无此项）
ZH = {
    ('bkbkchoice.xsch', 0): ('闪电战狂热！！！',
                             '是的，我愿为祖国而战，我自愿报名！<CRLF>'),
    ('bkbkchoice.xsch', 1): ('柏林的派对<CRLF>',
                             NO + '！ <CRLF><CRLF>这将跳过5个场景，并于1942年10月重新开始。'),
    ('bn10c21.xsch', 0): ('柏林总司令部', YES_SPEC),
    ('bn10c21.xsch', 1): ('高加索冬季营地<CRLF>', NO + '！'),
    ('bn10c31.xsch', 0): ('柏林总司令部', YES_SPEC),
    ('bn10c31.xsch', 1): ('英格兰冬季营地<CRLF>', NO + '！'),
    ('bn10c40.xsch', 0): ('英属圭亚那乔治市', YES_SPEC),
    ('bn10c40.xsch', 1): ('美国冬季营地<CRLF>', NO + '！'),
    ('bn10c42.xsch', 0): ('纽芬兰圣约翰斯', YES_SPEC),
    ('bn10c42.xsch', 1): ('美国冬季营地<CRLF>', NO + '！'),
}


def main():
    files = sorted(f for f in os.listdir(BASE) if f.lower().endswith('.xsch'))
    rows = []
    for f in files:
        hdr, recs = xsch.parse(xsch._load(os.path.join(BASE, f)))
        for r in recs:
            zh = ZH.get((f, r['idx']))
            if zh is None:
                print('  ⚠️ 未定义译文：%s rec%d' % (f, r['idx']))
                continue
            a_zh, b_zh = zh
            a_src = '\x00'.join(xsch._decode_slot_a(r['A']))
            b_src = r['B'].decode('cp1252')
            if not b_src:
                print('  ⚠️ 槽B 为空：%s rec%d' % (f, r['idx']))
                continue
            rows.append((f, r['idx'], 'A', a_src, a_zh))
            rows.append((f, r['idx'], 'B', b_src, b_zh))

    def esc(s):
        return s.replace('\r\n', '<CRLF>')

    with io.open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('file\tidx\tfield\tsrc\tdst\n')
        for f, i, fld, src, dst in rows:
            fh.write('%s\t%d\t%s\t%s\t%s\n' % (f, i, fld, esc(src), esc(dst)))
    print('译文表 %d 条（%d 文件）-> %s' % (len(rows), len(files), OUT))
    # 槽 A 定长 104B 硬约束自检
    worst = 0
    for f, i, fld, src, dst in rows:
        if fld != 'A':
            continue
        n = len(dst.replace('<CRLF>', '\r\n').encode('gbk'))
        worst = max(worst, n)
        if n > xsch.SLOT_A:
            print('  ❌ 槽A 超长 %s rec%d: %dB' % (f, i, n))
    print('槽A 译文最长 %dB / 上限 %dB' % (worst, xsch.SLOT_A))


if __name__ == '__main__':
    main()
