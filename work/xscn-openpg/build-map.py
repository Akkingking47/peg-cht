"""生成 EFILE_OPENPG 的 .xscn 回写映射（5 列）。

优先级：overrides（本轮新译 + 截断修正） > OLGWW2 已完成映射 > PGForever 地图地名表 > 保留原文。

输出 work\\xscn-openpg\\openpg-map.tsv，格式与 tools\\xscn-patch.ps1 的要求一致：
    <xscn 文件名> <组，-1=标题> <索引> <期望原文> <新译文>
未命中的条目一律不写入映射 —— 补丁脚本会原字节保留，无害。
"""
import pathlib
import re

W = pathlib.Path(r"D:\DSH\军事游戏汉化\work")
OUT = W / "xscn-openpg"

# ---- 输入 ----
rows = []
for ln in (W / "xscn" / "openpg-orig.tsv").read_text(encoding="utf-8").splitlines():
    c = ln.split("\t")
    if len(c) >= 5:
        rows.append((c[0], c[1], c[2], c[3]))

raw = (OUT / "overrides.tsv").read_bytes()
if raw.startswith(b"\xef\xbb\xbf"):
    print("注意：overrides.tsv 带 UTF-8 BOM，已自动剥除")
    raw = raw[3:]
(OUT / "overrides.tsv").write_bytes(raw)

over = {}
for ln in raw.decode("utf-8").splitlines():
    if not ln.strip():
        continue
    k, v = ln.split("\t")[:2]
    over[k] = v

olg = {}
for ln in (W / "xscn-all-map.tsv").read_text(encoding="utf-8").splitlines():
    c = ln.split("\t")
    if len(c) >= 5 and c[3] and c[4]:
        olg.setdefault(c[3], c[4])

pgf = {}
for ln in (W / "xscn" / "pgf-lookup.tsv").read_text(encoding="utf-8").splitlines():
    c = ln.split("\t")
    if len(c) >= 2 and c[0] and c[1]:
        pgf.setdefault(c[0], c[1])

# ---- 自检：overrides 的键必须在语料里出现过 ----
orig_set = set(r[3] for r in rows)
for k in over:
    if k not in orig_set:
        raise SystemExit("overrides 里的原文未在语料中出现：" + k)
print("overrides 自检通过：%d 条，全部命中语料" % len(over))

# ---- 生成映射 ----
out = []
stat = {"overrides": 0, "olgww2": 0, "pgforever": 0}
miss = set()
for fn, grp, idx, orig in rows:
    if not orig:
        continue
    if orig in over:
        tgt, src = over[orig], "overrides"
    elif orig in olg:
        tgt, src = olg[orig], "olgww2"
    elif orig in pgf:
        tgt, src = pgf[orig], "pgforever"
    else:
        miss.add(orig)
        continue
    stat[src] += 1
    out.append("%s\t%s\t%s\t%s\t%s" % (fn, grp, idx, orig, tgt))

# ---- 结构自检：分隔符数量一致 ----
bad = []
for line in out:
    c = line.split("\t")
    if len(c) != 5:
        bad.append(("列数异常", line))
        continue
    o, t = c[3], c[4]
    for ch in "/[]()":
        if o.count(ch) != t.count(ch):
            bad.append(("符号 %s 不匹配" % ch, line))
            break
print("分隔符自检：%d 处异常" % len(bad))
for b in bad[:20]:
    print("   ", b)

(OUT / "openpg-map.tsv").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")

print()
print("写入映射行数 :", len(out), "/ 总条目", len(rows))
print("  本轮 overrides :", stat["overrides"])
print("  复用 OLGWW2     :", stat["olgww2"])
print("  复用 PGForever  :", stat["pgforever"])
print("  未命中(保留原文):", len(miss))
if miss:
    (OUT / "untranslated.tsv").write_text(
        "\n".join(sorted(miss)) + "\n", encoding="utf-8", newline="\n")
    print("  未命中清单 ->", OUT / "untranslated.tsv")
    for u in sorted(miss):
        print("     ", u)
