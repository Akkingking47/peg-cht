# -*- coding: utf-8 -*-
r"""合并 GCE 场景 `.txt` 人工批次译文（`_txt_dst_partNN.txt`）→ 校验 → `txt-zh.tsv`。

用法:
    python merge_txt_parts.py --check
    python merge_txt_parts.py --apply

校验（任一不过 ⇒ 不写盘）:
  1. 行数 == 对应 `_txt_todo_partNN.txt` 行数；
  2. 译文非空、无 TAB/CR；
  3. `ok_dst`：译文含汉字，或 `src == dst`（口径保留）；
  4. GBK 可编码；
  5. ⭐ 与 `gce-xscn-map.tsv` 同键不同值 ⇒ **报错**（跨层口径漂移；本批键理论上都
     不在 `.xscn` 表里，出现即说明 miss 导出有误）。
"""
import argparse
import glob
import io
import os
import re
import sys
import collections

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "txt-zh.tsv")
XSCN_MAP = os.path.join(HERE, "gce-xscn-map.tsv")
HAN = re.compile(r"[\u4e00-\u9fff]")


def rd2(path, enc="utf-8-sig"):
    rows = []
    if not os.path.exists(path):
        return rows
    with io.open(path, encoding=enc, newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2 and c[0]:
                rows.append((c[0], c[1]))
    return rows


def ok_dst(s, d):
    d = d.strip()
    if not d:
        return False
    if d == s.strip():
        return True
    return bool(HAN.search(d))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    xmap = dict(rd2(XSCN_MAP))
    errors, warnings = [], []
    merged = {}
    for p in sorted(glob.glob(os.path.join(HERE, "_txt_todo_part*.txt"))):
        tag = re.search(r"part(\d+)", os.path.basename(p)).group(1)
        src = [l for l in io.open(p, encoding="utf-8", newline="").read()
               .replace("\r\n", "\n").split("\n") if l.strip()]
        keys = [l.split("|", 1)[1] for l in src]
        dp = os.path.join(HERE, "_txt_dst_part%s.txt" % tag)
        if not os.path.exists(dp):
            errors.append("缺译文 _txt_dst_part%s.txt（%d 条）" % (tag, len(keys)))
            continue
        raw = io.open(dp, encoding="utf-8", newline="").read()
        if raw.startswith("\ufeff"):
            errors.append("_txt_dst_part%s.txt 含 BOM" % tag)
        lines = [x for x in raw.replace("\r\n", "\n").split("\n") if x.strip()]
        if len(lines) != len(keys):
            errors.append("_txt_dst_part%s.txt 行数不符：待译 %d / 译文 %d" % (tag, len(keys), len(lines)))
            continue
        n = 0
        for s, d in zip(keys, lines):
            d = d.strip()
            if "\t" in d or "\r" in d:
                errors.append("part%s 译文含 TAB/CR: %r" % (tag, s[:40]))
                continue
            if not ok_dst(s, d):
                errors.append("part%s 译文既无汉字又非恒等（疑似漏译）: %r -> %r" % (tag, s[:40], d[:40]))
                continue
            if s in xmap and xmap[s] != d:
                errors.append("part%s 与 `.xscn` 表冲突: %r 本批=%r xscn=%r"
                              % (tag, s[:40], d[:30], xmap[s][:30]))
                continue
            try:
                d.encode("gbk")
            except UnicodeEncodeError as e:
                errors.append("part%s GBK 不可编码: %r (%s)" % (tag, s[:40], e))
                continue
            if s in merged and merged[s] != d:
                warnings.append("跨块不一致 %r: %r / %r" % (s[:40], merged[s][:20], d[:20]))
            merged.setdefault(s, d)
            n += 1
        print("  part%s: %d 条（源 %d）" % (tag, n, len(keys)))

    print("\n合并后唯一 %d 条" % len(merged))
    if warnings:
        print("提示（非错误）%d 条：" % len(warnings))
        for w in warnings[:10]:
            print("   ~ %s" % w)
    print("错误 %d" % len(errors))
    if errors:
        print("!! 校验失败：")
        for e in errors[:40]:
            print("   - %s" % e)
        return 1
    if a.apply:
        with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write("src\tdst\n")
            for s in sorted(merged):
                f.write("%s\t%s\n" % (s, merged[s]))
        back = dict(rd2(OUT))
        assert back == merged, "回读不一致"
        print("已写 %s（%d 条）" % (os.path.basename(OUT), len(merged)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
