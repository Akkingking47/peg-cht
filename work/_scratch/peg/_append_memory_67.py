# -*- coding: utf-8 -*-
"""向 .workbuddy/memory/MEMORY.md 追加第 67 条（幂等）。"""
import io, os, sys

MEM = r"D:\DSH\军事游戏汉化\.workbuddy\memory\MEMORY.md"
MARK = "67. ⭐ **运行时取证器 peg_trace.py"
TEXT = """
67. ⭐ **运行时取证器 `peg_trace.py`（停止盲测；P0 落地，2026-10-14）**

* **背景判读**：236 条常量补丁连跑两轮实机，用户两次反馈「没任何变化 / 还是老样子」（m02865、m02892）。结论：**常量猜谜路线停止**，改用运行时取证（`docs\\67` §6）。
* **脚本**：`work\\peg\\peg_trace.py`（约 720 行）。`CreateProcessW(DEBUG_ONLY_THIS_PROCESS)` 直接创建游戏进程当调试器；`CREATE_PROCESS_DEBUG_EVENT` 时读 32 位 PEB 取模块基址；校验母本 md5 `c462e897b3aa1c384870c857ce9e01df`；先用与 `peg_launcher.py` 同一套 `build_plan` 写 236 条尺寸补丁（先全量校验→统一写入→回读一致）；再在探针函数入口写 `0xCC`。
* **探针（`POINTS`）**：`0x41EB70` 位块助手（x,y,src面,RECT*,color,flags）· `0x424C73` 视口设置器（left,top,right,bottom,flag）· `0x43CDCE` 屏幕→地图坐标（战斗图）· `0x44B1D7` 战略图映射 · `0x41C342` 视口右边界 · `0x41FF8A` 视口窗口→后备 · `0x4700C6` 文本排版 · `0x448E94` 选格判定。每次命中记录「函数 / `[esp]` 调用方返回地址 / 栈上参数 / 鼠标·滚动·视口快照」；每断点上限 `POINT_CAP=24` 次，到顶撤断点防拖慢。
* **三个已实测的坑（重要，勿重犯）**：① 64 位调试器看 WOW64(32 位) 进程时 **INT3 命中码是 `0x4000001F`（STATUS_WX86_BREAKPOINT）**，单步是 `0x4000001E`；不认就表现为「断点没命中」，继续执行时 `0xCC` 还在 ⇒ 死循环 + `0xC0000005` @ 断点+2。② **`DEBUG_EVENT` 字段偏移在 64 位调试器下不同**：事件头 12 字节 + 4 字节对齐，联合体从 +0x10 起（EXCEPTION：code@+0x10、addr@+0x20）。③ **Dr 硬件断点在 WOW64 下不可用**：两种上下文写法都「成功」但不触发且弄崩被调试线程（`work\\peg\\_dr_test.py` 证据）⇒ 默认不用 Dr，改 INT3 + 状态快照。
* **自测**：`python peg_trace.py --selftest-debug`（用 SysWOW64 的 32 位测试进程，脚本未启动游戏）→ `① INT3 断点 ✅`、`② Dr 跳过`，连跑 3 次稳定。
* **用户入口**：`work\\peg\\_make_forensics_cmd.py` 生成 `D:\\Program Files\\PeG\\诊断-16比9取证.cmd`（GBK + CRLF + 命令全 ASCII），另建快捷方式 `诊断-16比9取证.lnk`；日志 `work\\peg\\out\\trace-log.txt`，窗口实时滚动命中。
* **教训**：静态推断「某个字面量 → 某个症状」在 269 个站点规模下不可靠；两条证据链（静态清单 + 运行时参数）必须闭合才动补丁。
"""

with io.open(MEM, "r", encoding="utf-8") as f:
    cur = f.read()
if MARK in cur:
    print("已存在第 67 条，跳过")
    sys.exit(0)
with io.open(MEM, "a", encoding="utf-8") as f:
    f.write("\n" + TEXT)
with io.open(MEM, "r", encoding="utf-8") as f:
    n = len(f.read().splitlines())
print("已追加第 67 条；MEMORY.md 现在 %d 行" % n)
