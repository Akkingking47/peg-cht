# -*- coding: utf-8 -*-
"""修正不一致 → 合并 → 生成 TEXT-ZH 分发包（UTF-8 预览 + GBK 部署）。"""
import pathlib, re

ROOT = pathlib.Path(r"D:\OpenPG2")
EF = ROOT / "EFILE_NASHORNPBEM"
OUT = pathlib.Path(r"D:\DSH\军事游戏汉化\work\efile-nashornpbem")
O = OUT / "out"
DIST = OUT / "dist"
DIST.mkdir(exist_ok=True)

def read_any(p):
    b = p.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return b.decode(enc)
        except Exception:
            continue
    return b.decode("gbk", errors="replace")

def raw_lines(p):
    """返回 [(原始字节行首, 行尾字节)]，行尾 b'\r\n' / b'\n' / b''"""
    raw = p.read_bytes()
    parts = raw.split(b"\n")
    out = []
    for i, lb in enumerate(parts):
        if i == len(parts) - 1 and lb == b"":
            out.append((b"", b""))   # 末尾空
            break
        if lb.endswith(b"\r"):
            out.append((lb[:-1], b"\r\n"))
        else:
            out.append((lb, b"\n"))
    return out

# ---------- 1. 载入分块译文（按行号） ----------
zh_eq, zh_nm = {}, {}
for tag, tgt in (("equip-blk1", zh_eq), ("equip-blk2", zh_eq), ("equip-blk3", zh_eq),
                 ("names-blk1", zh_nm), ("names-blk2", zh_nm), ("names-blk3", zh_nm)):
    for l in read_any(O / f"{tag}.zh.tsv").splitlines():
        if l.count("\t") != 1:
            continue
        k, v = l.split("\t", 1)
        tgt[int(k)] = v

zh_nat, zh_ui = {}, {}
for l in read_any(O / "ui-blk1.zh.tsv").splitlines():
    if l.count("\t") != 1:
        continue
    k, v = l.split("\t", 1)
    if k.startswith("N"):
        zh_nat[int(k[1:])] = v
    elif k.startswith("S"):
        zh_ui[int(k[1:])] = v

zh_intro = {}
for l in read_any(O / "intro-blk1.zh.tsv").splitlines():
    if l.count("\t") != 1:
        continue
    k, v = l.split("\t", 1)
    zh_intro[int(k)] = v

print(f"载入：equip={len(zh_eq)} names={len(zh_nm)} nations={len(zh_nat)} "
      f"strings_efile={len(zh_ui)} intro={len(zh_intro)}")

# ---------- 2. 全局修正 ----------
FIX = {
    "阿德莱里奇": "阿德勒里奇",
    "空运": None, "": None,
}
# 2a. 6 条跨批不一致 —— 按统一译法全局替换
UNIFY = {
    "Adleric": "阿德勒里奇",
    "Air Transport": "运输机",
    "Hv Fortified Base": "重型筑垒基地",
    "Ingesson": "英格松",
    "Staff Car": "参谋车",
    "Stjernkvist": "谢恩奎斯特",
}
# 原文 → 统一译法：逐行按原文本对照替换
for tag, tgt in (("equip-blk1", zh_eq), ("equip-blk2", zh_eq), ("equip-blk3", zh_eq),
                 ("names-blk1", zh_nm), ("names-blk2", zh_nm), ("names-blk3", zh_nm)):
    src = read_any(OUT / f"{tag}.tsv").splitlines()
    smap = {l.split("\t", 1)[0]: l.split("\t", 1)[1] for l in src if l.strip()}
    fixed = 0
    for k, v in list(tgt.items()):
        o = smap.get(str(k))
        if o in UNIFY and v != UNIFY[o]:
            tgt[k] = UNIFY[o]; fixed += 1
    if fixed:
        print(f"  {tag}: 统一译法修正 {fixed} 处")
# 2b. (not used) 注记统一保留原文
NU = 0
for d in (zh_eq,):
    for k, v in list(d.items()):
        nv = v.replace("（未使用）", "(not used)").replace("(未使用)", "(not used)")
        if nv != v:
            d[k] = nv; NU += 1
print(f"  (not used) 注记还原: {NU} 处")

# ---------- 3. 复用表 ----------
def load_reuse(efile, fname):
    a = (ROOT / efile / fname).read_bytes().decode("gbk", errors="replace").splitlines()
    b = (ROOT / efile / "TEXT-ZH" / fname).read_bytes().decode("gbk", errors="replace").splitlines()
    m = {}
    for x, y in zip(a, b):
        if x != y and y.strip():
            m.setdefault(x, y)
    return m

REUSE = {}
for f in ("equip.txt", "names.txt", "nations.txt"):
    r = {}
    for ef in ("EFILE_OLGWW2", "EFILE_OPENPG"):
        r.update(load_reuse(ef, f))
    REUSE[f] = r
    print(f"  复用表 {f}: {len(r)} 条")

# ---------- 4. 构建逐行译文文件 ----------
def build(fname, zh_by_line, use_reuse=True):
    src = raw_lines(EF / fname)
    out_lines, stat = [], {"new": 0, "reuse": 0, "keep": 0, "skip": 0}
    for idx, (core, eol) in enumerate(src, 1):
        if core == b"":
            out_lines.append(core + eol); stat["skip"] += 1; continue
        try:
            s = core.decode("gbk")
        except Exception:
            out_lines.append(core + eol); stat["skip"] += 1; continue
        s = s.rstrip("\r")
        if idx in zh_by_line:
            new = zh_by_line[idx]; stat["new"] += 1
        elif use_reuse and s in REUSE.get(fname, {}):
            new = REUSE[fname][s]; stat["reuse"] += 1
        else:
            out_lines.append(core + eol); stat["keep"] += 1; continue
        out_lines.append(new.encode("gbk") + eol)
    return b"".join(out_lines), stat

jobs = [
    ("equip.txt",          zh_eq,    "TEXT-ZH"),
    ("names.txt",          zh_nm,    "TEXT-ZH"),
    ("nations.txt",        zh_nat,   "TEXT-ZH"),
    ("strings_efile.txt",  zh_ui,    "TEXT-ZH"),
]
for fname, table, where in jobs:
    data, st = build(fname, table)
    (DIST / fname).write_bytes(data)
    print(f"  {fname:20s} 新译={st['new']:4d} 复用={st['reuse']:4d} 保留={st['keep']:4d} → {len(data)} B")

# intro（SCENARIO 文本，需覆盖原文）
data, st = build("SCENARIO/utopianparadoxintro.txt", zh_intro, use_reuse=False)
# raw_lines 已按 \n 切分，此处路径含子目录
(DIST / "utopianparadoxintro.txt").write_bytes(data)
print(f"  intro                新译={st['new']:4d} 保留={st['keep']:4d} → {len(data)} B")

print()
print("=== dist 目录 ===")
for p in sorted(DIST.iterdir()):
    print(f"  {p.name:28s} {p.stat().st_size:8d} B")
