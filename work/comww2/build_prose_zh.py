# -*- coding: utf-8 -*-
"""合成最终 `prose-zh.tsv` = 原表 + `prose-zh-blocks/*.tsv`（后者优先）。

守卫:
  - 键必须存在于待译集（防越界）
  - 同键在后块覆盖前块（但**不得**覆盖原表的既有人工译法，除非块内显式重译且不同）
    ⇒ 实际口径：块内条目一律并入；若与原表冲突，**报出**并以原表为准（人工先译优先）
  - 输出 UTF-8 **无 BOM**（BOM 会让 `read_tsv` 吞掉首条）
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "prose-zh-blocks")
BASE = os.path.join(HERE, "prose-zh.tsv")
TODO = os.path.join(HERE, "_prose_narrative_todo.txt")
AUTH = os.path.join(HERE, "_prose_authority.txt")

# ⛔ 硬坑（09-29）：待译清单带 `  N|` 行号前缀；权威键集在 `prose-miss.tsv`
NUM_PREFIX = re.compile(r"^\s*\d+\|")


def load(path):
    d = {}
    if not os.path.exists(path):
        return d
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        raw = f.read()
    for i, ln in enumerate(raw.replace("\r\n", "\n").split("\n")):
        if i == 0 or not ln.strip():
            continue
        c = ln.split("\t")
        if len(c) >= 2 and c[0]:
            d[c[0]] = c[1]
    return d


def main():
    # 权威键集：固化的 715 条（⚠️ 不用 prose-miss.tsv，它会随进度缩水）
    todo = set()
    for ln in io.open(AUTH, encoding="utf-8", newline="").read().split("\n"):
        if ln.strip():
            todo.add(ln.rstrip("\n"))

    base = load(BASE)
    blocks = {}
    for fn in sorted(os.listdir(OUTDIR)):
        if not fn.endswith(".tsv"):
            continue
        for k, v in load(os.path.join(OUTDIR, fn)).items():
            if k not in todo:
                raise SystemExit("越界键 %s :: %r" % (fn, k[:80]))
            if k in blocks and blocks[k] != v:
                print("  ~ 块间重名不一致 %r: %s -> %s" % (k[:50], blocks[k][:30], v[:30]))
            blocks[k] = v

    clash = 0
    merged = dict(base)
    for k, v in blocks.items():
        # ⚠️ 口径（2026-09-30 订正）：**块内条目为准**。
        #    原实现「与原表冲突则保留原表」，导致 `fix_prose_rest.py` 的术语订正
        #    （写成块内 rest-*.tsv）在合成时被 `prose-zh.tsv` 里的旧值**静默回滚**（实测 17 条）。
        #    块是后做的、更晚的人工成果 ⇒ 必须覆盖原表；冲突**报出**以便追溯。
        if k in base and base[k] != v:
            print("  ! 块内覆盖原表 %r: %r -> %r" % (k[:50], base[k][:40], v[:40]))
            clash += 1
        merged[k] = v

    with io.open(BASE, "w", encoding="utf-8", newline="") as f:
        f.write("src\tdst\n")
        for k in sorted(merged):
            f.write("%s\t%s\n" % (k, merged[k]))
    print("合成 %s：原表 %d + 块内 %d = %d 条（冲突 %d）"
          % (BASE, len(base), len(blocks), len(merged), clash))
    # 回读
    back = load(BASE)
    if back != merged:
        raise SystemExit("回读不一致")
    print("回读一致 OK，无 BOM:", open(BASE, "rb").read(3) != b"\xef\xbb\xbf")


if __name__ == "__main__":
    main()
