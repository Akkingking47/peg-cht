# -*- coding: utf-8 -*-
"""全库 `USERSCEN\` 量测（2026-09-30 新发现的盲区）。

背景：`work\\audit\\progress.py` 只扫 `SCENARIO\\` 与 `TEXT-ZH\\SCENARIO\\`，
⇒ 各 efile 的 `USERSCEN\`（用户场景目录）**从未进入任何报表**。

本脚本直读文件，输出每个 efile 的 USERSCEN 规模：
  - `.xscn`：用 `xscn.py::parse()` 取**标题**与**串区条目**（USERSCEN 多为「仅标题」）
  - `.ply`：正文大小（含 NUL 判空壳）
  - `.txt`：行数与字符数
  - 是否已存在同名 `TEXT-ZH\\` 交付件

用法: python measure_userscen.py [--json]
"""
import collections
import importlib.util
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\OpenPG2"
spec = importlib.util.spec_from_file_location(
    "xscn", r"D:\DSH\军事游戏汉化\work\xscn\xscn.py")
xscn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(xscn)


def han(s):
    return sum(1 for c in s if "\u4e00" <= c <= "\u9fff")


def main():
    want_json = "--json" in sys.argv
    out = {}
    print("%-20s %5s %8s %6s | %5s %8s | %5s %7s" %
          ("efile", "xscn", "标题英", "有串区", "ply", "ply字符", "txt", "txt字符"))
    print("-" * 84)
    tot = collections.Counter()
    for d in sorted(os.listdir(ROOT)):
        us = os.path.join(ROOT, d, "USERSCEN")
        if not os.path.isdir(us):
            continue
        xs = sorted(f for f in os.listdir(us) if f.lower().endswith(".xscn"))
        pl = sorted(f for f in os.listdir(us) if f.lower().endswith(".ply"))
        tx = sorted(f for f in os.listdir(us) if f.lower().endswith(".txt"))
        tzh = os.path.join(ROOT, d, "TEXT-ZH", "USERSCEN")

        n_titled = n_zh_title = 0
        n_items = 0
        n_items_lat = 0
        for f in xs:
            try:
                data, items, meta = xscn.parse(os.path.join(us, f))
            except Exception:
                continue
            if meta is None:
                continue
            to, tl = meta[0], meta[1]
            if to is not None:
                t = data[to + 2:to + 2 + tl].decode("cp1252")
                n_titled += 1
                n_items += len(items or [])
                if han(t):
                    n_zh_title += 1
                for gi, i, off, L in (items or []):
                    s = xscn.raw_at(data, off, L).decode("cp1252", "replace")
                    if any(c.isalpha() and ord(c) < 128 for c in s):
                        n_items_lat += 1
        ply_chars = 0
        ply_body = 0
        for f in pl:
            raw = open(os.path.join(us, f), "rb").read()
            core = raw.replace(b"\x00", b"").strip()
            if core:
                ply_body += 1
                ply_chars += len(core.decode("cp1252", "replace"))
        txt_chars = txt_zh = 0
        for f in tx:
            raw = open(os.path.join(us, f), "rb").read()
            s = raw.decode("cp1252", "replace")
            txt_chars += len(s)
            if han(s):
                txt_zh += 1
        print("%-20s %5d %8d %6d | %5d %8d | %5d %7d" %
              (d, len(xs), n_titled, n_items_lat, ply_body, ply_chars, len(tx), txt_chars))
        tot["xscn"] += len(xs)
        tot["ply"] += len(pl)
        tot["txt"] += len(tx)
        tot["ply_chars"] += ply_chars
        tot["txt_chars"] += txt_chars
        tot["items_lat"] += n_items_lat
        out[d] = dict(xscn=len(xs), xscn_titled=n_titled, xscn_title_zh=n_zh_title,
                      xscn_items=n_items, xscn_items_lat=n_items_lat,
                      ply=len(pl), ply_body=ply_body, ply_chars=ply_chars,
                      txt=len(tx), txt_chars=txt_chars, txt_zh=txt_zh,
                      text_zh_dir=os.path.isdir(tzh))
    print("-" * 84)
    print("合计：xscn %d（含拉丁条目 %d） · ply %d（正文 %d 字符） · txt %d（%d 字符）"
          % (tot["xscn"], tot["items_lat"], tot["ply"], tot["ply_chars"], tot["txt"], tot["txt_chars"]))
    if want_json:
        p = os.path.join(r"D:\DSH\军事游戏汉化\work\audit", "_userscen_stat.json")
        with io.open(p, "w", encoding="utf-8", newline="") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print("→ %s" % p)


if __name__ == "__main__":
    main()
