#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bon./Bn → 「营」误译修复执行器（对位表驱动 · 各阶段 dry-run 默认 · 幂等）。

对位表（唯一输入）：`work/_sync-audit/bon76-fix-table.tsv`
  列：file  slot  en  zh_old  zh_new  tier
  范围：44 槽 / 40 键 / 13 个 .xscn（A 组西语 Bon. 37 槽 + B 组法语 Bn/Bon 7 槽）
  分档：19-词库回填（19 键，词库已正确，只需重铺）
        21-删76   （21 键，词库与交付双错，先改词库再重铺）
  ⛔ C 组 2 槽（RSBUR03 g1#61 / RSCHI06 g1#40 的 HQ/LVXI Army）与 4 项家族译名分歧不在表内。

阶段（每次调用只做一个阶段；写盘一律需要 `--apply`）：
  backup   备份 13 个交付件 + 受影响中间层 → backup/bon76-fix-<date>/ + sha256 清单
  glossary 词库真源 glossary/standard-glossary.tsv 定点改 21 键
  layers   调既有层表链重建：glossary/ingest_layers.py --apply → converge_plan.py --apply
  zhpart   句级译文层 work/xscn/zh/part-14.tsv 定点回填 40 行
  deploy   13 个交付 .xscn 槽级定点写回（复用 ef-nashornpbem/apply_residual.parse）
  verify   只读自查：逐槽 diff / 槽数 / 定长槽阈值计数

用法:
  python bon76_apply.py backup
  python bon76_apply.py glossary --apply
  ...
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys

WS = r"D:\DSH\军事游戏汉化"
CUR = r"D:\OpenPG2\EFILE_OLGWW2\SCENARIO"
ORIG = os.path.join(WS, "backup", "ORIGINAL-EFILE_OLGWW2", "SCENARIO")
FIX = os.path.join(WS, "work", "_sync-audit", "bon76-fix-table.tsv")
DATE = "2026-10-15"
BACK = os.path.join(WS, "backup", "bon76-fix-" + DATE)
PY = r"C:\Python314\python.exe"
sys.path.insert(0, os.path.join(WS, "work", "efile-nashornpbem"))
from apply_residual import parse  # noqa: E402

MID = [
    r"work\xscn\zh\part-14.tsv",
    r"work\xscn\master-glossary.tsv",
    r"work\xscn\master-words.tsv",
    r"work\xscn\master-resolve.tsv",
    r"work\xscn-all-map.tsv",
    r"work\atomic\atomic-xscn-map.tsv",
    r"work\atomic\_xscn-crossmap.json",
    r"work\gce\gce-xscn-map.tsv",
    r"work\gce\userscen-zh.tsv",
    r"work\basekorp\_xscn-crossmap.json",
    r"glossary\standard-glossary.tsv",
    r"glossary\glossary-occ.tsv",
    r"glossary\glossary-conflicts.tsv",
    r"glossary\xscn-division-trunc.tsv",
    r"glossary\layers\common-glossary.tsv",
    r"glossary\layers\series-glossary.tsv",
    r"glossary\layers\scope-glossary.tsv",
    r"glossary\layers\common-drift.tsv",
    r"glossary\layers\converge-list.tsv",
    r"glossary\layers\scope-diff.tsv",
    r"work\efile-nashornpbem\olgww2-glossary.tsv",
]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def load_fix():
    rows = []
    txt = io.open(FIX, encoding="utf-8").read().replace("\r\n", "\n")
    for i, ln in enumerate(txt.split("\n")):
        if i == 0 or not ln.strip():
            continue
        c = ln.split("\t")
        assert len(c) == 6, "对位表格式异常行 %d: %r" % (i + 1, ln)
        f, slot, en, old, new, tier = c
        gi, idx = slot.split("#")
        rows.append({"file": f, "slot": slot, "gi": int(gi[1:]), "idx": int(idx),
                     "en": en, "old": old, "new": new, "tier": tier})
    return rows


def files_of(rows):
    out = []
    for r in rows:
        if r["file"] not in out:
            out.append(r["file"])
    return sorted(out)


def confirm(mutating):
    return ("--apply" in sys.argv) if mutating else True


