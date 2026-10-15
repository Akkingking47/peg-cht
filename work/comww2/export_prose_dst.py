# -*- coding: utf-8 -*-
"""导出 COMWW2 prose 层「剩余待译」原文清单（含制表符自动拆分，便于直接翻译）。

用法:
    python export_prose_dst.py                 # 全量
    python export_prose_dst.py --n 50          # 只导前 50 条
    python export_prose_dst.py --offset 50 --n 50   # 导第 51-100 条

产物:
    `_prose_todo_rest.txt`  —— 形如 `  N|原文`（可直接读），与 `_prose_narrative_todo.txt` 同格式
    `_prose_todo_rest_len.tsv` —— `N<TAB>chars<TAB>nsegs<TAB>首60字`

口径:
    - 权威键集 `_prose_authority.txt`（715 条，顺序 == `_prose_narrative_todo.txt`）
    - 已译键集 = `prose-zh.tsv` 第 1 列
    - 制表符是**列分隔**：导出时把 `\t` 换成 ` ⟦T⟧ ` 显示，翻译时须原样拆回（见 merge_prose_seg.py）
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
AUTH = os.path.join(HERE, "_prose_authority.txt")
ZH = os.path.join(HERE, "prose-zh.tsv")
OUT = os.path.join(HERE, "_prose_todo_rest.txt")
OUTLEN = os.path.join(HERE, "_prose_todo_rest_len.tsv")

TABMARK = " \u27e6T\u27e7 "


def read_first_col(path):
    s = set()
    if not os.path.exists(path):
        return s
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if c and c[0]:
                s.add(c[0])
    return s


def main():
    a = sys.argv
    n = int(a[a.index("--n") + 1]) if "--n" in a else None
    off = int(a[a.index("--offset") + 1]) if "--offset" in a else 0

    auth = [x for x in io.open(AUTH, encoding="utf-8", newline="").read()
            .replace("\r\n", "\n").split("\n") if x.strip()]
    done = read_first_col(ZH)
    rest = [(i + 1, s) for i, s in enumerate(auth) if s not in done]
    total = len(rest)
    if off:
        rest = rest[off:]
    if n is not None:
        rest = rest[:n]

    seg_total = sum(len(s.split("\t")) for _, s in rest)
    ch = sum(len(s) for _, s in rest)
    print("剩余 %d 条（导出 %d 条，偏移 %d）｜原文 %d 字符｜制表符分段 %d"
          % (total, len(rest), off, ch, seg_total))

    with io.open(OUT, "w", encoding="utf-8", newline="") as f:
        for i, s in rest:
            f.write("%4d|%s\n" % (i, s.replace("\t", TABMARK)))
    with io.open(OUTLEN, "w", encoding="utf-8", newline="") as f:
        f.write("N\tchars\tnsegs\thead\n")
        for i, s in rest:
            f.write("%d\t%d\t%d\t%s\n" % (i, len(s), len(s.split("\t")), s[:60].replace("\t", TABMARK)))
    print("→ %s\n→ %s" % (OUT, OUTLEN))
    print("BOM 检查:", open(OUT, "rb").read(3) != b"\xef\xbb\xbf")


if __name__ == "__main__":
    main()
