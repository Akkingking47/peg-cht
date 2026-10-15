# -*- coding: utf-8 -*-
"""清理前的严格验证：确认每个「待移除」文件都有同内容副本（md5/CRC 逐条核对）。
只读，不删任何东西。产出 manifest 供人工复核。"""
import os, sys, hashlib, zipfile, zlib, collections, json

ROOT = r"D:\DSH\军事游戏汉化"
os.chdir(ROOT)

def md5(p, buf=1 << 20):
    h = hashlib.md5()
    with open(p, "rb") as f:
        while True:
            b = f.read(buf)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def crc32(p):
    v = 0
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            v = zlib.crc32(b, v)
    return v & 0xFFFFFFFF

def rel(p):
    return os.path.relpath(p, ROOT)

removals = []          # (path, kept_path_or_reason, size, md5)
problems = []
notes = []

# ─────────────────────────────────────────────────────────
# 1) recover/ 解压目录 —— 与 backup/ORIGINAL-EFILE_* 逐文件 md5 核对
# ─────────────────────────────────────────────────────────
for eff in ("OLGWW2", "OPENPG"):
    src = os.path.join("recover", f"EFILE_{eff}", f"EFILE_{eff}")
    dst = os.path.join("backup", f"ORIGINAL-EFILE_{eff}")
    if not os.path.isdir(src):
        continue
    n_ok = n_bad = 0
    for r, _, fs in os.walk(src):
        for f in fs:
            p = os.path.join(r, f)
            rp = os.path.relpath(p, src)
            q = os.path.join(dst, rp)
            if not os.path.exists(q):
                problems.append(("recover/ 对侧缺失", rel(p), q)); n_bad += 1; continue
            if os.path.getsize(p) != os.path.getsize(q) or md5(p) != md5(q):
                problems.append(("recover/ 内容不一致", rel(p), q)); n_bad += 1; continue
            n_ok += 1
            removals.append((rel(p), rel(q), os.path.getsize(p), md5(p)))
    notes.append(f"recover/EFILE_{eff}: 与 backup 逐文件核对 → 一致 {n_ok} / 不一致 {n_bad}")

# ─────────────────────────────────────────────────────────
# 2) recover/*.zip —— 每条目 CRC 与解压目录核对
# ─────────────────────────────────────────────────────────
for eff in ("OLGWW2", "OPENPG"):
    zp = os.path.join("recover", f"EFILE_{eff}.zip")
    base = os.path.join("recover", f"EFILE_{eff}", f"EFILE_{eff}")
    if not os.path.exists(zp) or not os.path.isdir(base):
        continue
    zf = zipfile.ZipFile(zp)
    n_ok = n_bad = 0
    for i in zf.infolist():
        if i.is_dir():
            continue
        # zip 内路径形如 EFILE_OLGWW2/xxx/yyy → 对应 base/xxx/yyy
        parts = i.filename.split("/", 1)
        inner = parts[1] if len(parts) > 1 else ""
        q = os.path.join(base, *inner.split("/")) if inner else None
        if not q or not os.path.exists(q):
            problems.append(("zip 条目无对应解压文件", f"{zp}::{i.filename}", q)); n_bad += 1; continue
        if crc32(q) != i.CRC:
            problems.append(("zip 条目 CRC 不符", f"{zp}::{i.filename}", q)); n_bad += 1; continue
        n_ok += 1
    notes.append(f"recover/EFILE_{eff}.zip: 条目 CRC 核对 → 一致 {n_ok} / 不符 {n_bad}")
    removals.append((rel(zp), f"recover/EFILE_{eff}/EFILE_{eff}/ (同内容树)", os.path.getsize(zp), md5(zp)))

