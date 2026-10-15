# -*- coding: utf-8 -*-
r"""USERSCEN 待译清单导出 + 切分（`.xscn` 串区 ＋ `.ply`/`.txt`）。

填译链的先例来源＝`gce-xscn-map.tsv`（跨层词典，1675 条）；其余进待译。

用法: python export_userscen_todo.py [N=6]
产出: _us_todo.tsv          src \t n \t kind（xscn/ply/txt）
      _us_todo_partNN.txt   格式 `   n|src`
      _us_todo_parts.tsv    分块索引
"""
import io
import os
import re
import sys
import collections

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
U = r"D:\OpenPG2\EFILE_GCE\USERSCEN"
MAP = os.path.join(HERE, "gce-xscn-map.tsv")
UNIQ = r"D:\DSH\军事游戏汉化\work\userscen\gce-userscen-uniq.tsv"
GLOSS = r"D:\DSH\军事游戏汉化\glossary\standard-glossary.tsv"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 6

KEEP_PAT = [
    re.compile(r"^\[[^a-z\u00e0-\u00ff]*\]?$"),
    re.compile(r"^[A-Z]{1,4}$"),
    re.compile(r"^\u00af+$"),
    re.compile(r"^\d+$"),
    re.compile(r"^[\W_]+$"),
]


def rd2(p, enc="utf-8-sig"):
    d = {}
    if not os.path.exists(p):
        return d
    with io.open(p, encoding=enc, newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2 and c[0]:
                d.setdefault(c[0], c[1])
    return d


def keep_ok(s):
    return any(rx.match(s.strip()) for rx in KEEP_PAT)


def main():
    pre = rd2(MAP)
    gloss = rd2(GLOSS)
    todo = collections.Counter()
    kind = {}

    # (a) .xscn 串区（读 userscen_tool.py strings 导出的 `src\tn`）
    with io.open(UNIQ, encoding="utf-8", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) < 2:
                continue
            s = c[0]
            cnt = int(c[1])
            if s in pre or s in gloss or keep_ok(s):
                continue
            todo[s] += cnt
            kind.setdefault(s, "xscn")

    # (b) .ply / .txt
    for f in sorted(os.listdir(U)):
        ext = os.path.splitext(f)[1].lower()
        if ext not in (".ply", ".txt"):
            continue
        raw = open(os.path.join(U, f), "rb").read().replace(b"\x00", b"")
        for l in raw.decode("cp1252", "replace").replace("\r\n", "\n").split("\n"):
            if not l.strip():
                continue
            if l in pre or l in gloss or keep_ok(l):
                continue
            todo[l] += 1
            kind.setdefault(l, ext[1:])

    k = collections.Counter(kind[s] for s in todo)
    total = sum(len(s) for s in todo)
    print("待译唯一 %d 条 / %d 字符（来源：%s）" % (len(todo), total, dict(k)))

    with io.open(os.path.join(HERE, "_us_todo.tsv"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("src\tn\tkind\n")
        for s in sorted(todo, key=lambda x: (kind[x], -todo[x], x)):
            fh.write("%s\t%d\t%s\n" % (s, todo[s], kind[s]))

    # 切分：先按 kind（xscn / ply / txt）分组，再在组内按**固定字符数**切
    CHARS_PER_PART = int(sys.argv[2]) if len(sys.argv) > 2 else 4800
    parts = []
    for kd in ("xscn", "ply", "txt"):
        items = [s for s in sorted(todo, key=lambda x: -todo[x]) if kind[s] == kd]
        if not items:
            continue
        tgt = CHARS_PER_PART
        cur, curch = [], 0
        for s in items:
            cur.append(s)
            curch += len(s)
            if curch >= tgt:
                parts.append((kd, cur)); cur, curch = [], 0
        if cur:
            parts.append((kd, cur))

    idx = []
    for i, (kd, p) in enumerate(parts, 1):
        tag = "%02d" % i
        with io.open(os.path.join(HERE, "_us_todo_part%s.txt" % tag), "w",
                     encoding="utf-8", newline="\n") as fh:
            for s in p:
                fh.write("   %d|%s\n" % (todo[s], s))
        idx.append((tag, kd, len(p), sum(len(s) for s in p)))
    with io.open(os.path.join(HERE, "_us_todo_parts.tsv"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("part\tkind\tn\tnchars\n")
        for tag, kd, n, c in idx:
            fh.write("%s\t%s\t%d\t%d\n" % (tag, kd, n, c))
            print("  part%s [%s]: %3d 条 / %6d 字符" % (tag, kd, n, c))
    print("共 %d 块" % len(parts))


if __name__ == "__main__":
    main()
