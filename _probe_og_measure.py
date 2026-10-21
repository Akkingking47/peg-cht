# -*- coding: utf-8 -*-
r"""_probe_og_measure.py — 对 D:\OpenGeneral（波兰 GUS 发行版）的 5 个 efile 做
「开工前全层量测」（`docs\24` §六之一 纪律）。

为什么另起一个探针而不用 `work\audit\measure_efile.py`：
  * 它写死 `ROOT = r"D:\OpenPG2"`；
  * 它的 `--efile` 会 `.upper()`，无法命中 `EFILE_GUS_Wx` 这种大小写混合目录；
  * 它只扫 SCENARIO，不单列 TEXT-PL / MAPFILES 等本发行版特有的层。
本脚本只读，复用 `work\xscn\xscn.py` 的解析器，不写任何项目文件。
"""
import collections
import importlib.util
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"D:\OpenGeneral"
WORK = r"D:\DSH\军事游戏汉化\work"

spec = importlib.util.spec_from_file_location("xscn", os.path.join(WORK, "xscn", "xscn.py"))
xscn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(xscn)

ROOT_FILES = ["equip.txt", "names.txt", "nations.txt", "strings_efile.txt"]
OTHER_ROOT = ["efile.txt", "efile.xml", "weather.txt", "fronts.txt", "colors.txt",
              "TerrainEx.txt", "equip.cfg", "OpenFont.cfg"]


def han(s):
    return sum(1 for c in s if "\u4e00" <= c <= "\u9fff")


def lines_of(raw, enc="cp1252"):
    return raw.decode(enc, "replace").replace("\r\n", "\n").split("\n")


def root_measure(e, fn):
    p = os.path.join(e, fn)
    if not os.path.exists(p):
        return None
    raw = open(p, "rb").read()
    ls = lines_of(raw)
    body = [l for l in ls if l.strip() and not l.lstrip().startswith("*")]
    return dict(bytes=len(raw), lines=len(ls), rows=len(body),
                uniq=len(set(body)), han=han("\n".join(body)))


GRAND = collections.Counter()


def measure(ef, e):
    print("=" * 78)
    print("%s  全层量测" % ef)
    print("=" * 78)
    tot_items = 0

    print("\n[根级]")
    for fn in ROOT_FILES:
        m = root_measure(e, fn)
        if m:
            print("  %-18s %7d B  %5d 行（去注释 %5d / 唯一 %5d）汉字 %d"
                  % (fn, m["bytes"], m["lines"], m["rows"], m["uniq"], m["han"]))
            GRAND["root_rows"] += m["rows"]
            GRAND["root_uniq"] += m["uniq"]
        else:
            print("  %-18s (无)" % fn)
    for fn in OTHER_ROOT:
        p = os.path.join(e, fn)
        if os.path.exists(p):
            raw = open(p, "rb").read()
            print("  %-18s %7d B  非 ASCII %d"
                  % (fn, len(raw), sum(1 for c in raw if c > 127)))

    for sub in ("SCENARIO", "USERSCEN"):
        d = os.path.join(e, sub)
        if not os.path.isdir(d):
            continue
        names = sorted(os.listdir(d))
        ext = collections.Counter(os.path.splitext(f)[1].lower() for f in names)
        print("\n[%s] %d 文件：%s" % (sub, len(names),
              ", ".join("%s×%d" % (k or "(无扩展)", v)
                        for k, v in sorted(ext.items(), key=lambda x: -x[1]))))
        GRAND[sub + "_files"] += len(names)

        xs = sorted(f for f in names if f.lower().endswith(".xscn"))
        if xs:
            n_items = 0
            lat = collections.Counter()
            for f in xs:
                try:
                    data, items, meta = xscn.parse(os.path.join(d, f))
                except Exception:
                    continue
                if meta is None:
                    continue
                for gi, i, off, L in (items or []):
                    lat[xscn.raw_at(data, off, L).decode("cp1252", "replace")] += 1
                n_items += len(items or [])
            print("  .xscn  %d 文件 / %d 条 / 唯一 %d"
                  % (len(xs), n_items, len(lat)))
            tot_items += n_items
            GRAND["xscn_files"] += len(xs)
            GRAND["xscn_items"] += n_items
            GRAND["xscn_uniq"] += len(lat)

        for extn, label in ((".txt", ".txt"), (".ply", ".ply")):
            fs = sorted(f for f in names if f.lower().endswith(extn))
            if not fs:
                continue
            chars = body = 0
            for f in fs:
                raw = open(os.path.join(d, f), "rb").read()
                core = raw.replace(b"\x00", b"").strip()
                if core:
                    body += 1
                    chars += len(core.decode("cp1252", "replace"))
            print("  %-5s %d 文件（有正文 %d）/ %d 字符" % (label, len(fs), body, chars))
            GRAND[extn.lstrip(".") + "_files"] += len(fs)
            GRAND[extn.lstrip(".") + "_chars"] += chars

        for extn in (".tmsg", ".xsch", ".front", ".xcam", ".doc"):
            fs = [f for f in names if f.lower().endswith(extn)]
            if fs:
                print("  %-6s %d 文件" % (extn, len(fs)))

    for sub in ("TEXT-ZH", "TEXT-PL", "TEXT-EN", "TEXT-DE", "TEXT-ZH\\SCENARIO"):
        d = os.path.join(e, sub)
        if os.path.isdir(d):
            n = len(os.listdir(d))
            print("\n[%s] %d 文件" % (sub, n))
            GRAND[sub.replace("\\", "/")] += n

    print()
    return tot_items


def main():
    dirs = sorted(d for d in os.listdir(ROOT)
                  if d.upper().startswith("EFILE_")
                  and os.path.isdir(os.path.join(ROOT, d)))
    print("D:\\OpenGeneral 下 efile 目录：%s\n" % ", ".join(dirs))
    for ef in dirs:
        measure(ef, os.path.join(ROOT, ef))

    print("=" * 78)
    print("【全库合计】")
    print("=" * 78)
    print("  efile 数              %d" % len(dirs))
    print("  根级待译行（去注释）   %d（唯一 %d）"
          % (GRAND["root_rows"], GRAND["root_uniq"]))
    print("  .xscn 文件 / 条目      %d / %d（唯一 %d）"
          % (GRAND["xscn_files"], GRAND["xscn_items"], GRAND["xscn_uniq"]))
    print("  .txt 文件 / 字符       %d / %s"
          % (GRAND["txt_files"], format(GRAND["txt_chars"], ",")))
    print("  .ply 文件 / 字符       %d / %s"
          % (GRAND["ply_files"], format(GRAND["ply_chars"], ",")))
    print("  SCENARIO 文件总数      %d" % GRAND["SCENARIO_files"])
    print("  USERSCEN 文件总数      %d" % GRAND["USERSCEN_files"])


if __name__ == "__main__":
    main()
