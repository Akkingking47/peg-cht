# -*- coding: utf-8 -*-
r"""订正 GCE 人工批次的**两类越界**（2026-10-08，接 09-30 中断的会话）。

背景：09-30 的 `_gce_dst_partNN.txt` 有 6 份回稿，但当时写下的守卫
「方括号内容为纯 ASCII ⇒ 必须保留」与 POLICY 六 互斥，把 `[Navarra]`→`[纳瓦拉]`
这类**正确**译文也判成违规 ⇒ 6 份一份都没合并，会话随之中断。

本脚本只做两件有据可查的事（逐行断言行数、逐条断言命中数）：

  ① **罗马数字方括号回归**（POLICY 三）：part01 把 `[XIV]` `[I]` `[X]` … 译成了 `[第14]`
     `[第1]` `[第10]` ⇒ 一律还原成 src 里的罗马数字形式（这些是军团/地域编号，不是部队番号）。
  ② **全角标点归半角**（`.xscn` 分层口径为半角）：`（临时）`→`(临时)`、`（战壕）`→`(战壕)`、
     `，`→`,`。

用法:
    python fix_gce_parts.py --check
    python fix_gce_parts.py --apply
"""
import argparse
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROMAN = re.compile(r"^[IVXLCDM]+$")
FW2HW = {"（": "(", "）": ")", "［": "[", "］": "]", "，": ",", "、": ",", "；": ";", "：": ":"}

TAGS = ("01", "02", "04", "05", "06", "07", "03", "08")


def rd_lines(p):
    if not os.path.exists(p):
        return None
    return [l for l in io.open(p, encoding="utf-8", newline="").read()
            .replace("\r\n", "\n").split("\n") if l.strip()]


def roman_brackets(s):
    return re.findall(r"\[([^\]]*)\]", s)


def fix_pair(src, dst):
    """返回订正后的 dst（无改动则原样返回）。"""
    out = dst
    romans = [t for t in roman_brackets(src) if ROMAN.match(t)]
    if romans:
        assert len(romans) == 1, "本批不应出现一行多个罗马数字方括号: %r" % src
        rb = re.findall(r"\[([^\]]*)\]", out)
        assert len(rb) == 1, "罗马数字行在 dst 里的方括号数 != 1: %r -> %r" % (src, dst)
        if not ROMAN.match(rb[0]):
            out = re.sub(r"\[[^\]]*\]", "[%s]" % romans[0], out)
    # 半角化：仅原文侧为半角标点时才归半角
    for fw, hw in FW2HW.items():
        if fw in out and fw not in src:
            out = out.replace(fw, hw)
    # 原文 `[X] (` 的空格位置保留（POLICY 一.1）
    if "] (" in src and "](" in out:
        out = out.replace("](", "] (")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    n_fix = 0
    plans = []
    for tag in TAGS:
        sp = os.path.join(HERE, "_gce_todo_part%s.txt" % tag)
        dp = os.path.join(HERE, "_gce_dst_part%s.txt" % tag)
        src = rd_lines(sp)
        dst = rd_lines(dp)
        if src is None or dst is None:
            print("  part%s: (缺文件，跳过)" % tag)
            continue
        assert len(src) == len(dst), "part%s 行数不符 %d/%d" % (tag, len(src), len(dst))
        keys = [l.split("|", 1)[1] for l in src]
        new = [fix_pair(k, d) for k, d in zip(keys, dst)]
        ch = [(k, d, n) for k, d, n in zip(keys, dst, new) if d != n]
        n_fix += len(ch)
        print("  part%s: %d 行，需订正 %d" % (tag, len(src), len(ch)))
        for k, d, n in ch:
            print("       %-38s %s -> %s" % (k[:38], d[:34], n[:34]))
        if ch and a.apply:
            plans.append((dp, new))

    print("合计需订正 %d 行" % n_fix)
    if a.apply:
        for dp, new in plans:
            io.open(dp, "w", encoding="utf-8", newline="\n").write("\n".join(new) + "\n")
            back = rd_lines(dp)
            assert back == new, "回读不一致: %s" % dp
            print("  已写 %s（%d 行）" % (os.path.basename(dp), len(new)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
