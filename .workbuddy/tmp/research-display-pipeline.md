# PeG030.exe 画面显示机制完整测绘（只读逆向）

- 母本：`D:\Program Files\PeG\PeG030.exe`（md5 `c462e897b3aa1c384870c857ce9e01df`，**本次未做任何修改**，游戏**未启动**）
- 高分辨率产物：`D:\DSH\军事游戏汉化\work\peg\out\PeG030-1920x1080.exe`（md5 `44ac5cfe5a5875aa5ef51efd3d1afcf4`，只读比对）
- 工具：`work\peg\` 下的 `disasm_range.py` / `vtcalls.py` / `find_mem.py` / `find_bytes.py` / `xref_call.py` / `imp_list.py` / `peek_va.py`
- 证据规则：所有结论给出 VA + 关键指令原文；无法从字节确定的写「**未证实**」。

---

## 0. 结论速览

1. 显示模块由**两个 IDirectDraw 对象**驱动：`[0x6768FC]`（base IDirectDraw）与 `[0x6761E0]`（QueryInterface 拿到的较新接口）。任务书里说的「第二个 IDirectDraw `[0x4AF26C]`」**不是** IDirectDraw，而是一个 **DirctDrawSurface**（证据见 §1.1）。
2. 主链是 **Flip 双缓冲链**：`[0x61F900]` = 带 1 个后备缓冲的主表面，`[0x676904]` = 它的**后备缓冲**（实际绘制目标，通过 GetAttachedSurface 取得）。全 exe **只有 1 个 Flip 调用点**（`0x41FE4C`）。
3. 一帧上屏 = `PresentFrame(0x41FE12)` → 先 `0x44C66E`（帧合成 / 屏幕局部存档回填）→ 再 `Flip(NULL, DDFLIP_WAIT)`。失败时按 HRESULT 触发整表 Restore 或重试。
4. **全 exe 没有任何 SetClipper 调用**（`vtcalls.py 0x70` 零命中），裁剪完全靠自绘 struct + DDBLT_KEYSRC。
5. 显示路径里写死 800/600 的位置**不止两组**：除了任务书给的两组（`0x441796/0x44179B`、`0x441A79/0x441A7E`），还有**第三组**在帧合成器里（`0x44C55E` 起 `68 58 02 00 00 68 20 03 00 00`），以及 6 处合成器裁剪常数。**1920×1080 产物把这三组 + 6 处裁剪常数都改对了，但 draw-target 的 799/599 边界（`0x4421DA`/`0x4421E4`/`0x44221F`/`0x442229`）没有跟着改**（§6）。

---

## 1. 显示对象与全局

### 1.1 三个「类 IDirectDraw」对象

| 全局 | 真实类型 | 证据 |
|---|---|---|
| `[0x6768FC]` | **IDirectDraw（base）** | `0x441A02 call [edx+0x50]` = SetCooperativeLevel(this=`[0x6768FC]`, hwnd=`[0x676134]`, 0x11)；`0x441A47 call [ecx]` = QueryInterface(this=`[0x6768FC]`)；`0x44168D mov dword ptr [0x6768FC], 0`（释放时置 0） |
| `[0x6761E0]` | **IDirectDraw2/4**（QI 得到） | `0x441A2F push 0x6761E0`（ppv）/ `0x441A35 push 0x48C040`（riid，.rdata）/ `0x441A40 push [0x6768FC]` / `0x441A47 call [ecx]`；之后 SetDisplayMode 与全部 9 次 CreateSurface 都用它 |
| `[0x6A8DE0]` | **IDirectDraw**（DDraw 辅助模块自己的） | `0x47D5F3 mov edx,[eax]`（eax=`[0x6A8DE0]`）/ `0x47D600 call [edx+0x18]` = CreateSurface；由 `0x47D8A0` 第 3 个参数写入 |

补充：DDraw 导出函数在 `0x47E690` 是个 thunk：`0x47E690 jmp dword ptr [0x6AA3CC]`（IAT 0x006AA3CC = **DirectDrawCreate**，ddraw.dll 唯一直接导入项）。**整个 exe 只有 1 个 DirectDrawCreate 调用点**：`0x4419BC call 0x0047E690`（`xref_call.py` 全量重建缓存后确认）。

### 1.2 `[0x4AF26C]` 是 surface，不是 IDirectDraw

vtableslot 重叠是陷阱：`+0x18` 在 IDirectDraw 上是 CreateSurface、在 IDirectDrawSurface 上是 BltBatch；`+0x50` 分别是 SetCooperativeLevel / GetPalette；`+0x58` 分别是 WaitForVerticalBlank / GetSurfaceDesc。对 `[0x4AF26C]` 的调用**全部**落在只有 surface 才有的槽位上：

| VA | 槽位 | 方法 |
|---|---|---|
| `0x41BCC2` | +0x18 | BltBatch（surface） |
| `0x41BD4E` / `0x41BFE3` | +0x60 | **IsLost**（IDirectDraw 无此槽） |
| `0x41C026` | +0x64 | **Lock**（IDirectDraw 无此槽） |
| `0x41C14C` | +0x74 | **SetColorKey**（IDirectDraw 无此槽） |
| `0x41BDC2` | +0x30 | GetAttachedSurface |
| `0x41BE84` | +0x50 | GetPalette（**不是** SetCooperativeLevel） |
| `0x41BEDC` / `0x41BF28` | +0x58 | GetSurfaceDesc |

结论：`[0x4AF26C]` 是一个 **IDirectDrawSurface**，由 `0x41BB00–0x41C200` 那个模块（自带 CreateSurface / IsLost / Lock / Unlock / SetColorKey 包装）管理，模块用 `[0x4AF268]` 作为「已就绪」标志（`0x41BC95 cmp dword ptr [0x4AF268], 0`）。**它的创建点未证实**（`find_mem.py 0x4AF26C` 只找到读点 `0x41BB54 / 0x41BB83 / 0x41BBB1 / 0x41BBD3 / 0x41BBFA / 0x41BCB4 / 0x41BD3F / 0x41BD73`，没有直接写点；`0x41BB83 push 0x4AF26C` 紧接 `push 0x48C100 / push 1 / push 0`，形态像另一个 QueryInterface 调用，故可能由 QI 写入）。

### 1.3 Surface 全局总表（创建点 + DDSURFACEDESC2 字段 + 色键 + 角色）

所有 CreateSurface 都建在 `[0x6761E0]` 上，都用 `DDSURFACEDESC2`（`dwSize = 0x7C`，`0x441ACE mov dword ptr [ebp-0x7C], 0x7C`；每次创建前 `call 0x47F190` = memset(desc, 0, 0x7C)）。字段偏移用 `ebp-0x7C` 为 desc 基址换算：`ebp-0x78`=+0x04 dwFlags，`ebp-0x74`=+0x08 dwHeight，`ebp-0x70`=+0x0C dwWidth，`ebp-0x68`=+0x14 dwBackBufferCount，`ebp-0x14`=+0x68 ddsCaps.dwCaps。

| # | 创建点 | out 全局 | dwFlags | dwWidth | dwHeight | ddsCaps.dwCaps | 其他字段 | 角色 |
|---|---|---|---|---|---|---|---|---|
| 1 | `0x441B03` | **`[0x61F900]`** | `0x21` (DDSD_CAPS\|DDSD_BACKBUFFERCOUNT) | 未设(0) | 未设(0) | `0x218` (PRIMARYSURFACE\|FLIP\|COMPLEX) | `dwBackBufferCount=1`（`0x441AE3 mov [ebp-0x68],1`） | **主表面**，可 Flip |
| 2 | `0x441B53` GetAttachedSurface(+0x30) on `[0x61F900]` | **`[0x676904]`** | — | 800 | 600 | `0x4` (DDSCAPS_BACKBUFFER，`0x441B2F mov [ebp-0xC4],4`) | — | **后备缓冲 / 实际绘制目标** |
| 3 | `0x441C22` | `[0x655574]` | `7` (CAPS\|HEIGHT\|WIDTH) | `0x780`=1920 | `0x780`=1920 | `0x840` (SYSTEMMEMORY\|OFFSCREENPLAIN) | — | 大画布 #1（系统内存） |
| 4 | `0x441CB4` | `[0x622A10]` | `7` | 1920 | 1920 | `0x840` | — | 大画布 #2 |
| 5 | `0x441D44` | `[0x686528]` | `7` | `0x5A`=90 | `0x46`=70 | `0x40` (OFFSCREENPLAIN) | — | **屏幕局部存档缓冲**（实际用 80×60 区域：`0x44C6EF [0x4A2730]=0x50`） |
| 6 | `0x441DA6` | `[0x6633FC]` | `7` | 90 | 70 | `0x40` | **SetColorKey** `0x441E07` flags=`8`(DDCKEY_SRCBLT) key=`word [0x6769B0]` | UI/sprite 面（带色键） |
| 7 | `0x441E3F` | `[0x61F3E0]` | `7` | `0x12C`=300 | `0x3C`=60 | `0x40` | — | 300×60 存档 #1 |
| 8 | `0x441EA1` | `[0x62CE10]` | `7` | 300 | 60 | `0x40` | **SetColorKey** `0x441F02` | 300×60 面（带色键） |
| 9 | `0x441F3A` | `[0x681D0C]` | `7` | `0x1A4`=420 | `0xC8`=200 | `0x40` | **SetColorKey** `0x441F9B` | 420×200 面（带色键） |
| 10 | `0x441FD3` | `[0x675538]` | `7` | `0x320`=800 | `0x258`=600 | `0x40` | **SetColorKey** `0x442034` | **全屏离屏画布**（带色键），是画中画/对话框的第二绘制目标 |

色键值 `[0x6769B0]` 的来源（`0x441B7F–0x441BCC`）：
```
0x441B7F  mov dword ptr [ebp-0xF0], 0x20            ; DDPIXELFORMAT.dwSize = 32
0x441B89  lea ecx, [ebp-0xF0]
0x441B8F  push ecx
0x441B90  push [0x61F900] ... 0x441B9E call [ecx+0x54]   ; GetPixelFormat(0x61F900, &pf)
0x441BA1  cmp dword ptr [ebp-0xDC], 0x3E0           ; pf.dwRGBBitCount（=0x3E0 表示 ARGB1555 路线）
0x441BA1.. => 0x441BAD mov dword ptr [0x62666C], 1
0x441BB7  mov word ptr [0x6769B0], 0x7C1F           ; RGB565 品红
             否则
