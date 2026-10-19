# -*- coding: utf-8 -*-
"""PeG 场景列表「数字序号」映射生成器（分组版，2026-10-10 第 27 轮）
================================================================
背景：
  场景列表的**显示名**取自 `<场景>_m.txt` 的第 [SCN@offset4] 行（通常第 0 行）；
  列表**按显示名的字节序排序** ⇒ 名字全译成中文后按 GBK 码序排 ⇒ 与汉化前顺序不同。

两种列表（官方 `Scenario Types.txt`）：
  - **进行场景**（Play A Scenario）＝ Human vs Computer，**只列 ≤2 人场景**
  - **开始多人场景**（Start A Multiplayer Scenario）＝ **2–4 名真人**，列 3–4 人场景

⇒ 分组编号（第 27 轮，用户要求）：
  - **单人组**（`.SCN` Player3 主国家 @216 == 0）⇒ `01`–`51`
  - **多人组**（@216 != 0）                      ⇒ `01`–`10`
  各组**各自**按「原英文名字节序」编号（＝该组汉化前的本来顺序）。
  两个列表分开显示，两组都用 `01` 起**不冲突**。

产出：peg/research/scn-number.tsv
      (stem \t NN \t entry \t 原名 \t 现名 \t 组别)
"""
import os
import struct

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


ROOT = WS
BACKUP = os.path.join(ROOT, r"peg\testbed\backup")
OUT = os.path.join(ROOT, r"peg\research\scn-number.tsv")

NAME_CANDS = ("{stem}_m.txt", "{stem}.txt", "{stem}.ply")


def read_lines(path, encs=("cp1252", "gbk")):
    b = open(path, "rb").read()
    if path.lower().endswith(".ply"):
        b = b.split(b"\x00")[0]
    t = None
    for enc in encs:
        try:
            t = b.decode(enc)
            break
        except Exception:
            t = None
    if t is None:
        return []
    return t.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def find_name(stem, d, entry, encs=("cp1252", "gbk")):
    for pat in NAME_CANDS:
        p = os.path.join(d, pat.format(stem=stem))
        if os.path.exists(p):
            lines = read_lines(p, encs)
            name = lines[entry] if entry < len(lines) else ""
            return os.path.basename(p), name
    return None, ""


def main():
    rows = []
    for sub in ("Scenario", "Userscen"):
        d = os.path.join(BACKUP, sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.lower().endswith(".scn"):
                continue
            b = open(os.path.join(d, f), "rb").read()
            if len(b) < 6:
                continue
            if b[0] == 1:                       # $1 = not active ⇒ 不进任何列表
                continue
            stem = f[:-4]
            entry = struct.unpack_from("<H", b, 4)[0]
            # Player3 主国家：@216（P1@22 / P2@119 / P3@216 / P4@313，每组 97B）
            p3 = b[216] if len(b) > 216 else 0
            grp = "多人" if p3 != 0 else "单人"
            src, orig = find_name(stem, d, entry)
            if src is None:
                print(f"  ⚠️ 无名字文件，跳过：{sub}/{f}（entry={entry}）")
                continue
            rows.append({"sub": sub, "scn": f, "stem": stem, "entry": entry,
                         "orig": orig, "grp": grp})

    # 分组内按【原英文名字节序】排序 ⇒ 复原该组汉化前的顺序
    rows.sort(key=lambda r: (r["grp"], r["orig"].encode("cp1252", "replace"), r["stem"]))

    # 组内连续编号（各组都从 01 起）
    counters = {"单人": 0, "多人": 0}
    for r in rows:
        counters[r["grp"]] += 1
        r["nn"] = f"{counters[r['grp']]:02d}"
        gd = os.path.join(GAME, r["sub"])
        _, cur = find_name(r["stem"], gd, r["entry"], encs=("gbk", "cp1252"))
        r["cur"] = cur

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("# PeG 场景列表数字序号（**分组**；组内按原英文名字母序）\n")
        f.write("# 单人组＝「进行场景」列表（Player3 主国家=0）共 51；多人组＝「开始多人场景」共 10\n")
        f.write("# stem\tNN\tentry\t原名\t现名\t组别\n")
        for r in rows:
            f.write(f"{r['stem']}\t{r['nn']}\t{r['entry']}\t{r['orig']}\t{r['cur']}\t{r['grp']}\n")

    print(f"已写 {OUT}（单人 {counters['单人']} + 多人 {counters['多人']} = {len(rows)}）\n")
    for g in ("单人", "多人"):
        print(f"===== {g}组（{counters[g]} 个）=====")
        for r in rows:
            if r["grp"] != g:
                continue
            print(f"  {r['nn']}  {r['orig'][:38]:40s}  {r['cur'][:26]!r}")
        print()


if __name__ == "__main__":
    main()
