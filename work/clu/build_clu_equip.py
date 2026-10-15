# -*- coding: utf-8 -*-
r"""合并 equip97.txt 的子代理产出 → 严校验 → 生成 `TEXT-ZH\equip97.txt`。

输入: work\clu\equip-chunks\chunk-NN.tsv（单列）＋ work\clu\equip-zh\part-NN.tsv（src<TAB>dst）
输出: D:\OpenPG2\EFILE_Clu\TEXT-ZH\equip97.txt（GBK / 无 BOM / CRLF / 行数逐行对齐）

校验（任一不过即拒绝落盘）：行数与输入相等、每行恰 1 TAB、TAB 前逐字符相同、
`/ [ ] ( )` 计数一致、译文非空无首尾空格、GBK 可编码、不得引入 src 之外的拉丁字母；
**首行版本横幅照 10/11 个已交付 efile 的先例原样保留**。
用法: python build_clu_equip.py [--apply]
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
EFILE = r"D:\OpenPG2\EFILE_Clu"
CHUNKS = os.path.join(HERE, "equip-chunks")
PARTS = os.path.join(HERE, "equip-zh")
LATRUN = re.compile(r"[A-Za-z]+")
STRUCT = re.compile(r"[/\[\]()（）]")


def rd_lines(p):
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        return f.read().replace("\r\n", "\n").split("\n")


def main():
    apply = "--apply" in sys.argv
    tr = {}
    errs = []
    parts = sorted(f for f in os.listdir(PARTS) if f.startswith("part-") and f.endswith(".tsv"))
    allch = sorted(f for f in os.listdir(CHUNKS) if f.startswith("chunk-"))
    if not parts:
        raise SystemExit("!! 还没有任何 equip-zh/part-*.tsv")
    if len(parts) < len(allch):
        msg = "!! 只回了 %d/%d 块（缺 %s）——只允许干跑" % (
            len(parts), len(allch),
            ",".join(sorted(set(allch) - {p.replace("part-", "chunk-") for p in parts})))
        if apply:
            raise SystemExit(msg)
        print(msg)
    for pf in parts:
        cf = os.path.join(CHUNKS, pf.replace("part-", "chunk-"))
        srcs = [l for l in rd_lines(cf)]
        outs = [l for l in rd_lines(os.path.join(PARTS, pf))]
        if srcs and srcs[-1] == "":
            srcs.pop()
        if outs and outs[-1] == "":
            outs.pop()
        if len(srcs) != len(outs):
            errs.append("%s 行数 %d != %d" % (pf, len(outs), len(srcs)))
            continue
        for n, (a, b) in enumerate(zip(srcs, outs), 1):
            c = b.split("\t")
            if len(c) != 2:
                errs.append("%s:%d 不是恰好 1 个 TAB" % (pf, n))
                continue
            if c[0] != a:
                errs.append("%s:%d 原文列不符 %r != %r" % (pf, n, c[0][:40], a[:40]))
                continue
            dst = c[1]
            if not dst.strip():
                errs.append("%s:%d 译文为空" % (pf, n))
                continue
            if len(STRUCT.findall(a)) != len(STRUCT.findall(dst)):
                errs.append("%s:%d 结构符号数不符 %r -> %r" % (pf, n, a[:40], dst[:40]))
                continue
            bad = [t for t in LATRUN.findall(dst) if t not in a]
            if bad:
                errs.append("%s:%d 新拉丁 %s: %r -> %r" % (pf, n, bad, a[:40], dst[:40]))
                continue
            try:
                dst.encode("gbk")
            except UnicodeEncodeError:
                errs.append("%s:%d GBK 装不下 %r" % (pf, n, dst[:30]))
                continue
            tr[a] = dst
    raw = open(os.path.join(EFILE, "equip97.txt"), "rb").read()
    nl = "\r\n" if raw.count(b"\r\n") else "\n"
    lines = raw.decode("cp1252").split(nl)
    out, used, kept = [], 0, 0
    for i, l in enumerate(lines):
        if not l.strip():
            out.append(l)
            continue
        if i == 0:                       # 版本横幅：照先例保留
            out.append(l)
            kept += 1
            continue
        if l in tr:
            out.append(tr[l])
            used += 1
        else:
            out.append(l)
            kept += 1
    blob = nl.join(out).encode("gbk")
    print("equip97.txt 行 %d；已译 %d 行；照抄/未覆盖 %d 行" % (len(lines), used, kept))
    if errs:
        print("!! 校验未过 %d 条：" % len(errs))
        for e in errs[:40]:
            print("   " + e)
        return 1
    if blob.decode("gbk").split(nl) != out:
        raise SystemExit("!! 编解码往返不一致")
    print("字节 %d -> %d" % (len(raw), len(blob)))
    if not apply:
        print("(dry-run，加 --apply 落盘)")
        return 0
    d = os.path.join(EFILE, "TEXT-ZH")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "equip97.txt")
    with open(p, "wb") as f:
        f.write(blob)
    back = open(p, "rb").read()
    assert back == blob and back[:3] != b"\xef\xbb\xbf", "回读不一致"
    assert back.count(b"\n") == back.count(b"\r\n"), "出现裸 LF"
    print("已写 %s（GBK / 无 BOM / CRLF；原文未动）" % p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
