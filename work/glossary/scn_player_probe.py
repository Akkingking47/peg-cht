#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**补视角**：在 `.scn` 里找能预测「扮演势力（文本视角）」的字段。

背景（`docs/44` §4.3）：
  现有视角判定链覆盖 **83%**（3042/3682），未判定 **640 个（17%）**，恰是地图/名单文件（`_m`/`_u`）。
  兜底层现在用的是 `@22`＝**场景国别**，而 `阵营视角-约定.md` 已记录它**不等于**「谁的文本」
  （`oakridge-R_m.txt` 据此误改 3 行，已撤回）。故本探针要找**更贴近视角**的字段。

方法（**带训练/测试分离，避免自证**）：
  · 标签沿用 `faction_place_audit.resolve_sides()`（**同一套判定链，不另写一份**）
  · `train` = 口吻标签（最强证据）· `test` = 同场景/战役族/人工钉（派生标签）
  · 逐偏移 × 编码（u8 / u16le / u32le）建「值→阵营」表（train 纯度 ≥70% 且样本 ≥8）
  · 在 **test** 上算准确率与覆盖率 ⇒ 只有 test 上仍强的才是真字段
  · 与 `@22`（现兜底）对比；并在「文本标签 与 @22 不一致」的子集上做二轮搜索

用法: python scn_player_probe.py [--max-offset N]
"""
import collections
import io
import json
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
sys.path.insert(0, os.path.join(WS, "work", "glossary"))
import faction_place_audit as FPA                                    # noqa: E402

EVID = os.path.join(WS, "glossary", "evidence")
PURITY = 0.70          # train 上某取值要达成的纯度
MINS = 8               # train 上某取值的最少样本


def stem_key(fn):
    return FPA.stem_of(fn).lower()


def scn_index(gamedir):
    """{小写文件名: 完整路径}（含 zz 前缀）。"""
    idx = {}
    for d in (gamedir,):
        if not os.path.isdir(d):
            continue
        for n in os.listdir(d):
            if n.lower().endswith(".scn"):
                idx.setdefault(n.lower(), os.path.join(d, n))
    return idx


def find_scn(fn, idx):
    stem = FPA.stem_of(fn)
    for cand in (stem + ".scn", "zz" + stem + ".scn"):
        p = idx.get(cand.lower())
        if p:
            return p
    return None


def getv(b, off, kind):
    if kind == "u8":
        return b[off] if off < len(b) else None
    if kind == "u16":
        return (b[off] | (b[off + 1] << 8)) if off + 1 < len(b) else None
    if kind == "u32":
        return (b[off] | (b[off + 1] << 8) | (b[off + 2] << 16) | (b[off + 3] << 24)) \
            if off + 3 < len(b) else None
    return None


def build_map(train, kind, off):
    m = collections.defaultdict(collections.Counter)
    for _k, lab, b in train:
        v = getv(b, off, kind)
        if v is not None:
            m[v][lab] += 1
    table = {}
    for v, c in m.items():
        tot = sum(c.values())
        if tot >= MINS:
            lab, n = c.most_common(1)[0]
            if n / tot >= PURITY:
                table[v] = lab
    return table


def evaluate(table, rows, kind, off):
    hit = tot = 0
    for _k, lab, b in rows:
        v = getv(b, off, kind)
        if v is None or v not in table:
            continue
        tot += 1
        if table[v] == lab:
            hit += 1
    return (hit, tot)


def main():
    maxoff = 4000
    if "--max-offset" in sys.argv:
        maxoff = int(sys.argv[sys.argv.index("--max-offset") + 1])

    data = FPA.load_scenarios()
    pin = FPA.load_pin()
    side, origin, voice = FPA.resolve_sides(data, pin)
    idx = scn_index(FPA.GAME)
    print("场景文件 %d · 判定视角 %d · 未判定 %d" % (len(data), len(side), len(data) - len(side)))
    print(".scn 索引 %d 个（目录 %s）" % (len(idx), FPA.GAME))

    rows = []
    no_scn = 0
    for fn in data:
        lab = side.get(fn)
        if not lab:
            continue
        p = find_scn(fn, idx)
        if not p:
            no_scn += 1
            continue
        try:
            rows.append((fn, lab, open(p, "rb").read()))
        except Exception:
            no_scn += 1
    print("有标签且对上 .scn：%d 个（缺 %d，标签文件 %d）" % (len(rows), no_scn, len(side)))

    train = [(k, l, b) for k, l, b in rows if origin.get(k) == "口吻"]
    test = [(k, l, b) for k, l, b in rows if origin.get(k) in ("同场景", "战役族", "人工钉")]
    print("train（口吻）= %d · test（同场景/战役族/人工钉）= %d" % (len(train), len(test)))
    if len(train) < 50 or len(test) < 50:
        print("⚠️ 样本不足，退出")
        return 0
    # ⚠️ 必须报**多数类基线**：否则"某字段 90%"可能只是"测试集本来就 90% 是同一方"
    tdist = collections.Counter(l for _k, l, _b in test)
    BASELINE = tdist.most_common(1)[0][1] / len(test)
    print("test 标签分布 %s ⇒ 多数类基线 %.1f%%（任何字段都必须显著超过它才算发现）"
          % (dict(tdist.most_common()), BASELINE * 100))
    L = min(len(b) for _k, _l, b in rows)
    print("扫描偏移 0..%d（最短 .scn = %d）" % (min(maxoff, L) - 1, L))

    results = []
    for kind in ("u8", "u16", "u32"):
        for off in range(min(maxoff, L - 3)):
            t = build_map(train, kind, off)
            if not t:
                continue
            hit, tot = evaluate(t, test, kind, off)
            if tot >= 40:
                acc = hit / tot
                results.append((acc - BASELINE, acc, tot, len(t), kind, off))
    results.sort(reverse=True)

    print("\n=== 全量搜索：按 **相对基线的增益(lift)** 排序（覆盖≥40）===")
    for lift, acc, tot, nv, kind, off in results[:12]:
        print("   @%-5d %-4s  acc %.1f%%（lift %+.1f%%）· 覆盖 %d/%d · 取值 %d 种"
              % (off, kind, acc * 100, lift * 100, tot, len(test), nv))

    # @22 基线（现兜底）
    def baseline_map():
        t = {}
        for _k, lab, b in train:
            if len(b) > 22:
                t.setdefault(b[22], collections.Counter())[lab] += 1
        out = {}
        for v, c in t.items():
            if sum(c.values()) >= MINS and c.most_common(1)[0][1] / sum(c.values()) >= PURITY:
                out[v] = c.most_common(1)[0][0]
        return out
    b22 = baseline_map()
    h22, t22 = evaluate(b22, test, "u8", 22)
    print("\n=== 基线：现兜底 @22（场景国别）===")
    print("   @22  u8  test 准确率 %.1f%%（覆盖 %d/%d）" % (100.0 * h22 / max(1, t22), t22, len(test)))

    # 二轮：只在「文本标签 与 @22 不一致」的子集上找
    dis = []
    for _k, lab, b in rows:
        if len(b) > 22:
            pv = b22.get(b[22])
            if pv and pv != lab:
                dis.append((_k, lab, b))
    dtr = [r for r in dis if origin.get(r[0]) == "口吻"]
    dte = [r for r in dis if origin.get(r[0]) in ("同场景", "战役族", "人工钉")]
    d2 = collections.Counter(l for _k, l, _b in dte)
    b2 = d2.most_common(1)[0][1] / max(1, len(dte))
    print("\n=== 二轮：@22(单字节) 与文本标签不一致的 %d 个文件 ===" % len(dis))
    print("   train(口吻) %d · test %d · test 标签分布 %s ⇒ 多数类基线 %.1f%%"
          % (len(dtr), len(dte), dict(d2.most_common()), b2 * 100))
    res2 = []
    if len(dtr) >= 20 and len(dte) >= 10:
        for kind in ("u8", "u16"):
            for off in range(min(maxoff, L - 3)):
                t = build_map(dtr, kind, off)
                if not t:
                    continue
                hit, tot = evaluate(t, dte, kind, off)
                if tot >= 10:
                    res2.append((hit / tot - b2, hit / tot, tot, len(t), kind, off))
        res2.sort(reverse=True)
        for lift, acc, tot, nv, kind, off in res2[:8]:
            print("   @%-5d %-4s  acc %.1f%%（lift %+.1f%%）· 覆盖 %d/%d · 取值 %d 种"
                  % (off, kind, acc * 100, lift * 100, tot, len(dte), nv))
    else:
        print("   （子集样本不足，跳过）")

    # 应用若干候选到「未判定」的 640 个：**看谁真能补出来**
    und = [fn for fn in data if fn not in side]
    cands = []
    if results:
        cands.append(results[0][1:])                       # 按 lift 最优
    for kind, off in (("u8", 22), ("u16", 22), ("u32", 20), ("u8", 12)):
        t = build_map(train, kind, off)
        hit, tot = evaluate(t, test, kind, off)
        if tot:
            cands.append((hit / tot, tot, len(t), kind, off))
    applied = []
    print("\n=== 把候选字段应用到「未判定」的 %d 个 ===" % len(und))
    for acc, _tot, _nv, kind, off in cands:
        table = build_map(train, kind, off)
        got = collections.Counter()
        for fn in und:
            p = find_scn(fn, idx)
            if not p:
                continue
            try:
                b = open(p, "rb").read()
            except Exception:
                continue
            v = getv(b, off, kind)
            if v in table:
                got[table[v]] += 1
        n = sum(got.values())
        applied.append(dict(off=off, kind=kind, test_acc=round(acc * 100, 1),
                            undetermined=len(und), resolved=n,
                            pct=round(100.0 * n / max(1, len(und)), 1), dist=dict(got)))
        print("   @%-5d %-4s  test acc %.1f%% ⇒ 补出 %d/%d（%.0f%%） %s"
              % (off, kind, acc * 100, n, len(und), 100.0 * n / max(1, len(und)), dict(got)))

    os.makedirs(EVID, exist_ok=True)
    out = ["# 补视角 · `.scn` 字段搜索（train=口吻 / test=派生标签）",
           "扫描偏移 0..%d · 纯度阈值 %.0f%% · 最小样本 %d" % (min(maxoff, L) - 1, PURITY * 100, MINS),
           "train %d · test %d · test 多数类基线 %.1f%%" % (len(train), len(test), BASELINE * 100),
           "@22(单字节) 现兜底：test acc %.1f%%（覆盖 %d/%d）lift %+.1f%%"
           % (100.0 * h22 / max(1, t22), t22, len(test), 100.0 * h22 / max(1, t22) - BASELINE * 100),
           "", "## 按 lift 排序（前 20）"]
    for lift, acc, tot, nv, kind, off in results[:20]:
        out.append("@%d\t%s\tacc=%.1f%%\tlift=%+.1f%%\tcovered=%d\tvalues=%d"
                   % (off, kind, acc * 100, lift * 100, tot, nv))
    out += ["", "## 二轮（@22 不一致子集，多数类基线 %.1f%%，前 10）" % (b2 * 100)]
    for lift, acc, tot, nv, kind, off in res2[:10]:
        out.append("@%d\t%s\tacc=%.1f%%\tlift=%+.1f%%\tcovered=%d\tvalues=%d"
                   % (off, kind, acc * 100, lift * 100, tot, nv))
    out += ["", "## 应用到未判定"]
    for a in applied:
        out.append(json.dumps(a, ensure_ascii=False))
    io.open(os.path.join(EVID, "scn-player-probe.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print("\n报告 → glossary/evidence/scn-player-probe.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
