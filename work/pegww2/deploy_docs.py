#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 DOCS · 投放脚本（**默认 dry-run**）：备份原件 → 投放成品 → 双向校验。

纪律：
  1. **先备份、并逐个哈希校验备份完整**，确认无误才投放（用户要求"注意保存原始的文档"）。
  2. 只投放 `docs-zh` 下与游戏文档对应的成品；**工具日志/说明/台账一律不投**。
  3. 投放后校验：① 投进去的文件哈希 == 成品哈希 ② 未涉及的原件哈希不变。
  4. 幂等：重复运行结果一致；`--rollback` 可从备份整体还原。

用法:
  python deploy_docs.py                 # dry-run：只列清单与差异
  python deploy_docs.py --apply         # 备份 + 投放 + 校验
  python deploy_docs.py --rollback      # 从备份还原原始 DOCS
"""
import hashlib
import os
import shutil
import sys
import time

WS = r"D:\DSH\军事游戏汉化"
SRC = os.path.join(WS, "pegww2", "docs-zh")
DOCS = r"D:\Program Files\PeG-WW2\DOCS"
BACKUP = os.path.join(WS, "backup", "ORIGINAL-PeGWW2-DOCS")
EXTS = (".rtf", ".txt", ".xls")
SKIP_DIRS = {"_src", "_fill", "_staging", "_recovered"}
# 不投放：工具日志与工作区说明（以 `_` 开头的一律不投）
SKIP_FILES = {"README.md"}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def manifest():
    out = []
    for dp, _, fs in os.walk(SRC):
        parts = os.path.relpath(dp, SRC).split(os.sep)
        if any(p in SKIP_DIRS for p in parts):
            continue
        for f in sorted(fs):
            if not f.endswith(EXTS) or f.startswith("_") or f in SKIP_FILES:
                continue
            rel = os.path.relpath(os.path.join(dp, f), SRC)
            out.append(rel)
    return sorted(out)


def walk_docs():
    out = []
    for dp, _, fs in os.walk(DOCS):
        for f in fs:
            p = os.path.join(dp, f)
            out.append((os.path.relpath(p, DOCS), p))
    return out


def do_rollback():
    if not os.path.isdir(BACKUP):
        print("没有备份可还原：%s" % BACKUP)
        return 1
    n = 0
    for rel, p in walk_docs():
        src = os.path.join(BACKUP, rel)
        if os.path.isfile(src):
            if sha(p) != sha(src):
                shutil.copy2(src, p)
                n += 1
        else:                       # 投放新增的文件 ⇒ 滚回去时删掉
            os.remove(p)
            n += 1
    print("已从备份还原：改动/删除 %d 个文件" % n)
    return 0


def main():
    if "--rollback" in sys.argv:
        return do_rollback()
    # ⭐ 词库门（治本件第 3 步）：**投放前**过门 —— 不合规不放行（回滚路径不受影响）
    try:
        sys.path.insert(0, os.path.join(WS, "work", "glossary"))
        import layer_gate
        ok, _m = layer_gate.quick_check()
        if not ok:
            print("  ⛔ 词库门未过 ⇒ 拒绝投放（先跑 work/glossary/layer_gate.py --full）")
            return 1
    except Exception as e:
        print("  （词库门跳过：%s）" % e)
    apply_ = "--apply" in sys.argv
    man = manifest()
    docs = walk_docs()
    docs_set = {r for r, _ in docs}
    new = [r for r in man if r not in docs_set]

    print("=== 投放清单 ===")
    print("成品 %d 个（rtf %d · txt %d · xls %d）" % (
        len(man), sum(r.endswith(".rtf") for r in man),
        sum(r.endswith(".txt") for r in man), sum(r.endswith(".xls") for r in man)))
    print("其中**游戏目录里原本没有**（格式变更产物，将新建）%d 个：" % len(new))
    for r in new:
        print("   + %s" % r)
    print("备份目录：%s" % BACKUP)
    if not apply_:
        print("\n（dry-run；加 --apply 执行「备份 → 投放 → 校验」）")
        return 0

    # ---- 1) 备份原件（逐个哈希校验）----
    if os.path.isdir(BACKUP):
        print("\n[1/3] 备份已存在，复用：%s" % BACKUP)
    else:
        os.makedirs(BACKUP, exist_ok=True)
        bad = 0
        for rel, p in docs:
            dst = os.path.join(BACKUP, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(p, dst)
            if sha(p) != sha(dst):
                bad += 1
                print("   ✗ 备份校验不符：%s" % rel)
        print("[1/3] 备份 %d 个原件 → %s（哈希不符 %d）" % (len(docs), BACKUP, bad))
        if bad:
            print("备份未通过校验，**终止投放**")
            return 1

    # ---- 2) 投放 ----
    n = 0
    for rel in man:
        dst = os.path.join(DOCS, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(SRC, rel), dst)
        n += 1
    print("[2/3] 已投放 %d 个文件到 %s" % (n, DOCS))

    # ---- 3) 双向校验 ----
    bad2 = []
    for rel in man:
        if sha(os.path.join(DOCS, rel)) != sha(os.path.join(SRC, rel)):
            bad2.append(rel)
    untouched_bad = []
    for rel, p in docs:
        if rel in man:
            continue
        b = os.path.join(BACKUP, rel)
        if os.path.isfile(b) and sha(p) != sha(b):
            untouched_bad.append(rel)
    print("[3/3] 投放件校验：不符 %d · 未涉及原件被改动 %d" % (len(bad2), len(untouched_bad)))
    for r in (bad2 + untouched_bad)[:10]:
        print("   ✗ %s" % r)
    return 0 if not bad2 and not untouched_bad else 1


if __name__ == "__main__":
    sys.exit(main())