# ── backup ────────────────────────────────────────────────────────────────
def stage_backup(rows):
    dd = os.path.join(BACK, "deliver")
    md = os.path.join(BACK, "midlayer")
    os.makedirs(dd, exist_ok=True)
    os.makedirs(md, exist_ok=True)
    man = ["kind\trel\tsha256\tsize"]
    n = 0
    for fn in files_of(rows):
        src = os.path.join(CUR, fn)
        dst = os.path.join(dd, fn)
        shutil.copy2(src, dst)
        man.append("deliver\t%s\t%s\t%d" % (fn, sha256(src), os.path.getsize(src)))
        n += 1
    for rel in MID:
        src = os.path.join(WS, rel)
        if not os.path.isfile(src):
            print("  ! 中间层缺失，跳过：%s" % rel)
            continue
        dst = os.path.join(md, rel.replace("\\", "__"))
        shutil.copy2(src, dst)
        man.append("midlayer\t%s\t%s\t%d" % (rel, sha256(src), os.path.getsize(src)))
        n += 1
    io.open(os.path.join(BACK, "manifest-sha256.tsv"), "w", encoding="utf-8", newline="\n") \
        .write("\n".join(man) + "\n")
    print("备份完成：%d 个文件 → %s" % (n, BACK))
    print("清单：%s" % os.path.join(BACK, "manifest-sha256.tsv"))
    return 0


