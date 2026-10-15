# -*- coding: utf-8 -*-
"""向 MEMORY.md 追加第 66 条（docs\\67 分层策略方案）。"""
import io, sys

MEM = r"D:\DSH\军事游戏汉化\.workbuddy\memory\MEMORY.md"

ITEM = """66. ⭐ **宽屏方案从「逐常量盲测」转为「分层策略 + 运行时几何拦截 + 证据驱动」（2026-10-14，用户 m02941 要求出靠谱方案）**。落档 [`docs\\67-PeG宽屏方案（分层策略与实施路线）.md`](docs/67-PeG宽屏方案（分层策略与实施路线）.md)。
    * **判断依据（务必记住）**：G/H/I 三组补丁实机**零可见变化**，K 组（165 条 dx/dy 整批 +1120）造成左栏文字右移 + 大黑洞，**已回退默认不打**（`--dx` 才开）。⇒ 战略地图接续绘制、子界面居中、「更多选项」面板位置这三类症状的**控制点不在常量上，而在函数行为上**；继续扫常量是死路。
    * **分层**：L1 显示层＝DDrawCompat v0.7.1（`26275ed572a4df16141b26e952b50106`，i386，已收档 `archive\\ddraw\\`）当默认 ddraw.dll，`--ddraw` 启动前换入/退出还原 ⇒ 整类消灭色键/透明/拖影；L2 分辨率常量＝现有 236 条（**冻结，不再加**）；L3 几何策略层＝**拦截函数改实参**（`0x41EB70` 位块、`0x424C73` 视口、`0x4704D2` 布局表读取、`0x44ACDA` 控件绘制、`0x4700C6` 文本矩形、`0x41FF8A` 视口上屏），按元素类别（右栏 +1120／左锚不动／全宽拉右端／居中 960/540／面板容器连子项）制定唯一策略表；L4 输入一致性＝鼠标屏幕→格子换算必须与渲染共用同一套视口全局（`[0x4AF2F8]`/`[0x4AF2FC]`，鼠标缓存 `[0x4AF2E8]`/`[0x4AF2EC]`），修用户 m02926 报的「x>800 点选错位/点不中」；L5 特殊画面归入 L3；L6 每次运行自动留日志、一次只改一类、无证据不算完成。
    * **实现 α（先做）**：`CreateProcessW(DEBUG_ONLY_THIS_PROCESS)` + 目标 VA 写 `0xCC` + `Wow64GetThreadContext`/`SetThreadContext` 读写寄存器与栈 ⇒ 纯 Python、免汇编、免注入、exe 零改动、天然带日志。**β**（性能不够时）：`VirtualAllocEx` 代码洞 detour。
    * **社区对照结论**：宽屏修复 DLL/ASI 的「hook 引擎几何函数」模式最贴合 PeG；MultiCAD 不适用（无独立图形模块）；OpenGen/VCMI 是重实现；DDrawCompat/cnc-ddraw 只管 API 语义；十六进制改常量+启动器只能解决常量类问题。
    * **路线**：P0 拦截器+trace（只记录不改写，自测用 32 位进程）→ P1 带 DDrawCompat 采证据 → P2 分类实施 → P3 输入一致性 → P4 特殊画面与分发。
"""

s = io.open(MEM, "r", encoding="utf-8").read()
if "66. ⭐ **宽屏方案从" in s:
    print("skip"); sys.exit(0)
if not s.endswith("\n"):
    s += "\n"
with io.open(MEM, "a", encoding="utf-8") as f:
    f.write(ITEM)
print("OK lines =", len(io.open(MEM, "r", encoding="utf-8").read().splitlines()))
