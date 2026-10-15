# -*- coding: utf-8 -*-
"""复用 progress.py 的判据，导出某 efile 的 `.xscn` 疑似漏译清单（人工复核用）。"""
import io
import sys
import os
import glob
import importlib.util

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
P = r"D:\DSH\军事游戏汉化\work\audit\progress.py"
spec = importlib.util.spec_from_file_location("prog", P)
prog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prog)

EF = sys.argv[1] if len(sys.argv) > 1 else "BASEKORP"
base = os.path.join(prog.GAME, "EFILE_" + EF)
fake = prog.build_fake_han("EFILE_" + EF)

leaks = []
for f in sorted(glob.glob(os.path.join(base, "SCENARIO", "*.xscn"))):
    try:
        _t, ent = prog.parse_xscn(open(f, "rb").read())
    except Exception as e:
        print("!! parse fail", f, e)
        continue
    for e in ent:
        if not e.strip():
            continue
        if prog.is_zh(e, fake):
            continue
        if prog.kept_style(e):
            continue
        leaks.append((os.path.basename(f), e.decode("gbk", "replace")))

print("EFILE_%s  `.xscn` 疑似漏译: %d 条" % (EF, len(leaks)))
out = os.path.join(HERE, "_xscn_leak_%s.tsv" % EF.lower())
with io.open(out, "w", encoding="utf-8", newline="\n") as fh:
    for fn, s in leaks:
        fh.write("%s\t%s\n" % (fn, s))
    print("saved ->", out)
for fn, s in leaks:
    print("  %-24s %r" % (fn, s))
