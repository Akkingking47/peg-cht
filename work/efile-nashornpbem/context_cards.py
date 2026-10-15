# -*- coding: utf-8 -*-
"""为每个含未译条目的文件输出「语境卡」：已译邻居 + 未译条目，便于按战役/地区翻译。"""
import os
import io

D = r"D:/OpenPG2/EFILE_OLGWW2/SCENARIO"
resid = io.open(r"D:/DSH/军事游戏汉化/work/efile-nashornpbem/olgww2-residual.tsv",
                encoding="utf-8").read().split("\n")[1:]
rows = [l.split("\t") for l in resid if l.strip()]


def parse(path):
    f = open(path, "rb").read()
    st = f.find(b"<N:")
    if st < 0:
        return None
    off = f.index(b">", st) + 1
    title = b""
    if off + 2 <= len(f):
        L = f[off] | (f[off + 1] << 8)
        if 0 < L and off + 2 + L <= len(f):
            title = f[off + 2:off + 2 + L]
            off += 2 + L
    items, groups = [], []
    gi = 0
    while off + 2 <= len(f):
        cnt = f[off] | (f[off + 1] << 8)
        if cnt <= 0 or cnt > 4000:
            break
        off += 2
        bad = False
        for k in range(cnt):
            if off + 2 > len(f):
                bad = True
                break
            L = f[off] | (f[off + 1] << 8)
            if L <= 0 or off + 2 + L > len(f):
                bad = True
                break
            items.append((gi, k, f[off + 2:off + 2 + L]))
            off += 2 + L
        if bad:
            break
        groups.append(cnt)
        gi += 1
        if gi > 64:
            break
    return dict(title=title, groups=groups, items=items)


def dec(raw):
    try:
        return raw.decode("gbk")
    except Exception:
        return raw.decode("cp1252", "replace")


def han(s):
    return any("\u4e00" <= c <= "\u9fff" for c in s)


# 按文件归类未译条目
byfile = {}
for r in rows:
    byfile.setdefault(r[0], []).append(r)

# 只关心硬漏译
HARD = {"TITLE", "PLACE", "UNIT_W"}
out = []
for fn in sorted(byfile):
    x = parse(os.path.join(D, fn))
    if x is None:
        continue
    hard = [r for r in byfile[fn] if r[3] in HARD]
    if not hard:
        continue
    neighbors = []
    for g, i, raw in x["items"]:
        s = dec(raw)
        if han(s):
            neighbors.append((g, i, s))
    out.append((fn, x["title"], hard, neighbors))

print("含硬漏译的文件数:", len(out))
for fn, t, hard, nb in out:
    print("### %s   标题=%r" % (fn, dec(t) if t else ""))
    print("  未译 %d 条:" % len(hard))
    for r in hard:
        print("     [%s] g%s i%s  %r" % (r[3], r[1], r[2], r[4]))
    if nb:
        print("  已译邻居(前 8): %s" % " / ".join(s for _, _, s in nb[:8]))
    print()
