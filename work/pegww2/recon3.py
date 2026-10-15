#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 阶段0.3/0.4 文本层普查：载体分类 / 行数 / 编码 / 行尾 / 样本。"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

GAME = r"D:\Program Files\PeG-WW2"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recon3-out")
os.makedirs(OUT, exist_ok=True)

# 本沙箱下 PowerShell 管道/重定向包裹原生 exe 会 "Access is denied" ⇒ 脚本自行落盘报告
_REPORT = os.path.join(OUT, "recon3-report.txt")
_sink = io.StringIO()


class _Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            st.write(s)
        return len(s)

    def flush(self):
        for st in self.streams:
            st.flush()


sys.stdout = _Tee(sys.stdout, _sink)


def rd(p):
    with open(p, "rb") as f:
        return f.read()


def splitlines(b):
    return re.split(rb"\r\n|\r|\n", b)


def classify(name):
    n = name.lower()
    if n.endswith(".ply"):
        return "ply(描述框)"
    if n.endswith("_m.txt"):
        return "m.txt(地图格名)"
    if n.endswith("_u.txt"):
        return "u.txt(部队名)"
    if n.endswith("_cb.txt"):
        return "CB(战役内简报)"
    if n.endswith("_bv.txt"):
        return "BV(大胜评述)"
    if n.endswith("_tv.txt"):
        return "TV(战术胜评述)"
    if n.endswith("_l.txt"):
        return "L(败报)"
    if n.endswith("_v.txt"):
        return "V(胜报)"
    if n.endswith("_i.txt"):
        return "I(战役内场景)"
    if n.endswith(".txt"):
        return "txt(场景简报/其他)"
    if n.endswith(".tx"):
        return "tx(?)"
    if n.endswith(".scn"):
        return "scn(场景元数据)"
    if n.endswith(".map"):
        return "map(地图)"
    if n.endswith(".cam"):
        return "cam(战役)"
    return name.rsplit(".", 1)[-1]


def main():
    print("=" * 96)
    print("A. SCENARIO / USERSCEN / DOCS / MAP 文本载体普查")
    print("=" * 96)
    for sub in ["SCENARIO", "USERSCEN", "DOCS", "MAP", "SAVE"]:
        d = os.path.join(GAME, sub)
        if not os.path.isdir(d):
            print(f"\n[{sub}] 不存在")
            continue
        agg = defaultdict(lambda: {"n": 0, "bytes": 0, "lines": 0, "hi_files": 0, "hi_bytes": 0,
                                   "crlf": 0, "bare_lf": 0, "bare_cr": 0, "bom": 0,
                                   "ext": Counter(), "maxline": 0, "samples": []})
        files = [f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))]
        for f in files:
            fp = os.path.join(d, f)
            b = rd(fp)
            k = classify(f)
            a = agg[k]
            a["n"] += 1
            a["bytes"] += len(b)
            a["ext"][os.path.splitext(f)[1].lower()] += 1
            ls = splitlines(b)
            a["lines"] += len(ls)
            a["maxline"] = max(a["maxline"], max((len(x) for x in ls), default=0))
            hi = sum(1 for x in b if x > 127)
            if hi:
                a["hi_files"] += 1
                a["hi_bytes"] += hi
            a["crlf"] += b.count(b"\r\n")
            a["bare_lf"] += b.count(b"\n") - b.count(b"\r\n")
            a["bare_cr"] += b.count(b"\r") - b.count(b"\r\n")
            if b[:3] == b"\xef\xbb\xbf":
                a["bom"] += 1
            if len(a["samples"]) < 2:
                a["samples"].append((f, ls[:4]))
        print(f"\n[{sub}]  共 {len(files)} 文件")
        for k, a in sorted(agg.items(), key=lambda kv: -kv[1]["n"]):
            print(f"  {k:22s} n={a['n']:<6d} bytes={a['bytes']:>12,d} lines={a['lines']:>9,d} "
                  f"最长行={a['maxline']:<7d} 高字节文件={a['hi_files']:<6d} 高字节={a['hi_bytes']:<8d} "
                  f"CRLF={a['crlf']:<8d} 裸LF={a['bare_lf']:<7d} 裸CR={a['bare_cr']:<7d} BOM={a['bom']}")
            print(f"        ext={dict(a['ext'])}")
            for sn, ls in a["samples"]:
                print(f"        样本 {sn}: {[l.decode('cp1252', 'replace')[:70] for l in ls]}")

    print()
    print("=" * 96)
    print("B. 根级文本载体：头部样本（判层）")
    print("=" * 96)
    for f in ["WW2Gui.txt", "WW2Misc.txt", "WW2NAME.TXT", "WW2Tips.TXT", "ww2-eqp.txt",
              "ww2-eqp.aux", "WW2gen.txt", "PEOPLES.INT"]:
        fp = os.path.join(GAME, f)
        if not os.path.isfile(fp):
            print(f"\n--- {f} 不存在")
            continue
        b = rd(fp)
        ls = splitlines(b)
        print(f"\n--- {f}  {len(b):,} B / {len(ls):,} 行")
        for i, l in enumerate(ls[:14]):
            print(f"   [{i:>3d}] {l.decode('cp1252', 'replace')[:88]}")

    print()
    print("=" * 96)
    print("C. 启动入口线索（lnk/bat/ini/快捷方式/readme）")
    print("=" * 96)
    for root, dirs, files in os.walk(GAME):
        for f in files:
            if re.search(r"(?i)\.(lnk|bat|cmd|ini|url|cfg)$", f):
                print(f"  {os.path.relpath(os.path.join(root, f), GAME)}")
    print("  --- DESKTOP/START MENU lnk ---")
    for d in [os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"),
              r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
              os.path.join(os.environ.get("USERPROFILE", ""), "AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs")]:
        if os.path.isdir(d):
            for root, dirs, files in os.walk(d):
                for f in files:
                    if re.search(r"(?i)(peg|ww2|general|peoples)", f):
                        print(f"  {os.path.join(root, f)}")


if __name__ == "__main__":
    main()
    with open(_REPORT, "w", encoding="utf-8") as f:
        f.write(_sink.getvalue())
    print(f"\n[report] {_REPORT}")
