#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 `fix_tarnopol_6v.py` 写进覆盖表的改动**落盘**（铁律三：先重建到临时 → 回读校验 → 才写正式）。

流程（任一步不过 ⇒ 中止，一个字节都不写正式目录）：
  ① 读覆盖表，确认目标 2 条在表里；
  ② **临时目录重建**（`gen_scn.OUTROOT` 指到 `work/glossary/_rebuild-tmp`）——
     不碰 `testbed/out` 与游戏目录；
  ③ 临时产物 vs `testbed/out` **逐文件 md5 比对**：必须**只有目标文件**不同
     （证明本次重建对其余 3778 个文件是 no-op，没有夹带别的改动）；
  ④ 备份 `out` 与游戏目录里的目标文件到 `backup/before-tarnopol-6v/`；
  ⑤ 写 `.new` → 回读逐字节比对 → 才 `os.replace` 覆盖正式文件；
  ⑥ 终检：正式文件 md5 == 临时产物 md5，并打印 4 行实况。

用法: python deploy_tarnopol_6v.py [--apply]
"""
import hashlib
import io
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
SUB = "SCENARIO"
FN = "RM_usvsruss6v.txt"
OVF = os.path.join(WS, "pegww2", "research", "_scn-file-overrides.tsv")
OUT = os.path.join(WS, "pegww2", "testbed", "out", SUB)
GAME = os.path.join(r"D:\Program Files\PeG-WW2", SUB)
TMPROOT = os.path.join(WS, "work", "glossary", "_rebuild-tmp")
COPYBK = os.path.join(WS, "backup", "before-tarnopol-6v")
EVID = os.path.join(WS, "glossary", "evidence")

sys.path.insert(0, os.path.join(WS, "work", "pegww2"))


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def walk_hashes(root):
    out = {}
    for dp, _dn, fns in os.walk(root):
        for f in fns:
            p = os.path.join(dp, f)
            out[os.path.relpath(p, root).replace("\\", "/")] = md5(p)
    return out


def main():
    apply_ = "--apply" in sys.argv
    reuse = "--reuse-tmp" in sys.argv      # 复用上一次已建好的临时产物（省一次全量重建）
    # ① 覆盖表
    rows = [l.rstrip("\n") for l in io.open(OVF, encoding="utf-8")
            if not l.startswith("#") and l.split("\t")[:2] == [SUB, FN]]
    print("① 覆盖表中 %s/%s 的条目：%d 条" % (SUB, FN, len(rows)))
    for l in rows:
        c = l.split("\t")
        print("    行%-3s → %s" % (c[2], c[4]))
    if len(rows) != 2:
        print("   ⛔ 预期 2 条，实际 %d 条 ⇒ 中止（先跑 fix_tarnopol_6v.py --apply）" % len(rows))
        return 1

    # ② 临时目录重建
    if reuse and os.path.isdir(os.path.join(TMPROOT, SUB)):
        print("\n② 复用既有临时产物（--reuse-tmp，跳过重建）：%s" % os.path.join(TMPROOT, SUB))
    else:
        if os.path.isdir(TMPROOT):
            shutil.rmtree(TMPROOT)
        os.makedirs(TMPROOT, exist_ok=True)
        import gen_scn
        gen_scn.OUTROOT = TMPROOT      # ⭐ 只改这一处：构建输出改到临时目录
        print("\n② 临时目录重建（OUTROOT → %s）……" % TMPROOT)
        gen_scn.main()
    tp = os.path.join(TMPROOT, SUB, FN)
    if not os.path.isfile(tp):
        print("   ⛔ 临时产物缺失 %s" % tp)
        return 1

    # ③ 逐文件比对 —— 注意：OUT 指向的就是 SCENARIO 目录本身，
    #    所以左边必须取 TMPROOT/SCENARIO，两边相对路径才是同一个命名空间。
    ht, ho = walk_hashes(os.path.join(TMPROOT, SUB)), walk_hashes(OUT)
    diff = sorted(k for k in ht if ho.get(k) != ht[k])
    extra = sorted(k for k in ho if k not in ht)
    print("\n③ 临时产物 %d 个 · 现有 out %d 个 · 内容不同 %d 个 · out 多出 %d 个"
          % (len(ht), len(ho), len(diff), len(extra)))
    for k in diff:
        print("   Δ %s" % k)
    if extra:
        print("   （out 多出：%s%s）" % (", ".join(extra[:5]), " …" if len(extra) > 5 else ""))
    want = FN                          # 两侧根都指向 SCENARIO 目录，键即文件名
    if diff != [want]:
        print("   ⛔ 预期「只有 %s 不同」，实际 %s ⇒ 中止，未写任何正式文件" % (want, diff))
        return 1

    # ④⑤⑥ 部署
    gp = os.path.join(GAME, FN)
    print("\n④ 部署目标\n     out : %s  md5=%s\n     game: %s  md5=%s"
          % (os.path.join(OUT, FN), md5(os.path.join(OUT, FN)), gp, md5(gp)))
    if not apply_:
        print("\n（dry-run；加 --apply 才写正式文件）")
        return 0
    os.makedirs(COPYBK, exist_ok=True)
    for tag, p in (("out", os.path.join(OUT, FN)), ("game", gp)):
        b = os.path.join(COPYBK, "%s_%s" % (tag, FN))
        if not os.path.isfile(b):
            shutil.copy2(p, b)
            print("   备份 %s ⇒ %s" % (tag, b))
    tmd5 = md5(tp)
    for tag, p in (("out", os.path.join(OUT, FN)), ("game", gp)):
        new = p + ".new"
        shutil.copy2(tp, new)
        if md5(new) != tmd5:                      # 回读校验
            os.remove(new)
            print("   ⛔ %s 回读校验失败 ⇒ 中止" % tag)
            return 1
        os.replace(new, p)
        if md5(p) != tmd5:
            print("   ⛔ %s 写入后校验失败" % tag)
            return 1
        print("   ✅ %s 已更新 = %s" % (tag, tmd5))

    print("\n⑥ 终检（正式文件实况）")
    for tag, d in (("out", OUT), ("game", GAME)):
        lines = io.open(os.path.join(d, FN), encoding="gbk", errors="replace").read().split("\n")
        print("   %-5s %s" % (tag, " ｜ ".join("行%d=%s" % (i, lines[i]) for i in range(4))))
    os.makedirs(EVID, exist_ok=True)
    with io.open(os.path.join(EVID, "tarnopol-6v.txt"), "w", encoding="utf-8", newline="\n") as w:
        w.write("# Tarnopol 第 7 个同族文件 · 落盘留痕\n")
        w.write("文件\t%s/%s\n临时产物md5\t%s\nout md5\t%s\ngame md5\t%s\n"
                % (SUB, FN, tmd5, md5(os.path.join(OUT, FN)), md5(gp)))
        w.write("\n覆盖条目\n")
        for l in rows:
            w.write(l + "\n")
        w.write("\n临时重建 vs out 内容不同文件数\t%d\n" % len(diff))
    print("留痕 → %s" % os.path.join(EVID, "tarnopol-6v.txt"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
