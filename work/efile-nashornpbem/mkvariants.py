# -*- coding: utf-8 -*-
"""Build prefix-variant names.txt files: first N lines Chinese, rest English.

Output: work/efile-nashornpbem/tests/names_pNNN.txt  (GBK, no BOM, CRLF)
"""
import io
import os

EN = r"D:/OpenPG2/EFILE_NASHORNPBEM/names.txt"
ZH = r"D:/DSH/军事游戏汉化/work/efile-nashornpbem/dist/names.txt"
OUTDIR = r"D:/DSH/军事游戏汉化/work/efile-nashornpbem/tests"

os.makedirs(OUTDIR, exist_ok=True)

en = io.open(EN, encoding="gbk", errors="replace", newline="").read().split("\r\n")
zh = io.open(ZH, encoding="gbk", errors="replace", newline="").read().split("\r\n")
assert len(en) == len(zh), (len(en), len(zh))

# how many lines actually differ?
diff = [i for i in range(len(en)) if en[i] != zh[i]]
print("lines total=%d  differing=%d" % (len(en), len(diff)))
print("first 5 differing line nos:", [i + 1 for i in diff[:5]])
print("last differing line no:", diff[-1] + 1 if diff else None)
# sanity: are ALL differing lines non-empty zh?
bad = [i for i in diff if not zh[i].strip()]
print("differing lines with empty zh:", bad[:10], "count", len(bad))

for n in (1, 4, 16, 64, 256, 512):
    out = list(en)
    for i in range(min(n, len(out))):
        out[i] = zh[i]
    p = os.path.join(OUTDIR, "names_p%03d.txt" % n)
    data = "\r\n".join(out)
    with io.open(p, "wb") as f:
        f.write(data.encode("gbk"))
    print("wrote %s  bytes=%d" % (p, os.path.getsize(p)))
