#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""部署 `USERSCEN/Third Reich.ply`（场景说明面板）的中文版。

⚠️ 此前**延后未处理**的层（全库仅 2 个 .ply：一个 868 B 有效，一个 2 B 垃圾）。
格式：CRLF 分行，末段用 NUL 填充（引擎按固定长度读）⇒ 译文更短时补 NUL，保持总长不变。
纪律：先备份原文 → 写入 → 回读校验（与本项目其它部署一致）。
"""
import os
import shutil

WS = r"D:\DSH\军事游戏汉化"
G = r"D:\Program Files\PeG-WW2\USERSCEN\Third Reich.ply"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "USERSCEN", "Third Reich.ply")

# 逐行译文（行号对齐原文结构：0 标题 / 2 说明 / 4 依靠 / 6 中立 / 8 技巧）
ZH = {
    0: "第三帝国的兴亡",
    2: "假想战役：1939 年 9 月，德国向波兰、法国、英国、比利时、挪威以及苏联发动全面战争。",
    4: "德国可依靠意大利、芬兰、罗马尼亚、保加利亚与匈牙利。",
    6: "民族主义西班牙保持中立。",
    8: "技巧：登陆舰可将新部队投送到敌方海岸。",
}


def main():
    raw = open(G, "rb").read()
    size = len(raw)
    lines = raw.decode("latin-1").split("\r\n")
    print(f"原文 {size} B · CRLF 分行 {len(lines)} 段")
    out = []
    for i, l in enumerate(lines):
        if i in ZH:
            out.append(ZH[i])
            print(f"  行{i}: {l[:56]!r}\n       → {ZH[i]}")
        else:
            if set(l) <= {"\x00"} and l:      # NUL 填充段：留到最后统一补
                out.append("")
            else:
                out.append(l)
    body = "\r\n".join(out).encode("gbk")
    # 保持总长：不足则补 NUL
    if len(body) < size:
        body = body + b"\x00" * (size - len(body))
    else:
        print(f"  ⚠️ 译文比原文长（{len(body)} > {size}），按实际长度写入")
    if not os.path.isfile(BK):
        os.makedirs(os.path.dirname(BK), exist_ok=True)
        shutil.copy2(G, BK)
        print(f"  已备份原文 → {os.path.relpath(BK, WS)}")
    with open(G, "wb") as f:
        f.write(body)
    chk = open(G, "rb").read()
    ok = len(chk) == max(size, len(body)) and ZH[0] in chk.decode("gbk", "replace")
    print(f"  写入 {len(chk)} B · 回读校验 {'✅ 通过' if ok else '❌ 失败'}")
    t = chk.decode("gbk", "replace")
    for i, l in enumerate(t.split("\r\n")[:10]):
        print(f"    行{i}: {l[:70]!r}")


if __name__ == "__main__":
    main()
