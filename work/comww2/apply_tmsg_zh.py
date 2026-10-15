# -*- coding: utf-8 -*-
"""COMWW2 `.tmsg` 层落盘器（自带转义，避免依赖 `tmsg.py` 的 map 转义细节）。

用法:
    python apply_tmsg_zh.py --dry
    python apply_tmsg_zh.py --apply

机制（`MECHANICS §14`）：
    `.tmsg` = 「首部 N 个 CRLF」+「正文（可含 CRLF）」+「尾部 M 个 CRLF」
    首尾段是屏幕定位/清屏指令 ⇒ **逐字节原样保留**；只换正文，用 **GBK** 编码。

守卫（任一不过 ⇒ 不落盘）：
  1. 15 个有正文的文件必须全部在 map 内；
  2. map 的 src 必须与当前文件正文**逐字节一致**（防错位）；
  3. 正文 CRLF 个数 src/dst 一致；
  4. 写盘后回读：首尾段逐字节相同、GBK 可解、无 BOM。
"""
import importlib.util
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SD = r"D:\OpenPG2\EFILE_COMWW2\SCENARIO"
MAP = os.path.join(HERE, "comww2-tmsg-map.tsv")

spec = importlib.util.spec_from_file_location(
    "tmsg", r"D:\DSH\军事游戏汉化\work\tmsg\tmsg.py")
tmsg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tmsg)


def unesc(s):
    """还原转义：`\\r\\n` → CRLF，**其余** `\\n` → LF。

    ⚠️ 顺序敏感（实测踩坑）：
      - 先 `'\\\\r\\\\n' → '\\r'` 再 `'\\\\n' → '\\n'` ⇒ 前面生成的 CR 后面那个 `\\n` 也被转掉，
        CRLF 被打散成「CR + CR + LF…」（实测 40 个尾部 CRLF 变成一串裸 CR）；
      - 先 `'\\\\n' → '\\n'` 也会把 `\\r\\n` 拆成 CR+LF 两段（看似对，但依赖后续修复）。
    正确顺序：**先 `\\\\r\\\\n` → CRLF，再 `\\\\n` → LF**（长模式优先）。
    """
    return s.replace("\\r\\n", "\r\n").replace("\\n", "\n")


def load_map():
    mp = {}
    with io.open(MAP, encoding="utf-8", newline="") as fh:
        fh.readline()
        for ln in fh:
            ln = ln.rstrip("\n")
            if not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) < 3:
                continue
            mp[c[0]] = (unesc(c[1]), unesc(c[2]))
    return mp


def region_of(d):
    """待替换字节区 = `split_msg()` 的 head+body+tail（**整文件**）。

    ⚠️ 不能改用「ASCII 正文的最小跨度」：`tmsg.py apply` 的 map 里 src 是整文件解码串
    （保持与既有工具一致），两种切法在 `bkonrad` 这类「前置 0 / 后置 80」文件上并不等价。
    """
    head, body, tail = tmsg.split_msg(d)
    return head + body + tail, body


def main():
    apply = "--apply" in sys.argv
    mp = load_map()
    have = []
    miss = []
    for f in sorted(x for x in os.listdir(SD) if x.lower().endswith(".tmsg")):
        d = open(os.path.join(SD, f), "rb").read()
        _, body = region_of(d)
        if not body:
            continue                      # 纯空行文件
        have.append(f)
        if f not in mp:
            miss.append(f)
    print("有正文 %d 个；map 条目 %d；缺译文 %d %s" % (len(have), len(mp), len(miss), miss))
    if miss:
        raise SystemExit("缺译文，不落盘")

    written = 0
    for f in have:
        src, dst = mp[f]
        p = os.path.join(SD, f)
        d = open(p, "rb").read()
        head, body, tail = tmsg.split_msg(d)
        cur = (head + body + tail).decode("cp1252")
        if cur != src:
            raise SystemExit("正文原文不符 %s：\n  cur=%r\n  src=%r" % (f, cur[:90], src[:90]))
        if cur.count("\n") != dst.count("\n"):
            raise SystemExit("换行数不符 %s" % f)
        new = dst.encode("gbk")
        # 结构守卫：GBK 往返一致 + head/body/tail 三段仍自洽 + 首尾白空段逐字节未变
        if new.decode("gbk") != dst:
            raise SystemExit("GBK 往返不一致 %s" % f)
        h2, b2, t2 = tmsg.split_msg(new)
        if h2 + b2 + t2 != new:
            raise SystemExit("三段切分不自洽 %s" % f)
        if h2 != head or t2 != tail:
            raise SystemExit("首尾白空段被改动 %s" % f)
        if b2 != dst.encode("gbk")[len(head):len(new) - len(tail)]:
            raise SystemExit("正文段不一致 %s" % f)
        if apply:
            with open(p, "wb") as fh:
                fh.write(new)
            back = open(p, "rb").read()
            if back != new:
                raise SystemExit("回读不一致 %s" % f)
        written += 1
        print("  %s %-14s %4dB -> %4dB  正文 %d 汉字"
              % ("已写" if apply else "干跑", f, len(d), len(new),
                 sum(1 for c in b2.decode("gbk") if "\u4e00" <= c <= "\u9fff")))
    print("%s：%d 个文件" % ("已写" if apply else "干跑", written))


if __name__ == "__main__":
    main()
