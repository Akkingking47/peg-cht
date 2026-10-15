#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**用已知视角反查 `.scn` 的玩家国别字段**（Task 3）。

思路：`faction_place_audit.py` 已用**文本口吻**判出 2,289 个文件的视角（德/苏/盟/意/波/罗/芬）。
  ⇒ 把「文件名 stem → `.scn`」对上，逐字节偏移做**相关性搜索**：
     若某偏移的字节值能高准确率预测视角 ⇒ 那就是**国别/阵营字段** ✓
     （项目已知 `@216` = "PeG 的 Player3 主国家"，故重点看 200–230 区，但全扫 0–320。）

用法: python scn_side_probe.py
"""
import collections
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
WS = r"D:\DSH\军事游戏汉化"
sys.path.insert(0, os.path.join(WS, "work", "glossary"))
GAME = r"D:\Program Files\PeG-WW2"
BK = os.path.join(GAME, "SCENARIO")
MARK = {
    "苏": ("将军同志", "同志，", "斯大林同志", "最高统帅部同志"),
    "德": ("将军阁下", "元首", "德意志", "我们德国"),
    "盟": ("指挥官，", "盟军将", "艾森豪威尔", "蒙哥马利", "巴顿将军", "美国陆军"),
    "罗": ("罗马尼亚军队", "安东内斯库", "Conducator", "我们罗马尼亚"),
    "芬": ("芬兰军队", "曼纳海姆", "Mannerheim", "我们芬兰"),
    "波": ("家乡军", "华沙起义", "波兰流亡政府", "我们波兰"),
    "意": ("意大利军队", "墨索里尼", "意军指挥官"),
}
NO_VOICE = re.compile(r"(?i)(_m|_u)$")


def persp(text):
    sc = {f: sum(text.count(m) for m in ms) for f, ms in MARK.items()}
    b = max(sc, key=lambda f: sc[f])
    return b if sc[b] > 0 else None


labels = {}
for fn in sorted(os.listdir(BK)):
    if not fn.lower().endswith(".txt") or NO_VOICE.search(os.path.splitext(fn)[0]):
        continue
    stem = re.sub(r"(?i)(_i|_l|_bv|_tv|_v)$", "", os.path.splitext(fn)[0])
    stem = re.sub(r"(?i)(?<=[0-9v])e$", "", stem)
    try:
        t = io.open(os.path.join(BK, fn), encoding="gbk", errors="replace").read()
    except Exception:
        continue
    f = persp(t)
    if f:
        labels.setdefault(stem, f)
print("已知视角 stem：%d 个" % len(labels))

data = []
miss = 0
GAMEDIR = os.path.join(GAME, "SCENARIO")
for stem, f in labels.items():
    p = None
    for d in (BK, GAMEDIR):                     # ⚠️ 备份里没有 .scn（它从不被覆盖⇒不进备份）⇒ 必须读游戏目录
        names = [stem + ".scn", stem + ".SCN", "zz" + stem + ".scn", "zz" + stem + ".SCN",
                 "ZZ" + stem + ".scn"]
        for cand in names:
            low = [x for x in os.listdir(d) if x.lower() == cand.lower()]
            if low:
                p = os.path.join(d, low[0])
                break
        if p:
            break
    if not p:
        miss += 1
        continue
    try:
        data.append((stem, f, open(p, "rb").read()))
    except Exception:
        miss += 1
print("对上 .scn 的：%d 个（缺 %d）" % (len(data), miss))
if not data:
    sys.exit(0)
L = min(len(b) for _s, _f, b in data)
print("最短 .scn 长度 %d" % L)

print("\n=== 偏移相关性（准确率 = 用该字节值预测视角的命中率，仅统计≥8 样本的取值）===")
best = []


def score(nv_of):
    out = []
    for off in range(min(L, 340)):
        m = collections.defaultdict(collections.Counter)
        for _s, f, b in data:
            v = nv_of(b, off)
            if v is None:
                continue
            m[v][f] += 1
        hit = tot = 0
        for v, c in m.items():
            if sum(c.values()) < 8:
                continue
            hit += c.most_common(1)[0][1]
            tot += sum(c.values())
        if tot >= 40:
            out.append((hit / tot, off, len(m), tot))
    out.sort(reverse=True)
    return out


byte_of = lambda b, o: b[o]
best = score(byte_of)
print("-- 按单字节 --")
for acc, off, nv, tot in best[:8]:
    print("   @%-4d 准确率 %.1f%%（取值 %d 种 · 样本 %d）" % (off, acc * 100, nv, tot))
u16 = lambda b, o: (b[o] | (b[o + 1] << 8)) if o + 1 < len(b) else None
b16 = score(u16)
print("-- 按 u16(LE) --")
for acc, off, nv, tot in b16[:8]:
    print("   @%-4d 准确率 %.1f%%（取值 %d 种 · 样本 %d）" % (off, acc * 100, nv, tot))

if best:
    off = best[0][1]
    print("\n=== 最佳偏移 @%d 的取值 → 视角对应表 ===" % off)
    m = collections.defaultdict(collections.Counter)
    for _s, f, b in data:
        m[b[off]][f] += 1
    for v in sorted(m, key=lambda v: -sum(m[v].values()))[:12]:
        c = m[v]
        print("   值 %-5d (0x%02x) → %s" % (v, v, dict(c.most_common(4))))
