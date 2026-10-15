# -*- coding: utf-8 -*-
r"""参数化「开工前全层量测」（`docs\24` §六之一 纪律：每批开工先全 efile 量测）。

为什么参数化：`work\comww2\` 下的量测器把 `EFILE_COMWW2` 写死，每个新 efile 都要抄一份。
本脚本一次覆盖**全部层**，用 `--efile` 切换，输出可直接粘进报告。

量测层（直读文件，不看映射表）：
  根级  equip / names / nations / strings_efile（非空非 `*` 行 + 唯一）
  `.xscn`（用 `xscn.py` 的解析器；含「组表为空 ⇒ 只有标题」的情形）
  `.txt` / `.ply` / `.tmsg` / `.xsch` / `.front` / `.xcam` / `.doc`
  `USERSCEN\`（同层，但**单列**——它不在 progress.py 的扫描范围内）
  `TEXT-ZH\` 现有交付件

用法: python measure_efile.py --efile GCE [--json]
"""
import argparse
import collections
import importlib.util
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\OpenPG2"
WORK = r"D:\DSH\军事游戏汉化\work"
ROOT_FILES = ["equip.txt", "names.txt", "nations.txt", "strings_efile.txt"]

spec = importlib.util.spec_from_file_location(
    "xscn", os.path.join(WORK, "xscn", "xscn.py"))
xscn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(xscn)

HAN = re.compile(r"[\u4e00-\u9fff]")


def han(s):
    return sum(1 for c in s if "\u4e00" <= c <= "\u9fff")


def lines_of(raw, enc="cp1252"):
    s = raw.decode(enc, "replace")
    return s.replace("\r\n", "\n").split("\n")


