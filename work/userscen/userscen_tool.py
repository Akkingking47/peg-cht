# -*- coding: utf-8 -*-
r"""`USERSCEN` 层汉化器（2026-09-30 新建，补全库统计盲区）。

结构（直读实测，全库 4 个 efile 同型）：
  - `.xscn`：与 `SCENARIO` 同格式（`<N:...>` + `u16 原标题长 + 标题` + 组表）。
    USERSCEN 的组表几乎全为 `[0,0]`（**只有标题**），少数有串区（GCE/KAISER/PzLIGA）。
  - `.ply` ：**纯文本简报**（无二进制头，`SCENARIO` 侧同型）⇒ 落 `TEXT-ZH\\USERSCEN\\`。
  - `.txt` ：纯文本说明 ⇒ 落 `TEXT-ZH\\USERSCEN\\`。

硬约束：
  1. 原文侧只读；`.xscn` 只能**原地**改（引擎读 `<efile>\\USERSCEN\\`，无 TEXT-ZH 覆盖层）；
  2. `.xscn` 改写前必须 `write_checked`：先写 `.new` → 回读校验 → 才替换；
  3. `.ply`/`.txt` 逐文件沿用**自己的**换行（有 CRLF 也有 LF），译文 GBK/无 BOM；
  4. 标题长度 `u16` 必须同步更新；`<N:####>` 标记与组表**逐字节不动**。

用法:
    python userscen_tool.py --efile COMWW2 verify
    python userscen_tool.py --efile COMWW2 titles                # 列出标题与串区
    python userscen_tool.py --efile COMWW2 apply --map FILE [--apply]        # 标题（3 列：文件\tsrc\tdst）
    python userscen_tool.py --efile GCE strings [--out F]        # ⭐ 串区唯一串导出（2 列：src\tn）
    python userscen_tool.py --efile GCE apply --strings-map F [--apply]      # ⭐ 串区回写（2 列：src\tdst）

⭐ 2026-10-08 增量（GCE 需要；KAISER/PzLIGA 同型）：COMWW2 的 USERSCEN `.xscn` **只有标题**，
   所以旧版只做标题。GCE 的 USERSCEN `.xscn` 有真实串区（14 个文件 / 1741 条）⇒ 补上
   串区导出与**原地**回写。既有 `titles` / `verify` / `apply --map`（标题）行为**一字未改**。
"""
import argparse
import collections
import importlib.util
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\OpenPG2"
BACKUP = r"D:\DSH\军事游戏汉化\backup"
ENC_IN, ENC_OUT = "cp1252", "gbk"

spec = importlib.util.spec_from_file_location(
    "xscn", r"D:\DSH\军事游戏汉化\work\xscn\xscn.py")
xscn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(xscn)


def ctx(efile):
    e = efile.strip().upper()
    if not e.startswith("EFILE_"):
        e = "EFILE_" + e
    return (e,
            os.path.join(ROOT, e, "USERSCEN"),
            os.path.join(BACKUP, "ORIGINAL-" + e, "USERSCEN"),
            os.path.join(ROOT, e, "TEXT-ZH", "USERSCEN"))


def list_files(game, ext):
    if not os.path.isdir(game):
        return []
    return sorted(f for f in os.listdir(game) if f.lower().endswith(ext))


def read_title(path):
    """复用 `xscn.py::parse()`（字节级结构唯一真源），取出标题与串区。"""
    data, items, meta = xscn.parse(path)
    if meta is None:
        return data, None, None, (None, None)
    to, tl, groups, end, size = meta
    title = data[to + 2:to + 2 + tl].decode(ENC_IN) if to is not None else None
    return data, (to, tl), title, (items, meta)


