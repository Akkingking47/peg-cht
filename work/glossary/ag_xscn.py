# -*- coding: utf-8 -*-
"""EFILE_AG .xscn 导出 / 应用工具（字节级定点替换，可重入）。

结构（与 OLGWW2 同源）：
  <场景数据>  <N:####>  标题(u16 len + bytes)  组1(u16 cnt) [u16 len + bytes]...  组2 ...

用法：
  python ag_xscn.py export [--full]   # 导出唯一串清单 -> ag-xscn-uniq.tsv
  python ag_xscn.py apply [--apply]   # 按 ag-xscn-map.tsv 替换（默认 dry-run）
  python ag_xscn.py verify            # 与备份逐文件结构比对
"""
import os
import io
import sys
import collections

GAME = r"D:/OpenPG2/EFILE_AG/SCENARIO"
BAK = r"D:/DSH/军事游戏汉化/backup/ORIGINAL-EFILE_AG/SCENARIO"
WORK = r"D:/DSH/军事游戏汉化/work/glossary"
UNIQ = os.path.join(WORK, "ag-xscn-uniq.tsv")
MAP = os.path.join(WORK, "ag-xscn-map.tsv")
ENC_IN = "cp1252"
ENC_OUT = "gbk"


def _printable(b):
    """条目字节合法性：可打印 ASCII / 西欧高位(cp1252 变音符) / 制表换行"""
    return b >= 0x20 or b in (0x09, 0x0A, 0x0D)


def parse(path):
    """返回 (data, items, meta)；items=[(gi, idx, off, L)]
    meta=(title_off, title_len, groups, end, size)

    ⚠ 与 OLGWW2 的关键差异：**AG 允许 cnt==0 的空组**（20/86 个文件的组 0 为空）。
    沿用 OLGWW2「cnt<=0 即 break」的旧规则会把这些文件的整个串区漏掉。
    修正后 86/86 文件均恰好解析到 EOF。
    """
    with open(path, "rb") as f:
        data = f.read()
    st = data.find(b"<N:")
    if st < 0:
        return data, None, None
    off = data.index(b">", st) + 1
    title_off = title_len = None
    if off + 2 <= len(data):
        L = data[off] | (data[off + 1] << 8)
        if 0 < L and off + 2 + L <= len(data):
            title_off, title_len = off, L
            off += 2 + L
    items = []
    groups = []
    gi = 0
    while off + 2 <= len(data):
        cnt = data[off] | (data[off + 1] << 8)
        if cnt > 4000:
            break
        off += 2
        bad = False
        for k in range(cnt):
            if off + 2 > len(data):
                bad = True
                break
            L = data[off] | (data[off + 1] << 8)
            if L <= 0 or L > 2000 or off + 2 + L > len(data):
                bad = True
                break
            if not all(_printable(b) for b in data[off + 2:off + 2 + L]):
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
    return data, items, (title_off, title_len, groups, off, len(data))


def raw_at(data, off, L):
    return data[off + 2:off + 2 + L]


def decode(raw):
    """返回 (enc, text)"""
    try:
        s = raw.decode(ENC_OUT)
        if any("\u4e00" <= c <= "\u9fff" for c in s):
            return ENC_OUT, s
    except Exception:
        pass
    return ENC_IN, raw.decode(ENC_IN, "replace")


def han_count(s):
    return sum(1 for c in s if "\u4e00" <= c <= "\u9fff")


def files():
    return sorted(f for f in os.listdir(GAME) if f.lower().endswith(".xscn"))


# ---------------------------------------------------------------- export
def cmd_export():
    full = "--full" in sys.argv
    cnt = collections.Counter()
    groups_of = collections.defaultdict(set)
    where = collections.defaultdict(list)
    titles = []
    nfiles = 0
    nitems = 0
    tails = []
    for fn in files():
        p = os.path.join(GAME, fn)
        data, items, meta = parse(p)
        if items is None:
            print("!! 解析失败 %s" % fn)
            continue
        nfiles += 1
        title_off, title_len, groups, end, size = meta
        tails.append(size - end)
        if title_off is not None:
            titles.append((fn, decode(raw_at(data, title_off, title_len))[1]))
        nitems += len(items)
        if title_off is not None:      # 标题也计入唯一串（组号 -1）
            enc, s = decode(raw_at(data, title_off, title_len))
            if enc != ENC_OUT:
                key = s.strip()
                cnt[key] += 1
                groups_of[key].add(-1)
                if len(where[key]) < 3:
                    where[key].append(fn)
        for gi, idx, off, L in items:
            enc, s = decode(raw_at(data, off, L))
            if enc == ENC_OUT:
                continue
            key = s.strip()
            cnt[key] += 1
            groups_of[key].add(gi)
            if len(where[key]) < 3:
                where[key].append(fn)
    print("文件 %d  条目 %d  唯一(非中文) %d  尾部残留 %s" % (
        nfiles, nitems, len(cnt), collections.Counter(tails).most_common(3)))
    print("标题样例:", titles[:5])
    with io.open(UNIQ, "w", encoding="utf-8", newline="") as f:
        f.write("src\tfreq\tgroups\texample\n")
        for k, n in cnt.most_common():
            gs = ",".join(str(x) for x in sorted(groups_of[k]))
            f.write("%s\t%d\t%s\t%s\n" % (k, n, gs, where[k][0]))
    print("已写 %s" % UNIQ)
    if full:
        out = os.path.join(WORK, "ag-xscn-full.tsv")
        with io.open(out, "w", encoding="utf-8", newline="") as f:
            f.write("file\tgroup\tidx\tsrc\n")
            for fn in files():
                p = os.path.join(GAME, fn)
                data, items, meta = parse(p)
                if items is None:
                    continue
                for gi, idx, off, L in items:
                    f.write("%s\t%d\t%d\t%s\n" % (
                        fn, gi, idx, decode(raw_at(data, off, L))[1].rstrip()))
        print("已写 %s" % out)


