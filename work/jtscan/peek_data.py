#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only peek at a data file: size, first bytes (hex), printable-ASCII
ratio, and decode attempts under several code pages. Helps decide whether a
file is plain text (localizable) and which encoding it uses."""
import sys

def main():
    path = sys.argv[1]
    with open(path, 'rb') as f:
        data = f.read()
    print("=== %s ===" % path)
    print("size: %d bytes" % len(data))
    head = data[:256]
    print("hex[0:64]: " + ' '.join('%02X' % b for b in head[:64]))
    # printable ascii ratio over whole file
    printable = sum(1 for b in data if 32 <= b <= 126 or b in (9,10,13))
    print("printable/control ratio: %.3f" % (printable/len(data) if data else 0))
    # null byte ratio (binary indicator)
    nulls = data.count(0)
    print("null byte ratio: %.3f" % (nulls/len(data) if data else 0))
    # decode attempts on first 200 bytes
    for enc in ('ascii','cp1252','cp1250','gbk','latin-1','utf-8'):
        try:
            s = data[:400].decode(enc)
            sample = ''.join(c if (32<=ord(c)<127 or c in '\t\r\n') else '·' for c in s)
            print("  decode %-8s OK : %s" % (enc, sample[:120]))
        except Exception as e:
            print("  decode %-8s FAIL: %s" % (enc, e))
    # show first ~40 lines as latin-1 to eyeball structure
    print("--- first lines (latin-1) ---")
    text = data.decode('latin-1', 'replace')
    for ln in text.splitlines()[:40]:
        print(ln[:160])

if __name__ == '__main__':
    main()
