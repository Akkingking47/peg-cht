# -*- coding: utf-8 -*-
"""OLGWW2 残留条目「字节级定点写回」。

读 olgww2-glossary.tsv（真源）→ 对每个 .xscn 只改写命中条目的
「2 字节长度字段 + 内容」，其余字节逐字节不动。天然可重入。

用法：
  python apply_residual.py            # dry-run，只报告
  python apply_residual.py --apply    # 写入（写 .new → 回读校验 → 替换）
"""
import os
import io
import sys

D = r"D:/OpenPG2/EFILE_OLGWW2/SCENARIO"
GLOSS = r"D:/DSH/军事游戏汉化/work/efile-nashornpbem/olgww2-glossary.tsv"


def load_gloss():
    g = {}
    L = io.open(GLOSS, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")
    for i, ln in enumerate(L):
        if i == 0 or not ln.strip():
            continue
        c = ln.split("\t")
        if len(c) < 3:
            print("!! 格式异常行 %d: %r" % (i + 1, ln))
            continue
        src, dst, cat = c[0], c[1], c[2]
        g[src] = (dst, cat)
    return g


def parse(path):
    """返回 (data, items)。items=[(gi, idx, val_off, val_len)]"""
    f = open(path, "rb").read()
    st = f.find(b"<N:")
    if st < 0:
        return f, None, None
    off = f.index(b">", st) + 1
    items = []
    title_off = title_len = None
    if off + 2 <= len(f):
        L = f[off] | (f[off + 1] << 8)
        if 0 < L and off + 2 + L <= len(f):
            title_off, title_len = off, L
            off += 2 + L
    gi = 0
    groups = []
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
            items.append((gi, k, off, L))
            off += 2 + L
        if bad:
            break
        groups.append(cnt)
        gi += 1
        if gi > 64:
            break
    return f, items, (title_off, title_len, groups)


def main():
    apply = "--apply" in sys.argv
    g = load_gloss()
    d2s = {}
    for k, (dst, cat) in g.items():
        if dst and cat not in ("PENDING", "KEEP"):
            d2s[dst] = k
    plan = []          # (fn, gi, idx, off, L, old, new)
    unknown = set()    # glossary 里未在文件中命中的 key
    hitkeys = set()

    files = sorted(f for f in os.listdir(D) if f.lower().endswith(".xscn"))
    for fn in files:
        p = os.path.join(D, fn)
        data, items, meta = parse(p)
        if items is None:
            continue
        title_off, title_len, groups = meta
        todo = []
        # 标题
        if title_off is not None:
            raw = data[title_off + 2:title_off + 2 + title_len]
            try:
                s = raw.decode("ascii")
            except Exception:
                s = None
            if s is not None:
                key = s.rstrip()
                if key in g and g[key][1] not in ("PENDING", "KEEP"):
                    dst, cat = g[key]
                    hitkeys.add(key)
                    if dst and dst != key:
                        todo.append((-1, 0, title_off, title_len, raw, dst))
            else:
                try:
                    v = raw.decode("gbk")
                except Exception:
                    v = None
                if v in d2s:
                    hitkeys.add(d2s[v])
        for gi, idx, off, L in items:
            raw = data[off + 2:off + 2 + L]
            try:
                s = raw.decode("ascii")
            except Exception:
                try:
                    v = raw.decode("gbk")
                except Exception:
                    continue
                if v in d2s:
                    hitkeys.add(d2s[v])
                continue
            key = s.rstrip()
            if key in g:
                dst, cat = g[key]
                hitkeys.add(key)
                if dst and dst != key and cat not in ("PENDING", "KEEP"):
                    todo.append((gi, idx, off, L, raw, dst))
        for gi, idx, off, L, raw, dst in todo:
            plan.append((fn, gi, idx, off, L, raw, dst.encode("gbk")))

    for k, (dst, cat) in g.items():
        if cat != "PENDING" and cat != "KEEP" and k not in hitkeys:
            unknown.add(k)

    per = {}
    for fn, gi, idx, off, L, raw, new in plan:
        per.setdefault(fn, []).append((gi, idx, off, L, raw, new))

    if "--files" in sys.argv:
        for fn in sorted(per):
            print(fn)
        return

    print("=== 计划改动 ===")
    print("命中条目总数:", len(plan), " 涉及文件:", len(per))
    if unknown:
        print("\n!! glossary 中以下 key 在文件里未命中（检查空格/引号）:")
        for k in sorted(unknown):
            print("   %r" % k)

    if not apply:
        print("\n(dry-run，未写入)")
        for fn in sorted(per):
            xs = per[fn]
            print("  %-24s %2d 条  (例) %s -> %s" % (fn, len(xs), xs[0][4][:34], xs[0][5][:24]))
        return

    print("\n=== 写入 ===")
    for fn in sorted(per):
        p = os.path.join(D, fn)
        data = bytearray(open(p, "rb").read())
        for gi, idx, off, L, raw, new in sorted(per[fn], key=lambda x: -x[2]):
            data[off:off + 2 + L] = len(new).to_bytes(2, "little") + new
        tmp = p + ".new"
        open(tmp, "wb").write(bytes(data))
        # 回读校验
        d2, items2, meta2 = parse(tmp)
        d1, items1, meta1 = parse(p)
        ok = (items2 is not None and items1 is not None
              and meta2[2] == meta1[2] and len(items2) == len(items1))
        if d2 == bytes(data) and ok:
            os.replace(tmp, p)
            print("  OK  %-24s %2d 条  %d -> %d B" % (fn, len(per[fn]), len(d1), len(d2)))
        else:
            os.remove(tmp)
            print("  !!  %-24s 校验失败，已回滚" % fn)


if __name__ == "__main__":
    main()
