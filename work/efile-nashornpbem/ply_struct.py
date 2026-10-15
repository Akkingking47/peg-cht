# -*- coding: utf-8 -*-
"""Analyse the structure of scenario .ply files: how many language blocks,
what separates them, what encoding, and whether they end with a newline."""
import glob
import io
import os

ROOT = r"D:/OpenPG2"
pats = [r"EFILE_OLGWW2/SCENARIO/*.ply", r"EFILE_OPENPG/SCENARIO/*.ply",
        r"EFILE_AO/SCENARIO/*.ply", r"EFILE_Clu/SCENARIO/*.ply"]

for pat in pats:
    files = sorted(glob.glob(os.path.join(ROOT, pat)))
    if not files:
        continue
    print("=" * 90)
    print(pat, "->", len(files), "files")
    for p in files[:4]:
        d = open(p, "rb").read()
        txt = d.decode("latin-1")
        lines = txt.split("\r\n")
        # find separator lines (>= 8 dashes)
        seps = [i for i, l in enumerate(lines) if l.strip("-").strip() == "" and len(l.strip()) >= 8]
        hi = sum(1 for b in d if b > 0x7F)
        print("-" * 90)
        print("%-28s %6d B  lines=%d  hi-bytes=%d  sep-lines=%s"
              % (os.path.basename(p), len(d), len(lines), hi, seps))
        for i, l in enumerate(lines[:4]):
            print("     %2d: %r" % (i, l[:80]))
        if seps:
            s = seps[0]
            print("     --- after separator ---")
            for i in range(s, min(len(lines), s + 3)):
                print("     %2d: %r" % (i, lines[i][:80]))
