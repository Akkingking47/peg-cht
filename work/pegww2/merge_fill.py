#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2：把 `<Name>-fill.tsv` 合并进 `<Name>-map.tsv`（译法真源）。

哨兵：
  @KEEP   ⇒ 译文 = 原文，来源 = 保留（注释/永不显示的行）
  类别=@订正 ⇒ 强制覆盖已有译文（用于统一前作遗留的不一致），来源 = 订正
  其它    ⇒ 仅当译文列为空时填入，来源 = 新译确认
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
PAIRS = [("WW2Gui-map.tsv", "WW2Gui-fill.tsv"),
         ("WW2Misc-map.tsv", "WW2Misc-fill.tsv"),
         ("WW2Tips-map.tsv", "WW2Tips-fill.tsv")]
_sink = io.StringIO()


class _Tee:
    def __init__(self, *s):
        self.s = s

    def write(self, x):
        for t in self.s:
            t.write(x)
        return len(x)

    def flush(self):
        for t in self.s:
            t.flush()


sys.stdout = _Tee(sys.stdout, _sink)


def read_rows(p):
    head, rows = [], []
    with open(p, encoding="utf-8-sig") as f:
        for line in f:
            s = line.rstrip("\r\n")
            if s.startswith("#") or not s:
                head.append(s)
            elif s.split("\t")[0].strip() in ("行号", "原文"):
                head.append(s)
            else:
                rows.append(s.split("\t"))
    return head, rows


def main():
    for mapn, filln in PAIRS:
        mp = os.path.join(RES, mapn)
        fp = os.path.join(RES, filln)
        if not os.path.isfile(fp):
            print(f"  {mapn}: 无 fill，跳过")
            continue
        head, rows = read_rows(mp)
        _, frows = read_rows(fp)
        by = {}
        for r in rows:
            if len(r) >= 3 and re.fullmatch(r"\d+", r[0].strip()):
                by[int(r[0])] = r
        filled = over = kept = skipped = 0
        for fr in frows:
            if len(fr) < 2 or not re.fullmatch(r"\d+", fr[0].strip()):
                continue
            ln = int(fr[0])
            zh = fr[1].strip()
            kind = fr[2].strip() if len(fr) >= 3 else ""
            r = by.get(ln)
            if r is None:
                print(f"    ⚠ {mapn} 行 {ln} 不存在于 map，跳过")
                continue
            cur = r[2].strip() if len(r) >= 3 else ""
            if zh == "@KEEP":
                r[2], r[3] = r[1], "保留"
                kept += 1
            elif kind == "@订正":
                print(f"    订正 行{ln}: {cur!r} → {zh!r}")
                r[2], r[3] = zh, "订正"
                over += 1
            elif not cur:
                r[2], r[3] = zh, "新译确认"
                filled += 1
            else:
                skipped += 1
        with open(mp, "w", encoding="utf-8", newline="\n") as f:
            for h in head:
                f.write(h + "\n")
            for r in rows:
                f.write("\t".join(r) + "\n")
        print(f"  {mapn}: 新填 {filled} · @KEEP {kept} · 订正 {over} · 已有跳过 {skipped}")

    print()
    print("=" * 84)
    print("合并后剩余待填统计")
    print("=" * 84)
    for mapn, _ in PAIRS:
        p = os.path.join(RES, mapn)
        if not os.path.isfile(p):
            continue
        head, rows = read_rows(p)
        empty = [r for r in rows if len(r) >= 4 and r[2].strip() == "" and r[3].strip() != "保留"]
        print(f"  {mapn}: 总 {len(rows)} 行 / **仍待填 {len(empty)}**")
        for r in empty[:15]:
            print(f"      行{r[0]:<5s} {r[1][:76]}")


if __name__ == "__main__":
    main()
    os.makedirs(os.path.join(RES, "evidence"), exist_ok=True)
    with open(os.path.join(RES, "evidence", "merge-fill.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
