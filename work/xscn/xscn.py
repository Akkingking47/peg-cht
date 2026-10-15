# -*- coding: utf-8 -*-
"""通用 `.xscn` 尾部串区工具（参数化 efile；字节级定点替换，可重入）。

结构（全库同源）：
  <场景数据>  <N:####>  标题(u16 len + bytes)  组1(u16 cnt) [u16 len + bytes]...  组2 ...

用法：
  python xscn.py --efile AG verify [--detail]
  python xscn.py --efile AO export [--full] [--out FILE]
  python xscn.py --efile AO apply --map FILE [--apply]        # 按 src->dst 替换（默认 dry-run）
  python xscn.py --efile AG zhfix --sub 旧 新 [--apply]       # 中文侧二次修正（子串）
  python xscn.py --efile AG zhfix --map FILE [--apply]        # 中文侧二次修正（整条）

来源：`work/glossary/ag_xscn.py`（AG 专用版）的泛化。**parse() 逐字沿用**，
以保证与既有 AG 结果完全一致（已用 `verify` 对拍）。

⚠️ 三个已踩过的坑（`MECHANICS.md` 有详情）：
  1) `cnt == 0` 是**合法空组**，不是结束信号 —— AG 有 20/86 文件组 0 为空；
     旧「cnt<=0 即 break」规则会把整个串区当尾部残留丢掉（AG 低估 1,143 条）。
     判据只能是「解析位置 == 文件长度」。
  2) key 必须统一 `strip()`（否则前导空格串对不上）。
  3) 词典必须**允许空译文**（`the` / `!` → 空）。

⚠️ 写入已汉化文件的唯一正确入口是 `zhfix`：`apply` 按**原文 src** 匹配，
   汉化后再跑必然 0 命中（`xscn-patch.ps1` 同样受限于此）。
   反之，修「保留原文」条目（如 cp1252 残留）要用 `apply --map`，
   因为那些条目不是 `ENC_OUT`，`zhfix` 会跳过。
"""
import io
import os
import sys
import collections

ROOT = r"D:/OpenPG2"
BACKUP = r"D:/DSH/军事游戏汉化/backup"
ENC_IN = "cp1252"
ENC_OUT = "gbk"


def norm_efile(s):
    s = s.strip().upper()
    if not s.startswith("EFILE_"):
        s = "EFILE_" + s
    return s


class Ctx(object):
    def __init__(self, efile):
        self.efile = norm_efile(efile)
        self.game = os.path.join(ROOT, self.efile, "SCENARIO")
        self.bak = os.path.join(BACKUP, "ORIGINAL-" + self.efile, "SCENARIO")
        self.tag = self.efile.split("_", 1)[1]
        self.work = os.path.join(r"D:/DSH/军事游戏汉化/work", self.tag.lower())

    def files(self):
        if not os.path.isdir(self.game):
            print("!! 目录不存在: %s" % self.game)
            sys.exit(2)
        return sorted(f for f in os.listdir(self.game) if f.lower().endswith(".xscn"))


def _printable(b):
    """条目字节合法性：可打印 ASCII / 西欧高位(cp1252 变音符) / 制表换行 —— 沿用 ag_xscn.py"""
    return b >= 0x20 or b in (0x09, 0x0A, 0x0D)


