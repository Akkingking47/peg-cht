# 53 PeG 高分辨率支持：现状抢救、同类方案调研与路线思路

> **本轮定位**：只做「盘点 ＋ 调研 ＋ 理线」，**未改动任何游戏文件、未新建/修改任何脚本**（用户要求「先理清思路，不要直接开始做」）。
> 本文是**决策前的路线图**；第七节的四个问题拍板后才动手。
> 承接：`docs\41-分支工作区经验吸收清单.md` §二 P2 #21 / §六 P2 #10；`docs\42-游戏安装目录(PeG-1)可吸收项与保护清单.md` §二-C #10。

---

## 一、本轮要回答的三件事

1. 上一轮（`军事游戏汉化-1` 分支）的分辨率实验线**到底做到哪一步、还剩什么**；
2. **同类游戏/GitHub 社区**是怎么解「1997–1998 年 SSI DirectDraw 老游戏 ＋ 现代高分辨率屏」的；
3. PeG 该走哪条路，**先做哪个最小验证**。

---

## 二、遗产盘点（最关键：知识已丢失，但可逆）

| 项 | 内容 | 现状 |
|---|---|---|
| 分支工作区 | `D:\DSH\军事游戏汉化-1` | ⛔ **已不存在**（`Test-Path` 全 False，`D:\DSH` 下已无该目录） |
| 分辨率实验脚本 | `patch_resolution.py`（21 KB，v4）· `probe_res5.py … probe_res32.py` · `verify_resolution_patch.py` | ⛔ **全盘（`D:\DSH`，Depth 8）搜不到** |
| 日志/常量清单 | `out\res_constants.txt` · `out\probe_res{5..8}.txt`（153 KB）· `out\shot-v3*.png` | ⛔ 同上，已随副本消失 |
| backup 快照 | `D:\DSH\军事游戏汉化\backup\` | ⛔ 60+ 目录全是汉化/词库/OpenGen 相关，**没有该线快照** |
| ⭐ 幸存产物 | `D:\Program Files\PeG-1\PeG030res.exe`（734720 B，2026-10-13 01:12:02） | ✅ **v4 版 1024×768 产物** |
| 母本 | `D:\Program Files\PeG\PeG030.exe` | ✅ 734720 B，MD5 `C462E897B3AA1C384870C857CE9E01DF` |

### ⭐ 好消息：改动点是**可逆**的

实测确认：`D:\Program Files\PeG\PeG030.exe` 与 `D:\Program Files\PeG-1\PeG030.exe` **逐字节相同**（`diffbytes=0`）。

⇒ **`PeG030.exe` ↔ `PeG-1\PeG030res.exe` 的逐字节 diff，就是 v1–v4 全部改动点的完整清单。**
`patch_resolution.py` 的 `SITES` / `DATA_SITES` / `CONST_SITES` / `COLUMN_RECS` / `BOTTOM_RECS` 可以**从这份 diff 反推重建**，不必依赖已消失的脚本；已知映射规则（`800→w`、`799→w-1`、`600→h`、`599→h-1`、`572→h-28`）足以给每个改动点标出语义。

### ⛔ 教训（要写进纪律）

该实验线在 `-1` 的 `MEMORY.md` 与 `PeG汉化经验总结.md`（停在 10-12 23:40）里**一行都没有**——
知识只存在于脚本 docstring 与日志里，**副本一删即不可复现**。
⇒ 重要实验线必须**当场落档**（状态进 `MEMORY.md`、机制进 `MECHANICS.md`、经验进 `peg\方法\`），不能只活在脚本注释里。

---

## 三、上一轮做到哪、卡在哪

### v1 → v4 的演进（从 `patch_resolution.py` docstring 提取，见 `docs\41` §二 #21）

- **v1** 窗口尺寸 / 显示模式 / 主表面 / 矩形裁剪（`.text` 立即数）
- **v2** `.data` 界面矩形记录（6 个全屏根窗口 ＋ 13 个地图视口）
- **v3** 代码直读的布局常量（`.rdata`：地图视口 `{22,799,571}`、屏幕边框 `796/570`）
- **v4** 右侧工具列整体右移（82 条贴着右边界的 `.data` 记录，`.text` 内无 `760/799` 立即数）＋ 底部状态条拉伸

纪律全套沿用：**绝不改母本**（只读 `PeG030.exe`，产物为副本 `PeG030res.exe`）· 幂等 · 内容断言不过即整体拒改 · 先写内存→回读校验→才落盘 · 复核中文补丁仍在（`CHARSET 0x4718E3`＝`6a 86`、`MBCODE 0x4ABC8C`＝936、`LCID 0x7BE86`＝`b8 04 08 00 00`）。

### 已经对的部分（v3 截图 `shot-v3.png`）

⚠️ **时间对照**：截图 01:01:51 **早于** `PeG030res.exe` 01:12:02 ⇒ 该截图只代表 **v3**，**v4 没有任何视觉证据**。

✅ 顶栏横跨全宽 · ✅ 底部状态条跨新宽度（三段）· ✅ 地图主体仍正确渲染 · ✅ 中文显示正常。
（v3 阶段右侧图标列仍在旧 800 宽画布的右缘，尚未右移——与 v3 的实现范围一致。）

### 卡住的地方（同一张截图）

右侧新区域（约 x 870–1035 / y 450–780）出现**品红-绿横向色条 ＋ 1–2 px 黑白竖条 ＋ 成片未绘制的黑块**——
典型的「表面内存未正确初始化／按错误 stride 读写」特征。

### 上一轮最后的假设与遗留

- 三条最后探针（`probe_res30/31/32`，01:12–01:13）的目标都是同一个假设：
  **像素缓冲 stride/pitch 未随表面宽度同步**（16bpp：800 宽 = **1600 B/行**，1024 宽 = **2048 B/行**）。
  - `probe_res30`：猎 pitch 硬编码（`imul 0x320`/`0x258`，候选 1600/1200/3200/2400/1596/1604/640/2048/4096）
  - `probe_res31`：反汇编 pitch 候选上下文（`0x4145F0`/`0x4146A0`/`0x410D80`）
  - `probe_res32`：盯关键对象看谁创建/谁填尺寸（画布 `0x655538`、尺寸缓存 `0x655560/64/68/6c`、地图表面 `0x655574`、后台缓冲 `0x676904`、`IDirectDraw 0x6761e0`、1600 B 缓冲 `0x69d020`、视口 `0x4af2f8/2fc/300`）
- **没有任何收口结论**；该线在 2026-10-13 01:13 停止（是 `-1` 分支的最后一次动作）。
- **v4 未验收**：右列是否真的右移、花屏是否仍在，全都未知。

### 已掌握的 PeG 引擎事实（本项目档案）

| 事实 | 出处 |
|---|---|
| DirectDraw **16bpp High Color**；主程序实际使用 **800×600** | `docs\38` 第 52 行 |
| 兼容层 `ddraw.dll` = **Svens Wrapper**（DirectDraw→OpenGL，Win7+ 全屏），随附 `FullScreenModeWin7\`（2012 版） | `docs\38` 第 53 行 |
| ⭐ **全部游戏内文字走 GDI**：`0x4718ac mov ecx,[0x676904]` → `0x4718bb call [eax+0x44]`（`IDirectDrawSurface::GetDC`）→ `CreateFontA` → `DrawTextExA` → `0x471918 call [eax+0x68]`（`ReleaseDC`） | `docs\38` 第 65–79 行 |
| ⭐ **全 exe 只有 1 处 `CreateFontA`**（FO `0x70CFA` → VA `0x4718FA`），`lfHeight = -12`（12 px 字高）、`pszFaceName = NULL`（系统默认字体） | `docs\38` 第 62–74 行 |
| 中文化已可用（MBCS＋日期 LCID＋5 文本文件＋825 `.txt`＋14 `.ply`＋UI/装备名） | `MEMORY.md` |

---

## 四、同类是怎么解的（四条路线 ＋ 出处）

### 路线① 外部放大（零引擎风险）

| 工具 | 能力 | 与 PeG 的关系 |
|---|---|---|
| **cnc-ddraw**（FunkyFr3sh，MIT） | 把 `ddraw.dll` 丢进游戏目录；borderless/windowed、**upscaling via shaders**、FPS 限制、VSync、鼠标灵敏度补偿、Alt+Enter | ⭐ 支持列表**含 Pacific General**（SSI 同门 1997）⇒ 同族引擎命中率高。**限制**：游戏须用 **DirectDraw (Software)** 渲染器、**不支持 D3D 游戏**、须先设为全屏。PeG 是纯 2D DirectDraw 16bpp、无 D3D ⇒ 适配面干净 |
| **DDrawCompat**（narzoul） | 只修 DirectX 1–7 的兼容性与性能 | ⛔ **明确「no API conversion」⇒ 没有放大/改分辨率能力**，**不作为放大方案**；且不能与其它 wrapper/overlay 叠加。仅当「兼容性出问题」时当备胎 |
| **dgVoodoo2**（dege-diosg） | Glide/DirectX 在 D3D11/12 上重实现，支持**强制分辨率**与缩放 | Windows 上最接近「gamescope」的东西 |
| **DxWnd** | 强制桌面分辨率／窗口化／API 挂钩 | 社区「Forced desktop resolution」常用 |
| **Magpie**（Blinue/Magpie 及 cewer、xwmp3 分支） | **窗口级**放大到全屏（整数/最近邻、Anime4K 等） | Windows 上 gamescope 的等价物；对**任何**窗口游戏适用，不碰游戏文件 |

- 出处：[cnc-ddraw README](https://cdn.jsdelivr.net/gh/FunkyFr3sh/cnc-ddraw@master/README.md) · [DDrawCompat README](https://cdn.jsdelivr.net/gh/narzoul/DDrawCompat@master/README.md) · [dege-diosg/dgVoodoo2](https://github.com/dege-diosg/dgVoodoo2) · [cewer/Magpie](https://github.com/cewer/Magpie) · [xwmp3/Magpie](https://github.com/xwmp3/Magpie) · [DxWnd 讨论串](https://sourceforge.net/p/dxwnd/discussion/general/thread/4ea8556dcd/?page=1#1)
- ⚠️ 本机现实：PeG 目录里**已经有** `ddraw.dll`（Svens Wrapper，实测 VersionInfo：`FileVersion 1.3.13.3` / `FileDescription D3D-Wrapper` / `InternalName d3d2ogl`；字符串含 `DirectX5/6/7-Wrapper`、`OPENGL32.DLL`、`glScalef`）⇒ **换/叠加 wrapper 前必须先备份**（本项目纪律：备份与覆盖分两条命令）。
- ⚠️ 本机网络：PowerShell 直连外网被阻断（`Invoke-WebRequest` 报「基础连接已经关闭」）⇒ **下载 wrapper 必须由用户手动或用 web 工具**，脚本里不要写自动下载。

### 路线② 拉高引擎内部画布（我们 v1–v4 走的路）

**同类唯一的公开路线图**：[wicanr2/pg-cht](https://github.com/wicanr2/pg-cht) 的 `pacgen/docs/09-a1-hires-canvas-roadmap.md`（本工作区已有克隆 `_ref\pg-cht`）。

- 静态可靠事实：**`IDirectDraw::SetDisplayMode` 是唯一控制点**（vtable offset **0x54**）。PacGen 在 file `0x40cdfa`(height)/`0x40cdff`(width)：`push 8`（bpp）／`push 0x1e0`(480)／`push 0x280`(640)／`call [eax+0x54]`。
- ⭐ **可照抄的判据**：静态扫 .text 做计数——`SetDisplayMode` 调用数、back buffer size（640×480＝307200）、`shl reg,7`(＝×640) 次数、`push 640` 次数、全 exe dword 640/480 次数，用来判断「常数是否可枚举」。
  PacGen 结论：**个位到数十处 ⇒ 有限工程**。我们 PeG 的 v1–v4 得到同量级（47 条 `.text` 立即数 ＋ 6 根窗口记录 ＋ 13 地图视口 ＋ 82 右侧列 ＋ 1 底栏 ＋ 4 `.rdata`）——**两条独立证据互相印证「这条路是有限工程，不是无底洞」**。
- ⚠️ **该文件的状态声明要一起读**：它把先前「present stretch 已用动态 trace 确认、4-word patch 让画面放大」的结论**全部撤回**，理由是「在 tool 输出不稳、截图无法可靠判读的 session 产生，未能在干净环境定案」。
  ⇒ **这正是我们该吸取的教训**：我们的 v3 结论来自**单张截图**，v4 更是**零截图**。涉及「跑起来看画面」的结论必须在可靠环境**当场做、当场验**。

**方法论框架**：`_ref\pg-cht\skills\retro-directdraw-hires-cjk\SKILL.md`（亦被 [SkillsMP 收录](https://skillsmp.com/creators/wicanr2/pg-cht/skills-retro-directdraw-hires-cjk)）：

- Step1 静态定位 `SetDisplayMode`（vtable `0x54`）——**这一步纯静态，可靠**。
- present 走 **Blt**（vtable `0x14`，指纹 `push 0x1000000`＝`DDBLT_WAIT`，字节 `68 00 00 00 01`）还是 **Lock+copy**，**必须动态判**（`WINEDEBUG=+ddraw` 里 grep `SetDisplayMode`/`CreateSurface`/`surface1_Blt` 看 surface 尺寸与 src/dst rect）。别靠静态猜 vtable offset。
- ⚠️ **两个陷阱**：① present 的 **dst/src RECT 可能共用**（改错就变成同尺寸复制）；② **present 常是多层的**（render buffer → 中间 surface → primary），**改错层只会修好 stride mismatch、不会放大** ⇒ 必须对照 `CreateSurface` 的 `DDSCAPS_PRIMARYSURFACE` 确认改的 dst 就是 primary。
- Lock+copy 路线的正解：用 **Lock 返回的 `lPitch`** 当 dst stride，而不是硬编旧宽度。
- VA↔file offset 换算：`file = VA − 0x401000 + 0x400`。
- 三路线对比：**A** 标准（back buffer 拉高、底图 nearest ×2、font 24×24；工程最大）／**B** font 半尺寸（画 12×12 再放大；排版会挤）／**C** 不动画布只拉字高（工程量最小）。

⭐ **PeG 与 PacGen/PG2 的根本差异（决定不该照抄它的路线选择）**：
PacGen/PG2 拉高画布的**动机是「8×8 点阵字物理上塞不下可读中文」**（`pacgen/docs/08-tfont-re.md`、`pg2/中文化經驗-方法論.md`）。
而 **PeG 的文字走 GDI**（见 §三 表），**中文早就清晰**（截图可证）。
⇒ 对 PeG，「拉高画布」的价值只有 **「一屏看到更多地图／更大的 UI」**，**不是「让中文能看」**。
**这个目标差异必须先确认**，否则会照抄一条动机不存在的路线、白做大量工程。

### 路线③ 不动画布、只放大字（route C）

- 同类实证：PacGen **已实机成功**（`pacgen/docs/11-2byte-engine.md`：把 `TFONT1.DAT` header `0x08` 的字高由 8 改 16、glyph 补到 16 列，**EXE 一行不动**）；PG2 也选 route C（`pg2/中文化經驗-方法論.md`）。
- 对 PeG：**不适用也无需**。PeG 文字走 GDI，要放大字只需改**唯一那处 `CreateFontA` 的 `lfHeight`**（`docs\38`：VA `0x4718D2` 处 `mov dword [ebp-0x3c], -12`），**不动画布、不动布局、不动 present**。route C 的「2-byte hook ＋ atlas 烘字」对 PeG 是**多做的**。
- 可借鉴的**零成本增量**是它的 Windows 外围经验：
  - PacGen 的 Windows 处方（`pacgen/docs/02-modern-windows.md` 第 44–51 行）：兼容模式 **XP SP3** ＋「缩小显示比例：**256 色**」＋「**停用全螢幕最佳化**」；若画面挤成小窗/定位跑掉，**取消 256 色缩放、改试「640×480 萤幕解析度」**。
  - `skills\wing-portable-sfx\SKILL.md` 第 62–65 行：PE 旗标 **`256COLOR` ＋ `GDIDPISCALING DPIUNAWARE`**——缺 DPI 旗标时，高 DPI 桌面会对游戏 **GDI 文字做 DPI 虚拟化放大 → 笔画糊成粗体**；标记 DPI-unaware 可走干净 bitmap 路径保留细笔画。
  - ⭐ **PeG 正好是「GDI 文字 ＋ 固定像素」**（`docs\38`）⇒ 这两个旗标值得试（改 PE 可选头，不动代码、不动布局）。

### 路线④ 换引擎（社区实际的答案）

社区对「老 SSI 游戏 ＋ 现代屏幕」的主流答案**不是 patch 原 exe，而是重制引擎**（Open General/OpenGen、PG Forever、LGeneral…）。

⭐ **本项目已经把这条路当主线**：`README.md` 第 17 行——**OpenPG（主线）＝ Open General / OpenGen 26.3.30.0，SDL2＋SDL2_ttf，`D:\OpenPG2`，全库 21 efile、收官 11**。现代引擎原生支持高分辨率，且项目已在做它的汉化。
⇒ 对「**在 4K 屏上舒服地玩 PeG**」这个用户价值，**可能根本不需要动 `PeG030.exe`**。

### 论坛线索（登录墙，仅记线索，未取到内容）

Open General 论坛上与 PeG ＋ 分辨率最贴近的三串（**需注册才能读**）：

- 「Problem z odpalaniem People's General w wysokich rozdzielczościach」（PeG 在高分辨率下启动的问题）— <https://forum.open-general.com/viewtopic.php?p=18566>
- 「Installation of mods to PEG」— <https://forum.open-general.com/viewtopic.php?f=94&p=18590>
- 「New user - screen resolution question」— <https://forum.open-general.com/viewtopic.php?f=6&p=9355&t=569>

若用户有账号或愿意注册，这三串是**最贴近的一手社区讨论**。（本次 web_fetch 均被重定向到登录页，零内容。）

---

## 五、路线对照表（决策用）

| 路线 | 拿到什么 | 拿不到什么 | 工程/风险 | 动母本？ |
|---|---|---|---|---|
| ① 外部放大 | 同一画面**更大更清**（整数/最近邻） | **不增加地图可视范围** | 零引擎风险；换 `ddraw.dll` 可回滚（先备份）；要试哪个 wrapper 对 PeG 有效 | ❌ 不动 |
| ② 拉高画布 | **真正更多地图／更大 UI**（原生渲染） | — | 工程最大：常数 → 表面尺寸 → present → stride → 布局 → UI 逐层；已有 v1–v4 基础，但 **v3 花屏未解、v4 未验** | ❌ 产物是副本 |
| ③ 只放大字 | 字更大（PeG 中文本来就清楚） | 不解决屏幕占比 | 极小（改 1 处 `lfHeight`；＋PE 旗标） | ❌ 不动母本 |
| ④ 换引擎 | 现代分辨率 ＋ 现代 UI（OpenGen） | **不是「PeG 原版」体验** | 零 RE（若 OpenGen 能吃 PeG 内容） | ❌ 不动 |

⭐ **一句话**：①③ 解「**看得清**」，② 解「**看得多**」，④ 解「**不用再跟 1998 年的 exe 较劲**」。

---

## 六、建议的下一步（按成本排序，均不动游戏文件）

| 步 | 内容 | 成本 | 依赖 |
|---|---|---|---|
| **S0** | **先验证「外部放大」够不够**：用 **Magpie**（或另备份后换 **cnc-ddraw**）跑一次 PeG，看观感是否满足。若满足，**本轮需求即结束**，不必碰 exe | 几分钟，零风险 | **用户实机**（纪律：代理严禁自行启动/点击游戏） |
| **S1** | **抢救**：`PeG030.exe` ↔ `PeG-1\PeG030res.exe` **逐字节 diff** → 重建全部改动点清单 → 按已知映射规则反推语义 → **重建 v4 等价的 `patch_resolution.py`（干跑模式）放进本工作区** | 半小时，纯静态只读 | 无 |
| **S2** | **定位 v3 花屏根因**：静态扫 stride/pitch 候选（`imul 0x320`、1600/2048、`shl ×640` 等）＋ 动态确认 present 层与 stride（Windows 侧可用 DDrawCompat 日志/`ddraw.dll` 行为，而非 wine 的 `+ddraw`） | 半天，需 `capstone`（**当前环境缺：`pip install capstone`**） | S1 |
| **S3** | **v4 实机验收**：跑 `PeG030res.exe`（1024×768）截图，看右列是否真右移、花屏是否仍在——目前 v4 **零视觉证据** | 几分钟 | 用户实机 |
| **S4** | 可选：给 `PeG030.exe` 加 `DPI unaware` / 停用全螢幕最佳化旗标，消除高 DPI 桌面对 GDI 文字的虚拟化模糊 | 小 | 无 |

---

## 七、待用户拍板（四个问题）

1. 目标到底是「**同一画面更大更清**」还是「**一屏看更多地图**」？
   （决定走 ① 还是 ②；**若只是前者，S0 就可能收工**，② 的大量工程可以不做。）
2. 能否接受用「**换引擎**」（OpenGen 已是本仓主线且已汉化）来满足高分屏体验？还是**坚持 PeG 原版 exe**？
3. 是否授权先做 **S1（diff 重建 patch 脚本）＋ S2（静态扫 stride）**？两者都**只读/只新增脚本，不改任何游戏文件**。
4. 实机验证（S0/S3）由谁做？本项目纪律：**需要截图时停下告知用户，代理严禁自行启动/点击游戏**。

---

## 八、本轮纪律声明

- 本轮**未修改任何游戏文件、未新建或修改任何脚本**；只做只读盘点 ＋ 只读静态/网络调研。
- 唯一新增的临时产物：`.workbuddy\tmp\ctx-b5-raw.md` / `ctx-b6-raw.md`（上下文压缩恢复用的转储，可随时删）；`work\_res_tmp\`（空目录，pwsh 直连外网被阻断，未取得任何文件）。
- 全部结论标出处；**未实测的一律标 `[推定]`**（本文中「v3 花屏＝stride 不同步」即属 **`[推定]`**，尚未证实）。
