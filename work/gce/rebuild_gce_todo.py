# -*- coding: utf-8 -*-
r"""GCE `.xscn` 待译清单重建 + 分批导出。

用法:
    python rebuild_gce_todo.py --dump            # 重建并通过「覆盖判定」列出剩余
    python rebuild_gce_todo.py --split 6         # 切成 6 份 -> _gce_todo_partNN.txt

覆盖判定（与 COMWW2 同源，`MECHANICS §24`）：
    词典命中（`gce-xscn-map.tsv` / `_xscn_covered.tsv`） ∪ 人工批次（`xscn-new-*.tsv`）
"""
import argparse
import collections
import glob
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
HAN = re.compile(r"[\u4e00-\u9fff]")


def rd2(path, enc="utf-8-sig"):
    out = []
    if not os.path.exists(path):
        return out
    with io.open(path, encoding=enc, newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2 and c[0]:
                out.append((c[0], c[1]))
    return out


def load_covered():
    m = {}
    for p in [os.path.join(HERE, "gce-xscn-map.tsv"), os.path.join(HERE, "_xscn_covered.tsv")]:
        for s, d in rd2(p):
            if s not in m and d.strip():
                m[s] = d
    for p in sorted(glob.glob(os.path.join(HERE, "xscn-new-*.tsv"))):
        for s, d in rd2(p):
            m.setdefault(s, d)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--split", type=int, default=0)
    a = ap.parse_args()

    uniq = []
    with io.open(os.path.join(HERE, "xscn-uniq.tsv"), encoding="utf-8", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2:
                uniq.append((c[0], int(c[1])))
    cov = load_covered()
    todo = [(s, fr) for s, fr in uniq if s not in cov]
    done = [(s, fr) for s, fr in uniq if s in cov]
    print("唯一串 %d：已覆盖 %d（%.1f%%）/ 待译 %d（%d 字符）"
          % (len(uniq), len(done), 100.0 * len(done) / max(1, len(uniq)), len(todo),
             sum(len(s) for s, _ in todo)))

    if a.dump:
        rows = sorted(todo, key=lambda x: (-x[1], x[0]))
        with io.open(os.path.join(HERE, "_gce_todo.tsv"), "w", encoding="utf-8", newline="") as f:
            f.write("src\tfreq\n")
            for s, fr in rows:
                f.write("%s\t%d\n" % (s, fr))
        print("→ _gce_todo.tsv")
        b = collections.Counter()
        for s, fr in rows:
            if not re.search(r"[A-Za-z]", s):
                b["纯数字/符号"] += 1
            elif len(s) <= 8:
                b["短<=8"] += 1
            elif len(s) <= 30:
                b["中9-30"] += 1
            elif len(s) <= 80:
                b["长31-80"] += 1
            else:
                b["超长>80"] += 1
        print("构成:", dict(b))
        print("freq>=5 的 %d 条" % sum(1 for _, fr in rows if fr >= 5))

    if a.split:
        rows = sorted(todo, key=lambda x: (-x[1], x[0]))
        n = a.split
        base, rem = divmod(len(rows), n)
        idx = 0
        for p in range(1, n + 1):
            k = base + (1 if p <= rem else 0)
            chunk = rows[idx:idx + k]
            idx += k
            fn = os.path.join(HERE, "_gce_todo_part%02d.txt" % p)
            with io.open(fn, "w", encoding="utf-8", newline="") as f:
                for s, fr in chunk:
                    f.write("%4d|%s\n" % (fr, s))
            print("  part%02d: %4d 条 / %5d 字符 -> %s"
                  % (p, len(chunk), sum(len(s) for s, _ in chunk), os.path.basename(fn)))
        assert idx == len(rows)


if __name__ == "__main__":
    main()
