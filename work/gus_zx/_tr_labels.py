# -*- coding: utf-8 -*-
"""把 `SCENARIO\\<name>.txt` 标签表（地名 + 番号清单）译成中文。

译文来源优先级：`xscn-map.tsv`（与已写入 `.xscn` 的译名保持一致）→ `txt_labels_extra.LABEL_EXTRA`
→ 不含拉丁字母则原样保留。其余一律报未映射（不静默漏译）。
逐行保留原 `\\r` 与末尾换行。
"""
import os
import re
import sys

sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\gus_zx")
from txt_labels_extra import LABEL_EXTRA  # noqa: E402

B = r"D:\DSH\军事游戏汉化\work\gus_zx"
SRC = os.path.join(B, "src")
ZH = os.path.join(B, "zh")

# 非标签文件（散文 / 战役说明 / 引擎报表），由别的脚本处理
SKIP = {"G06.txt", "G06__flow.txt", "G27_STA.txt", "H02_Blitz.txt",
        "H02_Blitzloss.txt", "H02__flow.txt"}


def load_map():
    m = {}
    for i, l in enumerate(open(os.path.join(B, "xscn-map.tsv"), encoding="utf-8")):
        if i == 0:
            continue
        p = l.rstrip("\n").split("\t")
        if len(p) >= 2:
            m[p[0].strip()] = p[1]
    m.update(LABEL_EXTRA)
    return m


def is_label(n):
    if n in SKIP:
        return False
    if not n.lower().endswith(".txt"):
        return False
    b = n.rsplit(".", 1)[0]
    return not (b.endswith("i") or b.endswith("bv") or b.endswith("tv")
                or b.endswith("v") or b.endswith("l") or b.endswith("loss")
                or b.endswith("__flow"))


M = load_map()
unmapped = {}


def tr(s):
    k = s.strip()
    if k == "":
        return s
    if k in M:
        return M[k]
    if not re.search(r"[A-Za-z]", k):
        return s
    unmapped.setdefault(k, 0)
    unmapped[k] += 1
    return s


def main():
    files = sorted(n for n in os.listdir(SRC) if is_label(n))
    total = hit = 0
    for n in files:
        t = open(os.path.join(SRC, n), encoding="utf-8", newline="").read()
        ls = t.split("\n")
        tnl = ls and ls[-1] == ""
        if tnl:
            ls = ls[:-1]
        out = []
        for ln in ls:
            cr = "\r" if ln.endswith("\r") else ""
            body = ln[:-1] if cr else ln
            lead = body[:len(body) - len(body.lstrip())]
            trail = body[len(body.rstrip()):]
            new = tr(body.strip())
            out.append(lead + new + trail + cr)
            if body.strip():
                total += 1
                hit += 1 if (body.strip() in M or not re.search(r"[A-Za-z]", body.strip())) else 0
        with open(os.path.join(ZH, n), "w", encoding="utf-8", newline="") as f:
            f.write("\n".join(out) + ("\n" if tnl else ""))
    print("标签文件 %d 个，非空行 %d，已译/已定 %d (%.1f%%)"
          % (len(files), total, hit, 100.0 * hit / max(1, total)))
    if unmapped:
        print("\n未映射 %d 个唯一串：" % len(unmapped))
        for k in sorted(unmapped):
            print("   %-40s x%d" % (k, unmapped[k]))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
