# -*- coding: utf-8 -*-
r"""EFILE_Clu 根级「小文件」中文侧生成器：nations.txt ＋ strings_efile.txt。

口径（与 11 个已交付 efile 对齐，实测既有 TEXT-ZH 反查得到）：
  · `*` 开头的注释行**原样保留**（引擎跳过，不译）
  · 值行逐行对应，**行数与顺序不变**（引擎按行号/索引读）
  · 出稿 **GBK(936) / 无 BOM / 换行沿用原文**（两份原文均 CRLF）
  · `[terrain]` 20 项**按引擎索引**取值（TOWN→城镇、FORD→渡口、ROADS→公路、RAILS→铁路 …）

用法: python make_clu_small_root.py [--apply]      # 默认干跑
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
EFILE = r"D:\OpenPG2\EFILE_Clu"
ZH = os.path.join(EFILE, "TEXT-ZH")

NATIONS = {
    "Axis": "轴心国", "Allied": "盟军", "All Countries": "所有国家",
    "Austria": "奥地利", "Belgium": "比利时", "Bulgaria": "保加利亚",
    "Czechoslovakia": "捷克斯洛伐克", "Denmark": "丹麦", "Finland": "芬兰",
    "France": "法国", "Germany": "德国", "Greece": "希腊", "USA": "美国",
    "Hungary": "匈牙利", "Turkey": "土耳其", "Italy": "意大利",
    "Netherlands": "荷兰", "Norway": "挪威",
    "Poland - LWP": "波兰-波兰人民军", "Portugal": "葡萄牙", "Romania": "罗马尼亚",
    "Spain": "西班牙", "SSSR": "苏联", "Sweden": "瑞典", "Switzerland": "瑞士",
    "United Kingdom": "英国", "Yugoslavia": "南斯拉夫",
    # 西语题材口径（GCE=西班牙内战权威；BASEKORP 作 西班牙国民军/西班牙共和国）
    "Nationalist - Eastern Front": "国民军-东线", "Republican": "共和军",
}

TERRAIN = {
    "CLEAR": "开阔地", "TOWN": "城镇", "AIRFIELD": "机场", "FOREST": "森林",
    "UNDERWOOD/FIELD": "树篱地", "HILL": "丘陵", "MOUNTAIN": "山地",
    "SNOW/SAND": "雪地/沙地", "SWAMP": "沼泽", "OCEAN": "海洋", "FORD": "渡口",
    "FORTIFICATION": "要塞", "PORT": "港口", "STREAM": "溪流",
    "ESCARPMENT": "断崖", "IMPASSABLE RIVER": "不可通行河流", "ROUGH": "崎岖地",
    "CUSTOM": "自定义", "ROADS": "公路", "RAILS": "铁路",
}

JOBS = [("nations.txt", NATIONS), ("strings_efile.txt", TERRAIN)]


def main():
    apply = "--apply" in sys.argv
    for name, table in JOBS:
        src = os.path.join(EFILE, name)
        raw = open(src, "rb").read()
        if raw[:3] == b"\xef\xbb\xbf":
            raise SystemExit("原文含 BOM: %s" % name)
        nl = "\r\n" if raw.count(b"\r\n") else "\n"
        if nl == "\n" and raw.count(b"\r\n"):
            raise SystemExit("混合换行: %s" % name)
        lines = raw.decode("cp1252").split(nl)
        out, hit, miss = [], 0, []
        for l in lines:
            # 注释行（`*` 开头）与**段头**（`[section]`）都是结构，原样保留
            if not l.strip() or l.lstrip().startswith("*") or (
                    l.strip().startswith("[") and l.strip().endswith("]")):
                out.append(l)
                continue
            if l in table:
                out.append(table[l])
                hit += 1
            else:
                out.append(l)
                miss.append(l)
        blob = nl.join(out).encode("gbk")
        print("%-20s 行 %d  命中 %d  未覆盖 %s  %d -> %d B"
              % (name, len(lines), hit, miss if miss else "无", len(raw), len(blob)))
        if miss:
            raise SystemExit("!! 有值行未覆盖，拒绝落盘")
        if blob.decode("gbk").split(nl) != out:
            raise SystemExit("!! 编解码往返不一致: %s" % name)
        if not apply:
            continue
        os.makedirs(ZH, exist_ok=True)
        tgt = os.path.join(ZH, name)
        with open(tgt, "wb") as f:
            f.write(blob)
        back = open(tgt, "rb").read()
        if back != blob or back[:3] == b"\xef\xbb\xbf":
            raise SystemExit("!! 回读不一致: %s" % name)
        print("   已写 %s（GBK / 无 BOM / %s）" % (tgt, "CRLF" if nl == "\r\n" else "LF"))
    if not apply:
        print("(dry-run，加 --apply 落盘)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
