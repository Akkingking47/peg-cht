# -*- coding: utf-8 -*-
"""Probe .SCN unit records for nationality/side columns.
Layout hypothesis: 65 bytes/unit, S0 = len - 65*n, n = lines in _u.txt.
"""
import os, sys, io
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SCN_DIR = r"D:\Program Files\PeG-WW2\SCENARIO"
P = 65

# index dir case-insensitively
idx = {}
for f in os.listdir(SCN_DIR):
    idx[f.lower()] = f

def find(stem, ext):
    return idx.get((stem + ext).lower())

def load_scn(stem):
    name = find(stem, ".scn")
    if not name: return None
    with open(os.path.join(SCN_DIR, name), "rb") as fh:
        return fh.read()

def load_u(stem):
    name = find(stem, "_u.txt")
    if not name: return None
    with open(os.path.join(SCN_DIR, name), "rb") as fh:
        raw = fh.read()
    txt = raw.decode("gbk", errors="replace")
    lines = txt.split("\r\n")
    if lines and lines[-1] == "": lines.pop()
    return lines

def probe(stem, note=""):
    data = load_scn(stem)
    u = load_u(stem)
    if data is None:
        print(f"== {stem}: SCN NOT FOUND"); return
    n = len(u) if u else 0
    L = len(data)
    S0 = L - P * n
    print(f"== {stem}  ({note})  len={L} u_lines={n} S0={S0}")
    # header non-zero in 64..600
    hz = [(i, data[i]) for i in range(64, min(600, L)) if data[i] != 0]
    # compress: show as list
    print("   hdr[64:600] nonzero:", hz[:80])
    print("   hdr[0:16]:", list(data[:16]))
    if S0 < 0 or n == 0:
        print("   !! bad S0"); return
    # per-column distinct counts for 30..48
    colinfo = []
    for c in range(28, 50):
        vals = Counter(data[S0 + i * P + c] for i in range(n))
        colinfo.append((c, len(vals), vals.most_common(4)))
    for c, d, top in colinfo:
        print(f"   +{c:2d} distinct={d:3d} top={top}")
    # +36 sequence transitions
    seq = [data[S0 + i * P + 36] for i in range(n)]
    trans = [(i, seq[i]) for i in range(1, n) if seq[i] != seq[i-1]]
    print(f"   +36 transitions (idx,val): {trans[:40]}")
    # per-unit dump of +34/+35/+36 with _u text where +36 deviates from mode of its half
    vals = Counter(seq)
    print(f"   +36 dist: {vals.most_common()}")

if __name__ == "__main__":
    stems = [
        ("RTB01", "Sov vs Ger"),
        ("kanev", "Ger vs Sov"),
        ("fi01", "Ger vs Fra?"),
        ("ciechan", "Ger vs Pol"),
        ("salerno1", "Ger vs US"),
        ("antisal", "UK? vs Ger"),
        ("oakridge", "Sov vs US"),
        ("viipuri", "Sov vs Fin"),
        ("DAK_DAK1", "Ger/Ita vs UK"),
    ]
    for s, note in stems:
        probe(s, note)
