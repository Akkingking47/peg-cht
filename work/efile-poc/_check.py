# -*- coding: utf-8 -*-
"""校验 8 个译文分块：行数/行号/TAB/空值/替换字符/跨批同名一致性。"""
import pathlib, sys, collections

OUT = pathlib.Path(r"D:\DSH\军事游戏汉化\work\efile-nashornpbem")
O = OUT / "out"

def read_any(p):
    b = p.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return b.decode(enc), enc
        except Exception:
            continue
    return b.decode("gbk", errors="replace"), "gbk-replace"

PAIRS = []
for tag in ("equip-blk1", "equip-blk2", "equip-blk3",
            "names-blk1", "names-blk2", "names-blk3",
            "ui-blk1", "intro-blk1"):
    PAIRS.append((OUT / f"{tag}.tsv", O / f"{tag}.zh.tsv", tag))

ok_all = True
name_map = collections.defaultdict(dict)   # 原文 -> {tag: 译文}
for src, dst, tag in PAIRS:
    print("=" * 74)
    print(f"### {tag}")
    if not dst.exists():
        print("  ✗ 输出文件不存在"); ok_all = False; continue
    sin = read_any(src)[0].splitlines()
    txt, enc = read_any(dst)
    sout = txt.splitlines()
    ids_in = [l.split("\t", 1)[0] for l in sin if l.strip()]
    ids_out, bad_tab, empty, repl = [], [], [], []
    for l in sout:
        if not l.strip():
            continue
        if l.count("\t") != 1:
            bad_tab.append(l[:60]); continue
        k, v = l.split("\t", 1)
        ids_out.append(k)
        if not v.strip():
            empty.append(k)
        if "\ufffd" in v:
            repl.append(k)
    print(f"  编码={enc}  输入行={len(ids_in)}  输出行={len(ids_out)}  "
          f"{'✓行数一致' if len(ids_in)==len(ids_out) else '✗行数不一致'}")
    if ids_in != ids_out:
        ok_all = False
        miss = set(ids_in) - set(ids_out); extra = set(ids_out) - set(ids_in)
        print(f"    缺失行号 {sorted(miss)[:10]}  多余行号 {sorted(extra)[:10]}")
        print(f"    顺序是否一致: {ids_in == sorted(ids_out)}")
    if bad_tab: ok_all = False; print(f"  ✗ TAB 异常 {len(bad_tab)} 行: {bad_tab[:3]}")
    if empty:   ok_all = False; print(f"  ✗ 空译文 {len(empty)} 行: {empty[:10]}")
    if repl:    ok_all = False; print(f"  ✗ 含替换字符 U+FFFD {len(repl)} 行: {repl[:10]}")
    if not (bad_tab or empty or repl) and ids_in == ids_out:
        print("  ✓ 格式全部通过")
    # 记录原文-译文对（用于跨批一致性）
    src_map = dict(l.split("\t", 1) for l in sin if l.strip())
    for l in sout:
        if l.count("\t") != 1: continue
        k, v = l.split("\t", 1)
        o = src_map.get(k)
        if o:
            name_map[o][tag] = v

# 跨批一致性
print()
print("=" * 74)
print("### 跨批次同名/同原文译法一致性")
print("=" * 74)
conflict = 0
for orig, d in name_map.items():
    vals = set(d.values())
    if len(vals) > 1:
        conflict += 1
        if conflict <= 25:
            print(f"  ✗ {orig!r}")
            for t, v in sorted(d.items()):
                print(f"       {t:12s} → {v}")
print(f"\n冲突总数: {conflict}（跨文件出现同名且译法不同的条目数）")
print()
print("总体:", "✓ 全部通过" if ok_all and conflict == 0 else "⚠ 需修复")
