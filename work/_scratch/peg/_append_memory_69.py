# -*- coding: utf-8 -*-
"""追加 MEMORY 第 69 条：DDrawCompat+独占全屏的实机结论（输入通、文字通、无色键问题；地图不画）。"""
import io, re, os

P = r"D:\DSH\军事游戏汉化\.workbuddy\memory\MEMORY.md"
MARK = "DDrawCompat+独占全屏 首次拿到「输入+文字+无色键异常」"

src = io.open(P, encoding="utf-8").read()
if MARK in src:
    print("已有该条目，跳过")
else:
    nums = [int(m.group(1)) for m in re.finditer(r"(?m)^(\d+)\.\s", src)]
    nxt = (max(nums) + 1) if nums else 1
    item = u"""
%d. ⭐ **DDrawCompat+独占全屏 首次拿到「输入+文字+无色键异常」**（2026-10-15，用户 m03523 实测）
- 配置：DDrawCompat 0.7.1 + `FullscreenMode = exclusive(0)` + `MouseSensitivity/MousePollingRate = native` + `GdiInterops = all`，其余同 236 条内存补丁。
- 结果：①**鼠标可以动、可以点**（输入问题由 `borderless` → `exclusive` 解决，证实「borderless 自建窗口盖住游戏窗口」的判断）；②**悬停按钮出说明文字**（GDI 文本在这层是好的）；③**完全没有品红**（色键在这层是真正生效的）；④**地图不显示，且带上一屏残留**；⑤**截图全黑**（独占全屏截不到，borderless 能截）。
- 意义：色键（品红）+ GDI 文字这两类问题**在显示层这层就解决了**，不需要再改 exe；剩下的是「地图层不显示/残留」。
- 下一步：同入口改 `--mode borderless`（画面/截图已知正常）+ 原生鼠标，验证「鼠标死」到底是 borderless 本身还是 DDrawCompat 的鼠标模拟；若 borderless+原生鼠标输入正常 ⇒ DDrawCompat 路线四要素（画面/输入/文字/色键）齐活。
- 工具：`work\\peg\\diag_ddraw.py` 现有 `--play [--mode exclusive|borderless]`、`--restore`、`--selftest`；入口 `D:\\Program Files\\PeG\\进游戏-16比9-DDrawCompat试玩.cmd`。
""" % nxt
    with io.open(P, "a", encoding="utf-8") as f:
        f.write(item)
    print("已追加第 %d 条，文件现 %d 字节" % (nxt, os.path.getsize(P)))
