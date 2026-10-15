# -*- coding: utf-8 -*-
"""① 已投放成品里「该译未译」的行（该行含 ≥3 字符、无汉字、有 ≥3 拉丁字母、且非元数据/噪音）
② 六张映射表里的**自等行**（`en == zh`，即登记了却等于原文 ⇒ 静默漏译）。

自等行是漏译的**结构性信号**：译文列与原文列相同，成品自然还是英文。本轮实测命中
`Viel Glück!`（→ 已修为「祝好运！」，ASCII 兄弟行 `Viel Gluck!` 早已是「祝好运！」）。
"""
import io, os, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

RES = r"D:\DSH\军事游戏汉化\pegww2\research"
GAME = r"D:\Program Files\PeG-WW2"
TABLES = ["ww2-scn-map.tsv", "ww2-eqp-map.tsv", "WW2Gui-map.tsv", "WW2Misc-map.tsv",
          "WW2Tips-map.tsv", "WW2NAME-map.tsv"]

CJK = re.compile(r"[\u4e00-\u9fff]")
WORD = re.compile(r"[A-Za-z]{3,}")
NO = re.compile(r"^[0-9\s\-/\.\(\)#:,]+$|^[A-Z]?\d+[\s/\-\.\d]*$|^\(?\d+\s*[,/]\s*\d+\)?$|^[Dd]ummy$"
                r"|^(Equipment|Gameset|Scenario|Version)\s*:|^Loading Scen|^Map file|^[\w\- ]+\.(scn|map|txt)$"
                r"|^Choice\d$|^#[A-Za-z]?\d+$|^\d{4}-\d{2}-\d{2}|^Wed \w+ \d+|^CreationTime|conversion\s*:"
                r"|converted by|Campaign Designer|http|skynet|rmypegww2")
SK = re.compile(r"(?i)(read ?me|report|^info\.txt)")

n, files, rows = 0, set(), []
for d in ("SCENARIO", "USERSCEN"):
    p = os.path.join(GAME, d)
    if not os.path.isdir(p):
        continue
    for fn in os.listdir(p):
        if not fn.lower().endswith(".txt") or SK.search(fn):
            continue
        try:
            t = io.open(os.path.join(p, fn), encoding="gbk", errors="replace").read()
        except Exception:
            continue
        for l in t.split("\n"):
            s = l.strip()
            if len(s) >= 3 and not CJK.search(s) and not NO.match(s) and WORD.search(s):
                n += 1
                files.add(fn)
                rows.append((fn, s[:56]))
print("① 该译未译：**%d 行 / %d 文件**" % (n, len(files)))
for r in rows:
    print("      %-28s %s" % r)

print("\n② 映射表自等行（en == zh）——区分**策略保留**与**可疑漏译**")
tot = pol = 0
for t in TABLES:
    p = os.path.join(RES, t)
    if not os.path.isfile(p):
        continue
    keep, susp = [], []
    for l in io.open(p, encoding="utf-8-sig"):
        c = l.rstrip("\r\n").split("\t")
        if len(c) >= 2 and c[0].strip() and c[0].strip() == c[1].strip():
            (keep if (len(c) > 2 and c[2].strip() == "保留") else susp).append(c[0].strip())
    tot += len(keep) + len(susp)
    pol += len(keep)
    print("   %-22s 策略保留 %d ｜ ⚠️ 可疑 %d %s"
          % (t, len(keep), len(susp),
             ("→ " + " / ".join(h[:26] for h in susp[:6])) if susp else ""))
print("   合计自等行 %d（其中策略保留 %d · 可疑 %d）" % (tot, pol, tot - pol))
