# -*- coding: utf-8 -*-
"""校验 xscn 译文并生成最终回写映射。"""
import pathlib

W = pathlib.Path(r"D:\DSH\军事游戏汉化\work")
OUT = W / "efile-nashornpbem"
O = OUT / "out"

def read_any(p):
    b = p.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return b.decode(enc)
        except Exception:
            continue
    return b.decode("gbk", errors="replace")

# 输入清单
todo = []
for l in read_any(OUT / "xscn-todo.tsv").splitlines():
    if not l.strip() or l.startswith("#"):
        continue
    if l.count("\t") != 1:
        continue
    k, v = l.split("\t", 1)
    todo.append((k, v))
print(f"输入 {len(todo)} 条")

# 译文
zh = {}
bad = []
for l in read_any(O / "xscn.zh.tsv").splitlines():
    if not l.strip():
        continue
    if l.count("\t") != 1:
        bad.append(("TAB异常", l[:60])); continue
    k, v = l.split("\t", 1)
    zh[k] = v
print(f"译文 {len(zh)} 条  TAB异常 {len(bad)}")
for b in bad[:5]:
    print("   ", b)

ids_in = [k for k, _ in todo]
ids_out = list(zh.keys())
print(f"编号集合一致: {ids_in == ids_out}")
if ids_in != ids_out:
    print("  缺失:", sorted(set(ids_in) - set(ids_out))[:10])
    print("  多余:", sorted(set(ids_out) - set(ids_in))[:10])

# 空译/替换字符
empty = [k for k, v in zh.items() if not v.strip()]
repl = [k for k, v in zh.items() if "\ufffd" in v]
print(f"空译文 {len(empty)}  替换字符 {len(repl)}")
if empty: print("  ", empty[:10])
if repl: print("  ", repl[:10])

# 前后空格保留检查
sp_mismatch = []
for k, o in todo:
    v = zh.get(k, "")
    if o != o.lstrip() and v.lstrip() == "":   # 原文有前导空格，译文没有
        pass
    lo, lv = len(o) - len(o.lstrip()), len(v) - len(v.lstrip())
    to, tv = len(o) - len(o.rstrip()), len(v) - len(v.rstrip())
    if lo != lv or to != tv:
        sp_mismatch.append((k, o, v, lo, lv, to, tv))
print(f"空格不一致 {len(sp_mismatch)} 条")
for m in sp_mismatch[:10]:
    print(f"    #{m[0]} 前导 {m[3]}->{m[4]}  尾随 {m[5]}->{m[6]}   [{m[1]}] -> [{m[2]}]")

# 生成最终映射
omap = {k: v for k, v in todo}
rows = []
for l in read_any(OUT / "xscn-orig.tsv").splitlines():
    if not l.strip():
        continue
    c = l.split("\t")
    if len(c) < 5:
        continue
    if c[1] == "-1":
        rows.append(c[:5]); continue
    orig = c[3]
    n = None
    for k, o in todo:
        if o == orig:
            n = k; break
    new = (zh.get(n) or orig) if n else orig    # 空译文 → 保留原文（如单空格占位条）
    rows.append([c[0], c[1], c[2], orig, new])

with open(OUT / "xscn-map.tsv", "w", encoding="utf-8", newline="\n") as fh:
    for r in rows:
        fh.write("\t".join(r) + "\n")
changed = sum(1 for r in rows if r[3] != r[4])
print(f"\n写出 xscn-map.tsv：{len(rows)} 行，已译 {changed} 条")
print()
print("=== 抽样 12 条 ===")
n = 0
for r in rows:
    if r[3] != r[4] and n < 12:
        n += 1
        print(f"  [{r[3]}] -> [{r[4]}]")
