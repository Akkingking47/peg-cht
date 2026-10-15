# -*- coding: utf-8 -*-
"""定点修正 .xscn 里「括号别名被译成与主名相同」的 5 条。

设计要点（与 xscn-patch.ps1 的「按 map 重建整串区」不同）：
  * 只做**字节级定点替换** —— 只改目标条目的 2 字节长度字段 + 内容，
    其余任何字节都不动（因此结构不可能被破坏）。
  * 从后往前替换，避免偏移失效。
  * 先写临时文件 → 回读校验（data_end / groups / 条目数 / 标题逐字节）→ 通过才写正式文件。
  * 脚本内含中文，保存为 UTF-8（Python 3 源码默认 UTF-8，无 PS 的 GBK 误读问题）。
"""
import os
import struct
import sys

EFILE_DIR = r"D:/OpenPG2/EFILE_OLGWW2/SCENARIO"
BACKUP_DIR = r"D:/DSH/军事游戏汉化/backup/xscn-aliasfix-before"

# (文件, 组, 下标, 期望的当前文本, 修正后文本)
TARGETS = [
    ("18days8.xscn",   0, 27, "埃克洛 (埃克洛)",           "埃克洛 (Eecloo)"),
    ("18days8.xscn",   0, 46, "登德尔 (登德尔)",           "登德尔 (Dendre)"),
    ("18days8.xscn",   0, 60, "根特 (根特)",               "根特 (Gand)"),
    ("18days8.xscn",   0, 64, "夸特雷赫特 (夸特雷赫特)",   "夸特雷赫特 (Quatrecht)"),
    ("n42s13a.xscn",   0, 21, "杜克拉山口 (杜克拉山口)",   "杜克拉山口 (Dukla Pass)"),
]


def decode_smart(raw):
    """含 CJK 则按 GBK，否则按 cp1252。"""
    try:
        s = raw.decode("gbk")
        if any("\u4e00" <= c <= "\u9fff" for c in s):
            return s
    except Exception:
        pass
    return raw.decode("cp1252", "replace")


def parse(path):
    f = open(path, "rb").read()
    st = f.find(b"<N:")
    if st < 0:
        raise RuntimeError("no <N: marker in " + path)
    data_end = f.index(b">", st) + 1
    off = data_end
    title = b""
    if off + 2 <= len(f):
        L = f[off] | (f[off + 1] << 8)
        if 0 < L and off + 2 + L <= len(f):
            title = f[off + 2:off + 2 + L]
            off += 2 + L
    groups = []
    items = []          # (group, idx, len_field_off, raw)
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
            items.append((gi, k, off, f[off + 2:off + 2 + L]))
            off += 2 + L
        if bad:
            break
        groups.append(cnt)
        gi += 1
        if gi > 64:
            break
    return dict(data=f, size=len(f), data_end=data_end, title=title,
                groups=groups, items=items, parsed_end=off)


def main():
    dry = "--apply" not in sys.argv
    by_file = {}
    for fn, g, i, old, new in TARGETS:
        by_file.setdefault(fn, []).append((g, i, old, new))

    rc = 0
    for fn, lst in sorted(by_file.items()):
        p = os.path.join(EFILE_DIR, fn)
        x = parse(p)
        splices = []
        for g, i, old, new in lst:
            hit = [it for it in x["items"] if it[0] == g and it[1] == i]
            if not hit:
                print("  MISS g%d i%d in %s" % (g, i, fn)); rc = 1; continue
            _, _, loff, raw = hit[0]
            cur = decode_smart(raw)
            if cur != old:
                print("  MISMATCH %s g%d i%d: file has %r, expected %r"
                      % (fn, g, i, cur, old)); rc = 1; continue
            nb = new.encode("gbk")
            splices.append((loff, len(raw), nb))

        if not splices:
            print("  no-op %s" % fn); continue

        data = bytearray(x["data"])
        # 从后往前替换
        for loff, oldLen, nb in sorted(splices, key=lambda t: -t[0]):
            data[loff:loff + 2 + oldLen] = struct.pack("<H", len(nb)) + nb
        out = bytes(data)

        # ---- 回读校验 ----
        tmp = p + ".tmpfix"
        open(tmp, "wb").write(out)
        y = parse(tmp)
        errs = []
        if y["data_end"] != x["data_end"]: errs.append("data_end")
        if y["groups"] != x["groups"]: errs.append("groups")
        if len(y["items"]) != len(x["items"]): errs.append("items")
        if y["title"] != x["title"]: errs.append("title")
        # 确认只有目标条目变了
        changed = [n for n, (a, b) in enumerate(zip(x["items"], y["items"])) if a[3] != b[3]]
        if len(changed) != len(splices):
            errs.append("changed=%d expected=%d" % (len(changed), len(splices)))
        for g, i, old, new in lst:
            got = decode_smart([it for it in y["items"] if it[0] == g and it[1] == i][0][3])
            if got != new:
                errs.append("g%d i%d -> %r" % (g, i, got))

        os.remove(tmp)
        if errs:
            print("  PREFLIGHT FAILED %s: %s" % (fn, "; ".join(errs))); rc = 1; continue

        print("  %s: %d -> %d B  (%+d)  仅 %d 条改动 %s"
              % (fn, x["size"], len(out), len(out) - x["size"], len(changed),
                 "DRY" if dry else "WRITTEN"))
        if not dry:
            open(p, "wb").write(out)

    print("rc=%d  mode=%s" % (rc, "dry" if dry else "apply"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
