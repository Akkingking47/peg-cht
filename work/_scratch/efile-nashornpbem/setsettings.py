# -*- coding: utf-8 -*-
"""切换 Settings.cfg 的 EFolder / LastOpen（先备份一次，可 restore）。

  python setsettings.py --game D:\\OpenPG2 --efolder EFILE_NASHORNPBEM\\ \
                        --lastopen EFILE_NASHORNPBEM\\SCENARIO\\utopianparadox.xscn
  python setsettings.py --game D:\\OpenPG2 --restore
"""
import argparse
import io
import os
import shutil


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", required=True)
    ap.add_argument("--efolder")
    ap.add_argument("--lastopen")
    ap.add_argument("--restore", action="store_true")
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()

    p = os.path.join(a.game, "Settings.cfg")
    bak = p + ".poc-backup"

    if a.restore:
        if not os.path.exists(bak):
            print("no backup at %s" % bak)
            return 1
        shutil.copy2(bak, p)
        print("restored from %s" % bak)
        return 0

    if a.efolder:
        if not os.path.exists(bak):
            shutil.copy2(p, bak)
            print("backup -> %s" % bak)
        with io.open(p, "r", encoding="gbk", errors="replace", newline="") as f:
            txt = f.read()
        lines = txt.split("\n")
        seen = 0
        for i, ln in enumerate(lines):
            s = ln.strip().lower()
            if s.startswith("efolder="):
                lines[i] = "EFolder=" + a.efolder
                seen |= 1
            elif s.startswith("lastopen="):
                lines[i] = "LastOpen=" + a.lastopen
                seen |= 2
        with io.open(p, "w", encoding="gbk", newline="") as f:
            f.write("\n".join(lines))
        print("patched EFolder=%s LastOpen=%s seen=%d" % (a.efolder, a.lastopen, seen))

    if a.show or a.efolder:
        with io.open(p, "r", encoding="gbk", errors="replace") as f:
            for ln in f:
                s = ln.strip()
                if s.lower().startswith(("efolder=", "lastopen=", "ui_lang=", "font1=", "szfont1=")):
                    print("   " + s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
