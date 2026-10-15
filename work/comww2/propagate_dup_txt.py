# -*- coding: utf-8 -*-
"""把已交付的 rep 译文**铺到同组重复文件**（原文 md5 相同的文件必须内容一致）。

起因（2026-09-30）：`gen_prose_zh.py` / `gen_label_zh.py` 只写 rep-list 里的
**代表文件**（671 prose + 227 label = 898），而 `SCENARIO\\` 实际有 **1,032** 个 `.txt`
⇒ 86 个内容组只落了 rep，**134 个同组成员缺文件**（85% → 100%）。

保守按 md5 判定重复：原文 md5 相同才复制（不猜文件名规律）。
⚠️ 换行必须**逐文件沿用目标自己的原文**（COMWW2 有 516 CRLF + 52 LF）。

用法:
    python propagate_dup_txt.py [--dry]
"""
import hashlib
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"D:\OpenPG2\EFILE_COMWW2\SCENARIO"
ZH = r"D:\OpenPG2\EFILE_COMWW2\TEXT-ZH\SCENARIO"


def md5b(b):
    return hashlib.md5(b).hexdigest()


def main():
    dry = "--dry" in sys.argv
    src_raw = {}
    groups = {}
    for f in sorted(os.listdir(SRC)):
        if not f.lower().endswith(".txt"):
            continue
        b = open(os.path.join(SRC, f), "rb").read()
        src_raw[f] = b
        groups.setdefault(md5b(b), []).append(f)

    written = 0
    skipped = 0
    missing_rep = []
    for h, fs in sorted(groups.items()):
        dep = [f for f in fs if os.path.exists(os.path.join(ZH, f))]
        if not dep:
            missing_rep.append(fs)
            continue
        rep = sorted(dep)[0]          # 取已部署成员中字母序最小者当样板
        rep_blob = open(os.path.join(ZH, rep), "rb").read()
        rep_text_gbk = rep_blob.decode("gbk")
        for f in fs:
            if f == rep:
                continue
            tgt = os.path.join(ZH, f)
            if os.path.exists(tgt):
                skipped += 1
                continue
            # 逐文件判定换行：用**本文件自己的**原文
            sraw = src_raw[f]
            n_lf, n_crlf = sraw.count(b"\n"), sraw.count(b"\r\n")
            nl = "\n" if (n_lf > 0 and n_crlf == 0) else "\r\n"
            if nl == "\r\n":
                out = rep_text_gbk.replace("\r\n", "\n").split("\n")
                blob = "\r\n".join(out).encode("gbk")
            else:
                blob = rep_text_gbk.replace("\r\n", "\n").encode("gbk")
            if not dry:
                with open(tgt, "wb") as fh:
                    fh.write(blob)
                back = open(tgt, "rb").read()
                if back != blob:
                    raise SystemExit("回读不一致: %s" % f)
                if back[:3] == b"\xef\xbb\xbf":
                    raise SystemExit("输出含 BOM: %s" % f)
                if nl == "\r\n" and back.count(b"\n") != back.count(b"\r\n"):
                    raise SystemExit("输出含裸 LF: %s" % f)
                if nl == "\n" and back.count(b"\r\n"):
                    raise SystemExit("输出混入 CRLF: %s" % f)
            written += 1
            print("  %s <- %s  (%s, %d B)" % (f, rep, "LF" if nl == "\n" else "CRLF", len(blob)))

    print("%s：铺 %d 个同组文件；已存在跳过 %d；整组缺失 %d 组"
          % ("已写" if not dry else "干跑", written, skipped, len(missing_rep)))
    if missing_rep:
        print("  整组缺失示例:", missing_rep[:5])


if __name__ == "__main__":
    main()