def root_measure(e, fn):
    """根级文件：非空非 `*` 行、唯一、含汉字（原文侧应为 0）"""
    p = os.path.join(e, fn)
    if not os.path.exists(p):
        return None
    raw = open(p, "rb").read()
    ls = lines_of(raw)
    body = [l for l in ls if l.strip() and not l.lstrip().startswith("*")]
    return dict(bytes=len(raw), lines=len(ls), rows=len(body), uniq=len(set(body)),
                han=han("\n".join(body)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--efile", required=True)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    ef = a.efile.strip().upper()
    if not ef.startswith("EFILE_"):
        ef = "EFILE_" + ef
    e = os.path.join(ROOT, ef)
    if not os.path.isdir(e):
        raise SystemExit("无此 efile: %s" % e)
    out = {"efile": ef}

    print("=" * 78)
    print("%s 全层量测" % ef)
    print("=" * 78)

    # ---------- 根级 ----------
    print("\n[根级]")
    for fn in ROOT_FILES:
        m = root_measure(e, fn)
        if m:
            out[fn] = m
            print("  %-18s %7d B  %5d 行（去注释 %5d / 唯一 %5d）汉字 %d"
                  % (fn, m["bytes"], m["lines"], m["rows"], m["uniq"], m["han"]))
        else:
            print("  %-18s (无)" % fn)
    for fn in ("efile.txt", "efile.xml", "weather.txt", "fronts.txt", "colors.txt",
               "TerrainEx.txt", "equip.cfg"):
        p = os.path.join(e, fn)
        if os.path.exists(p):
            raw = open(p, "rb").read()
            out[fn] = dict(bytes=len(raw), nonascii=sum(1 for c in raw if c > 127))
            print("  %-18s %7d B  非 ASCII %d" % (fn, len(raw), out[fn]["nonascii"]))

    # ---------- SCENARIO / USERSCEN ----------
    for sub in ("SCENARIO", "USERSCEN"):
        d = os.path.join(e, sub)
        if not os.path.isdir(d):
            continue
        ext = collections.Counter(os.path.splitext(f)[1].lower() for f in os.listdir(d))
        print("\n[%s] %d 文件：%s" % (sub, len(os.listdir(d)),
                                     ", ".join("%s×%d" % (k or "(无扩展)", v)
                                               for k, v in sorted(ext.items(), key=lambda x: -x[1]))))
        sub_out = {}

        # .xscn
        xs = sorted(f for f in os.listdir(d) if f.lower().endswith(".xscn"))
        if xs:
            n_items = n_uniq = n_title_zh = 0
            lat = collections.Counter()
            tails = []
            for f in xs:
                p = os.path.join(d, f)
                data, items, meta = xscn.parse(p)
                if meta is None:
                    continue
                to, tl, groups, end, size = meta
                if to is not None:
                    t = data[to + 2:to + 2 + tl].decode("cp1252", "replace")
                    if han(t):
                        n_title_zh += 1
                items = items or []
                n_items += len(items)
                for gi, i, off, L in items:
                    s = xscn.raw_at(data, off, L).decode("cp1252", "replace")
                    lat[s] += 1
                tails.append(size - end)
            n_uniq = len(lat)
            lat_only = sum(1 for s in lat if any(c.isalpha() and ord(c) < 128 for c in s))
            sub_out["xscn"] = dict(files=len(xs), items=n_items, uniq=n_uniq,
                                   uniq_lat=lat_only, title_zh=n_title_zh,
                                   tail_residue=sum(1 for x in tails if x))
            print("  .xscn  %d 文件 / %d 条 / 唯一 %d（含拉丁 %d）/ 标题已中文 %d / 尾部残留文件 %d"
                  % (len(xs), n_items, n_uniq, lat_only, n_title_zh,
                     sub_out["xscn"]["tail_residue"]))

        # .txt / .ply
        for extn, label in ((".txt", ".txt"), (".ply", ".ply")):
            fs = sorted(f for f in os.listdir(d) if f.lower().endswith(extn))
            if not fs:
                continue
            chars = body_files = zhn = 0
            for f in fs:
                raw = open(os.path.join(d, f), "rb").read()
                core = raw.replace(b"\x00", b"").strip()
                if core:
                    body_files += 1
                    s = core.decode("cp1252", "replace")
                    chars += len(s)
                    if han(s):
                        zhn += 1
            sub_out[extn] = dict(files=len(fs), body=body_files, chars=chars, zh_files=zhn)
            print("  %-5s %d 文件（有正文 %d）/ %d 字符 / 已含汉字 %d"
                  % (label, len(fs), body_files, chars, zhn))

        # .tmsg / .xsch
        for extn in (".tmsg", ".xsch"):
            fs = sorted(f for f in os.listdir(d) if f.lower().endswith(extn))
            if fs:
                sub_out[extn] = len(fs)
                print("  %-5s %d 文件" % (extn, len(fs)))
        # 其它
        for extn in (".front", ".xcam", ".doc", ".jpg", ".png", ".PLY"):
            fs = [f for f in os.listdir(d) if f.endswith(extn)]
            if fs:
                sub_out[extn] = len(fs)
                print("  %-5s %d 文件" % (extn, len(fs)))
        out[sub] = sub_out

    # ---------- TEXT-ZH ----------
    tz = os.path.join(e, "TEXT-ZH")
    print("\n[TEXT-ZH 现有交付件]")
    if os.path.isdir(tz):
        for f in sorted(os.listdir(tz)):
            p = os.path.join(tz, f)
            if os.path.isfile(p):
                raw = open(p, "rb").read()
                print("  %-20s %7d B  %d 汉字" % (f, len(raw), han(raw.decode("gbk", "replace"))))
            else:
                print("  %-20s %5d 文件" % (f + "\\", len(os.listdir(p))))
        out["TEXT-ZH"] = sorted(os.listdir(tz))
    else:
        print("  (无 → 0% 起点)")
        out["TEXT-ZH"] = []

    # ---------- OPENGUI / OPENDAT ----------
    for sub in ("OPENGUI", "OPENDAT", "SOUND", "README", "TEXT-ES"):
        d = os.path.join(e, sub)
        if os.path.isdir(d):
            fs = sorted(os.listdir(d))
            out[sub] = fs
            print("\n[%s] %d 文件：%s" % (sub, len(fs), ", ".join(fs[:10]) + ("…" if len(fs) > 10 else "")))

    if a.json:
        p = os.path.join(WORK, "audit", "_measure_" + ef.replace("EFILE_", "").lower() + ".json")
        with io.open(p, "w", encoding="utf-8", newline="") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print("\n→ %s" % p)


if __name__ == "__main__":
    main()