def rewrite_title(data, to, tl, new_title):
    """只替换标题槽（u16 长度 + 字节），`<N:####>` 与组表逐字节不动。"""
    b = new_title.encode(ENC_OUT)
    if len(b) > 0xFFFF:
        raise SystemExit("标题过长")
    return data[:to] + bytes([len(b) & 0xFF, len(b) >> 8]) + b + data[to + 2 + tl:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--efile", required=True)
    ap.add_argument("op", choices=["verify", "titles", "apply", "strings"])
    ap.add_argument("--map")
    ap.add_argument("--strings-map")
    ap.add_argument("--out")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    ef, game, bak, tzh = ctx(a.efile)
    xs = list_files(game, ".xscn")
    pl = list_files(game, ".ply")
    tx = list_files(game, ".txt")
    print("%s\\USERSCEN：xscn %d / ply %d / txt %d" % (ef, len(xs), len(pl), len(tx)))

    if a.op == "titles":
        for f in xs:
            p = os.path.join(game, f)
            data, tt, title, rest = read_title(p)
            if tt is None:
                print("  %-28s (无标题)" % f)
                continue
            items, meta = rest
            lat = [xscn.raw_at(data, off, L).decode(ENC_IN, "replace")
                   for gi, i, off, L in (items or [])]
            lat = [s for s in lat if any(c.isalpha() and ord(c) < 128 for c in s)]
            print("  %-28s 标题=%r  串区条目=%d（拉丁 %d）" % (f, title, len(items or []), len(lat)))
            for s in lat[:5]:
                print("        · %s" % s[:70])
        return

    if a.op == "strings":
        # ⭐ 串区唯一串导出（格式 `src\tn`，与 `xscn.py export` 同型）
        cnt = collections.Counter()
        n = 0
        for f in xs:
            data, items, meta = xscn.parse(os.path.join(game, f))
            if items is None:
                continue
            for gi, i, off, L in xscn.slots_of(data, items, meta):
                raw = xscn.raw_at(data, off, L)
                enc, s = xscn.decode(raw)
                if enc == ENC_OUT:              # 已是中文，跳过
                    continue
                key = s.strip()
                if not key:
                    continue
                cnt[key] += 1
                n += 1
        out = a.out or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "%s-userscen-uniq.tsv" % ef.split("_", 1)[1].lower())
        with io.open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("src\tn\n")
            for s, c in sorted(cnt.items(), key=lambda x: (-x[1], x[0])):
                fh.write("%s\t%d\n" % (s, c))
        print("  USERSCEN 串区未汉化 %d 处 / 唯一 %d -> %s" % (n, len(cnt), out))
        return

    if a.op == "verify":
        bad = []
        for f in xs:
            p = os.path.join(game, f)
            data, tt, title, rest = read_title(p)
            items, meta = rest
            if meta is None or meta[3] != meta[4]:
                bad.append((f, "残留 %s" % (meta[4] - meta[3] if meta else "?")))
        print("  .xscn 结构异常 %d %s" % (len(bad), bad[:5]))
        han = lambda s: sum(1 for c in s if "\u4e00" <= c <= "\u9fff")
        for f in xs:
            p = os.path.join(game, f)
            data, tt, title, rest = read_title(p)
            if title is not None and han(title):
                print("    标题已中文化: %-24s %s" % (f, title))
        for f in pl + tx:
            p = os.path.join(tzh, f)
            if os.path.exists(p):
                s = open(p, "rb").read().decode("gbk", "replace")
                print("    交付件已存在: %-24s %d 汉字" % (f, han(s)))
            else:
                print("    ⬜ 未交付: %s" % f)
        return

    # apply
    if a.strings_map:
        # ⭐ 串区**原地**回写（2 列 src\tdst）。与 `xscn.py apply` 同判据：按 cp1252 读、
        #    strip 后精确匹配；已是 GBK 的槽位跳过。写入必走 `write_checked`。
        mp2 = {}
        with io.open(a.strings_map, encoding="utf-8-sig", newline="") as fh:
            for i, ln in enumerate(fh.read().replace("\r\n", "\n").split("\n")):
                if i == 0 or not ln.strip():
                    continue
                c = ln.split("\t")
                if len(c) >= 2 and c[0]:
                    mp2[c[0]] = c[1]
        print("串区 map 条目 %d" % len(mp2))
        tot = 0
        nfile = 0
        for f in xs:
            p = os.path.join(game, f)
            data, items, meta = xscn.parse(p)
            if items is None:
                print("  !! 解析失败 %s" % f)
                continue
            before = xscn.parse(p)
            plan = []
            miss = 0
            for gi, i, off, L in xscn.slots_of(data, items, meta):
                raw = xscn.raw_at(data, off, L)
                enc, s = xscn.decode(raw)
                if enc == ENC_OUT:
                    continue
                key = s.strip()
                if not key:
                    continue
                if key in mp2:
                    lead = raw[:len(raw) - len(raw.lstrip())]
                    trail = raw[len(raw.rstrip()):]
                    new = lead + mp2[key].encode(ENC_OUT) + trail
                    if new != raw:
                        plan.append((off, L, raw, new))
                else:
                    miss += 1
            if not plan:
                continue
            blob = bytearray(data)
            for off, L, raw, new in sorted(plan, key=lambda x: -x[0]):
                blob[off:off + 2 + L] = len(new).to_bytes(2, "little") + new
            if a.apply:
                if not xscn.write_checked(p, blob, before):
                    raise SystemExit("write_checked 失败（结构对拍不过）: %s" % f)
            tot += len(plan)
            nfile += 1
            print("  %s %-28s 改写 %d 条%s" % ("已写" if a.apply else "干跑", f, len(plan),
                                              ("，未命中 %d" % miss) if miss else ""))
        print("串区：%s %d 条 / %d 文件" % ("已写" if a.apply else "干跑", tot, nfile))
        return

    if not a.map:
        raise SystemExit("apply 需要 --map（标题）或 --strings-map（串区）")
    mp = {}
    with io.open(a.map, encoding="utf-8-sig", newline="") as fh:
        fh.readline()
        for ln in fh:
            c = ln.rstrip("\n").split("\t")
            if len(c) >= 3 and c[0]:
                mp[c[0]] = (c[1], c[2])
    print("map 条目 %d" % len(mp))

    done = 0
    for f in xs:
        if f not in mp:
            continue
        src, dst = mp[f]
        p = os.path.join(game, f)
        before = xscn.parse(p)                 # 结构基线（供 write_checked 对拍）
        data, tt, title, rest = read_title(p)
        if tt is None:
            print("  !! %s 无标题" % f)
            continue
        if title.strip() != src.strip():
            raise SystemExit("标题原文不符 %s：%r != %r" % (f, title, src))
        # ⚠️ 首尾空白沿用**原文**（`madrid_36.xscn` 标题尾带空格）；TSV 很难保住尾空格，
        #    故比对用 strip、拼回时用原文的 lead/trail。
        lead = title[:len(title) - len(title.lstrip())]
        trail = title[len(title.rstrip()):]
        blob = rewrite_title(data, tt[0], tt[1], lead + dst.strip() + trail)
        if a.apply:
            # ⚠️ 必须走 `xscn.write_checked(path, data, before)`：它先写 `.new`、
            #    再 parse 回来比对**组表与条目数**、才 os.replace —— 本层唯一安全入口。
            if not xscn.write_checked(p, bytearray(blob), before):
                raise SystemExit("write_checked 失败（结构对拍不过）: %s" % f)
        done += 1
        print("  %s %-28s %r -> %r（%d B）" % ("已写" if a.apply else "干跑", f, src, dst, len(blob)))
    print("%s：标题 %d 个" % ("已写" if a.apply else "干跑", done))


if __name__ == "__main__":
    main()
