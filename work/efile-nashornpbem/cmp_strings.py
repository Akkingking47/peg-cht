# -*- coding: utf-8 -*-
"""Compare strings-zh.txt against the official ES/DE translations line by line,
around the unit-ability legend (lines ~820-880)."""
import io

BASE = r"D:/OpenPG2/OPENGUI/"
FILES = ["strings-es.txt", "strings-de.txt", "strings-hu.txt", "strings-pl.txt", "strings-zh.txt"]

data = {}
for f in FILES:
    try:
        L = io.open(BASE + f, encoding="gbk", errors="replace", newline="").read().split("\r\n")
    except Exception as e:
        L = []
        print("ERR", f, e)
    data[f] = L
    print("%-18s lines=%d  empty=%d" % (f, len(L), sum(1 for x in L if x == "")))

# where do the ZH and ES line counts diverge?
zh = data["strings-zh.txt"]
es = data["strings-es.txt"]
print("\nzh=%d es=%d" % (len(zh), len(es)))

print("\n%-5s | %-40s | %-40s | %s" % ("line", "ES", "ZH", "flag"))
print("-" * 130)
for i in range(818, min(900, max(len(zh), len(es)))):
    e = es[i] if i < len(es) else "<oob>"
    z = zh[i] if i < len(zh) else "<oob>"
    flag = ""
    if z and all(ord(c) < 128 for c in z) and z.strip():
        flag = "EN-LEFT?"
    if z == "" and e.strip():
        flag = "EMPTY-in-ZH"
    print("%5d | %-40.40s | %-40.40s | %s" % (i + 1, e, z, flag))
