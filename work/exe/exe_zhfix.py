# -*- coding: utf-8 -*-
"""OpenGen.exe 已汉化串的**二次修正**工具（exe 侧的 zhfix）。

为什么需要它：汉化补丁脚本（unitpanel/unitdlg/maphud）靠**英文原文**匹配，
一旦该处已是中文，重跑只会报"原文不符" ⇒ 改译名/统一术语时无从下手。
本工具按 **FO 定点**替换现有译文，是汉化后唯一正确的修改入口。

安全约束（默认）：
  * 新译文 GBK 字节数 + 1 <= 旧译文 GBK 字节数 + 1  ⇒ 纯缩短，天然不越界；
  * 需要变长时必须显式 --limit N（该串可用空间 = 下一串起点 - FO），
    脚本会校验 len(new)+1 <= N，并把余量填 NUL，**总长不变**；
  * 幂等：当前已是新译文则跳过。

用法:
  python exe_zhfix.py --fo 0x511408 --old "SH 归属：拥有方" --new "SH 归属方"
  python exe_zhfix.py --fo 0x511408 --old "SH 归属：拥有方" --new "SH 归属方" --apply
  python exe_zhfix.py --tsv fix.tsv            # 列: FO<tab>旧译文<tab>新译文[<tab>limit]

  --limit 0x400 --fo ... --new ...             # 变长替换（给出该串可用空间）
"""
import io
import struct
import sys

EXE = r"D:/OpenPG2/OpenGen.exe"


def parse_fo(txt):
    return int(txt, 0)


def load_tsv(path):
    out = []
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        txt = f.read().replace("\r\n", "\n")
    for ln in txt.split("\n"):
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        c = ln.split("\t")
        if len(c) < 3:
            continue
        fo = parse_fo(c[0].strip())
        limit = parse_fo(c[3].strip()) if len(c) > 3 and c[3].strip() else None
        out.append((fo, c[1], c[2], limit))
    return out


def main():
    args = sys.argv[1:]
    apply_ = "--apply" in args
    if "--apply" in args:
        args.remove("--apply")

    jobs = []
    if "--tsv" in args:
        jobs = load_tsv(args[args.index("--tsv") + 1])
    else:
        fo = old = new = limit = None
        i = 0
        while i < len(args):
            if args[i] == "--fo":
                fo = parse_fo(args[i + 1]); i += 2
            elif args[i] == "--old":
                old = args[i + 1]; i += 2
            elif args[i] == "--new":
                new = args[i + 1]; i += 2
            elif args[i] == "--limit":
                limit = parse_fo(args[i + 1]); i += 2
            else:
                print("未知参数 %r" % args[i]); return
        if fo is None or old is None or new is None:
            print(__doc__); return
        jobs = [(fo, old, new, limit)]

    if not jobs:
        print(__doc__); return

    d = bytearray(open(EXE, "rb").read())
    orig_len = len(d)
    errs = []
    print("=== exe zhfix (%d 条) ===" % len(jobs))
    for fo, old, new, limit in jobs:
        ob = old.encode("gbk")
        nb = new.encode("gbk")
        cur = bytes(d[fo:fo + max(len(ob), len(nb)) + 2])
        if cur.startswith(nb + b"\x00"):
            print("  0x%06X  %-22s -> %-22s  已是新译文，跳过" % (fo, old, new))
            continue
        if not cur.startswith(ob + b"\x00"):
            errs.append("0x%06X 当前内容不符：%r（期望 %r）"
                        % (fo, cur[:len(ob) + 2], ob))
            continue
        if limit is None:
            if len(nb) > len(ob):
                errs.append("0x%06X 新译文更长 (%d>%d)，请给 --limit"
                            % (fo, len(nb), len(ob)))
                continue
            win = len(ob) + 1
        else:
            if len(nb) + 1 > limit:
                errs.append("0x%06X 超长 %d>%d" % (fo, len(nb) + 1, limit))
                continue
            win = limit
        d[fo:fo + win] = nb + b"\x00" * (win - len(nb))
        print("  0x%06X  %-22s -> %-22s  %d/%dB"
              % (fo, old, new, len(nb), win))

    if errs:
        print("\n!! 错误 %d 条，未写盘：" % len(errs))
        for e in errs:
            print("   " + e)
        return
    if not apply_:
        print("\n[干跑] 未写盘。加 --apply 正式写入。")
        return

    with open(EXE, "wb") as f:
        f.write(bytes(d))
    c = open(EXE, "rb").read()
    print("\n已写入。长度 %d (原 %d) %s" % (len(c), orig_len,
                                        "一致" if len(c) == orig_len else "不一致!"))
    ok = True
    for fo, old, new, limit in jobs:
        got = c[fo:c.find(b"\x00", fo)].decode("gbk", "replace")
        if got != new:
            print("  !! 校验失败 0x%X %r" % (fo, got)); ok = False
    print("回读校验: %s" % ("全部通过" if ok else "有失败"))


if __name__ == "__main__":
    main()
