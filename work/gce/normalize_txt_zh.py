# -*- coding: utf-8 -*-
r"""GCE 场景 `.txt` 译文**归一化**（2026-10-08，收子代理各自为政的尾巴）。

作用对象：`txt-zh.tsv`。原表已备份 `_bak-txt-zh.pre-norm.tsv`，回滚＝拷回。

规则（每条带命中数，任一为 0 报「未命中」提示）：

  A · **补译被误当「代号保留」的方括号散文**（11 处 / 5 种 + 1 处错括号）
        `[Mensaje de Burgos]` `[Message from Burgos]` `[Handwritten message received by courier]`
        `[El coronel Aranda se aproxima…]` `[Colonel Aranda comes to greet you…]` `[Guarnicion}`
      依据：`gen_txt_zh.py` 的 `KEEP_PAT` 原为 `^\[[^\]]*\]?$`（括号一律保留），
      实测把 4 行散文原样吞掉 ⇒ 已收紧为「括号内容不含小写字母才算代号」，此处补齐译文。

  B · **敬称统一为「您」**（POLICY §五：上级对将军说话用「您」）
      子代理把**英译段**写成了「你」、**西语段**写成「您」⇒ 同一场景两段读起来不像同一个人说话。
      规则：`你` → `您`，**但 `你们` 保留**（复数不能写「您们」）。

  C · **引号统一为「」**（POLICY §四：`''X''` → `「X」`）
      子代理部分用了 `“”`。

  D · **套话统一**：`命令发自：` / `命令来自` 并存 ⇒ 收敛为 `命令来自：`。

用法: python normalize_txt_zh.py --check | --apply
"""
import argparse
import collections
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
MAP = os.path.join(HERE, "txt-zh.tsv")
BAK = os.path.join(HERE, "_bak-txt-zh.pre-norm.tsv")

# A · 补译
ADD = {
    "[Mensaje de Burgos]": "[布尔戈斯来电]",
    "[Message from Burgos]": "[布尔戈斯来电]",
    "[Handwritten message received by courier]": "[由通信员送来的手写电文]",
    "[El coronel Aranda se aproxima a felicitarte con gesto de alegría en una de las cal"
    "les de Oviedo...]": "[阿兰达上校面带喜色，在奥维耶多的一条街上迎上来向您道贺……]",
    "[Colonel Aranda comes to greet you on one of the streets in Oviedo...]":
        "[阿兰达上校在奥维耶多的一条街上迎上来向您道贺……]",
    "[Guarnicion}": "[驻军]",          # 原文括号是错字（] 写成 }）
}
# D · 套话
PHRASE = [("命令发自：", "命令来自："), ("命令发自:", "命令来自：")]


def rd2(path):
    rows = []
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2 and c[0]:
                rows.append((c[0], c[1]))
    return rows


def norm(s, hits):
    if "\u4f60" in s:
        for m in re.finditer("\u4f60", s):
            if s[m.start():m.start() + 1] == "\u4f60" and not s.startswith("\u4f60\u4eec", m.start()):
                hits["B 你→您"] += 1
        s = re.sub("\u4f60\u4eec", "\u0001", s)      # 保护「你们」
        s = s.replace("\u4f60", "\u60a8")
        s = s.replace("\u0001", "\u4f60\u4eec")
    for a, b in (("\u201c", "\u300c"), ("\u201d", "\u300d")):
        if a in s:
            hits["C 引号→「」"] += s.count(a)
            s = s.replace(a, b)
    for a, b in PHRASE:
        if a in s:
            hits["D 套话统一"] += s.count(a)
            s = s.replace(a, b)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    raw_before = io.open(MAP, encoding="utf-8").read()
    rows = rd2(MAP)
    m = {}
    for s, d in rows:
        m.setdefault(s, d)
    hits = collections.Counter()
    added = []
    for s, d in ADD.items():
        if s in m:
            if m[s] != d:
                hits["A 覆盖旧值"] += 1
        else:
            added.append(s)
        m[s] = d

    out = []
    changed = []
    for s in sorted(m):
        n = norm(m[s], hits)
        out.append((s, n))
        if n != m[s]:
            changed.append((s, m[s], n))

    print("表 %d 条；A 新增 %d 条（%s）；改值 %d 条" % (len(out), len(added), ", ".join(x[:28] for x in added), len(changed)))
    print("\n规则命中：")
    for k in ("A 覆盖旧值", "B 你→您", "C 引号→「」", "D 套话统一"):
        print("   %-14s %d" % (k, hits.get(k, 0)))
        if hits.get(k, 0) == 0:
            print("      ⚠ 未命中，请核")
    print("\n改动样例（前 12）：")
    for s, x, y in changed[:12]:
        print("   %-34s\n      %s\n   -> %s" % (s[:34], x[:70], y[:70]))

    if a.apply:
        if not os.path.exists(BAK):
            with io.open(BAK, "w", encoding="utf-8", newline="") as bf:
                bf.write(raw_before)
            print("已备份归一**前**的表 -> %s" % os.path.basename(BAK))
        with io.open(MAP, "w", encoding="utf-8", newline="\n") as f:
            f.write("src\tdst\n")
            for s, d in out:
                f.write("%s\t%s\n" % (s, d))
        back = dict(rd2(MAP))
        assert back == dict(out), "回读不一致"
        print("已写 %s（%d 条）" % (os.path.basename(MAP), len(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
