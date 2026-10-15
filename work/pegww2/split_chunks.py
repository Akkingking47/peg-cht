#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 场景层：把待填批次切成**小片**（每片 ≤ N 行），供**串行**子代理逐片翻译。

背景（踩坑 W13）：一次并发 3 个重负载子代理把宿主压垮，三批全部零产出阵亡。
⇒ 纠正：**串行 + 小片 + 增量落盘**。本脚本只切片，不改内容。

产出：`_scn-todo-<bucket>-NN.tsv`（每片自带表头，行序保持）
用法: python split_chunks.py [每片行数，默认 600]
"""
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
BUCKETS = ("m", "u", "prose")


def main():
    size = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    tot = 0
    for b in BUCKETS:
        p = os.path.join(RES, f"_scn-todo-{b}.tsv")
        if not os.path.isfile(p):
            print(f"  {b}: 缺 {os.path.basename(p)}")
            continue
        lines = open(p, encoding="utf-8").read().split("\n")
        # ⚠️ 片头是 **2 行注释 + 1 行表头**；曾误写成 lines[:2]/lines[2:]，
        #    导致表头被当成数据 ⇒ **只有第 1 片带表头**，第 2 片起全部缺表头（核验器因此读到 0 行）
        head = [l for l in lines[:3]]
        data = [l for l in lines[3:] if l.strip()]
        # 清理旧片
        for f in os.listdir(RES):
            if f.startswith(f"_scn-todo-{b}-") and f.endswith(".tsv"):
                os.remove(os.path.join(RES, f))
        n = 0
        for i in range(0, len(data), size):
            n += 1
            chunk = data[i:i + size]
            out = os.path.join(RES, f"_scn-todo-{b}-{n:02d}.tsv")
            with open(out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(head + chunk) + "\n")
        tot += n
        print(f"  {b:6s} 数据 {len(data):>5d} 行 ⇒ 切 {n:>2d} 片（每片 ≤{size}）")
    print(f"  合计 {tot} 片；每片对应一个串行子代理任务")


if __name__ == "__main__":
    main()
