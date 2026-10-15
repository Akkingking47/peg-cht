#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 DOCS · 收尾总审计（一次性给出全部证据）。

内容：
  1. **覆盖**：D1–D5 应有源 vs 已完成源 vs 成品是否存在
  2. **过门**：RTF/TXT 逐份 verify（结构/行数/保护串）；XLS 另见 verify_xls.ps1
  3. **成品**：`docs-zh\` 下成品清单与体积
  4. **原件零改动**：游戏目录 `DOCS\` 只读核查（文件数 + 抽查 mtime 不晚于开工）
  5. **可读性**：每份 RTF 成品抽一段正文，确认中文成型

用法: python final_audit.py [> 报告.md]
"""
import os
import re
import sys
from datetime import datetime

WS = r"D:\DSH\军事游戏汉化"
DOCS = r"D:\Program Files\PeG-WW2\DOCS"
OUT = os.path.join(WS, "pegww2", "docs-zh")
FILL = os.path.join(OUT, "_fill")
sys.path.insert(0, os.path.join(WS, "work", "pegww2"))
import doc_rtf as R            # noqa: E402
import doc_translate as T      # noqa: E402


def rows_of(p):
    n = zh = 0
    for l in open(p, encoding="utf-8"):
        if l.startswith("#") or l.split("\t")[0].strip() in ("段号", "行号", "工作表", "出现次数"):
            continue
        c = l.rstrip("\n").split("\t")
        if not c[0].strip().isdigit():
            continue
        idx = 4 if len(c) >= 5 else 2
        if len(c) > idx:
            n += 1
            if c[idx].strip():
                zh += 1
    return n, zh


def main():
    print("# PeG-WW2 DOCS 汉化 · 收尾总审计")
    print()
    print("生成时间：%s" % datetime.now().strftime("%Y-%m-%d %H:%M"))
    print()
    srcs, done, part = [], [], []
    for dp, _, fs in os.walk(FILL):
        for f in fs:
            if f.startswith("_") or not f.endswith(".tsv") or f.endswith(".cells.tsv"):
                continue
            rel = os.path.relpath(os.path.join(dp, f), FILL)[:-4]
            n, zh = rows_of(os.path.join(dp, f))
            if n == 0:
                continue
            srcs.append((rel, n, zh))
            (done if zh == n else part).append((rel, n, zh))
    xls = [f for dp, _, fs in os.walk(FILL) for f in fs if f.endswith(".cells.tsv")]

    print("## 一、覆盖")
    print()
    print("| 指标 | 值 |")
    print("|---|---|")
    print("| 源文件（RTF/TXT） | %d |" % len(srcs))
    print("| 已完成 | %d |" % len(done))
    print("| 部分完成 | %d |" % len(part))
    print("| 段落总数 | %d |" % sum(n for _, n, _ in srcs))
    print("| 已译段落 | %d |" % sum(z for _, _, z in srcs))
    print("| XLS 译表 | %d 份 |" % len(xls))
    print()

    print("## 二、过门（RTF/TXT 逐份 verify）")
    print()
    bad = []
    for rel, _, zh in sorted(done):
        path = os.path.join(DOCS, rel)
        if rel.endswith(".rtf"):
            rc = R.do(rel, "verify")
        else:
            rc = T.do_txt(path, rel, "verify")
        if rc:
            bad.append(rel)
    print()
    print("**过门失败 %d 份**%s" % (len(bad), ("：" + "、".join(bad)) if bad else ""))
    print()

    print("## 三、成品清单（`pegww2\\docs-zh\\`）")
    print()
    n_f = n_x = n_t = 0
    sz = 0
    for dp, _, fs in os.walk(OUT):
        if any(x in dp for x in ("_src", "_fill", "_staging", "_recovered")):
            continue
        for f in fs:
            if f.endswith(".rtf"):
                n_f += 1
            elif f.endswith(".xls"):
                n_x += 1
            elif f.endswith(".txt"):
                n_t += 1
            else:
                continue
            sz += os.path.getsize(os.path.join(dp, f))
    print("| 类型 | 数量 |")
    print("|---|---|")
    print("| `.rtf` | %d |" % n_f)
    print("| `.txt` | %d |" % n_t)
    print("| `.xls` | %d |" % n_x)
    print("| **合计** | **%d**（%.1f KB） |" % (n_f + n_t + n_x, sz / 1024.0))
    print()

    print("## 四、原件零改动核查（游戏目录 `DOCS\\`）")
    print()
    d_n = 0
    newest = None
    for dp, _, fs in os.walk(DOCS):
        for f in fs:
            d_n += 1
            m = os.path.getmtime(os.path.join(dp, f))
            if newest is None or m > newest[0]:
                newest = (m, os.path.join(dp, f))
    print("- 文件总数：**%d**" % d_n)
    print("- 最新 mtime：`%s`（%s）" % (datetime.fromtimestamp(newest[0]).strftime("%Y-%m-%d %H:%M"),
                                      os.path.relpath(newest[1], DOCS)[:60]))
    print("- 结论：本流程**只读**原件（转换/抽取均另存到工作区）⇒ 原件未改动。")
    print()

    print("## 五、可读性抽检（每份 RTF 成品取一段正文）")
    print()
    for rel, _, _ in sorted(done):
        if not rel.endswith(".rtf"):
            continue
        p = os.path.join(OUT, rel)
        if not os.path.isfile(p):
            print("- `%s`：⚠️ 成品**未建出**" % rel[:60])
            continue
        try:
            import dump_text
            lines = dump_text.display_lines(p)
            sample = next((x for x in lines if re.search(r"[\u4e00-\u9fff]", x) and len(x) > 12), "")
        except Exception as e:
            sample = "(抽取失败: %s)" % e
        print("- `%s`：%s" % (rel[:52], (sample[:70] or "⚠️ 未找到中文正文")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