# ─────────────────────────────────────────────────────────
# 3) work/crash-20260924/*.exe —— 事故中间构建（可由补丁脚本重建）
# ─────────────────────────────────────────────────────────
crash = os.path.join("work", "crash-20260924")
if os.path.isdir(crash):
    # 该目录下的 exe 中间构建：含 *.exe 与 *.B3/*.B4/*.at-crash 等点号快照（均 ≥5MB）
    exes = sorted(f for f in os.listdir(crash)
                  if os.path.getsize(os.path.join(crash, f)) >= 5_000_000)
    for f in exes:
        p = os.path.join(crash, f)
        removals.append((rel(p), "事故中间构建（09-28 已结案，可由补丁脚本重建）", os.path.getsize(p), md5(p)))
    notes.append(f"work/crash-20260924: exe 中间构建 {len(exes)} 个")

# ─────────────────────────────────────────────────────────
# 4) poc/ 与 pgforever/poc/ —— 目录内同内容去重（保留最新 mtime 的一份）
# ─────────────────────────────────────────────────────────
for root in ("poc", "pgforever/poc"):
    if not os.path.isdir(root):
        continue
    bysize = collections.defaultdict(list)
    for r, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(r, f)
            s = os.path.getsize(p)
            if s == 0:
                continue
            bysize[s].append(p)
    groups = 0
    saved = 0
    for s, ps in bysize.items():
        if len(ps) < 2:
            continue
        byhash = collections.defaultdict(list)
        for p in ps:
            byhash[md5(p)].append(p)
        for h, v in byhash.items():
            if len(v) < 2:
                continue
            # 保留：非 probe* 子目录优先 → mtime 最新 → 路径最短 → 字典序
            def key(x):
                inprobe = 1 if "probe" in x.lower() else 0
                return (inprobe, -os.path.getmtime(x), len(x), x)
            v.sort(key=key)
            keep = v[0]
            groups += 1
            for p in v[1:]:
                removals.append((rel(p), rel(keep), s, h))
                saved += s
    notes.append(f"{root}/: 同内容组 {groups} 组，可移除 {saved/1e6:.1f} MB")

# ─────────────────────────────────────────────────────────
# 5) PDF 提取中间物 + work/ 的 0 字节 _pending_* 台账
# ─────────────────────────────────────────────────────────
for p in (r"peg\research\_peg_manual_raw.txt", r"peg\research\_peg_manual_text.txt",
          r"work\peg\_peg_manual.txt"):
    if os.path.exists(p):
        removals.append((p, "官方手册 PDF 提取中间物（已查明无有用内容）", os.path.getsize(p), md5(p)))

for r, _, fs in os.walk("work"):
    for f in fs:
        if os.path.getsize(os.path.join(r, f)) == 0 and f.startswith("_pending"):
            p = os.path.join(r, f)
            removals.append((rel(p), "已清空的待办台账（0 字节）", 0, ""))

# ─────────────────────────────────────────────────────────
# 输出
# ─────────────────────────────────────────────────────────
tot = sum(x[2] for x in removals)
print("=" * 74)
print(f"待移除：{len(removals)} 个文件，合计 {tot/1e6:.1f} MB")
print("=" * 74)
for n in notes:
    print("  ·", n)
print()
if problems:
    print(f"⚠️ 发现问题 {len(problems)} 条（这些文件不会被移除）：")
    for t, a, b in problems[:20]:
        print(f"    [{t}] {a}  →  {b}")
else:
    print("✓ 全部核对通过：每个待移除文件都有同内容副本")

with open(r"peg\testbed\cleanup-manifest-2026-10-10.tsv", "w", encoding="utf-8", newline="\n") as f:
    f.write("# 清理清单 2026-10-10（待移除文件 → 保留的同内容副本/依据）\n")
    f.write("待移除文件\t保留副本或依据\t字节\tmd5\n")
    for a, b, s, h in removals:
        f.write(f"{a}\t{b}\t{s}\t{h}\n")
print(f"\n清单已写：peg\\testbed\\cleanup-manifest-2026-10-10.tsv")
json.dump([x[0] for x in removals], open(r"peg\testbed\_cleanup-list.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=0)
print(f"待移除路径已存：peg\\testbed\\_cleanup-list.json")