def parse(path):
    """返回 (data, items, meta)；items=[(gi, idx, off, L)]
    meta=(title_off, title_len, groups, end, size)  —— 逐字沿用 ag_xscn.py.parse()
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
            # ⚠️ 非可打印 = 组内的「二进制项」（如 BASEKORP bc_it_teu.xscn 的
            #    b'\x04q~\xde\x90\x0c'，疑为坐标/marker）。它消耗 L 字节但**不可翻译**：
            #    必须跳过登记、但**继续推进 off** —— 旧版在此 break 整组 ⇒ 尾部残留 1438 B。
            if all(_printable(b) for b in data[off + 2:off + 2 + L]):
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
    try:
        s = raw.decode(ENC_OUT)
        if any("\u4e00" <= c <= "\u9fff" for c in s):
            return ENC_OUT, s
    except Exception:
        pass
    return ENC_IN, raw.decode(ENC_IN, "replace")


def han_count(s):
    return sum(1 for c in s if "\u4e00" <= c <= "\u9fff")


def slots_of(data, items, meta):
    out = []
    if meta[0] is not None:
        out.append((-1, 0, meta[0], meta[1]))
    out += items
    return out


def write_checked(path, data, before):
    """先写 .new → 回读校验 → 才替换正式文件（硬纪律 §2）"""
    tmp = path + ".new"
    with open(tmp, "wb") as f:
        f.write(bytes(data))
    after = parse(tmp)
    ok = (after[1] is not None and before[1] is not None
          and after[2][2] == before[2][2]
          and len(after[1]) == len(before[1])
          and open(tmp, "rb").read() == bytes(data))
    if ok:
        os.replace(tmp, path)
    else:
        os.remove(tmp)
    return ok


def load_map(p):
    m = {}
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2 and c[0]:
                m[c[0]] = c[1]
    return m


# ---------------------------------------------------------------- export
def cmd_export(ctx):
    full = "--full" in sys.argv
    out = os.path.join(ctx.work, "xscn-uniq.tsv")
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    cnt = collections.Counter()
    groups_of = collections.defaultdict(set)
    where = collections.defaultdict(list)
    nfiles = nitems = 0
    tails = []
    for fn in ctx.files():
        p = os.path.join(ctx.game, fn)
        data, items, meta = parse(p)
        if items is None:
            print("!! 解析失败 %s" % fn)
            continue
        nfiles += 1
        title_off, title_len, groups, end, size = meta
        tails.append(size - end)
        if title_off is not None:
            enc, s = decode(raw_at(data, title_off, title_len))
            if enc != ENC_OUT:
                key = s.strip()
                cnt[key] += 1
                groups_of[key].add(-1)
                if len(where[key]) < 3:
                    where[key].append(fn)
        nitems += len(items)
        for gi, idx, off, L in items:
            enc, s = decode(raw_at(data, off, L))
            if enc == ENC_OUT:
                continue
            key = s.strip()
            cnt[key] += 1
            groups_of[key].add(gi)
            if len(where[key]) < 3:
                where[key].append(fn)
    print("%s: 文件 %d  条目 %d  唯一(非中文) %d  尾部残留 %s" % (
        ctx.efile, nfiles, nitems, len(cnt), collections.Counter(tails).most_common(3)))
    os.makedirs(ctx.work, exist_ok=True)
    with io.open(out, "w", encoding="utf-8", newline="") as f:
        f.write("src\tfreq\tgroups\texample\n")
        for k, n in cnt.most_common():
            f.write("%s\t%d\t%s\t%s\n" % (k, n, ",".join(str(x) for x in sorted(groups_of[k])), where[k][0]))
    print("已写 %s" % out)
    if full:
        fo2 = os.path.join(ctx.work, "xscn-full.tsv")
        with io.open(fo2, "w", encoding="utf-8", newline="") as f:
            f.write("file\tgroup\tidx\tsrc\n")
            for fn in ctx.files():
                data, items, meta = parse(os.path.join(ctx.game, fn))
                if items is None:
                    continue
                for gi, idx, off, L in items:
                    f.write("%s\t%d\t%d\t%s\n" % (fn, gi, idx, decode(raw_at(data, off, L))[1].rstrip()))
        print("已写 %s" % fo2)


# ---------------------------------------------------------------- apply
def cmd_apply(ctx):
    do = "--apply" in sys.argv
    if "--map" not in sys.argv:
        print("apply 需要 --map <file>（禁止隐式套用其它 efile 的词典）")
        return
    mp = sys.argv[sys.argv.index("--map") + 1]
    m = load_map(mp)
    plan = collections.defaultdict(list)
    miss = collections.Counter()
    total = 0
    for fn in ctx.files():
        p = os.path.join(ctx.game, fn)
        data, items, meta = parse(p)
        if items is None:
            continue
        for gi, idx, off, L in slots_of(data, items, meta):
            raw = raw_at(data, off, L)
            enc, s = decode(raw)
            if enc == ENC_OUT:
                continue
            key = s.strip()
            if not key:
                continue
            if key in m:
                lead = raw[:len(raw) - len(raw.lstrip())]
                trail = raw[len(raw.rstrip()):]
                new = lead + m[key].encode(ENC_OUT) + trail
                if new != raw:
                    plan[fn].append((gi, idx, off, L, raw, new))
                    total += 1
            else:
                miss[key] += 1
    print("词典 %d 条；计划改写 %d 条 / 文件 %d / 总文件 %d" % (len(m), total, len(plan), len(ctx.files())))
    if miss:
        print("   未命中 %d 个唯一串（前 10）:" % len(miss))
        for k, n in miss.most_common(10):
            print("     %-42s x%d" % (k[:42], n))
    if not do:
        for fn in sorted(plan)[:5]:
            for gi, idx, off, L, raw, new in plan[fn][:4]:
                print("   %s g%d.%d %r -> %r" % (fn, gi, idx, decode(raw)[1], decode(new)[1]))
        print("(dry-run)")
        return
    nok = 0
    for fn in sorted(plan):
        p = os.path.join(ctx.game, fn)
        data = bytearray(open(p, "rb").read())
        before = parse(p)
        for gi, idx, off, L, raw, new in sorted(plan[fn], key=lambda x: -x[2]):
            data[off:off + 2 + L] = len(new).to_bytes(2, "little") + new
        if write_checked(p, data, before):
            nok += 1
        else:
            print("  !! %s 校验失败已回滚" % fn)
    print("写入完成 %d/%d" % (nok, len(plan)))


# ------------------------------------------------------------- zh 二次修正
def cmd_zhfix(ctx):
    do = "--apply" in sys.argv
    if "--sub" in sys.argv:
        i = sys.argv.index("--sub")
        mode = ("sub", sys.argv[i + 1], sys.argv[i + 2])
    elif "--map" in sys.argv:
        i = sys.argv.index("--map")
        mode = ("map", load_map(sys.argv[i + 1]), None)
    else:
        print("需要 --sub 或 --map")
        return
    total = 0
    per = collections.defaultdict(list)
    for fn in ctx.files():
        p = os.path.join(ctx.game, fn)
        data, items, meta = parse(p)
        if items is None:
            continue
        for gi, idx, off, L in slots_of(data, items, meta):
            raw = raw_at(data, off, L)
            enc, s = decode(raw)
            if enc != ENC_OUT:
                continue
            if mode[0] == "sub":
                if mode[1] not in s:
                    continue
                ns = s.replace(mode[1], mode[2])
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
                print("   %s g%d.%d %r -> %r" % (fn, gi, idx, decode(raw)[1], decode(new)[1]))
        print("(dry-run)")
        return
    nok = 0
    for fn in sorted(per):
        p = os.path.join(ctx.game, fn)
        data = bytearray(open(p, "rb").read())
        before = parse(p)
        for gi, idx, off, L, raw, new in sorted(per[fn], key=lambda x: -x[2]):
            data[off:off + 2 + L] = len(new).to_bytes(2, "little") + new
        if write_checked(p, data, before):
            nok += 1
        else:
            print("  !! %s 校验失败已回滚" % fn)
    print("修正完成 %d/%d" % (nok, len(per)))


# ------------------------------------------------------------- rawfix
def cmd_rawfix(ctx):
    """修「保留原文」的 cp1252 残留条目 —— apply / zhfix 都够不到的那一类。

    ⚠️ 为什么需要它：`decode()` 先试 GBK，只要解出汉字就判为「已汉化」。
       而 cp1252 高字节（ä 0xE4 / Ü 0xDC / é 0xE9）在 GBK 下会解出 `鋞`/`蹹`/`趿`
       ——**本身就是汉字码位**，于是这些乱码条目被 `apply`（`enc==ENC_OUT` 跳过）
       和 `zhfix`（`enc!=ENC_OUT` 跳过）双双漏掉，长期无人能修。
       反过来，`verify` 的「含汉字」统计也会把它们算作已汉化 ⇒ **校验被乱码骗过**。

    本操作**显式按 cp1252 读**每个槽位，与词典 key 精确匹配才替换。
    真正的中文条目的 cp1252 读法是拉丁乱码，不会撞上词典 key，故安全。
    """
    do = "--apply" in sys.argv
    if "--map" not in sys.argv:
        print("rawfix 需要 --map <file>")
        return
    m = load_map(sys.argv[sys.argv.index("--map") + 1])
    total = 0
    per = collections.defaultdict(list)
    for fn in ctx.files():
        p = os.path.join(ctx.game, fn)
        data, items, meta = parse(p)
        if items is None:
            continue
        for gi, idx, off, L in slots_of(data, items, meta):
            raw = raw_at(data, off, L)
            # ⚠️ 已汉化槽位是 GBK 字节，cp1252 解不了（0x8D/0x81/0x8F 等未定义码位）。
            #    必须容错跳过，否则整个 efile 一碰到中文槽位就崩。
            try:
                key = raw.decode(ENC_IN).strip()
            except UnicodeDecodeError:
                continue
            if not key or key not in m:
                continue
            lead = raw[:len(raw) - len(raw.lstrip())]
            trail = raw[len(raw.rstrip()):]
            new = lead + m[key].encode(ENC_OUT) + trail
            if new != raw:
                per[fn].append((gi, idx, off, L, raw, new))
                total += 1
    print("%s rawfix: 词典 %d 条；计划修正 %d 条 / 文件 %d" % (ctx.efile, len(m), total, len(per)))
    if not do:
        for fn in sorted(per)[:8]:
            for gi, idx, off, L, raw, new in per[fn][:4]:
                print("   %s g%d.%d %r -> %r" % (fn, gi, idx, raw.decode(ENC_IN), new.decode(ENC_OUT)))
        print("(dry-run)")
        return
    nok = 0
    for fn in sorted(per):
        p = os.path.join(ctx.game, fn)
        data = bytearray(open(p, "rb").read())
        before = parse(p)
        for gi, idx, off, L, raw, new in sorted(per[fn], key=lambda x: -x[2]):
            data[off:off + 2 + L] = len(new).to_bytes(2, "little") + new
        if write_checked(p, data, before):
            nok += 1
        else:
            print("  !! %s 校验失败已回滚" % fn)
    print("修正完成 %d/%d" % (nok, len(per)))


# ---------------------------------------------------------------- verify
def cmd_verify(ctx):
    detail = "--detail" in sys.argv
    if not os.path.isdir(ctx.bak):
        print("!! 无备份目录 %s（无法比对）" % ctx.bak)
        return
    bad = 0
    tot_old = tot_new = han = nohan = 0
    tails = []
    left = []
    for fn in ctx.files():
        pb = os.path.join(ctx.bak, fn)
        if not os.path.exists(pb):
            print("!! 备份缺文件 %s" % fn)
            bad += 1
            continue
        da, ia, ma = parse(pb)
        db, ib, mb = parse(os.path.join(ctx.game, fn))
        if ia is None or ib is None:
            print("!! %s 解析失败" % fn)
            bad += 1
            continue
        if ma[2] != mb[2] or len(ia) != len(ib):
            print("!! %s 结构偏差 groups %s->%s items %d->%d" % (fn, ma[2], mb[2], len(ia), len(ib)))
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
        if mb[0] is not None:
            enc, s = decode(raw_at(db, mb[0], mb[1]))
            if han_count(s) == 0 and detail:
                left.append((fn, -1, 0, "[标题] " + s))
    print("%s: 备份条目 %d / 现状条目 %d" % (ctx.efile, tot_old, tot_new))
    print("   现状含汉字 %d / 无汉字 %d" % (han, nohan))
    print("   尾部残留分布: %s" % collections.Counter(tails).most_common(5))
    if detail:
        print("   --- 无汉字条目样例（最多 40）---")
        for fn, gi, idx, s in left:
            print("     %-26s g%d.%d  %r" % (fn, gi, idx, s))
    print("   结构偏差文件: %d" % bad)


OPS = ("export", "apply", "verify", "zhfix", "rawfix")


def main():
    argv = sys.argv[1:]
    if "--efile" not in argv:
        print(__doc__)
        return
    i = argv.index("--efile")
    ctx = Ctx(argv[i + 1])
    cmd = next((a for a in argv if a in OPS), None)
    if cmd is None:
        print(__doc__)
        return
    {"export": cmd_export, "apply": cmd_apply, "verify": cmd_verify,
     "zhfix": cmd_zhfix, "rawfix": cmd_rawfix}[cmd](ctx)


if __name__ == "__main__":
    main()
