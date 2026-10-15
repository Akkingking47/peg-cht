# -*- coding: utf-8 -*-
r"""合并 USERSCEN 人工批次译文 → `userscen-zh.tsv`（= `gce-xscn-map.tsv` ∪ 本批新增）。

用法: python merge_userscen_parts.py --check | --apply

校验（任一不过 ⇒ 不写盘）:
  1. 行数 == 对应 `_us_todo_partNN.txt` 行数；
  2. 译文非空、无 TAB/CR、GBK 可编码；
  3. `ok_dst`：含汉字，或 `src == dst`（口径保留）；
  4. ⭐ 与 `gce-xscn-map.tsv` 同键不同值 ⇒ **报错**（跨层口径漂移）。
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
BASE = os.path.join(HERE, "gce-xscn-map.tsv")
OUT = os.path.join(HERE, "userscen-zh.tsv")
HAN = re.compile(r"[\u4e00-\u9fff]")

# ⭐ 补 28 条「导出阶段被译名库/口径保留兜住、因而没进待译」的串。
#    为什么不直接取译名库的值：译名库**破坏了两条硬口径**——
#      ① `EM/53 Div./[V]` 被重排成 `第53师司令部/[第5军]`（`/` 数量变了）；
#      ② 方括号罗马数字被改成「第N军」（POLICY 三 要求**原样保留** `[V]` `[XVIII]`）。
#    这里按 POLICY 结构优先重写：`EM` 保留缩写（US-POLICY 四.1）、方括号罗马数字原样、斜杠数不变。
EXTRA = {
    "DECA": "防空",
    "XV CE": "第15军", "EM/XV CE": "EM/第15军", "EM/XVIII CE": "EM/第18军",
    "EM/V CE": "EM/第5军", "EM/XXIV CE": "EM/第24军",
    "EM/53 Div./[V]": "EM/第53师/[V]", "EM/54 Div./[V]": "EM/第54师/[V]",
    "EM/46 Div./[V]": "EM/第46师/[V]", "EM/11 Div./[V]": "EM/第11师/[V]",
    "EM/45 Div./[V]": "EM/第45师/[V]", "EM/3 Div./[XV]": "EM/第3师/[XV]",
    "EM/35 Div./[XV]": "EM/第35师/[XV]", "EM/16 Div./[XII]": "EM/第16师/[XII]",
    "EM/56 Div./[XII]": "EM/第56师/[XII]", "EM/60 Div./[XVIII]": "EM/第60师/[XVIII]",
    "EM/42 Div./[XXIV]": "EM/第42师/[XXIV]", "EM/40 Div./-/": "EM/第40师/-/",
    "EM/27 BM/[XVIII]": "EM/第27营/[XVIII]",
    "EM/1 Div./[N]": "EM/第1师/[N]", "EM/4 Div./[N]": "EM/第4师/[N]",
    "AtyGrp./4 Div./[N]": "炮兵群/第4师/[N]",
    "EM/4 Div./[CTV]": "EM/第4师/[CTV]", "EM/50 Div./[CEM]": "EM/第50师/[摩洛哥军]",
    "Beach": "海滩",
    "Carreno Airfield OUT OF THE MAP LIMITS": "卡雷尼奥机场 地图范围之外",
    # 口径保留（与 gce-xscn-map.tsv 的恒等条目一致）
    "[CNT]": "[CNT]", "[N]": "[N]",
}


def rd2(path):
    rows = []
    with io.open(path, encoding="utf-8-sig", newline="") as f:
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

    base = {}
    for s, d in rd2(BASE):
        base.setdefault(s, d)
    print("基表（gce-xscn-map.tsv）%d 条" % len(base))

    errors, warnings = [], []
    new = {}
    for p in sorted(glob.glob(os.path.join(HERE, "_us_todo_part*.txt"))):
        tag = re.search(r"part(\d+)", os.path.basename(p)).group(1)
        src = [l for l in io.open(p, encoding="utf-8", newline="").read()
               .replace("\r\n", "\n").split("\n") if l.strip()]
        keys = [l.split("|", 1)[1] for l in src]
        dp = os.path.join(HERE, "_us_dst_part%s.txt" % tag)
        if not os.path.exists(dp):
            errors.append("缺译文 _us_dst_part%s.txt（%d 条）" % (tag, len(keys)))
            continue
        raw = io.open(dp, encoding="utf-8", newline="").read()
        if raw.startswith("\ufeff"):
            errors.append("_us_dst_part%s.txt 含 BOM" % tag)
        lines = [x for x in raw.replace("\r\n", "\n").split("\n") if x.strip()]
        if len(lines) != len(keys):
            errors.append("_us_dst_part%s.txt 行数不符：待译 %d / 译文 %d" % (tag, len(keys), len(lines)))
            continue
        n = 0
        for s, d in zip(keys, lines):
            d = d.strip()
            if "\t" in d or "\r" in d:
                errors.append("part%s 含 TAB/CR: %r" % (tag, s[:40]))
                continue
            if not ok_dst(s, d):
                errors.append("part%s 译文既无汉字又非恒等: %r -> %r" % (tag, s[:40], d[:40]))
                continue
            if s in base and base[s] != d:
                errors.append("part%s 与基表冲突: %r 本批=%r 基表=%r"
                              % (tag, s[:40], d[:30], base[s][:30]))
                continue
            try:
                d.encode("gbk")
            except UnicodeEncodeError as e:
                errors.append("part%s GBK 不可编码: %r (%s)" % (tag, s[:40], e))
                continue
            if s in new and new[s] != d:
                warnings.append("跨块不一致 %r: %r / %r" % (s[:40], new[s][:20], d[:20]))
            new.setdefault(s, d)
            n += 1
        print("  part%s: %d 条（源 %d）" % (tag, n, len(keys)))

    merged = dict(base)
    added = 0
    for s, d in new.items():
        if s not in merged:
            added += 1
        merged[s] = d
    n_extra = 0
    for s, d in EXTRA.items():
        if s in merged and merged[s] != d:
            errors.append("EXTRA 与既有冲突: %r EXTRA=%r 既有=%r" % (s[:40], d[:30], merged[s][:30]))
            continue
        if s not in merged:
            n_extra += 1
        merged[s] = d
    print("\n新增 %d 条；补 EXTRA %d 条；合并后 %d 条" % (added, n_extra, len(merged)))
    if warnings:
        print("提示 %d 条：" % len(warnings))
        for w in warnings[:8]:
            print("   ~ %s" % w)
    print("错误 %d" % len(errors))
    if errors:
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
