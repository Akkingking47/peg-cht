# -*- coding: utf-8 -*-
"""定点修复 TEXT-ZH 文本里的 cp1252 残留（假汉字 / 非法单字节 / 连续变音符）。

判定（逐字节扫描）：
  1. 双字节且能按 GBK 解出 **GB2312 字** ⇒ 真中文，保留。
  2. 双字节解出的字非 GB2312，但 ±6 字节内有其它 GB2312 字 ⇒ **GBK 生僻汉字**
     （焗/鵄/瞭…），保留。
  3. 其余双字节 ⇒ cp1252 残留：把每字节按 cp1252 折成 ASCII（变音符去掉），
     如 `F6 62`→`ob`、`FA F1`→`un`、`E9 65`→`ee`。
  4. 无法成对的孤立高位字节 ⇒ 按 cp1252 折 ASCII（`FC`→`u`）。

用法： python fix_mojibake.py             # dry-run
       python fix_mojibake.py --apply     # 写盘（备份 backup/mojibake-before/）
"""
import os, sys, glob, shutil, unicodedata

GAME = r'D:\OpenPG2'
ROOT = r'D:\DSH\军事游戏汉化'
BK = os.path.join(ROOT, 'backup', 'mojibake-before')
EFILES = ['EFILE_OLGWW2', 'EFILE_NASHORNPBEM', 'EFILE_OPENPG']


def gb2312(ch):
    try:
        ch.encode('gb2312'); return True
    except Exception:
        return False


def ascii_of(b):
    """cp1252 单字节 → 去变音符的 ASCII（可能为空串）。"""
    try:
        return unicodedata.normalize('NFKD', bytes([b]).decode('cp1252')).encode('ascii', 'ignore').decode()
    except Exception:
        return ''


def is_trail(b):
    return (0x40 <= b <= 0x7E) or (0x80 <= b <= 0xFE)


def near_cjk(d, i, k=6):
    n = len(d)
    for j in range(max(0, i - k), min(n - 1, i + 2 + k)):
        if i - 1 <= j <= i + 1:      # 排除与自身重叠的字节对
            continue
        b = d[j]
        if 0x81 <= b <= 0xFE and j + 1 < n and is_trail(d[j + 1]):
            try:
                if gb2312(d[j:j + 2].decode('gbk')):
                    return True
            except Exception:
                pass
    return False


def plan_fix(d):
    """返回 [(off, oldbytes, newbytes, kind, note)]，offset 升序。"""
    out, i, n = [], 0, len(d)
    while i < n:
        b = d[i]
        if b < 0x80:
            i += 1; continue
        if 0x81 <= b <= 0xFE and i + 1 < n and is_trail(d[i + 1]):
            pair = d[i:i + 2]
            try:
                ch = pair.decode('gbk')
            except Exception:
                ch = None
            if ch and gb2312(ch):
                i += 2; continue
            if ch and near_cjk(d, i):
                i += 2; continue
            b2 = d[i + 1]
            a1 = ascii_of(b)
            a2 = ascii_of(b2) if b2 >= 0x80 else chr(b2)
            if a1 and a2:
                out.append((i, pair, (a1 + a2).encode('ascii'), 'pair',
                            '%s|%s' % (hex(b), hex(b2))))
                i += 2; continue
            if a1:
                out.append((i, bytes([b]), a1.encode('ascii'), 'lone', hex(b)))
                i += 1; continue
            out.append((i, pair, None, 'skip', '%s|%s' % (hex(b), hex(b2))))
            i += 2; continue
        a1 = ascii_of(b)
        if a1:
            out.append((i, bytes([b]), a1.encode('ascii'), 'lone', hex(b)))
        else:
            out.append((i, bytes([b]), None, 'skip', hex(b)))
        i += 1
    return out


def apply_fix(d, plan):
    buf, last = bytearray(), 0
    for item in plan:
        off, old, new = item[0], item[1], item[2]
        if new is None:
            continue
        buf += d[last:off] + new
        last = off + len(old)
    buf += d[last:]
    return bytes(buf)


def line_of(d, off):
    s = d.rfind(b'\n', 0, off) + 1
    e = d.find(b'\n', off)
    if e < 0:
        e = len(d)
    return d[s:e].decode('gbk', 'replace').strip()


def main():
    apply = '--apply' in sys.argv
    files = []
    for ef in EFILES:
        root = os.path.join(GAME, ef, 'TEXT-ZH')
        if os.path.isdir(root):
            for p in glob.glob(os.path.join(root, '**', '*'), recursive=True):
                if os.path.isfile(p) and os.path.splitext(p)[1].lower() in ('.txt', '.ply'):
                    files.append((ef, p))
    total, touched, skipped = 0, 0, 0
    for ef, p in files:
        d = open(p, 'rb').read()
        pl = plan_fix(d)
        if not pl:
            continue
        rel = os.path.relpath(p, os.path.join(GAME, ef))
        print('\n== %s / %s  (%d 处) ==' % (ef, rel, len(pl)))
        for off, old, new, kind, note in pl:
            if new is None:
                print('   [%-4s] %-8s -> ???   | %s' % (kind, note, line_of(d, off)[:80]))
                skipped += 1
                continue
            print('   [%-4s] %-8s -> %-8s | %s' % (kind, note, new.decode('ascii', 'replace'), line_of(d, off)[:80]))
        total += len([x for x in pl if x[2] is not None])
        if apply:
            nd = apply_fix(d, pl)
            os.makedirs(BK, exist_ok=True)
            dst = os.path.join(BK, ef + '__' + rel.replace('\\', '_'))
            if not os.path.exists(dst):
                shutil.copy2(p, dst)
            tmp = p + '.new'
            open(tmp, 'wb').write(nd)
            assert open(tmp, 'rb').read() == nd
            os.replace(tmp, p)
            touched += 1
            print('   -> 写回 %d B -> %d B  (备份 %s)' % (len(d), len(nd), os.path.basename(dst)))
    print('\n合计可修 %d 处，跳过 %d 处，涉及 %d 文件%s' % (total, skipped, touched, '' if apply else '（dry-run，未写盘）'))


if __name__ == '__main__':
    main()
