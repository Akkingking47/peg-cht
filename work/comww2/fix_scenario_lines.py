# -*- coding: utf-8 -*-
"""场景 `.txt` 行级**精确**订正（prose 层残留的部队番号行）。

口径来源（不凭常识）：
  - `work\\xscn\\POLICY.md` 编制名对照表：`Jaeger`→猎兵 · `Batt.`→营 · `Brig.`→旅 ·
    `Abt.`→营 · `Aufklarungs`→侦察 · `Sturm.`→突击 · `SP Art.`→自行火炮 · `Jgd`→歼击 ·
    `Pz`→装甲 · `Fl.`→（航空）师 · 罗马数字→阿拉伯数字（`5CB`→第5骑兵旅）
  - 本 efile 已交付件实证：`19MnRom`→第19摩托化师（罗马尼亚）等 `NN Xx Rom` 型

⭐ 硬约束（本工程铁律）：
  1. 替换只作用于**中文侧** `TEXT-ZH\\SCENARIO`，原文侧**只读**；
  2. md5 相同的同组文件必须**同步**改写（否则组内不一致）；
  3. 逐文件沿用**自己的**换行（LF/CRLF），不统一；
  4. 命中数必须与预期一致，否则**不落盘**（防静默错改）。

用法:
    python fix_scenario_lines.py --dry
    python fix_scenario_lines.py --apply
"""
import hashlib
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"D:\OpenPG2\EFILE_COMWW2\SCENARIO"
ZH = r"D:\OpenPG2\EFILE_COMWW2\TEXT-ZH\SCENARIO"

# 原文 → 译文（**整行精确匹配**，strip 后比较，保留原行首尾空白）
FIX = {
    "2nd Jaeger Batt.": "第2猎兵营",
    "4th Anti-tank Brig.": "第4反坦克旅",
    "19th Aufklarungs Abt.": "第19侦察营",
    "13th SP Art. Brig.": "第13自行火炮旅",
    "244th Sturm. Abt.": "第244突击炮营",
    "5CBRom": "第5骑兵旅（罗马尼亚）",
    "6CBRom": "第6骑兵旅（罗马尼亚）",
    "19MnRom": "第19摩托化师（罗马尼亚）",
    "13. JgdFl.Div.": "第13歼击航空师",
    "15. SchlFl.Div.": "第15对地攻击航空师",
    "33. SchlFl.Div.": "第33对地攻击航空师",
    "6. JgdFl.Div.": "第6歼击航空师",
    # ⚠️ 邮箱混淆写法（`AT`=@ / `DOT`=.）是**反爬格式**，按口径保留原文，不译
}


def detect_nl(raw):
    return "\n" if (raw.count(b"\n") > 0 and raw.count(b"\r\n") == 0) else "\r\n"


def main():
    apply = "--apply" in sys.argv
    # 原文 md5 → 同组文件名（保证组内一致）
    groups = {}
    for f in sorted(os.listdir(SRC)):
        if f.lower().endswith(".txt"):
            groups.setdefault(hashlib.md5(open(os.path.join(SRC, f), "rb").read()).hexdigest(), []).append(f)

    total_hits = 0
    plan = []
    for f in sorted(os.listdir(ZH)):
        if not f.endswith(".txt"):
            continue
        p = os.path.join(ZH, f)
        raw = open(p, "rb").read()
        nl = detect_nl(raw)
        txt = raw.decode("gbk")
        lines = txt.split(nl)
        hits = []
        for i, l in enumerate(lines):
            key = l.strip()
            if key in FIX:
                hits.append((i, l, FIX[key]))
        if hits:
            plan.append((f, nl, lines, hits))
            total_hits += len(hits)

    print("命中文件 %d 个 / 行 %d 处（预期 12 处，另有 1 处邮箱行按口径保留）" % (len(plan), total_hits))
    for f, nl, lines, hits in plan:
        for i, old, new in hits:
            print("  %s:%d  %r -> %r" % (f, i + 1, old, new))
    if total_hits != 12:
        raise SystemExit("命中数 %d ≠ 12 ⇒ 不落盘（请复核）" % total_hits)

    # 组内一致：命中文件的所有同组文件必须一起改
    targets = set()
    for f, _, _, _ in plan:
        h = hashlib.md5(open(os.path.join(SRC, f), "rb").read()).hexdigest()
        for g in groups.get(h, [f]):
            targets.add(g)
    print("同组需同步文件 %d 个" % len(targets))

    if not apply:
        print("干跑完成（未写盘）")
        return

    done = 0
    for f in sorted(targets):
        p = os.path.join(ZH, f)
        if not os.path.exists(p):
            continue
        raw = open(p, "rb").read()
        nl = detect_nl(raw)
        lines = raw.decode("gbk").split(nl)
        n = 0
        for i, l in enumerate(lines):
            if l.strip() in FIX:
                lines[i] = l.replace(l.strip(), FIX[l.strip()])
                n += 1
        if not n:
            continue
        blob = nl.join(lines).encode("gbk")
        with open(p, "wb") as fh:
            fh.write(blob)
        back = open(p, "rb").read()
        if back != blob:
            raise SystemExit("回读不一致: %s" % f)
        if nl == "\r\n" and back.count(b"\n") != back.count(b"\r\n"):
            raise SystemExit("输出含裸 LF: %s" % f)
        if nl == "\n" and back.count(b"\r\n"):
            raise SystemExit("输出混入 CRLF: %s" % f)
        done += 1
    print("已写 %d 个文件" % done)


if __name__ == "__main__":
    main()