# ── glossary 真源 ─────────────────────────────────────────────────────────
def stage_glossary(rows):
    bank = os.path.join(WS, "glossary", "standard-glossary.tsv")
    raw = io.open(bank, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.replace("\r\n", "\n").split("\n")
    # ⚠️ 词库键不带槽位里的尾随空格（`Bn Pon ` 槽 vs `Bn Pon` 词库行）⇒ 按 strip 归一
    want = {r["en"].strip(): r for r in rows if r["tier"].startswith("21")}
    hit = {}
    out = []
    for ln in lines:
        c = ln.split("\t")
        if len(c) >= 2 and c[0].strip() in want and "第76" in c[1]:
            r = want[c[0].strip()]
            if c[1].strip() != r["old"].strip():
                print("  ! 旧值不符 %s\n     词库=%r\n     对位=%r" % (c[0], c[1], r["old"]))
            c[1] = r["new"].rstrip()
            hit[c[0].strip()] = 1
            out.append("\t".join(c))
        else:
            out.append(ln)
    miss = [k for k in want if k not in hit]
    print("词库真源：应改 %d 键 · 实命中 %d 键" % (len(want), len(hit)))
    if miss:
        print("  !! 未命中：%s" % miss)
    if not confirm(True):
        print("(dry-run，未写入 %s)" % bank)
        return 0 if not miss else 1
    io.open(bank, "w", encoding="utf-8", newline="").write(nl.join(out))
    print("已写 %s" % bank)
    return 0 if not miss else 1


# ── 既有层表链 ────────────────────────────────────────────────────────────
def stage_layers(rows):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    for script in (r"work\glossary\ingest_layers.py", r"work\glossary\converge_plan.py"):
        p = os.path.join(WS, script)
        args = [PY, p] + (["--apply"] if confirm(True) else [])
        print("\n$ %s" % " ".join(args))
        r = subprocess.run(args, cwd=WS, env=env, capture_output=True)
        sys.stdout.write(r.stdout.decode("utf-8", "replace"))
        if r.returncode:
            sys.stderr.write(r.stderr.decode("utf-8", "replace"))
            print("!! %s rc=%d" % (script, r.returncode))
            return r.returncode
    return 0


# ── 句级译文层 ────────────────────────────────────────────────────────────
def stage_zhpart(rows):
    want = {}
    for r in rows:
        want.setdefault(r["en"], []).append(r)
    hits = {}
    for rel in (r"work\xscn\zh\part-14.tsv",):
        p = os.path.join(WS, rel)
        raw = io.open(p, encoding="utf-8", newline="").read()
        nl = "\r\n" if "\r\n" in raw else "\n"
        out = []
        for ln in raw.replace("\r\n", "\n").split("\n"):
            c = ln.split("\t")
            if len(c) >= 2 and c[0] in want:
                rs = [x for x in want[c[0]] if x["old"] == c[1]]
                if rs:
                    new = rs[0]["new"]
                elif "第76" in c[1]:
                    # 句级层比交付件滞后（词干未译，如 M. Fernandez 未作 费尔南德斯）⇒ 只删「第76」
                    new = c[1].replace("第76", "", 1)
                    print("  ~ %s 句级层词干滞后，按删「第76」处理：%r -> %r（交付侧为 %r）"
                          % (c[0], c[1], new, want[c[0]][0]["new"]))
                else:
                    out.append(ln)
                    continue
                print("    %s  %r -> %r" % (c[0], c[1], new))
                c[1] = new
                hits[c[0]] = 1
                out.append("\t".join(c))
                continue
            out.append(ln)
        print("%s：命中 %d 行" % (rel, len(hits)))
        if confirm(True):
            io.open(p, "w", encoding="utf-8", newline="").write(nl.join(out))
            print("已写 %s" % p)
    miss = [r["en"] for r in rows if r["en"] not in hits]
    if miss:
        print("  !! 句级层未命中 %d 键：%s" % (len(miss), sorted(set(miss))))
    return 0


# ── 交付 .xscn 定点写回 ───────────────────────────────────────────────────
def slots_of(path):
    data, items, meta = parse(path)
    return data, items, meta


def stage_deploy(rows):
    apply_ = confirm(True)
    total_changed = 0
    for fn in files_of(rows):
        p = os.path.join(CUR, fn)
        data, items, meta = slots_of(p)
        idx = {(g, k): (o, L) for g, k, o, L in items}
        todo = []
        for r in rows:
            if r["file"] != fn:
                continue
            key = (r["gi"], r["idx"])
            if key not in idx:
                print("  ! %s %s 槽不存在" % (fn, r["slot"]))
                continue
            off, L = idx[key]
            cur = data[off + 2:off + 2 + L].decode("gbk")
            if cur == r["new"]:
                print("  = %s %s 已是目标值（幂等跳过）" % (fn, r["slot"]))
                continue
            if cur != r["old"]:
                print("  !! %s %s 现值不符\n     实=%r\n     期=%r" % (fn, r["slot"], cur, r["old"]))
                return 1
            todo.append((off, L, r))
        if not todo:
            print("%-20s 无需改动" % fn)
            continue
        if not apply_:
            print("%-20s 拟改 %d 槽（dry-run）" % (fn, len(todo)))
            total_changed += len(todo)
            continue
        new = bytearray(data)
        for off, L, r in sorted(todo, key=lambda x: -x[0]):
            nb = r["new"].encode("gbk")
            new[off:off + 2 + L] = len(nb).to_bytes(2, "little") + nb
        tmp = p + ".new"
        open(tmp, "wb").write(bytes(new))
        d2, it2, m2 = slots_of(tmp)
        ok = (d2 == bytes(new) and m2[2] == meta[2]
              and [(g, k) for g, k, _o, _l in it2] == [(g, k) for g, k, _o, _l in items])
        if not ok:
            os.remove(tmp)
            print("  !! %s 结构校验失败，已回滚" % fn)
            return 1
        os.replace(tmp, p)
        total_changed += len(todo)
        print("%-20s OK 改 %d 槽  %d -> %d B" % (fn, len(todo), len(data), len(new)))
    print("合计改动槽：%d（对位表 %d）" % (total_changed, len(rows)))
    return 0


# ── verify ────────────────────────────────────────────────────────────────
def stage_verify(rows):
    """全量逐槽 diff：交付 vs 修复前基线（backup/bon76-fix-<date>/deliver）。
    硬约束：变化槽数 == 该文件命中槽数；其余槽逐字节不变；槽数与原始侧一致。
    """
    print("%-20s %6s %6s %6s %6s %7s %7s %7s %7s %6s" %
          ("file", "槽数", "基槽数", "原槽数", "改槽数", "20B上前", "20B后", "5汉上前", "5汉后", "判定"))
    bad = 0
    n_changed = 0
    for fn in files_of(rows):
        cur, base, org = (os.path.join(d, fn) for d in (CUR, os.path.join(BACK, "deliver"), ORIG))
        dc, ic, mc = slots_of(cur)
        db, ib, mb = slots_of(base)
        do, io_, mo = slots_of(org)
        exp = {(r["gi"], r["idx"]) for r in rows if r["file"] == fn}
        keyc = {(g, k): (o, L) for g, k, o, L in ic}
        keyb = {(g, k): (o, L) for g, k, o, L in ib}
        changed, miss, drift = set(), set(), []
        for kk in keyc:
            if kk not in keyb:
                drift.append(("槽缺失", kk))
                continue
            o, L = keyc[kk]
            ob, Lb = keyb[kk]
            same = dc[o + 2:o + 2 + L] == db[ob + 2:ob + 2 + Lb]
            if kk in exp:
                if not same:
                    changed.add(kk)
                else:
                    miss.add(kk)
            elif not same:
                drift.append(("越界改动", kk))
        over20b = sum(1 for g, k, o, L in ib if L > 20)
        over20a = sum(1 for g, k, o, L in ic if L > 20)

        def n5(data, items):
            n = 0
            for g, k, o, L in items:
                s = data[o + 2:o + 2 + L].decode("gbk", "replace")
                if len(s) > 5 and any("\u4e00" <= ch <= "\u9fff" for ch in s):
                    n += 1
            return n
        ok = (len(ic) == len(ib) == len(io_) and changed == exp and not miss and not drift)
        bad += 0 if ok else 1
        n_changed += len(changed)
        print("%-20s %6d %6d %6d %6d %7d %7d %7d %7d %6s" %
              (fn, len(ic), len(ib), len(io_), len(changed), over20b, over20a,
               n5(db, ib), n5(dc, ic), "OK" if ok else "BAD"))
        for tag, kk in drift[:5]:
            print("     !! %s 槽 %s" % (tag, kk))
        if miss:
            print("     !! 应改未改：%s" % sorted(miss)[:5])
    tot = sum(len([r for r in rows if r["file"] == f]) for f in files_of(rows))
    print("\n变化槽合计 %d / 对位表 %d · 逐槽 diff 校验：%s" %
          (n_changed, tot, "全部一致 ✅" if bad == 0 else "%d 个文件异常 ❌" % bad))
    return 0 if bad == 0 else 1


# ── A：无在册生成器两表的定点同步 ─────────────────────────────────────────
SYNC_TARGETS = [
    # (相对路径, 值列下标, 是否无表头, 键列 [文件,group,idx] 下标)
    (r"work\xscn-all-map.tsv", 4, True, (0, 1, 2)),
    (r"glossary\xscn-division-trunc.tsv", 4, False, (0, 1, 2)),
]


def stage_syncmap(rows):
    """work/xscn-all-map.tsv 与 glossary/xscn-division-trunc.tsv 定点同步。

    二者均无在册生成器（全仓 grep 只找到读取方 / §2 已封存的一次性脚本），
    只能按（文件, group, idx）定点改值列。division-trunc 的行是 ' / ' 分段形态，
    故其值取「对位表新值的第 1 段」。
    """
    tot = 0
    for rel, vcol, nohead, (fc, gc, ic) in SYNC_TARGETS:
        p = os.path.join(WS, rel)
        raw = io.open(p, encoding="utf-8", newline="").read()
        nl = "\r\n" if "\r\n" in raw else "\n"
        lines = raw.replace("\r\n", "\n").split("\n")
        seg = rel.endswith("division-trunc.tsv")
        want = {}
        for r in rows:
            v = r["new"].split("/")[0].strip() if seg else r["new"]
            want[(r["file"], str(r["gi"]), str(r["idx"]))] = (v, r["old"])
        hit, out, changed = {}, [], 0
        for i, ln in enumerate(lines):
            if nohead and not ln.strip():
                out.append(ln)
                continue
            if not nohead and i == 0:
                out.append(ln)
                continue
            c = ln.split("\t")
            key = (c[fc], c[gc], c[ic]) if len(c) > vcol else None
            # division-trunc 一个槽对应多行（按 ' / ' 分段），只有首段行带本族错误值
            if key in want and (not seg or "第76" in c[vcol]):
                new, _old = want[key]
                if c[vcol] != new:
                    c[vcol] = new
                    changed += 1
                out.append("\t".join(c))
                hit[key] = 1
                continue
            if key in want:
                hit[key] = 1
            out.append(ln)
        miss = [k for k in want if k not in hit]
        print("%-42s 应同步 %d 行 · 命中 %d 行 · 实改 %d 行" % (rel, len(want), len(hit), changed))
        if miss:
            print("  !! 未命中 %d 条：%s" % (len(miss), sorted(miss)[:8]))
        tot += len(hit)
        if not confirm(True):
            print("  (dry-run，未写入)")
            continue
        io.open(p, "w", encoding="utf-8", newline="").write(nl.join(out))
        print("  已写 %s" % p)
    print("两表同步命中合计：%d（对位表 44 槽）" % tot)
    return 0


# ── C：EFILE_GCE 同族（32 槽 + 2 个 TEXT-ZH）─────────────────────────────
CURG = r"D:\OpenPG2\EFILE_GCE"
GCE_SCN = os.path.join(CURG, "SCENARIO")
GCE_TXT = ["TEXT-ZH/USERSCEN/raceov.txt", "TEXT-ZH/SCENARIO/gcn0.txt"]
BACKG = os.path.join(BACK, "GCE")
# 授权面：SCENARIO 侧 5 个（32 槽）；USERSCEN/raceov.xscn（23 槽）需 `--with-userscen`
GCE_TARGETS = ["gcn0.xscn", "gcn1.xscn", "gcn2.xscn", "gcn3.xscn", "gcn6.xscn"]
GCE_EXTRA = ["USERSCEN/raceov.xscn"]


def gce_xscn_files():
    """返回 [(标签, 绝对路径)]；默认＝SCENARIO 侧 5 文件，加 --with-userscen 追加 USERSCEN 侧。"""
    out = [(fn, os.path.join(GCE_SCN, fn)) for fn in GCE_TARGETS]
    if "--with-userscen" in sys.argv:
        for rel in GCE_EXTRA:
            p = os.path.join(CURG, rel.replace("/", os.sep))
            if os.path.isfile(p):
                out.append((rel, p))
    return out


def gce_base(label):
    """备份/基线路径：标签含 '/' 的落子目录，其余平铺（保持已建布局）。"""
    return os.path.join(BACKG, label.replace("/", os.sep))


def gce_plan(rows):
    """现盘实测枚举 GCE 侧本族命中（.xscn 逐槽 gbk / TEXT-ZH 逐文件计数）。"""
    byold = {r["old"]: r for r in rows}
    plan, unk, files = [], [], []
    for label, p in gce_xscn_files():
        data, items, _m = parse(p)
        for g, k, o, L in items:
            s = data[o + 2:o + 2 + L].decode("gbk", "replace")
            if s in byold:
                r = byold[s]
                plan.append({"file": label, "gi": g, "idx": k, "old": s,
                             "new": r["new"], "en": r["en"], "kind": "xscn",
                             "path": p})
                if label not in files:
                    files.append(label)
            elif any(v in s for v in byold):
                unk.append((label, g, k, s))
    txt = []
    for rel in GCE_TXT:
        p = os.path.join(CURG, rel)
        if not os.path.isfile(p):
            continue
        t = io.open(p, encoding="gbk", errors="replace").read()
        for v, r in byold.items():
            n = t.count(v)
            if n:
                txt.append({"file": rel.replace("\\", "/"), "old": v,
                            "new": r["new"], "n": n, "kind": "txt"})
    return plan, txt, unk, files


def stage_gceplan(rows):
    """只读：枚举并落盘 GCE 对位表 work/_sync-audit/bon76-fix-table-gce.tsv。"""
    plan, txt, unk, files = gce_plan(rows)
    print("GCE .xscn 命中 %d 槽（%d 个文件：%s）" % (len(plan), len(files), ",".join(files)))
    for r in plan:
        print("  %-13s g%d#%-3d %-30s %r -> %r" %
              (r["file"], r["gi"], r["idx"], r["en"][:30], r["old"], r["new"]))
    print("GCE TEXT-ZH 命中 %d 键 / 合计 %d 处" %
          (len(txt), sum(t["n"] for t in txt)))
    if unk:
        print("  !! 部分匹配但非整槽相等 %d 个：%s" % (len(unk), unk[:5]))
    out = ["file\tslot\ten\tzh_old\tzh_new"]
    for r in plan:
        out.append("%s\tg%d#%d\t%s\t%s\t%s" % (r["file"], r["gi"], r["idx"], r["en"],
                                               r["old"], r["new"]))
    for t in txt:
        out.append("%s\t-\t-\t%s\t%s" % (t["file"], t["old"], t["new"]))
    if confirm(True):
        q = os.path.join(WS, "work", "_sync-audit", "bon76-fix-table-gce.tsv")
        io.open(q, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
        print("已写 %s（%d 行）" % (q, len(out) - 1))
    return 0


def stage_gcebackup(rows):
    os.makedirs(BACKG, exist_ok=True)
    man = ["kind\trel\tsha256\tsize"]
    n = 0
    # 确定性备份整个授权面（不依赖当前命中数），故 --apply 之后重跑仍得到同一份清单
    xscn_targets = [(fn, os.path.join(GCE_SCN, fn)) for fn in GCE_TARGETS]
    if "--with-userscen" in sys.argv:
        for rel in GCE_EXTRA:
            p = os.path.join(CURG, rel.replace("/", os.sep))
            if os.path.isfile(p):
                xscn_targets.append((rel, p))
    for label, src in xscn_targets:
        dst = gce_base(label)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            print("  基线已存在，保留不改：%s" % label)   # 绝不覆盖真基线
        else:
            shutil.copy2(src, dst)
        man.append("deliver\t%s\t%s\t%d" % (label, sha256(dst), os.path.getsize(dst)))
        n += 1
    for rel in GCE_TXT:
        src = os.path.join(CURG, rel)
        if not os.path.isfile(src):
            continue
        dst = os.path.join(BACKG, rel.replace("/", "__"))
        if os.path.exists(dst):
            print("  基线已存在，保留不改：%s" % rel)
        else:
            shutil.copy2(src, dst)
        man.append("deliver\t%s\t%s\t%d" % (rel, sha256(dst), os.path.getsize(dst)))
        n += 1
    io.open(os.path.join(BACK, "manifest-GCE-sha256.tsv"), "w",
            encoding="utf-8", newline="\n").write("\n".join(man) + "\n")
    print("GCE 备份完成：%d 个文件 → %s" % (n, BACKG))
    print("清单：%s" % os.path.join(BACK, "manifest-GCE-sha256.tsv"))
    return 0


def stage_gceapply(rows):
    plan, txt, unk, files = gce_plan(rows)
    if unk:
        print("  !! 存在非整槽相等的部分匹配，拒绝写入：%s" % unk[:5])
        return 1
    apply_ = confirm(True)
    nchanged = 0
    pmap = {r["path"]: r for r in plan}
    for fn in files:
        p = dict(gce_xscn_files())[fn]
        data, items, meta = parse(p)
        idx = {(g, k): (o, L) for g, k, o, L in items}
        todo = []
        for r in plan:
            if r["file"] != fn:
                continue
            off, L = idx[(r["gi"], r["idx"])]
            cur = data[off + 2:off + 2 + L].decode("gbk")
            if cur == r["new"]:
                print("  = %s g%d#%d 已是目标值（幂等跳过）" % (fn, r["gi"], r["idx"]))
                continue
            if cur != r["old"]:
                print("  !! %s g%d#%d 现值不符 实=%r 期=%r" % (fn, r["gi"], r["idx"], cur, r["old"]))
                return 1
            todo.append((off, L, r))
        if not todo:
            print("%-14s 无需改动" % fn)
            continue
        if not apply_:
            print("%-14s 拟改 %d 槽（dry-run）" % (fn, len(todo)))
            nchanged += len(todo)
            continue
        new = bytearray(data)
        for off, L, r in sorted(todo, key=lambda x: -x[0]):
            nb = r["new"].encode("gbk")
            new[off:off + 2 + L] = len(nb).to_bytes(2, "little") + nb
        tmp = p + ".new"
        open(tmp, "wb").write(bytes(new))
        d2, it2, m2 = slots_of(tmp)
        ok = (d2 == bytes(new) and m2[2] == meta[2]
              and [(g, k) for g, k, _o, _l in it2] == [(g, k) for g, k, _o, _l in items])
        if not ok:
            os.remove(tmp)
            print("  !! %s 结构校验失败，已回滚" % fn)
            return 1
        os.replace(tmp, p)
        nchanged += len(todo)
        print("%-14s OK 改 %d 槽  %d -> %d B" % (fn, len(todo), len(data), len(new)))
    for t in txt:
        p = os.path.join(CURG, t["file"].replace("/", os.sep))
        raw = io.open(p, encoding="gbk", newline="").read()
        cur_n = raw.count(t["old"])
        if cur_n == 0 and raw.count(t["new"]):
            print("  = %s 已是目标值（幂等跳过）" % t["file"])
            continue
        if cur_n != t["n"]:
            print("  !! %s 现值计数不符 实=%d 期=%d（%r）" % (t["file"], cur_n, t["n"], t["old"]))
            return 1
        if not apply_:
            print("%-40s 拟改 %d 处（dry-run）" % (t["file"], cur_n))
            nchanged += cur_n
            continue
        io.open(p, "w", encoding="gbk", newline="").write(raw.replace(t["old"], t["new"]))
        nchanged += cur_n
        print("%-40s OK 改 %d 处" % (t["file"], cur_n))
    tot = len(plan) + sum(t["n"] for t in txt)
    print("GCE 改动合计：%d 处（槽 %d + 文本 %d · 授权面 %d）" %
          (nchanged, len(plan), sum(t["n"] for t in txt), tot))
    return 0


def stage_gceverify(rows):
    """只读自查：以备份为基线做全量逐槽 diff（不依赖当前盘面，故对已修盘面同样成立）。"""
    byold = {r["old"]: r for r in rows}
    bad = 0
    print("%-24s %6s %6s %6s %6s   %s" % ("file", "槽数", "基槽数", "改槽数", "应改数", "判定"))
    pairs = gce_xscn_files()
    tot_ch = tot_exp = 0
    for fn, cur in pairs:
        base = gce_base(fn)
        if not os.path.isfile(base):
            print("%-24s （无备份基线，跳过）" % fn)
            continue
        dc, ic, _mc = slots_of(cur)
        db, ib, _mb = slots_of(base)
        exp = {(g, k) for g, k, o, L in ib
               if db[o + 2:o + 2 + L].decode("gbk", "replace") in byold}
        kc = {(g, k): (o, L) for g, k, o, L in ic}
        kb = {(g, k): (o, L) for g, k, o, L in ib}
        ch, drift, miss = set(), [], set()
        for kk in kc:
            if kk not in kb:
                drift.append(kk)
                continue
            o, L = kc[kk]
            ob, Lb = kb[kk]
            same = dc[o + 2:o + 2 + L] == db[ob + 2:ob + 2 + Lb]
            if kk in exp:
                (miss if same else ch).add(kk)
            elif not same:
                drift.append(kk)
        ok = (len(ic) == len(ib) and ch == exp and not miss and not drift)
        bad += 0 if ok else 1
        tot_ch += len(ch)
        tot_exp += len(exp)
        print("%-24s %6d %6d %6d %6d   %s" % (fn, len(ic), len(ib), len(ch), len(exp),
                                              "OK" if ok else "BAD"))
        for kk in drift[:5]:
            print("     !! 越界改动 %s" % (kk,))
        if miss:
            print("     !! 应改未改：%s" % sorted(miss)[:5])
    print("\nGCE .xscn：变化槽 %d / 基线命中槽 %d · 逐槽 diff：%s" %
          (tot_ch, tot_exp, "一致 ✅" if bad == 0 and tot_ch == tot_exp else "异常 ❌"))
    nb = {}
    for rel in GCE_TXT:
        p = os.path.join(BACKG, rel.replace("/", "__"))
        if os.path.isfile(p):
            t = io.open(p, encoding="gbk", errors="replace").read()
            nb[rel] = sum(t.count(v) for v in byold)
    print("GCE TEXT-ZH 基线命中：%s（合计 %d 处）" %
          (", ".join("%s=%d" % (k.split("/")[-1], v) for k, v in nb.items()),
           sum(nb.values())))
    print("GCE 全域复扫残留本族旧值：", end="")
    left = _sweep_old(rows, CURG)
    auth = {l.replace("/", os.sep) for l, _p in gce_xscn_files()}
    inauth = [x for x in left if any(x[0].endswith(a) for a in auth)]
    outauth = [x for x in left if x not in inauth]
    print("%d 处（授权面内 %d · 授权面外 %d）" % (len(left), len(inauth), len(outauth)))
    for f, s in inauth[:6]:
        print("     !! 授权面内残留 %s  %r" % (f, s[:44]))
    for f, s in outauth[:6]:
        print("     · 授权面外（未触碰，待裁决）%s  %r" % (f, s[:44]))
    return 0 if bad == 0 and tot_ch == tot_exp and not inauth else 1


def _sweep_old(rows, root):
    """对 root 下所有 ≤3MB 文件复扫本族旧错值（.xscn 逐槽 gbk，其余按编码链）。"""
    olds = sorted({r["old"] for r in rows})
    out = []
    for dp, _dn, fns in os.walk(root):
        for fn in fns:
            p = os.path.join(dp, fn)
            try:
                if os.path.getsize(p) > 3 << 20:
                    continue
                if fn.lower().endswith(".xscn"):
                    data, items, _m = parse(p)
                    for g, k, o, L in items:
                        s = data[o + 2:o + 2 + L].decode("gbk", "replace")
                        if any(v in s for v in olds):
                            out.append((os.path.relpath(p, root), "g%d#%d %s" % (g, k, s)))
                    continue
                b = open(p, "rb").read()
            except Exception:
                continue
            for enc in ("gbk", "cp1252"):
                try:
                    t = b.decode(enc)
                except Exception:
                    continue
                for v in olds:
                    if v in t:
                        out.append((os.path.relpath(p, root), v))
                        break
                break
    return out


def stage_globalsweep(rows):
    """只读：对 D:\\OpenPG2 全域做权威复扫 —— 所有 .xscn 逐槽 gbk 解析，
    其他文件走编码链。用于证明「本族旧值只剩哪里」。
    """
    olds = sorted({r["old"] for r in rows})
    per_ef = {}
    detail = {}
    for ef in sorted(os.listdir(r"D:\OpenPG2")):
        root = os.path.join(r"D:\OpenPG2", ef)
        if not os.path.isdir(root):
            continue
        hits = []
        for dp, _dn, fns in os.walk(root):
            for fn in fns:
                p = os.path.join(dp, fn)
                rel = os.path.relpath(p, root)
                try:
                    if fn.lower().endswith(".xscn"):
                        data, items, _m = parse(p)
                        for g, k, o, L in items:
                            s = data[o + 2:o + 2 + L].decode("gbk", "replace")
                            if any(v in s for v in olds):
                                hits.append((rel, "g%d#%d" % (g, k), s[:40]))
                        continue
                    if os.path.getsize(p) > 3 << 20:
                        continue
                    b = open(p, "rb").read()
                except Exception:
                    continue
                for enc in ("gbk", "cp1252"):
                    try:
                        t = b.decode(enc)
                    except Exception:
                        continue
                    n = sum(t.count(v) for v in olds)
                    if n:
                        hits.append((rel, "-", "文本 %d 处" % n))
                    break
        if hits:
            per_ef[ef] = len(hits)
            detail[ef] = hits
    print("%-24s %s" % ("efile", "残留本族旧值的位置数"))
    for ef, n in sorted(per_ef.items(), key=lambda x: -x[1]):
        print("%-24s %d" % (ef, n))
        for rel, loc, s in detail[ef][:6]:
            print("      %-44s %-10s %s" % (rel, loc, s))
    if not per_ef:
        print("  （全域 0 残留 ✅）")
    return 0 if not per_ef else 1


AUDIT_TARGETS = [
    r"glossary\standard-glossary.tsv", r"glossary\glossary-occ.tsv",
    r"glossary\glossary-conflicts.tsv", r"glossary\glossary-residual.tsv",
    r"glossary\xscn-division-trunc.tsv",
    r"glossary\layers\common-glossary.tsv", r"glossary\layers\common-drift.tsv",
    r"glossary\layers\scope-glossary.tsv", r"glossary\layers\converge-list.tsv",
    r"glossary\layers\scope-diff.tsv",
    r"work\xscn\master-glossary.tsv", r"work\xscn\master-words.tsv",
    r"work\xscn\master-conflicts.tsv", r"work\xscn\master-resolve.tsv",
    r"work\xscn\_xscn_dict.tsv", r"work\xscn\_prose_dict.tsv", r"work\xscn\_root_dict.tsv",
    r"work\xscn\zh\part-14.tsv",
    r"work\atomic\atomic-xscn-map.tsv", r"work\atomic\_xscn-crossmap.json",
    r"work\basekorp\_xscn-crossmap.json", r"work\basekorp\bk-xscn-map.tsv",
    r"work\gce\gce-xscn-map.tsv", r"work\gce\userscen-zh.tsv",
    r"work\xscn-all-map.tsv",
]


def stage_audit(rows, apply=False):
    """下游派生表残留审计：统计每个表里还含「旧错值」的行数、已含「新值」的行数。"""
    olds = sorted({r["old"] for r in rows})
    news = sorted({r["new"] for r in rows})
    print("%-44s %7s %7s" % ("表", "含旧值", "含新值"))
    for rel in AUDIT_TARGETS:
        p = os.path.join(WS, rel)
        if not os.path.exists(p):
            print("%-44s %7s %7s" % (rel, "缺失", "-"))
            continue
        txt = io.open(p, encoding="utf-8", errors="replace").read()
        o = sum(1 for v in olds if v in txt)
        n = sum(1 for v in news if v in txt)
        print("%-44s %7d %7d" % (rel, o, n))
    return 0


CROSS_JSONS = [r"work\atomic\_xscn-crossmap.json", r"work\basekorp\_xscn-crossmap.json"]


def stage_derivedfix(rows, apply=None):
    """跨 efile 复用词典（atomic/basekorp 的 _xscn-crossmap.json）：其生成器已退役（work/_scratch），
    故按「值」把旧译法订正为对位表新值（字节级替换 '"旧"'→'"新"'，格式零改动），
    随后由在册生成器 work/atomic|basekorp/build_map.py 重新派生 .tsv ⇒ 派生结果与重建一致。"""
    if apply is None:
        apply = "--apply" in sys.argv
    olds = {}
    for r in rows:
        olds.setdefault(r["old"], r["new"])
    for rel in CROSS_JSONS:
        p = os.path.join(WS, rel)
        b = open(p, "rb").read()
        tot = 0
        for o, nv in olds.items():
            q = ('"' + o + '"').encode("utf-8")
            c = b.count(q)
            if c:
                tot += c
                b = b.replace(q, ('"' + nv + '"').encode("utf-8"))
        print("%-34s 旧值串 %d%s" % (rel, tot, "" if apply else "（dry-run）"))
        if apply and tot:
            open(p, "wb").write(b)
    return 0


DERIVED_GENS = [r"work\atomic\build_map.py", r"work\basekorp\build_map.py",
                r"work\gce\measure_xscn_cov.py", r"work\gce\build_xscn_map.py"]


def stage_derived(rows, apply=None):
    """按依赖顺序重跑在册派生生成器（gce 侧还需 merge_userscen_parts.py --apply）。"""
    rc = 0
    for rel in DERIVED_GENS:
        r = subprocess.run([PY, os.path.join(WS, rel)], cwd=WS, capture_output=True)
        tail = (r.stdout or b"").decode("utf-8", "replace").strip().splitlines()[-2:]
        print("  %-34s rc=%d  %s" % (rel, r.returncode, " | ".join(t.strip() for t in tail)))
        rc |= r.returncode
    r = subprocess.run([PY, os.path.join(WS, r"work\gce\merge_userscen_parts.py"), "--apply"],
                       cwd=WS, capture_output=True)
    tail = (r.stdout or b"").decode("utf-8", "replace").strip().splitlines()[-2:]
    print("  %-34s rc=%d  %s" % (r"work\gce\merge_userscen_parts.py --apply", r.returncode,
                                 " | ".join(t.strip() for t in tail)))
    return rc | r.returncode


def main():
    stages = {"backup": stage_backup, "glossary": stage_glossary, "layers": stage_layers,
              "zhpart": stage_zhpart, "deploy": stage_deploy, "verify": stage_verify,
              "audit": stage_audit, "syncmap": stage_syncmap,
              "gceplan": stage_gceplan, "gcebackup": stage_gcebackup,
              "gceapply": stage_gceapply, "gceverify": stage_gceverify,
              "globalsweep": stage_globalsweep,
              "derivedfix": stage_derivedfix, "derived": stage_derived}
    if len(sys.argv) < 2 or sys.argv[1] not in stages:
        print(__doc__)
        return 2
    rows = load_fix()
    st = sys.argv[1]
    print("=== bon76_apply: %s · 对位表 %d 槽 / %d 键 / %d 文件 · apply=%s ===" %
          (st, len(rows), len({r["en"] for r in rows}), len(files_of(rows)),
           "--apply" in sys.argv))
    return stages[st](rows)


if __name__ == "__main__":
    sys.exit(main())
