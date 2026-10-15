#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tmsg.py —— `.tmsg`（任务目标提示电文）结构解析 / 导出 / 回写。

★ 结构模型（2026-09-28 逆向；形态极简，**无二进制头**）：

    纯文本 = 「行首 N 个 \\r\\n」 + 「正文（可含 \\r\\n 分行）」 + 「行尾 M 个 \\r\\n」

    · 行首/行尾的连续 \\r\\n **不是装饰，是屏幕定位/清屏指令**（引擎按空行数排版），
      ⇒ **必须逐字节原样保留**（N、M 各自不定，逐文件实测）。
    · 正文里的 \\r\\n 是**真实换行**，与行首/行尾的连续空行在语用上不同 —— 但字节层面
      不做区分：**整体按「首尾空行段 + 正文段」切分**。

⚠️ 三条铁律：
  1. **首尾 \\r\\n 段必须原样保留**（数量不得增删），否则电文位置/清屏失效。
  2. 正文译文用 **GBK** 编码；`.tmsg` 是**单文件变长**，不吃槽宽限制，可自由增删（但不能动首尾段）。
  3. 正文若含 `<...>` 包裹的**内心独白/敌对方台词**（AO 的 `<...>` 段）⇒ 同样要译，
     但**保留尖括号**（它是引擎的样式标记，不是内容）。

用法：
    python tmsg.py --efile AO verify
    python tmsg.py --efile AO export [--out FILE]
    python tmsg.py --efile AO apply --map FILE [--apply]    # src(正文) -> dst
    python tmsg.py --efile AO apply --map FILE --apply --dry-run
"""
import sys, os, argparse

GAME = r"D:\OpenPG2"
ROOT = r"D:\DSH\军事游戏汉化"


def split_msg(d):
    """切分为 (head_crlf: bytes, body: bytes, tail_crlf: bytes)。

    head = 从 0 起连续的 \\r\\n 序列；tail = 从末尾向前连续的 \\r\\n 序列。
    注意：head 与 tail 可能覆盖整个文件（全空行文件），此时 body = b""。
    """
    n = len(d)
    i = 0
    while i + 1 < n and d[i] == 0x0D and d[i + 1] == 0x0A:
        i += 2
    head = d[:i]
    j = n
    while j - 2 >= i and d[j - 2] == 0x0D and d[j - 1] == 0x0A:
        j -= 2
    tail = d[j:]
    body = d[i:j]
    return head, body, tail


def build(head, body_zh, tail, encoding="gbk"):
    return head + body_zh.encode(encoding) + tail


def _load(p):
    with open(p, "rb") as fh:
        return fh.read()


def _iter_lib():
    for ef in sorted(os.listdir(GAME)):
        for sd in (os.path.join(GAME, ef, "SCENARIO"),
                   os.path.join(GAME, ef, "TEXT-ZH", "SCENARIO")):
            if not os.path.isdir(sd):
                continue
            for f in sorted(x for x in os.listdir(sd) if x.lower().endswith(".tmsg")):
                yield ef, f, os.path.join(sd, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--efile")
    ap.add_argument("op", choices=["verify", "verifyall", "export", "apply"])
    ap.add_argument("--map")
    ap.add_argument("--out")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    if a.op == "verifyall":
        nf = nb = ne = 0
        for ef, f, p in _iter_lib():
            nf += 1
            d = _load(p)
            head, body, tail = split_msg(d)
            if head + body + tail != d:
                print(f"  ❌ {ef}/{f} 切分不自洽")
                continue
            if (len(head) + len(tail)) % 2:
                print(f"  ⚠️ {ef}/{f} 首尾 \\r\\n 段字节数为奇（{len(head)}/{len(tail)})")
            if body:
                nb += 1
            else:
                ne += 1
        print(f"全库 .tmsg：{nf} 文件；有正文 {nb}；纯空行 {ne}")
        return 0

    if not a.efile:
        print("verify/export/apply 需要 --efile")
        return 2
    sd = os.path.join(GAME, "EFILE_" + a.efile, "SCENARIO")
    files = sorted(f for f in os.listdir(sd) if f.lower().endswith(".tmsg"))

    if a.op == "verify":
        for f in files:
            d = _load(os.path.join(sd, f))
            head, body, tail = split_msg(d)
            ok = head + body + tail == d
            print(f"  {f:16s} {len(d):5d}B  首{len(head):3d} 文{len(body):4d} 尾{len(tail):3d}"
                  f"  {'OK' if ok else '❌'}")
        print(f"{a.efile}: {len(files)} 文件")
        return 0

    if a.op == "export":
        out = a.out or os.path.join(ROOT, "work", a.efile.lower(),
                                    f"{a.efile.lower()}-tmsg-export.tsv")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        n = 0
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("file\thead_B\ttail_B\tlead_crlf\ttrail_crlf\tbody\n")
            for f in files:
                d = _load(os.path.join(sd, f))
                head, body, tail = split_msg(d)
                b = body.decode("cp1252")
                fh.write(f"{f}\t{len(head)}\t{len(tail)}\t{len(head)//2}\t{len(tail)//2}\t"
                         f"{b.replace(chr(13)+chr(10),'<CRLF>')}\n")
                n += 1
        print(f"导出 {n} 条 -> {out}")
        return 0

    if a.op == "apply":
        if not a.map:
            print("apply 需要 --map")
            return 2
        mp = {}
        with open(a.map, encoding="utf-8") as fh:
            next(fh, None)
            for line in fh:
                line = line.rstrip("\n")
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) < 3:
                    continue
                # 转义归一：<CRLF> / \n / \r\n 一律还原为真实 CRLF
                def unesc(s):
                    return (s.replace("<CRLF>", "\r\n")
                             .replace("\\r\\n", "\r\n")
                             .replace("\\n", "\r\n"))
                mp[parts[0]] = (unesc(parts[1]), unesc(parts[2]))
        for f in files:
            if f not in mp:
                continue
            src, dst = mp[f]
            p = os.path.join(sd, f)
            d = _load(p)
            head, body, tail = split_msg(d)
            cur = body.decode("cp1252")
            if cur != src:
                print(f"  ⚠️ {f} 正文原文不符，跳过")
                continue
            new = build(head, dst, tail)
            if a.apply:
                with open(p, "wb") as fh:
                    fh.write(new)
            print(f"  {'✅ 已写' if a.apply else '🔍 干跑'} {f}: {len(d)}B -> {len(new)}B")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
