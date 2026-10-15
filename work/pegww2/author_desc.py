#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B 方案样板：为「说明文件是数据文件」的场景**补写标准格式说明**。

⚠️ 安全要点：那些 `<stem>.TXT` 本身是**游戏数据文件**（据点名 / 部队番号代码）⇒ **绝不能覆盖**。
   做法：**新建** `<stem>_d.TXT`，再把 `.SCN@11329` 指过去；原数据文件一字不动。
标准格式（照 MOD 既有体例 `Race.TXT`）：标题 / 日期 / 描述 / N 名玩家 / M 回合
经用户批准采用 B 方案；本脚本产出**汉化补写**内容，需在工作区留痕（_desc-authored.tsv）。
"""
import os
import shutil

G = r"D:\Program Files\PeG-WW2\SCENARIO"
WS = r"D:\DSH\军事游戏汉化"
LOG = os.path.join(WS, "pegww2", "research", "_desc-authored.tsv")

# 样板：ptt / ptt-R（追击至托布鲁克）。标题取 MOD 自己文件第 0 行；
# 日期与玩家/回合数取自**同一场战斗的兄弟场景** `Race.TXT`（托布鲁克 / 1941年4月8日 / 2 名玩家 / 12 回合）。
DESC = {
    "ptt": {
        "file": "PTT_d.TXT",
        "body": [
            "追击至托布鲁克",
            "1941 年 4 月",
            "轴心国军队沿海岸追击英军，试图一举夺取托布鲁克要塞。",
            "2 名玩家",
            "12 回合",
        ],
    },
}
SCNS = ("ptt.scn", "ptt-R.SCN")


def main():
    made = []
    for stem, d in DESC.items():
        p = os.path.join(G, d["file"])
        data = ("\r\n".join(d["body"]) + "\r\n").encode("gbk")
        with open(p, "wb") as f:
            f.write(data)
        back = open(p, "rb").read()
        ok = back == data
        print(f"  新建 {d['file']} ({len(data)} B) 回读 {'✅' if ok else '❌'}")
        made.append((stem, d["file"], len(data)))
        # 指向新文件（原数据文件不动）
        for sfn in SCNS:
            sp = os.path.join(G, sfn)
            if not os.path.isfile(sp):
                continue
            b = bytearray(open(sp, "rb").read())
            cur = bytes(b[11329:11349]).split(b"\x00")[0].decode("latin-1")
            bak = sp + ".orig-backup"
            if not os.path.isfile(bak):
                shutil.copy2(sp, bak)
            nb = bytearray(b)
            nb[11329:11349] = d["file"][:-4].encode("latin-1")[:20].ljust(20, b"\x00")
            open(sp, "wb").write(nb)
            chk = bytes(open(sp, "rb").read()[11329:11349]).split(b"\x00")[0].decode("latin-1")
            print(f"  {sfn}: @11329 {cur!r} → {chk!r} {'✅' if chk == d['file'][:-4] else '❌'}")
    if not os.path.isfile(LOG):
        open(LOG, "w", encoding="utf-8", newline="\n").write(
            "# 汉化补写清单（B 方案）：这些说明文件是**我们补写的**，非 MOD 原作内容\n场景\t文件\t字节\t来源说明\n")
    with open(LOG, "a", encoding="utf-8", newline="\n") as f:
        for stem, fn, n in made:
            f.write(f"{stem}\tSCENARIO\\{fn}\t{n}\t标题取 MOD 数据文件行0；日期/玩家/回合取自兄弟场景 Race.TXT\n")
    print(f"  已记账 → {os.path.relpath(LOG, WS)}")


if __name__ == "__main__":
    main()
