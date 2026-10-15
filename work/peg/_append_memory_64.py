# -*- coding: utf-8 -*-
"""向 MEMORY.md 追加第 64 条（I 组：0x4A96E8 布局表右对齐记录）。"""
import io, sys

MEM = r"D:\DSH\军事游戏汉化\.workbuddy\memory\MEMORY.md"

ITEM = """64. ⭐ **I 组：0x4A96E8「面板布局表」右对齐记录 +1120（2026-10-14，静态可打已确证）**。为修「更多选项」这类弹出面板仍留在旧位置，逆向产出 `work\\peg\\out\\report-panel-table.md` + 机器可读清单 `work\\peg\\out\\panel_table_manifest.tsv`（272 行，列：idx/VA/x1/y1/x2/y2/w/h/+8/+a/+c/role/dx）。
    * **表结构**：`0x4A96E8` 起，**stride 15 字节、0x110=272 条**记录；每条 `x1@VA`、`y1@VA+2`、`x2@VA+4`、`y2@VA+6`（word）。
    * **静态可打的确证**：全 exe 对该表基址只有 **1 处写**——`0x45E4AE mov word[ecx+0x4A96E8],dx`（函数 `0x45E334`），其 idx 只可能取 **264/265/266**（`0x45E487`/`0x45E49D`/`0x45E495` 三条 `mov word[ebp-0x30],0x10x`），偏移 +2/+4/+6 的绝对引用也全在同一写入块 ⇒ **idx 0..263 的几何字段运行期绝不被写**。另：运行期 x 偏移 `[0x4AF320]` 只有 {0,7,8}（19 写 7 读），不影响锚定。
    * **只打 37 条**：`role=RIGHT(+1120)` 且宽 ≤ 500（右边缘小元素：菜单/标签/提示框，含 idx97 `(345,23)-(778,585)`），它们必须和已补的工具栏按钮一起 +1120 才对齐；宽 > 500 的跨屏长条（idx2/7/9/112/203）不动；`MID(+560)` 93 条与 `PANEL(+560)` 3 条**不动**（它们与面板内部按钮成组，只移背景会把按钮从面板上拆下来）。清单文件 `work\\peg\\out\\panel_table_v1.tsv`（生成脚本 `work\\peg\\_gen_panel_table.py`）。
    * **站点总数 236 条**（96 尺寸 + 10 代码侧 + 4 A + 1 B + 30 D + 3 F + 14 G + 4 H + 74 I）；`--selftest` 输出「✅ 内存补丁完成：236 条已写入并回读一致」。开关：`--no-panel` / `--no-extra` / `--no-tooltip`。
    * **若还要精确定位**：报告给了断点方案 `0x47053F`／`0x4709B0`（函数 `0x4704D2`/`0x47097A` 内 `add eax,0x4A96E8` 之后，抓 EAX 与 `[ebp+8]`，`idx=(EAX-0x4A96E8)/0xF`；`0x470545` 可直接读实画矩形），一次运行即可定案；因为 `0x4704D2` 有 233 个调用点、idx 多为运行时变量，静态无法唯一确定「更多选项」属于哪几条。
"""

s = io.open(MEM, "r", encoding="utf-8").read()
if "64. ⭐ **I 组" in s:
    print("已存在第 64 条，跳过"); sys.exit(0)
if not s.endswith("\n"):
    s += "\n"
with io.open(MEM, "a", encoding="utf-8") as f:
    f.write(ITEM)
print("OK 行数 =", len(io.open(MEM, "r", encoding="utf-8").read().splitlines()))
