# -*- coding: utf-8 -*-
"""向 MEMORY.md 追加第 65 条（K 组：res_diff_v4.tsv 的 165 条 dx/dy 位置行）。"""
import io, sys

MEM = r"D:\DSH\军事游戏汉化\.workbuddy\memory\MEMORY.md"

ITEM = """65. ⭐ **K 组：res_diff_v4.tsv 里被跳过的 165 条 dx/dy 位置行（2026-10-14；用户「没任何变化」后的转向）**。
    * 事实：`work\\peg\\out\\res_diff_v4.tsv` 共 259 行 = 96 尺寸行 + **163 dx + 2 dy**。`patch_res_wh.py`（默认 `--keep-dx`）与最初的 `peg_launcher.py` 都跳过了这 165 行。
    * 这 165 行**全在 .data**（`0x490000` 段 70、`0x4A0000` 段 95），`old` 集中在 **750–790**（`762`×73、`787`×71＝工具栏按钮 x/right 的**副本表**），另 2 条底部值 576/594。
    * 推论：D 组把 `0x4A22F8` 记录表的真按钮搬到了 1882/1907，但副本表仍是 762/787 ⇒ 读副本定位的代码（弹出面板/菜单/提示框）仍画老位置，与用户「打开更多选项后面板回到原位置」一致。
    * 映射：`dx` ⇒ `old+(w-800)`（1920 ⇒ +1120）、`dy` ⇒ `old+(h-600)`（+480）。`peg_launcher.py` 的 `add()` 自带去重＋冲突检查：与尺寸表/D 组重叠且目标一致 ⇒ 自动合并（实测一致，无冲突；这是一次额外的交叉校验）。
    * **站点总数 372 条**（96 尺寸 + 165 dx/dy 中的 136 条新站点 + 10 代码侧 + 4 A + 1 B + 2 D + 3 F + 14 G + 4 H + 74 I），`--selftest` 通过：『✅ 内存补丁完成：372 条已写入并回读一致（exe 文件未改动）』。回滚开关 `--keep-dx`。
    * 背景取证：用户 19:15 实机跑 162 条版、19:33 实机跑 236 条版（`work\\peg\\out\\launcher-log.txt` 两次都记『✅ … 已写入并回读一致』『▶ 已放行』），但反馈『对比之前，没任何变化，之前有的问题全部还在』⇒ 说明 G/I 两组定位的那些站点**并不是**这三个症状的实际控制点；日志同时证明启动器与补丁机制本身有效（A/B/D 组效果肉眼可见：16:9、按钮到 1882）。
    * 下一步（若 K 组仍无变化）：做 `--trace` 探针（`DEBUG_ONLY_THIS_PROCESS` + `Wow64GetThreadContext`，在 `0x41EB70`/`0x424C73`/`0x4704D2`/`0x44C66E` 下 INT3，把实参写进启动器自己的日志），一次运行拿到「实际画的矩形/记录号」，不再静态猜。
"""

s = io.open(MEM, "r", encoding="utf-8").read()
if "65. ⭐ **K 组" in s:
    print("skip"); sys.exit(0)
if not s.endswith("\n"):
    s += "\n"
with io.open(MEM, "a", encoding="utf-8") as f:
    f.write(ITEM)
print("OK lines =", len(io.open(MEM, "r", encoding="utf-8").read().splitlines()))