# ---------------------------------------------------------------- apply
def load_map():
    m = {}
    with io.open(MAP, encoding="utf-8-sig", newline="") as f:
        txt = f.read()
    for i, ln in enumerate(txt.replace("\r\n", "\n").split("\n")):
        if i == 0 or not ln.strip():
            continue
        c = ln.split("\t")
        if len(c) < 2 or not c[1].strip():
            continue
        m[c[0]] = c[1]
    return m


def cmd_apply():
    do = "--apply" in sys.argv
    m = load_map()
    plan = collections.defaultdict(list)
    miss = collections.Counter()
    total = 0
    for fn in files():
        p = os.path.join(GAME, fn)
        data, items, meta = parse(p)
        if items is None:
            continue
        title_off, title_len = meta[0], meta[1]
        slots = []
        if title_off is not None:
            slots.append((-1, 0, title_off, title_len))
        for gi, idx, off, L in items:
            slots.append((gi, idx, off, L))
        for gi, idx, off, L in slots:
            raw = raw_at(data, off, L)
            enc, s = decode(raw)
            if enc == ENC_OUT:
                continue
            key = s.strip()
            if not key:
                continue          # 空条目（占位）保持原样
            if key in m:
                # 保留原文前导/尾随空白（单位列表里存在缩进式前导空格）
                lead = raw[:len(raw) - len(raw.lstrip())]
                trail = raw[len(raw.rstrip()):]
                new = lead + m[key].encode(ENC_OUT) + trail
                if new != raw:
                    plan[fn].append((gi, idx, off, L, raw, new))
                    total += 1
            else:
                miss[key] += 1
    print("计划改写 %d 条 / 涉及文件 %d / 总文件 %d" % (total, len(plan), len(files())))
    if miss:
        print("!! 未命中 %d 个唯一串（前 30）:" % len(miss))
        for k, n in miss.most_common(30):
            print("   %-40s x%d" % (k, n))
    if not do:
        print("(dry-run)")
        return
    nok = 0
    for fn in sorted(plan):
        p = os.path.join(GAME, fn)
        data = bytearray(open(p, "rb").read())
        before = parse(p)
        for gi, idx, off, L, raw, new in sorted(plan[fn], key=lambda x: -x[2]):
            data[off:off + 2 + L] = len(new).to_bytes(2, "little") + new
        tmp = p + ".new"
        with open(tmp, "wb") as f:
            f.write(bytes(data))
        after = parse(tmp)
        ok = (after[1] is not None and before[1] is not None
              and after[2][2] == before[2][2]
              and len(after[1]) == len(before[1])
              and open(tmp, "rb").read() == bytes(data))
        if ok:
            os.replace(tmp, p)
            nok += 1
        else:
            os.remove(tmp)
            print("  !! %s 校验失败已回滚" % fn)
    print("写入完成 %d/%d" % (nok, len(plan)))


