#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""梳理 · 按裁定表统一 `ww2-scn-map.tsv` 里的**段级同词异译**。

读两张表：
  * `glossary\\layers\\seg-canon.tsv`            —— 段级规则（61 组真冲突）
      列：en_seg | 规范译名 | 依据 | 原分布 | 仅当(en行正则) | 排除(en行正则)
  * `glossary\\layers\\seg-canon-outliers.tsv`   —— 孤立异常行（精确匹配 en 行）
      列：en行 | 段en | 现行段zh | 应为段zh | 依据

做法（保留原分隔符与两侧空格）：
  1. `re.split(r'(/)', zh)` ⇒ 分隔符 `'/'` 作为 token 保留（段在偶数下标 0,2,4…），
     因此 `A/ B /C` 的空格风格原样不动。
  2. 按段位对齐 en 与 zh（段数不等 ⇒ 整行跳过并计数）。
  3. `en_seg` 命中规则且 `zh_seg.strip() != 规范译名`、且该行**不匹配排除正则** ⇒
     只替换 `strip()` 后的内容（前导/尾随空格保留）。
  4. 孤立异常行：整行 en 精确相等且该段位现值等于 `现行段zh` ⇒ 改写。
  5. 只动 `zh` 列，`en`/`src` 列不变；改完逐行自校验（段数一致、`/` 个数一致）。

用法：`python fix_map_segments.py [--apply]`（默认 dry-run）
备份：`backup\\before-seg-canon\\ww2-scn-map.tsv`
"""
import io
import os
import re
import shutil
import sys
from collections import Counter

WS = r"D:\DSH\军事游戏汉化"
MAP = os.path.join(WS, "pegww2", "research", "ww2-scn-map.tsv")
CANON = os.path.join(WS, "glossary", "layers", "seg-canon.tsv")
OUTL = os.path.join(WS, "glossary", "layers", "seg-canon-outliers.tsv")
BK = os.path.join(WS, "backup", "before-seg-canon")


def load_rulings():
    """en_seg → (规范译名, 仅当re, 排除re)"""
    r = {}
    for l in io.open(CANON, encoding="utf-8"):
        s = l.rstrip("\r\n")
        if not s or s.startswith("#"):
            continue
        c = s.split("\t")
        if len(c) >= 2 and c[0].strip():
            r[c[0].strip()] = (c[1].strip(),
                               (c[4].strip() if len(c) > 4 else ""),
                               (c[5].strip() if len(c) > 5 else ""))
    return r


def load_outliers():
    """[(en行, 段en, 现行段zh, 应为段zh, 依据)]"""
    o = []
    for l in io.open(OUTL, encoding="utf-8"):
        s = l.rstrip("\r\n")
        if not s or s.startswith("#"):
            continue
        c = s.split("\t")
        if len(c) >= 4 and c[0].strip():
            o.append((c[0], c[1].strip(), c[2].strip(), c[3].strip(),
                      c[4] if len(c) > 4 else ""))
    return o


def main():
    apply_ = "--apply" in sys.argv
    R = load_rulings()
    O = load_outliers()
    print("段级规则 %d 条 · 孤立异常行 %d 条" % (len(R), len(O)))
    if not R:
        print("❌ 裁定表为空")
        return 1
    lines = io.open(MAP, encoding="utf-8-sig").read().split("\n")
    hit = Counter()
    ohit = Counter()
    srcmix = Counter()
    rows_changed = 0
    aligned_fail = 0
    out = []
    for l in lines:
        s = l.rstrip("\r")
        if not s or s.startswith("#") or "\t" not in s:
            out.append(l)
            continue
        c = s.split("\t")
        if len(c) < 3 or "/" not in c[0] or "/" not in c[1]:
            out.append(l)
            continue
        et = re.split(r"(/)", c[0])
        zt = re.split(r"(/)", c[1])
        en_segs = [x.strip() for x in et[0::2]]
        zh_segs = [x.strip() for x in zt[0::2]]
        if len(en_segs) != len(zh_segs):
            aligned_fail += 1
            out.append(l)
            continue
        changed = False

        def put(i, new):
            nonlocal changed
            tok = zt[2 * i]
            st = tok.strip()
            if not st or st == new:
                return False
            zt[2 * i] = tok.replace(st, new, 1)
            zh_segs[i] = new
            changed = True
            return True

        # ① 段级规则
        # 复合番号（`2/7 R`、`1/4 Bde`、`9/102 Trento`）**不再豁免**：语料实测 83% 的复合
        # 尾段保留「第」（`第9/第102特伦托师`），且同一英文段在一份成品里出现两种写法时
        # 玩家直接看得到（`_seg_filecheck.py` 实测 12 组同文件并列）⇒ 段级全局一致优先。
        for i, e in enumerate(en_segs):
            if e not in R:
                continue
            canon, only_re, exc_re = R[e]
            if only_re and not re.search(only_re, c[0]):
                continue
            if exc_re and re.search(exc_re, c[0]):
                continue
            if put(i, canon):
                hit[e] += 1
        # ② 孤立异常行（精确匹配 en 行）
        for (erow, eseg, zfrom, zto, why) in O:
            if erow != c[0]:
                continue
            for i, e in enumerate(en_segs):
                if e == eseg and zh_segs[i] == zfrom:
                    if put(i, zto):
                        ohit["%s:%s" % (erow, eseg)] += 1
        if changed:
            new_zh = "".join(zt)
            nz = re.split(r"(/)", new_zh)
            if (len(nz[0::2]) != len(en_segs)
                    or new_zh.count("/") != c[1].count("/")):
                print("❌ 自校验失败，跳过该行：%s" % s[:80])
                out.append(l)
                continue
            c[1] = new_zh
            out.append("\t".join(c))
            rows_changed += 1
            srcmix[c[2].strip()] += 1
        else:
            out.append(l)
    print("段数不等(跳过) %d 行" % aligned_fail)
    print("**改动行 %d** · 命中段 %d 种 · 孤立异常 %d 处" % (rows_changed, len(hit), sum(ohit.values())))
    print("   改动行来源分布：%s" % dict(srcmix))
    for e, n in hit.most_common():
        print("   %-30s %-26s ×%d" % (e, R[e][0], n))
    for k, n in ohit.most_common():
        print("   [孤立] %-40s ×%d" % (k, n))
    for (erow, eseg, zfrom, zto, why) in O:
        if "%s:%s" % (erow, eseg) not in ohit:
            print("⚠️ 孤立异常未命中：%s 段=%s 期望现值=%s" % (erow, eseg, zfrom))
    missed = [e for e in R if e not in hit]
    if missed:
        print("⚠️ 未命中的段级规则 %d 条（可能原文拼写不同或已一致）：" % len(missed))
        for e in missed:
            print("   %r → %s" % (e, R[e][0]))
    if not apply_:
        print("\n（dry-run；加 --apply 写入）")
        return 0
    os.makedirs(BK, exist_ok=True)
    dst = os.path.join(BK, "ww2-scn-map.tsv")
    if not os.path.isfile(dst):
        shutil.copy2(MAP, dst)
        print("备份 → %s" % dst)
    else:
        print("备份已存在（未覆盖）→ %s" % dst)
    with io.open(MAP, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out))
    print("已写入 %s" % MAP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
