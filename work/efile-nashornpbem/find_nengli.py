# -*- coding: utf-8 -*-
"""Locate the '能力' line in strings-zh.txt and compare with ES/DE and the
built-in English table inside OpenGen.exe (916 x 0x100 at file offset 0x5857A0)."""
import io
import struct

Z = r"D:/OpenPG2/OPENGUI/strings-zh.txt"
ES = r"D:/OpenPG2/OPENGUI/strings-es.txt"
DE = r"D:/OpenPG2/OPENGUI/strings-de.txt"
EXE = r"D:/OpenPG2/OpenGen.exe"

zh = io.open(Z, encoding="gbk", errors="replace", newline="").read().split("\r\n")
print("strings-zh.txt lines = %d" % len(zh))
hits = [i for i, s in enumerate(zh) if "能力" in s]
print("lines containing 能力:", [i + 1 for i in hits])

def getline(path, n):
    try:
        L = io.open(path, encoding="gbk", errors="replace", newline="").read().split("\r\n")
        return L[n] if n < len(L) else "<oob>"
    except Exception as e:
        return "<err %s>" % e

# built-in English table in the exe
b = open(EXE, "rb").read()
FO = 0x5857A0
def enline(n):
    off = FO + n * 0x100
    raw = b[off:off + 0x100].split(b"\0")[0]
    return raw.decode("latin-1")

for i in hits:
    print("=" * 70)
    print("line %d" % (i + 1))
    print("  EN(exe) : %r" % enline(i))
    print("  ES      : %r" % getline(ES, i))
    print("  DE      : %r" % getline(DE, i))
    print("  ZH      : %r" % zh[i])

# also show a window around the first hit
if hits:
    i = hits[0]
    print("=" * 70)
    print("context (line no : EN | ZH):")
    for k in range(max(0, i - 6), min(len(zh), i + 5)):
        print("  %4d | %-34r | %r" % (k + 1, enline(k), zh[k]))
