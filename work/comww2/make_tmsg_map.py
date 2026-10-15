# -*- coding: utf-8 -*-
"""构造 COMWW2 `.tmsg` 修订表（`file<TAB>src<TAB>dst`）。

⭐ 关键设计（2026-09-30 踩坑后重构）：
  `.tmsg` 的「版面」不只是首尾连续 CRLF —— `hun07/10/11` 的**正文内部就带大量 CRLF**
  （屏幕定位/清屏），所以：
    1. **src 一律由 `split_msg()` 从文件实读**（head+body+tail 即待替换字节区），不手抄；
    2. **译文只提供「中间文字」**，前后白空**从 src 自动继承**（逐字节相同）；
       ⇒ 换行个数/空格永远不会因手写而错。
  只有「中间文字」本身是人工翻译内容。

用法: python make_tmsg_map.py --apply
"""
import importlib.util
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SD = r"D:\OpenPG2\EFILE_COMWW2\SCENARIO"
OUT = os.path.join(HERE, "comww2-tmsg-map.tsv")

spec = importlib.util.spec_from_file_location(
    "tmsg", r"D:\DSH\军事游戏汉化\work\tmsg\tmsg.py")
tmsg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tmsg)

def esc(s):
    """转义成单行 TSV 单元格：CRLF → `\\r\\n`，裸 LF → `\\n`（顺序敏感）。"""
    return s.replace("\r\n", "\\r\\n").replace("\n", "\\n")

# 只写「中间文字」（正文实义部分），前后白空由脚本从原文继承
DST_MID = {
    "bkonrad.tmsg": "胜利条件：要成功完成本剧本，你必须把6个地面单位移动到布达佩斯附近的外围防御圈内，"
                    "并不惜一切代价夺取并守住塞克什白堡！另外，在部署之后、决定行动之前，"
                    "请务必检查你部队的弹药与燃料装载量……",
    "bnordwind.tmsg": "提示：尽量让你所有的核心单位在本剧本结束前保持接近满编",
    "ga1for.tmsg": "你现在可以下令撤离，或者设法在本剧本结束时占领2个胜利点……",
    "ga1got.tmsg": "你已被分配到一个增援单位……",
    "ga1the.tmsg": "你已被分配到一个增援单位",
    "ga2_14.tmsg": "你现在可以部署你剩余的部队了……",
    "jh3don.tmsg": "司令部报告游击队活动增加，因此预计增援将在几天内抵达",
    "konrad.tmsg": "胜利条件：要成功完成本剧本，你必须把6个地面单位移动到布达佩斯附近的外围防御圈内，"
                   "并不惜一切代价夺取并守住塞克什白堡！另外，在部署之后、决定行动之前，"
                   "请务必检查你部队的弹药与燃料装载量……",
    "nordwind.tmsg": "提示：尽量让你所有的核心单位在本剧本结束前保持接近满编",
    "st05.tmsg": "你已被分配到一个增援单位",
    "st17.tmsg": "你已被分配到一个增援单位",
    "wg1.tmsg": "把6个地面单位移动到格罗莫斯拉夫卡，并确保你被标记的单位存活……",
    # ---- 多行条目：只给文字，行数与空格布局由脚本按原文还原 ----
    "hun07.tmsg": "我们的防线正在崩溃！保住你的核心部队，必要时撤退！",
    "hun10.tmsg": "情报显示，强大的红军装甲师正逼近穆列什河南岸。",
    "hun11.tmsg": "强大的苏军机械化师正从南面逼近！守住你的初始阵地！\n\n\n"
                  "等到第503重装甲营抵达后再发动反攻。",
}


def main():
    apply = "--apply" in sys.argv
    rows = []
    for f in sorted(x for x in os.listdir(SD) if x.lower().endswith(".tmsg")):
        d = open(os.path.join(SD, f), "rb").read()
        head, body, tail = tmsg.split_msg(d)
        if not body:
            continue                       # 纯空行文件，无需译
        src = (head + body + tail).decode("cp1252")
        if f not in DST_MID:
            print("  !! 有正文但无译文: %s :: %r" % (f, body[:60]))
            continue
        mid = DST_MID[f]
        # 前后白空逐字节继承
        lead = src[:len(src) - len(src.lstrip())]
        trail = src[len(src.rstrip()):]
        dst = lead + mid + trail
        if src.count("\n") != dst.count("\n"):
            raise SystemExit("%s 换行数不符：原文 %d / 译文 %d"
                             % (f, src.count("\n"), dst.count("\n")))
        if "\t" in mid or "\r" in mid:
            raise SystemExit("%s 译文含 TAB/CR" % f)
        rows.append((f, src, dst))
        print("  %-14s %4dB -> %4dB  中文 %3d 汉字  白空前 %d / 后 %d"
              % (f, len(src.encode("cp1252")), len(dst.encode("gbk")),
                 sum(1 for c in mid if "\u4e00" <= c <= "\u9fff"), len(lead), len(trail)))
    print("有正文 %d 条，全部配对" % len(rows))

    if not apply:
        print("干跑（未写 %s）" % OUT)
        return
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        # 换行写成**转义字面** `\r\n` / `\n`（否则 TSV 被多行内容切碎）
        fh.write("file\tsrc\tdst\n")
        for f, s, d in rows:
            fh.write("%s\t%s\t%s\n" % (f, esc(s), esc(d)))
    raw = open(OUT, "rb").read()
    print("已写 %s（%d B；BOM=%s；行数 %d）"
          % (OUT, len(raw), raw[:3] == b"\xef\xbb\xbf", raw.count(b"\n")))


if __name__ == "__main__":
    main()
