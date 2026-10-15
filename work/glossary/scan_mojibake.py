# -*- coding: utf-8 -*-
"""扫描 TEXT-ZH 文本里的 cp1252 残留（假汉字 / 非法 GBK 单字节）。
原理：真中文(GB2312)字 = 双字节且两字节都在 GB2312 区；cp1252 单字节被 GBK 吞并后
      产生的字**不在 GB2312 字库**，且可反推为 (Latin-1 字母 + ASCII 字母)。
用法：python scan_mojibake.py [--all]   默认只扫已汉化 3 个 efile。
"""
import os, sys, glob, collections, unicodedata

GAME = r'D:\OpenPG2'
EFILES = ['EFILE_OLGWW2', 'EFILE_NASHORNPBEM', 'EFILE_OPENPG']

def gb2312(ch):
    try:
        ch.encode('gb2312'); return True
    except Exception:
        return False

def ascii_of(ch):
    """把 Latin-1 带变音符字母折成 ASCII（é→e, ü→u, ñ→n …）。"""
    return unicodedata.normalize('NFKD', ch).encode('ascii', 'ignore').decode('ascii')

def is_trail(b):
    return (0x40 <= b <= 0x7E) or (0x80 <= b <= 0xFE)

def scan_bytes(d):
    """返回 (fixes, bads)。fixes=[(off,len,repl,orig,char)]；bads=[(off,byte)]"""
    fixes, bads, i, n = [], [], 0, len(d)
    while i < n:
        b = d[i]
        if b < 0x80:
            i += 1; continue
        if 0x81 <= b <= 0xFE and i + 1 < n and is_trail(d[i+1]):
            pair = d[i:i+2]
            try:
                ch = pair.decode('gbk')
            except Exception:
                ch = None
            if ch and ch not in (' ',) and not gb2312(ch):
                # 反推：b1 视作 cp1252 字母，b2 视作 ASCII
                try:
                    c1 = bytes([b]).decode('cp1252')
                except Exception:
                    c1 = None
                c2 = chr(d[i+1]) if 0x20 <= d[i+1] <= 0x7E else None
                if c1 and c2 and ascii_of(c1):
                    repl = (ascii_of(c1) + c2).encode('ascii')
                    fixes.append((i, 2, repl, pair, ch))
                    i += 2; continue
                # 不能反推成 ASCII ⇒ 可能真是生僻汉字，跳过
                i += 2; continue
            i += 2; continue
        # 非法单字节
        bads.append((i, b))
        i += 1
    return fixes, bads

def main():
    files = []
    for ef in EFILES:
        root = os.path.join(GAME, ef, 'TEXT-ZH')
        if os.path.isdir(root):
            for p in glob.glob(os.path.join(root, '**', '*'), recursive=True):
                if os.path.isfile(p) and os.path.splitext(p)[1].lower() in ('.txt', '.ply'):
                    files.append((ef, p))
    print('扫描 %d 个文件' % len(files))
    tot_f = tot_b = 0
    for ef, p in files:
        d = open(p, 'rb').read()
        f, b = scan_bytes(d)
        if f or b:
            rel = os.path.relpath(p, os.path.join(GAME, ef))
            print('\n%-18s %s' % (ef, rel))
            for off, ln, repl, orig, ch in f:
                print('   假汉字 off=%-7d %s (U+%04X) -> %s' % (off, orig.hex(), ord(ch), repl.decode()))
            for off, by in b:
                print('   非法单字节 off=%-7d 0x%02X' % (off, by))
            tot_f += len(f); tot_b += len(b)
    print('\n合计：假汉字 %d 处 / 非法单字节 %d 处' % (tot_f, tot_b))

if __name__ == '__main__':
    main()