# ------------------------------------------------------------- zh 二次修正
def cmd_zhfix():
    """中文侧二次修正（术语统一 / 润色），两种模式：

      python ag_xscn.py zhfix --sub 反壁垒 反围壁垒      # 子串替换
      python ag_xscn.py zhfix --map work/glossary/ag-xscn-zhfix.tsv   # 整条替换

    ⚠ 这是写入已汉化文件的唯一正确方式：apply 按英文 src 匹配，
      汉化后再跑必然 0 命中（xscn-patch.ps1 同样受限于此）。
    """
    do = "--apply" in sys.argv
    mode = None
    if "--sub" in sys.argv:
        i = sys.argv.index("--sub")
        old, new = sys.argv[i + 1], sys.argv[i + 2]
        mode = ("sub", old, new)
    elif "--map" in sys.argv:
        i = sys.argv.index("--map")
        mp = {}
        with io.open(sys.argv[i + 1], encoding="utf-8-sig", newline="") as f:
            for ln in f.read().replace("\r\n", "\n").split("\n")[1:]:
                c = ln.split("\t")
                if len(c) >= 2 and c[0]:
                    mp[c[0]] = c[1]
        mode = ("map", mp, None)
    if mode is None:
        print("需要 --sub 或 --map")
        return
    total = 0
    per = collections.defaultdict(list)
    for fn in files():
        p = os.path.join(GAME, fn)
        data, items, meta = parse(p)
        if items is None:
            continue
        slots = []
        if meta[0] is not None:
            slots.append((-1, 0, meta[0], meta[1]))
        slots += items
        for gi, idx, off, L in slots:
            raw = raw_at(data, off, L)
            enc, s = decode(raw)
            if enc != ENC_OUT:
                continue
            if mode[0] == "sub":
                if mode[1] in s:
                    ns = s.replace(mode[1], mode[2])
                else:
                    continue
            else:
                key = s.strip()
                if key not in mode[1]:
                    continue
                ns = s.replace(key, mode[1][key])
            new = ns.encode(ENC_OUT)
            if new != raw:
                per[fn].append((gi, idx, off, L, raw, new))
                total += 1
    print("计划修正 %d 条 / 文件 %d" % (total, len(per)))
    if not do:
        for fn in sorted(per)[:5]:
            for gi, idx, off, L, raw, new in per[fn][:3]:
                print("   %s g%d.%d %r -> %r" % (fn, gi, idx,
                                                 decode(raw)[1], decode(new)[1]))
        print("(dry-run)")
        return
    nok = 0
    for fn in sorted(per):
        p = os.path.join(GAME, fn)
        data = bytearray(open(p, "rb").read())
        before = parse(p)
        for gi, idx, off, L, raw, new in sorted(per[fn], key=lambda x: -x[2]):
            data[off:off + 2 + L] = len(new).to_bytes(2, "little") + new
        tmp = p + ".new"
        with open(tmp, "wb") as f:
            f.write(bytes(data))
        after = parse(tmp)
        ok = (after[1] is not None and after[2][2] == before[2][2]
              and len(after[1]) == len(before[1])
              and open(tmp, "rb").read() == bytes(data))
        if ok:
            os.replace(tmp, p)
            nok += 1
        else:
            os.remove(tmp)
            print("  !! %s 校验失败已回滚" % fn)
    print("修正完成 %d/%d" % (nok, len(per)))


# ---------------------------------------------------------------- verify
def cmd_verify():
    """与备份逐文件比对结构，并统计现状含汉字率；--detail 打印残留英文条目"""
    detail = "--detail" in sys.argv
    bad = 0
    tot_old = tot_new = han = nohan = 0
    tails = []
    left = []
    for fn in files():
        da, ia, ma = parse(os.path.join(BAK, fn))
        db, ib, mb = parse(os.path.join(GAME, fn))
        if ia is None or ib is None:
            print("!! %s 解析失败" % fn)
            bad += 1
            continue
        if ma[2] != mb[2] or len(ia) != len(ib):
            print("!! %s 结构偏差 groups %s->%s items %d->%d" % (
                fn, ma[2], mb[2], len(ia), len(ib)))
            bad += 1
            continue
        tails.append(len(db) - mb[3])
        tot_old += len(ia)
        tot_new += len(ib)
        for gi, idx, off, L in ib:
            enc, s = decode(raw_at(db, off, L))
            if han_count(s):
                han += 1
            else:
                nohan += 1
                if detail and len(left) < 40:
                    left.append((fn, gi, idx, s))
        # 标题
        if mb[0] is not None:
            enc, s = decode(raw_at(db, mb[0], mb[1]))
            if han_count(s) == 0 and detail:
                left.append((fn, -1, 0, "[标题] " + s))
    import collections
    print("备份条目 %d / 现状条目 %d" % (tot_old, tot_new))
    print("现状含汉字 %d / 无汉字 %d" % (han, nohan))
    print("尾部残留分布: %s" % collections.Counter(tails).most_common(5))
    if detail:
        print("--- 无汉字条目样例（最多 40）---")
        for fn, gi, idx, s in left:
            print("  %-26s g%d.%d  %r" % (fn, gi, idx, s))
    print("结构偏差文件: %d" % bad)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "export"
    {"export": cmd_export, "apply": cmd_apply, "verify": cmd_verify,
     "zhfix": cmd_zhfix}[cmd]()