0x441BC2  mov dword ptr [0x62666C], 0
0x441BCC  mov word ptr [0x6769B0], 0xF81F           ; ARGB1555 品红（默认路径）
```
即「源色键 = 品红，按主表面像素格式在 `0x7C1F` / `0xF81F` 之间二选一」。注意 `0x441B9E` 的 `+0x54` 是**取主表面像素格式**，**不是** 任务书里说的 SetDisplayMode（真正的 SetDisplayMode 只有 `0x441A91` 一处，见 §2）。

其它 surface 全局（本次新发现 / 交叉引用）：

| 全局 | 依据 | 角色 |
|---|---|---|
| `[0x675548]` | `0x447F88` 与 `0x4422F7 mov edx,[0x675548]` 都把它当 surface 用 | 未证实其创建点；被当作 90×70 档存档面（`0x65A9A0` draw-target 的 surf，right=0x59=89 bottom=0x45=69） |
| `[0x6756A8]` | `0x447F88 call [eax+0x30]` GetAttachedSurface on `[0x6756A8]` | 另一个带 attached surface 的面（未证实创建点） |
| `[0x640BC0]` | `0x43AB15 / 0x43AB53 / 0x43AD1E / 0x43AF25 / 0x4425FF` 五处 `call [reg+0x18]` CreateSurface on `[0x640BC0]` | 第三套 IDirectDraw，用于 0x43Axxx 模块 | 
| `[0x663410]` | 本次普查**未命中任何引用** | **未证实**（任务书列出但未找到使用点） |

### 1.4 「绘制目标」struct（20 字节）

`0x44219F` 是独立函数，负责批量初始化这类结构：

```
struct DrawTarget {          // 0x14 = 20 字节
  DWORD left, top, right, bottom;   // +0x00 / +0x04 / +0x08 / +0x0C
  LPDIRECTDRAWSURFACE surf;         // +0x10
};
```

| struct 基址 | surf 字段 | surf 值 | right / bottom | 证据 |
|---|---|---|---|---|
| `0x676980` | `0x676990` | `[0x676904]` | `0x31F`(799) / `0x257`(599) | `0x4421B6`/`0x4421BB`；`0x4421D4`/`0x4421DE` |
| `0x676960` | `0x676970` | `[0x675538]` | `0x31F` / `0x257` | `0x4421F9`/`0x4421FF`；`0x442219`/`0x442223` |
| `0x655560` | `0x655570` | `[0x676904]` | `word [0x4AF300]` / `[0x498D3C]` / `[0x498D40]` / `[0x498D44]` | `0x44223E`/`0x442244`；`0x442251`–`0x442277` |
| `0x676120` | `0x676130` | `[0x655574]` | `desc.lPitch-1`(`[ebp-0x6C]`) / `dwHeight-1`(`[ebp-0x74]`)，来自 GetSurfaceDesc(`0x442295` on `[0x655574]`) | `0x4422AF`；`0x4422C9`/`0x4422D4` |
| `0x65A9A0` | `0x65A9B0` | `[0x675548]` | `0x59`(89) / `0x45`(69) | `0x4422F1`/`0x4422F7`；`0x442311`/`0x44231B` |
| `0x6633A0` | `0x6633B0` | `[0x62CE10]` | （后续取） | `0x442336`/`0x44233B` |
| `0x675720` | — | — | 20 字节整体 memset 成 `0xFF`（`0x442037 push 0x14; 0x442039 push -1; 0x44203B push 0x675720; 0x442040 call 0x47F190`） | 未证实用途（疑为「无效目标」哨兵） |

另有帧合成用的两个全局 RECT：
- `0x663380` = 屏幕空间 RECT `{left, top, right, bottom}`（合成器写入）
- `0x4A2728` = 存档缓冲内部 RECT `{left, top, right, bottom}`（`0x4A2728/0x4A272C/0x4A2730/0x4A2734`）
- `0x6769A0` = `0x61F3E0` 那条路径用的屏幕 RECT；`0x685FF0` = 对应的内部 RECT

---

## 2. 初始化顺序（函数 `0x4416FF` – `0x44219E`）

函数入口 `0x4416FF`（`push ebp` / `0x441700 mov ebp, esp` / `0x441702 sub esp, 0xF4`）。

| 顺序 | VA | 动作 | 关键指令 |
|---|---|---|---|
| 1 | `0x441753` | `LoadCursorA` | `call [0x6AA5C4]`，参数 (0, `0x7F00`) |
| 2 | `0x441785` | `RegisterClassA` | `call [0x6AA5C8]`，`lea eax,[ebp-0xA4]` |
| 3 | `0x4417B7` | **`CreateWindowExA`（800×600 弹窗）** | `call [0x6AA5CC]`；实参 dwExStyle=8(WS_EX_TOPMOST)、class=`[0x498D2C]`、title=`[0x498D28]`、style=`0x80000000`(WS_POPUP)、x=0、y=0、**nWidth=`0x320`(push at `0x44179A`，立即数 `0x44179B`)**、**nHeight=`0x258`(push at `0x441795`，立即数 `0x441796`)**、parent=0、menu=0、hInstance=`[ebp+8]`、lpParam=0。窗口句柄存 **`[0x676134]`**（`0x4417BD mov dword ptr [0x676134], eax`），失败则 `0x4417CB xor al,al` 直接返回 |
| 4 | `0x4417DD` / `0x4417E9` | `ShowWindow` / `UpdateWindow` | `call [0x6AA5F0]` / `call [0x6AA5D0]` |
| 5 | `0x4417EF`–`0x4417F9` | 子系统初始化 | `call 0x439A00`、`call 0x438BF2`、`call 0x44324F` |
| 6 | `0x44180D` | `wsprintfA` | `call [0x6AA58C]` |
| 7 | `0x44182B` | `GetSystemTime` | `call [0x6AA420]`，`lea ecx,[ebp-0xB4]` |
| 8 | **`0x4419BC`** | **`DirectDrawCreate`（全 exe 唯一）** | `call 0x0047E690` → `0x47E690 jmp dword ptr [0x6AA3CC]` |
| 9 | **`0x441A02`** | **`SetCooperativeLevel`** | `0x4419EB push 0x11`；`0x4419F3 push [0x676134]`；`0x4419F9 push [0x6768FC]`；`0x441A02 call [edx+0x50]`。flags `0x11` = `DDSCL_FULLSCREEN \| DDSCL_EXCLUSIVE` |
| 10 | `0x441A47` | **`QueryInterface`** → `[0x6761E0]` | `0x441A2F push 0x6761E0`；`0x441A34 push 0x48C040`（riid）；`0x441A3F push [0x6768FC]`；`0x441A47 call [ecx]` |
| 11 | **`0x441A91`** | **`SetDisplayMode(800, 600, 16, 0, 0)`** | `0x441A72 push 0`；`0x441A74 push 0`；`0x441A76 push 0x10`；`0x441A78 push 0x258`（立即数 `0x441A79`）；`0x441A7D push 0x320`（立即数 `0x441A7E`）；`0x441A88 push [0x6761E0]`；`0x441A91 call [eax+0x54]` |
| 12 | `0x441ACE` 起 | 清 desc + 循环 CreateSurface | `memset(desc,0,0x7C)` → 填字段 → `call [reg+0x18]`；失败走 `0x4416B7`（错误上报）并 `jmp 0x44219B` 返回 |
| 13 | `0x441B03`/`0x441B39` | primary + back buffer | 见 §1.3 |
| 14 | 其余 8 次 | `0x441C22 / 0x441CB4 / 0x441D44 / 0x441DA6 / 0x441E3F / 0x441EA1 / 0x441F3A / 0x441FD3` | 见 §1.3 |
| 15 | `0x441E07`/`0x441F02`/`0x441F9B`/`0x442034` | 4 次 **SetColorKey** | `push &key(=[ebp-0xD0])`；`push 8`；`push [surface]`；`call [reg+0x74]` |
| 16 | `0x442037` | `memset(0x675720, 0xFF, 0x14)` | — |
| 17 | `0x442048` | `call 0x453D10`（返回 0 则报错 0x63 并退出） | — |
| 18 | `0x442111` | `memset(0x626880, 0, 0x6590)` | — |
| 19 | **`0x44212E`** | 清屏 | `0x442125 push 0`；`0x442127 mov edx,[0x676904]`；`0x44212E call 0x47DFA0`（= `Blt(NULL,NULL,NULL,DDBLT_COLORFILL\|DDBLT_WAIT,&fx)`，把 `[0x676904]` 填色） |
| 20 | `0x442136`–`0x44214C` | `call 0x440350(2,0)`、`call 0x460578`、`call 0x4147D0`、`call 0x4430E4` | — |
| 21 | `0x442151`–`0x442196` | `[0x640868]=0xFF`；`call 0x447F95(0x4C90F0)`；分支设 `[0x62CE34]`、`[0x498D78]` | 成功 `0x442199 mov al,1` |
| 22 | `0x44219F`（独立函数） | 建 §1.4 的 DrawTarget 结构 | 见 §1.4；**谁调用该函数未证实** |

**没有任何 SetClipper / CreateClipper / SetPalette 调用**（`vtcalls.py 0x70` 全表 0 命中）。DirectDrawCreate 的 out 指针是否直接写入 `[0x6768FC]`**未证实**（`0x4418C0–0x4419D0` 反汇编起点不是指令边界，未取到该段原文；`find_mem.py 0x6768FC` 在 .text 里只找到 `0x44168D` 的置 0 写点）。

---

## 3. 一帧怎么上屏

### 3.1 `PresentFrame`（入口 ≈ `0x41FE12`）

```
0x41FE15  sub      esp, 8
0x41FE18  mov      byte ptr [ebp - 8], 1            ; 重试标志
0x41FE1C  call     0x44C66E                         ; ← 帧合成 / 存档回填
0x41FE21  mov      eax, dword ptr [0x4AF394]
0x41FE26  add      eax, 1
0x41FE29  mov      dword ptr [0x4AF394], eax        ; 帧计数
0x41FE2E  movsx    ecx, byte ptr [ebp - 8]
0x41FE32  test     ecx, ecx
0x41FE34  je       0x41FEDE
0x41FE3A  push     1                               ; DDFLIP_WAIT
0x41FE3C  push     0                               ; lpDDSurfaceTargetOverride = NULL
0x41FE44  push     [0x61F900]
0x41FE4C  call     dword ptr [ecx + 0x2C]          ; ★ 全 exe 唯一的 Flip
```

成功（`eax == 0`）之后：
```
0x41FE58  movsx    edx, word ptr [0x4AF32C]
0x41FE5F  mov      eax, 1
0x41FE64  sub      eax, edx
0x41FE66  mov      word ptr [0x4AF32C], ax         ; 双缓冲索引翻转
0x41FE6C  push     1
0x41FE6E  call     0x423473                        ; 依据当前前台/后台面切换绘制目标
```

失败分支（`0x41FE78` 起，错误码在 `[ebp-4]`）：
- `0x41FE78` 打印 `0x491208`（level `0x3C8`，经 `0x437420`）
- `0x41FE8E cmp dword ptr [ebp-4], 0x887601C2`（**DDERR_SURFACELOST**）→ `0x41FEA4 call 0x456070`（**RestoreAllSurfaces**，见 §4），返回非 0 再打印 `0x491258`
- `0x41FEC1 cmp dword ptr [ebp-4], 0x8876021C`（**DDERR_WASSTILLDRAWING**）→ `0x41FED9 jmp 0x41FE2E` **重试 Flip**
- 其它错误 → `0x41FECA` 打印 `0x491290` 后放弃

### 3.2 帧合成器 `0x44C66E`

```
0x44C674  movsx    eax, byte ptr [0x4AF2E4]      ; 显示子系统就绪
0x44C67D  jne/…    若为 0 → 0x44C984 直接返回
0x44C684  movsx    ecx, byte ptr [0x4AF4AC]      ; “屏幕局部已存档” 标志
0x44C68D  jne      0x44C7BE                       ; 已存档 → 走恢复分支
```
未存档时（先把后备缓冲的一块 80×60 抓走）：
```
0x44C693  movsx edx, word [0x4AF2E8]
0x44C69A  movsx eax, word [0x4AF4B0]
0x44C6A1  sub   edx, eax
0x44C6A3  mov   [0x663380], edx                   ; destRect.left  = [0x4AF2E8]-[0x4AF4B0]
0x44C6B9  mov   [0x663384], ecx                   ; destRect.top   = [0x4AF2EC]-[0x4AF4B4]
0x44C6C7  mov   [0x663388], eax                   ; destRect.right = left + 0x50 (80)
0x44C6D5  mov   [0x66338C], ecx                   ; destRect.bottom= top  + 0x3C (60)
0x44C6DB  mov   [0x4A2728], 0
0x44C6E5  mov   [0x4A272C], 0
0x44C6EF  mov   [0x4A2730], 0x50                  ; srcRect = {0,0,80,...}
```
裁剪（这一段**写死 800/600**）：
```
0x44C70A  jge      0x44C724
0x44C70C  xor      edx, edx
0x44C70E  sub      edx, dword ptr [0x663380]
0x44C714  mov      dword ptr [0x4A2728], edx      ; src.left = -dest.left
0x44C71A  mov      dword ptr [0x663380], 0
0x44C724  cmp      dword ptr [0x663388], 0x320    ; ★ 800
0x44C730  mov      eax, 0x320                     ; ★ 800
0x44C73B  mov      dword ptr [0x4A2730], eax
0x44C740  mov      dword ptr [0x663388], 0x320    ; ★ 800
0x44C74A  cmp      dword ptr [0x663384], 0
0x44C75B  mov      dword ptr [0x4A272C], ecx
0x44C761  mov      dword ptr [0x663384], 0
0x44C76B  cmp      dword ptr [0x66338C], 0x258    ; ★ 600
0x44C777  mov      edx, 0x258                     ; ★ 600
0x44C782  mov      dword ptr [0x4A2734], edx
0x44C788  mov      dword ptr [0x66338C], 0x258    ; ★ 600
```
实际抓屏（**从后缓冲 `[0x676904]` 抓 80×60 到 `[0x686528]`**）：
```
0x44C792  push 0
0x44C794  push 0x1000000                          ; DDBLT_WAIT
0x44C799  push 0x663380                           ; lpSrcRect  (屏幕空间)
0x44C79E  mov  eax, dword ptr [0x676904]
0x44C7A3  push eax                                ; lpDDSrcSurface
0x44C7A4  push 0x4A2728                           ; lpDestRect (存档面内部)
0x44C7A9  mov  ecx, dword ptr [0x686528]
0x44C7AF  push ecx                                ; this = 目标 = 存档面
0x44C7B8  call dword ptr [eax + 0x14]             ; Blt
```
> 参数按 stdcall 从右向左解析：`this=[0x686528]`（目标面）、`lpDestRect=0x4A2728`、`lpDDSrcSurface=[0x676904]`、`lpSrcRect=0x663380`、`dwFlags=0x1000000`。即**目标 = 90×70 存档面，源 = 后备缓冲**。

反向恢复在 `0x44C5F0`（同一模块的另一个函数）：
```
0x44C5F4  movsx  eax, byte ptr [0x4AF2E4]      ; 子系统未就绪 → 0x44C66A 返回
0x44C601  call   0x44CB2C
0x44C606  movsx  ecx, byte ptr [0x4AF4AC]
0x44C60F  je     0x44C66A                       ; 没存过就不恢复
0x44C611  push 0
0x44C613  push 0x1000000                        ; DDBLT_WAIT
0x44C618  push 0x4A2728                         ; lpSrcRect (存档面内部)
0x44C623  push [0x686528]                       ; lpDDSrcSurface
0x44C624  push 0x663380                         ; lpDestRect (屏幕)
0x44C62F  push [0x676904]                       ; this = 目标 = 后备缓冲
0x44C637  call dword ptr [edx + 0x14]           ; Blt 反向
0x44C65B  call   0x4231DF(left, top, right, bottom)   ; 脏矩形通知
0x44C663  mov    byte ptr [0x4AF4AC], 0
```

同类第二条路径（300×60 存档面 `[0x61F3E0]`）在 `0x44C8D7` / `0x44CCD5`：`Blt(this=[0x61F3E0], dest=0x685FF0, src=[0x676904], src=0x6769A0, DDBLT_WAIT)`；`0x44C902` / `0x44C961` 调 `0x41EB70`（带裁剪的贴图/合成，flags `0x1008000` = `DDBLT_WAIT|DDBLT_KEYSRC`）与 `0x4235E5`。
`0x44C5C4` / `0x44C5E2`：`push 0x23A(570); push 0x31C(796); push 2; push 0x675540; push 0x676980; call 0x4235E5`。
`0x4235E5` 内部转调 `0x47E0A0`：
```
0x4235EB push 0
0x4235ED push 0x1008000
0x4235F2 push [ebp+0x18]   ; 0x23A
0x4235F5 push [ebp+0x14]   ; 0x31C
0x4235FA push [ebp+0x10]   ; 2
0x4235FD push [ebp+0x0C]   ; 0x675540
0x423601 push [ebp+0x08]   ; 0x676980
0x423606 call 0x47E0A0
```
并在目标面等于 `[0x676904]` 时更新 `0x69F1A0` 处的表项（`0x423640 imul eax, eax, 0x1C` → **每项 0x1C = 28 字节**，与 `0x47D5C3`–`0x47D6DE` 的同一张表一致）。这张表是**脏矩形 / 遮挡重绘表**。

### 3.3 绘制入口（谁往后备缓冲写）

- `Blt`（`+0x14`）19 处，投递到 `[0x676904]` 的关键点：`0x41ED0E`、`0x41F028`、`0x44C637`（恢复）、`0x44CB6E`、`0x45377A` 相关。
- `BltFast`（`+0x1C`）14 处，目标 `[0x676904]`：`0x41FFFF`、`0x425BBA`、`0x45377A`；目标 `[0x655574]`：`0x41FA5F`、`0x424AFD`、`0x424C56`；目标 `[0x622A10]`：`0x424B5B`；目标 `[0x675538]`：`0x425C0C`。
- 直接像素写入（Lock）三处：`0x4144A9`→`[0x676904]`、`0x41C026`→`[0x4AF26C]`、`0x43D6E1`→`[0x655574]`；辅助模块内 `0x47D826`→`esi`（`0x47D790` 的 Lock）。
- GDI 叠写（`GetDC`，`+0x44`）：`0x470160` 与 `0x4718BB` 都在 `[0x676904]` 上；`0x425837`、`0x471756` 用调用者传入的 surface。对应 `0x470xxx–0x471xxx` 的文字/对话框渲染（未证实细节）。
- `0x414470` = **截图存 BMP**：`Lock([0x676904], &desc{size=0x7C}, …)` at `0x4144A9`，把 `desc.lpSurface`（`[ebp-0x188]`）按 BMP 格式写出（`0x4144F4 mov word [ebp-0x25C], 0x4D42` = 'BM'；`0x414523 mov [ebp-0x244], 0x320` 宽、`0x41452D mov [ebp-0x240], 0x258` 高、`0x414540 mov word [ebp-0x23A], 0x18` = 24bpp；行循环下限 `0x4145F4 mov word [ebp-0x1B8], 0x257` = 599），最后 `0x4147BD call [ecx+0x80]` = **Unlock**。这条路径**硬编码 800/600/24bpp**，与分辨率无关。

---

## 4. Surface 丢失 / 恢复（IsLost / Restore）

**`0x456070` = `RestoreAllSurfaces()`**（`0x456070 push ebp` / `0x456071 mov ebp, esp` / `0x456073 sub esp, 0x10`），按固定顺序对 10 个面调 `Restore`（`+0x6C`）：

| 顺序 | VA | 对象 |
|---|---|---|
| 1 | `0x456084` | `[0x61F900]`（主表面） |
| 2 | `0x4560A6` | `[0x655574]` |
| 3 | `0x4560C8` | `[0x686528]` |
| 4 | `0x4560EA` | `[0x6633FC]` |
| 5 | `0x45610C` | `[0x622A10]` |
| 6 | `0x45612E` | `[0x686528]`（重复一次） |
| 7 | `0x456150` | `[0x62CE10]` |
| 8 | `0x456172` | `[0x61F3E0]` |
| 9 | `0x456194` | `[0x681D0C]` |
| 10 | `0x4561B6` | `[0x675538]` |

任一 Restore 返回非 0 立刻 `0x4561C2 mov eax, dword ptr [ebp-0xC]` → `0x4562B9` **直接返回该 HRESULT**（不继续恢复后续面、也不重建内容）。恢复成功后 `0x4561CA` 起把 `[0x498D38]/[0x498D34]/[0x498D3A]/[0x498D36]/[0x498D70]` 一片全局置 `0xFFFF`，然后 `0x45620F call 0x41F0D6` 触发一次全屏重绘。

调用者（`xref_call.py 0x456070`）：`0x41ED29`、`0x41EFA4`、`0x41F046`（三处都是写 `[0x676904]` 的 Blt 包装，写失败即恢复）、`0x41FEA4`（`PresentFrame` 收到 `DDERR_SURFACELOST`）、`0x423585`。

关键结论：
- **`[0x676904]`（后备缓冲）不在恢复表里** —— 它是 `[0x61F900]` Flip 链的一部分，随主表面的 `Restore` 一起由 DirectDraw 自动恢复。这与「全任务书把 `0x676904` 当主 surface」的预设不同。
- **`IsLost`（`+0x60`）全 exe 只有 2 处，且都作用在 `[0x4AF26C]`**：`0x41BD4E`、`0x41BFE3`。主链**不做「先探 IsLost 再画」**，只在 Flip 返回 `0x887601C2` 时才批量 Restore。
- `Unlock`（`+0x80`）7 处：`0x4147BD`（`[0x676904]`，截图）、`0x43EA85`、`0x47D861`、`0x47DC48`、`0x47DC73`、`0x47DF55`、`0x47DF83`。

辅助模块的失败处理：`0x47D790` 里 `Lock` 失败（`0x47D82B jne 0x47D86B`）→ 返回 0；`Unlock` 失败（`0x47D869 test edi,edi; jne 0x47D878`）→ 也走失败路径返回 0。`0x47D600` 的 CreateSurface 失败（`0x47D605 jne 0x47D6F0`）→ 函数返回 0，整批建面中止。

---

## 5. 显示路径里写死的 800 / 600 位置（VA + 现值）

| VA（指令） | 立即数位置 | 母本值 | 含义 |
|---|---|---|---|
| `0x441795` | `0x441796` | `0x258` = 600 | `CreateWindowExA` nHeight |
| `0x44179A` | `0x44179B` | `0x320` = 800 | `CreateWindowExA` nWidth |
| `0x441A78` | `0x441A79` | `0x258` = 600 | `SetDisplayMode` dwHeight |
| `0x441A7D` | `0x441A7E` | `0x320` = 800 | `SetDisplayMode` dwWidth |
| **`0x44C55E`** | `0x44C55F` | `0x258` = 600 | **第三组**：`0x44C55E` 起 `68 58 02 00 00 68 20 03 00 00 68 3C 02 00 00 6A 00 e8`（`push 600; push 800; push 0x23C=572; push 0; call`） |
| **`0x44C563`** | `0x44C564` | `0x320` = 800 | 同上组的 800 |
| `0x44C724` | `0x44C72A` | `0x320` = 800 | 合成器 `cmp [0x663388], 800` |
| `0x44C730` | `0x44C731` | `0x320` = 800 | 合成器 `mov eax, 0x320` |
| `0x44C740` | `0x44C746` | `0x320` = 800 | 合成器 `mov [0x663388], 0x320` |
| `0x44C76B` | `0x44C771` | `0x258` = 600 | 合成器 `cmp [0x66338C], 600` |
| `0x44C777` | `0x44C778` | `0x258` = 600 | 合成器 `mov edx, 0x258` |
| `0x44C788` | `0x44C78E` | `0x258` = 600 | 合成器 `mov [0x66338C], 0x258` |
| `0x4421D4` | `0x4421DA` | `0x31F` = 799 | DrawTarget `0x676980`.right（`[0x676904]`） |
| `0x4421DE` | `0x4421E4` | `0x257` = 599 | DrawTarget `0x676980`.bottom |
| `0x442219` | `0x44221F` | `0x31F` = 799 | DrawTarget `0x676960`.right（`[0x675538]`） |
| `0x442223` | `0x442229` | `0x257` = 599 | DrawTarget `0x676960`.bottom |
| `0x414523` | — | `0x320` = 800 | 截图 BMP 宽（`mov [ebp-0x244], 0x320`） |
| `0x41452D` | — | `0x258` = 600 | 截图 BMP 高 |
| `0x4145F4` | — | `0x257` = 599 | 截图行循环上限 |
| `0x41EBF0` / `0x41EBF8` | — | `0x320` | 贴图裁剪 helper `0x41EB70` |
| `0x423219` | — | `0x320` | 脏矩形通知 `0x4231DF` |

`find_bytes.py "68 58 02 00 00 68 20 03 00 00" .text` 全 .text 只有 **3** 个命中：`0x441795`、`0x441A78`、`0x44C55E` —— 即「push 600; push 800」这种成对形态只有三处，第三处（`0x44C55E`）在帧合成器里，**不在任务书给的两组补丁点之内**。

---

## 6. 分辨率补丁点位核对（母本 vs 1920×1080 产物）

逐字节比对结果（`MASTER` = `D:\Program Files\PeG\PeG030.exe`，`PROD` = `work\peg\out\PeG030-1920x1080.exe`）：

| 立即数 VA | 母本 | 产物 | 结果 |
|---|---|---|---|
| `0x441796` | `58 02 00 00` (600) | `38 04 00 00` (1080) | ✅ 已改 |
| `0x44179B` | `20 03 00 00` (800) | `80 07 00 00` (1920) | ✅ 已改 |
| `0x441A79` | `58 02 00 00` (600) | `38 04 00 00` (1080) | ✅ 已改 |
| `0x441A7E` | `20 03 00 00` (800) | `80 07 00 00` (1920) | ✅ 已改 |
| `0x44C55F` | `58 02 00 00` (600) | `38 04 00 00` (1080) | ✅ 已改 |
| `0x44C564` | `20 03 00 00` (800) | `80 07 00 00` (1920) | ✅ 已改 |
| `0x44C72A` | 800 | 1920 | ✅ 已改 |
| `0x44C731` | 800 | 1920 | ✅ 已改 |
| `0x44C746` | 800 | 1920 | ✅ 已改 |
| `0x44C771` | 600 | 1080 | ✅ 已改 |
| `0x44C778` | 600 | 1080 | ✅ 已改 |
| `0x44C78E` | 600 | 1080 | ✅ 已改 |
| **`0x4421DA`** | **799** | **799** | ❌ **未改** |
| **`0x4421E4`** | **599** | **599** | ❌ **未改** |
| **`0x44221F`** | **799** | **799** | ❌ **未改** |
| **`0x442229`** | **599** | **599** | ❌ **未改** |
| `0x414524`/`0x41452E`（截图 BMP 宽高） | 位置未精确命中 | — | **未证实**（疑仍为 800/600，仅影响调试截图） |
| `0x42321A`/`0x41EBF2`/`0x41EBFB` | 位置未精确命中 | — | **未证实**（疑仍为 800） |

**给出的可执行结论**：1920×1080 产物已把三组分辨率立即数与合成器的 6 处裁剪常数改成 1920/1080，但 `0x44219F` 里两个 DrawTarget 的可见区仍是 **799×599**。这两个结构是 `[0x676904]` 与 `[0x675538]` 的「绘制目标 + 裁剪框」，若高分辨率下仍按 799/599 裁剪，则所有走这两个目标的全屏绘制只会覆盖左上 800×600（是否真的有问题取决于这些结构在别处是否被改写 —— **未证实**，本次未追踪 `0x676988`/`0x67698C`/`0x676968`/`0x67696C` 的其他写点）。

---

## 7. 未证实清单（明确标注）

1. `DirectDrawCreate` 的结果是否直接写入 `[0x6768FC]` —— `0x4418C0–0x4419D0` 段未取到合法反汇编起点。
2. `[0x4AF26C]` surface 的创建点（无直接写点；怀疑经 `0x41BB83 push 0x4AF26C / push 0x48C100` 附近的 QueryInterface 写入）。
3. `[0x675548]`、`[0x6756A8]`、`[0x640BC0]`、`[0x686400]` 的创建点与尺寸。
4. `[0x663410]` 在本次普查中**零引用**。
5. `0x675720`（20 字节 memset 0xFF）的用途。
6. `0x676980` / `0x676960` 的 right/bottom 是否有第二处写点（决定 §6 的 799/599 是否会真的限制绘制）。
7. `0x414470`（截图）路径与 `0x470xxx–0x471xxx`（GDI on DDraw）的内部细节。
8. 辅助模块 `0x47D5A0` 里 `0x69F1A0` 表的完整字段语义（已确认条目步长 `0x1C`，字段位于 +0x00/+0x04/+0x08/+0x0C/+0x10/+0x14，+0x1C 为下一条）。
9. `0x44CBE0`–`0x44CD00` 一带（`0x44CB2C`、`0x44CB6E`、`0x44CCD5`）的第三条存档/恢复路径未逐条读完。

---

## 附：vtable 槽位对照（本次判定 [0x4AF26C] 类型所依据）

```
IUnknown            : 0x00 QueryInterface, 0x04 AddRef, 0x08 Release
IDirectDraw         : 0x0C Compact, 0x10 CreateClipper, 0x14 CreatePalette, 0x18 CreateSurface,
                      0x1C DuplicateSurface, 0x20 EnumDisplayModes, 0x24 EnumSurfaces,
                      0x28 FlipToGDISurface, 0x2C GetCaps, 0x30 GetDisplayMode, 0x34 GetFourCCCodes,
                      0x38 GetGDISurface, 0x3C GetMonitorFrequency, 0x40 GetScanLine,
                      0x44 GetVerticalBlankStatus, 0x48 Initialize, 0x4C RestoreDisplayMode,
                      0x50 SetCooperativeLevel, 0x54 SetDisplayMode, 0x58 WaitForVerticalBlank
IDirectDrawSurface  : 0x0C AddAttachedSurface, 0x10 AddOverlayDirtyRect, 0x14 Blt, 0x18 BltBatch,
                      0x1C BltFast, 0x20 DeleteAttachedSurface, 0x24 EnumAttachedSurfaces,
                      0x28 EnumOverlayZOrders, 0x2C Flip, 0x30 GetAttachedSurface, 0x34 GetBltStatus,
                      0x38 GetCaps, 0x3C GetClipper, 0x40 GetColorKey, 0x44 GetDC, 0x48 GetFlipStatus,
                      0x4C GetOverlayPosition, 0x50 GetPalette, 0x54 GetPixelFormat,
                      0x58 GetSurfaceDesc, 0x5C Initialize, 0x60 IsLost, 0x64 Lock, 0x68 ReleaseDC,
                      0x6C Restore, 0x70 SetClipper, 0x74 SetColorKey, 0x78 SetOverlayPosition,
                      0x7C SetPalette, 0x80 Unlock
```

（本报告只读产生；未修改母本 exe、未修改 1920×1080 产物、未启动游戏。）
