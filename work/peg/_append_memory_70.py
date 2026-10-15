# -*- coding: utf-8 -*-
"""向 MEMORY.md 追加第 70 条（M 组：地图面/地图绘制界 1920 -> 4096）。"""
import io, sys

MEM = "D:/DSH/军事游戏汉化/.workbuddy/memory/MEMORY.md"

ITEM = """70. ⭐ **M 组：地图面/地图绘制界 1920 → 4096（2026-10-15，根因定位；默认开打）**。治「进场景后地图不显示 / 移动两下就全黑 / 再动几下又有几率正常」。
    * **根因（反汇编确证）**：`0x41FF8A` 是每帧「地图上屏」——`src.left = x = [ebp+8]`、`src.top = y = [ebp+0xC]`、`src.right = x + ([0x498D40] - [0x4AF300]) + 1`、`src.bottom = y + ([0x498D44] - [0x498D3C]) + 1`，随后 `BltFast(dst=[0x676904] 后备缓冲, dstX=[0x4AF300], dstY=[0x498D3C], src=[0x655574] 地图面, &rect, 0x10)`；失败**只记日志**（`0x42000B` push `0x491308` / push `0x420` / call `0x437420`），不回退。源窗口 = 滚动坐标 + 视口宽高，而地图面只有 1920x1920（母本给 800x600 视口留了 1120 余量）；我们把视口补成 **1920x1031 后余量归零**（x>0 或 y>889 立刻越界）⇒ 这一笔整笔失败 ⇒ 地图区域保留黑/旧内容。
    * 同理，31 处绘制界的 `cmp …, 0x780` 会把世界坐标 >1920 的地块/直写剔除 ⇒ 右侧成片锯齿状空洞。
    * **地图面描述符**：面 A `[0x655574]` 在 `0x441BE5-0x441C22`（dwSize=0x7C、dwFlags=7、dwHeight 立即数 `0x441BFD`、dwWidth 立即数 `0x441C04`、caps 0x840 = OFFSCREENPLAIN|SYSTEMMEM），`CreateSurface([0x6761E0])`；面 B `[0x622A10]` 同构，立即数 `0x441C90`（高）/`0x441C97`（宽），`push 0x622A10` 在 `0x441C9E`。
    * **31 处 0x780 清单**（扫描器 `work/peg/_find_map_sites.py`；`work/peg/_plan_vs_780.py` 核对：与 236 条计划的立即数地址**零交集** ⇒ 全是母本原有，不是我们补出来的）：`0x41F3FA`；`0x424AD3`/`0x424ADA`/`0x424B31`/`0x424B38`/`0x424BA6`/`0x424BB1`/`0x424BE9`/`0x424BF4`；`0x43D733`/`0x43D747`/`0x43DB03`/`0x43DB72`/`0x43DB83`(imul 行距)/`0x43DEC7`/`0x43DF37`/`0x43DF48`/`0x43E2F0`/`0x43E360`/`0x43E371`/`0x43E6B5`/`0x43E725`/`0x43E736`；`0x441BFD`/`0x441C04`/`0x441C90`/`0x441C97`；`0x455BB6`/`0x455BBD`/`0x455BE1`/`0x455BE8`。全部字节 80 07 00 00 → 00 10 00 00（1920 → 4096），让面与所有界/行距自洽，滚动余量恢复 2176。
    * **落地**：`work/peg/peg_launcher.py` 新增 `MAP_SITES`（31 条 (va, note)）+ `build_plan(..., mapmargin=True)` 第 11 组 + CLI `--no-map`；`--selftest` 输出 **267 条**已写入并回读一致（236 + 31）。试玩链 `diag_ddraw.py --play --mode borderless` → `diag_run.launch_patched` → `build_plan(tooltip=False, extra=True, panel=True, dxdy=False)`，**默认就带上 M 组**，不需要新入口。
    * **B 组语义澄清（推翻旧猜测）**：`patch_fullrepaint.py` 在 `0x4489D8` nop 掉的是 `je`，语义是**改成每帧都走整屏刷新**——原始逻辑 `if(word[0x498D74]!=0 && byte[0x4AF360]==0){ call 0x44AC45 整屏刷新(顶栏 0x44C50A + 底栏 0x44C57B + 控件循环 0x423CD6); word[0x498D74]=0 } else { call 0x423CD6 控件增量 }`（标志置 1 于 `0x425CA8`）；所以「B 组导致黑」不成立。
    * **DDrawCompat 旁证**：`D:/Program Files/PeG/DDrawCompat-PeG030.log`（borderless + LogLevel=info 那次，190 行、12:50:42→12:53:09）只有配置与钩子记录、**无任何 Blt 失败行**；确认 `FullscreenMode=borderless`、`GdiInterops=all`、`MousePollingRate=native`、`MouseSensitivity=native` 都生效，`Using resource format: D3DDDIFMT_R5G6B5, plain, sysmem`（R5G6B5 离屏面被支持）。
    * **纪律**：`diag_ddraw.py --restore` 必须在下一轮测试前跑（本次实测后 ddraw.dll 停在 DDrawCompat v0.7.1 = 3,612,672 字节、ini 还在，已手工还原成 Svens 159,232 字节 / md5 337866f0c870384f5a16c8a11c46a963）。
    * **待验证**：请用户重开同一入口看地图滚动是否还黑；若仍黑，把 play ini 的 `LogLevel` 改成 `trace`，统计失败的 `BltFast` 调用（含源矩形）即可定案。
"""

s = io.open(MEM, "r", encoding="utf-8").read()
if "70. ⭐ **M 组" in s:
    print("已存在第 70 条，跳过"); sys.exit(0)
if not s.endswith("\n"):
    s += "\n"
with io.open(MEM, "a", encoding="utf-8") as f:
    f.write(ITEM)
print("OK 行数 =", len(io.open(MEM, "r", encoding="utf-8").read().splitlines()))
