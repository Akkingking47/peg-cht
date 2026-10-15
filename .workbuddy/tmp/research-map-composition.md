# PeG030.exe 地图画面生成机制（只读逆向）

- 母本：`D:\Program Files\PeG\PeG030.exe` md5 `c462e897b3aa1c384870c857ce9e01df`（未改，全部反汇编均读自此文件）
- 产物：`D:\DSH\军事游戏汉化\work\peg\out\PeG030-1920x1080.exe` md5 `44ac5cfe5a5875aa5ef51efd3d1afcf4`
- 工具：`work\peg\{disasm_range.py,vtcalls.py,find_mem.py,xref_call.py,cmp_va.py,peek_va.py}`；`cmp_va.py`（本次新建）支持 `show/scan/diff <lo> <hi>`，diff 全量输出已落盘 `work\peg\out\cmp_text_diff.txt`（87 行 = 母本与产物的全部 .text/.data 字节差）
- 约定：`[VA]` 表示该地址处的指针/全局；指令原文取自母本，除标注「产物」处。凡证据不足一律标注**未证实**。

---

## 0. 对象与角色速查（本次核实）

| 全局 | 角色 | 证据 |
|---|---|---|
| `[0x6768FC]` | `DirectDrawCreate` 得到的 IDirectDraw | `0x4419B5 push 0; push 0x6768FC; push 0; call 0x47E690` |
| `[0x6761E0]` | 主接口（后文所有 CreateSurface 都经它） | `0x441A2F..0x441A47 push 0x6761E0; push 0x48C040; call [ecx+0]`（QueryInterface） |
| `[0x61F900]` | 主面（flip 链，1 个后备缓冲） | `0x441AC6..0x441B03` CreateSurface(caps=0x218)，`0x441FE4C call [ecx+0x2C]` = Flip |
| `[0x676904]` | **后台缓冲**（GetAttachedSurface 得到） | `0x441B39..0x441B53 push 0x676904; push &{dwCaps=4}; push [0x61F900]; call [ecx+0x30]` |
| `[0x655574]` | **地图表面（常驻整幅地图）1920×1920，SysMem** | `0x441BE5..0x441C22`（见 §1.2） |
| `[0x622A10]` | 第二块 1920×1920 SysMem 面（地图/精灵层） | `0x441C9B..0x441CB4` |
| `[0x675538]` | 画布/工作缓冲；**产物 1920×1080** | `0x441FAC..0x441FD3`（`0x441FAF` dwWidth 0x320→产物 0x780；`0x441FB3` dwHeight 0x258→产物 0x438） |
| `[0x686528]` / `[0x6633FC]` | 90×70 覆盖层暂存（后者带色键） | `0x441D0F/0x441D71`；`0x441E07` SetColorKey |
| `[0x61F3E0]` / `[0x62CE10]` | 300×60 面板（带色键） | `0x441E18/0x441E6C`；`0x441EF1/0x441F8A` SetColorKey |
| `[0x6769B0]` | **色键值 = 品红** | `0x441BB7 mov word [0x6769B0],0x7C1F`（RGB555）/ `0x441BCC mov word [0x6769B0],0xF81F`（RGB565，正常路径） |
| `[0x4af2f8]` / `[0x4af2fc]` | 地图滚动坐标（源矩形左上角） | `0x41EB24..0x41EB33` |
| `[0x4af300]` / `[0x498d3c]` / `[0x498d40]` / `[0x498d44]` | 地图视口 left/top/right/bottom（运行期写入，文件初值未改） | `0x41FFA2..0x41FFF0`（每次 blit 读）；`0x4421F9..` 写进描述符#3 |
| `0x676980` / `0x676960` | **描述符#1/#2（漏斗裁剪框，写死 799/599）** | `0x4421D4/0x4421DE`、`0x442219/0x442223` |

---

## 1. 地图是怎么上屏的

### 1.1 初始化链（`0x4419A9`–`0x4422B5`，单函数）

```
0x4419B5 push 0; push 0x6768FC; push 0; call 0x47E690      ; DirectDrawCreate
0x4419EB push 0x11; push [0x676134]; push [0x6768FC]; call [edx+0x50]
                                                            ; SetCooperativeLevel(hwnd, 0x11=EXCLUSIVE|FULLSCREEN)
0x441A72 push 0; push 0; push 0x10; push 0x258; push 0x320; call [eax+0x54]
                                                            ; SetDisplayMode(800,600,16)
                                                            ; 产物：0x441A79=0x438(1080)、0x441A7E=0x780(1920)
0x441AD5 desc.dwFlags=0x21(DDSD_CAPS|BACKBUFFERCOUNT); [ebp-0x14]=0x218(PRIMARYSURFACE|COMPLEX|FLIP); [ebp-0x68]=1
0x441B03 call [ecx+0x18]                                    ; CreateSurface → [0x61F900]
0x441B39 push 0x676904; push &{dwCaps=4}; push [0x61F900]; call [ecx+0x30]
                                                            ; GetAttachedSurface → [0x676904] 后台缓冲
0x441B9E call [ecx+0x54]                                    ; GetPixelFormat(主面)
0x441BA1 cmp [ebp-0xDC],0x3E0                               ; dwGBitMask==0x3E0 → RGB555
0x441BC2 mov [0x62666C],0 ; 0x441BCC mov word [0x6769B0],0xF81F   ; RGB565 ⇒ 键色 = 品红
```

### 1.2 地图表面（整幅地图常驻一块表面，**不是**每帧逐地块贴到主面）

```
0x441BE5 mov [ebp-0x7C],0x7C        ; dwSize
0x441BEC mov [ebp-0x78],7           ; dwFlags = DDSD_CAPS|HEIGHT|WIDTH
0x441BF3 mov [ebp-0x14],0x840       ; ddsCaps = DDSCAPS_SYSTEMMEMORY|DDSCAPS_OFFSCREENPLAIN
0x441BFA mov [ebp-0x74],0x780       ; dwHeight = 1920
0x441C01 mov [ebp-0x70],0x780       ; dwWidth  = 1920
0x441C0A push 0x655574; ... ; 0x441C22 call [eax+0x18]   ; CreateSurface → [0x655574]
0x441C6D call [eax+0x54]                                 ; GetPixelFormat([0x655574])
```
- 尺寸/像素格式：**1920×1920，16bpp，系统内存**（这两个尺寸立即数**母本=产物**，补丁未动）。
- **pitch 假设：没有写死 pitch。** 唯一的软件访问路径 `0x43D6E1`（`Lock(this=[0x655574], flags=1, &desc)`）从 `desc+0x24` 取 `lpSurface`（`0x43D6ED mov ecx,[ebp-0x58]`），行距由 `Lock` 回填；`0x47D826/0x47D861`（Lock/Unlock 软件位图拷贝）按 `width*2` 逐行 `add edi,ebx` 且 `add esi,ecx`（`ecx=[esp+0x38]` 即 pitch），隐含 16bpp（`lea ebx,[ecx+ecx]`）。
- 地图内容由两类操作维护到该表面上，**不是每帧重建**：
  - 地块/精灵 `BltFast`：`0x424AFD`（this=`[0x655574]`，src=`[0x622A10]`，dx=0，dy=0，trans=`0x10`=DDBLTFAST_WAIT，srcRect `[ebp-0x10]`）、`0x424C56`（this=`[0x655574]`）、`0x41FA5F`；
  - 直接写像素：`0x43D6E1` Lock 之后用 `[ebp-0x58]`(lpSurface) 写，坐标在 `0x43D732/0x43D745 cmp eax,0x780` 被夹在 0<v<1920（旁证地图表面确为 1920×1920）。

### 1.3 每帧合成 + 上屏（关键：一次「视口整块 BltFast」）

合成函数尾部（`0x41EB63` 之前）：
```
0x41EB0C movsx eax,word [0x4af32c]          ; 翻页/缓冲索引
0x41EB1A mov word [eax*2+0x498d38], cx      ; 环形缓存
0x41EB22 push 0
0x41EB24 mov dx,word [0x4af2fc] ; push edx  ; 参数2 = 地图滚动 Y
0x41EB2C mov ax,word [0x4af2f8] ; push eax  ; 参数1 = 地图滚动 X
0x41EB33 call 0x41FF8A                      ; ← 地图视口 BltFast
0x41EB3B call 0x421E9B                      ; 叠加层（单位/城市/图标）
0x41EB40 push 0x4F; push 0; push 0; push 0; push 0x663408; push 0x676980; call 0x47E5A0
                                            ; 经描述符#1(0x676980) 的漏斗绘制
0x41EB5D call 0x425BCB                      ; 后台缓冲 → 画布 [0x675538]
```

`0x41FF8A` 全文（函数体，19 个调用者，含 `0x41EB33`）：
```
0x41FF90 movsx eax,word [ebp+8]  → [ebp-0x10]      ; srcRect.left = 地图滚动 X
0x41FF97 movsx ecx,word [ebp+0xC] → [ebp-0xC]      ; srcRect.top  = 地图滚动 Y
0x41FFA2 movsx eax,word [0x498d40]                 ; 视口 right
0x41FFA9 movsx ecx,word [0x4af300]                 ; 视口 left
0x41FFB2 lea edx,[edx+eax+1] → [ebp-8]             ; srcRect.right  = X + (right-left) + 1
0x41FFBD movsx ecx,word [0x498d44]                 ; 视口 bottom
0x41FFC4 movsx edx,word [0x498d3c]                 ; 视口 top
0x41FFCD lea eax,[eax+ecx+1] → [ebp-4]             ; srcRect.bottom = Y + (bottom-top) + 1
0x41FFD4 push 0x10                                 ; dwTrans = DDBLTFAST_WAIT
0x41FFD6 push &srcRect
0x41FFDA push [0x655574]                           ; 源 = 地图表面
0x41FFE1 push [0x498d3c]                           ; dwY = 视口 top (=22)
0x41FFE9 push [0x4af300]                           ; dwX = 视口 left (=0)
0x41FFF1 push [0x676904]                           ; 目标 = 后台缓冲
0x41FFFF call [ecx+0x1C]                           ; BltFast
0x42000B push 0x491308; push 0x420; push eax; call 0x437420   ; 失败仅记日志，无回退
```
**结论：地图 = 一块常驻的 1920×1920 系统内存表面 + 每帧一次「把该表面的可见窗口整块 BltFast 到后台缓冲视口 (0,22)」。** 后台缓冲再经 `0x425B8D`↔`0x425BDF`（画布 `[0x675538]` 与后台缓冲互拷，尺寸立即数产物=1920×1080）与 `0x41FE4C Flip([0x61F900])` 上屏；UI 文字走 GDI（`0x470160/0x4718BB GetDC([0x676904])` + DrawTextExA，见 docs/38:65）。

### 1.4 视口/覆盖层/脏矩形

- 覆盖层保存/恢复对（80×60 的 `0x4A2728` 矩形，坐标夹取用视口宽高）：`0x44C66E`（`[0x676904]`→`[0x686528]`，`0x44C7B8 call [eax+0x14]`=Blt）、`0x44C5F0`（反向恢复）；调用点 `0x41C5D9`、`0x41FE1C`（Flip 之前）。
- 统一绘制漏斗 `0x4235E5`（`0x41C520`、`0x4234xx` 等调用）→ `0x47E0A0` → 裁剪 `0x47E4E0`，裁剪框就是描述符#1/#2（**799/599**，见 §2）。
- 脏矩形/每帧 UI 刷新：`0x4489CC`（`0x4489D8 je` 决定是否整屏重绘，`0x4489E5 call 0x44AC45`）；`0x4234A0` 用计数 `[0x69A2F4]`、数组 `0x69A300`（stride 0x10 = RECT）逐条 `BltFast`（`0x423570`），失败码 `0x887601C2`(DDERR_SURFACELOST) → `0x456070` 恢复。
- 表面工厂 `0x47D5C0`–`0x47D6EF`：循环 `CreateSurface`（`0x47D600 call [edx+0x18]`）+ 每个表面 `0x47D61B..0x47D629 call [ecx+0x74]`（`push 8`=`DDCKEY_SRCBLT`，键值来自 `[0x6a8de4]`）+ `0x47D790` 软件位图填充（Lock/Unlock）。⇒ 地块/精灵表面**带 source color key**。

---

## 2. 地图链路里仍然写死的 800×600

| VA（指令）/ imm32 | 母本值 | 产物值 | 作用与症状 |
|---|---|---|---|
| `0x4421D4` / imm `0x4421DA` | 799 (0x31F) | **799（未改）** | 描述符#1 `0x676980`（surface=`[0x676904]`）right ⇒ 漏斗裁剪框右边界 |
| `0x4421DE` / imm `0x4421E4` | 599 (0x257) | **599（未改）** | 描述符#1 bottom |
| `0x442219` / imm `0x44221F` | 799 | **799（未改）** | 描述符#2 `0x676960`（surface=`[0x675538]` 画布）right |
| `0x442223` / imm `0x442229` | 599 | **599（未改）** | 描述符#2 bottom |
| `0x4567C4/0x4567DE/0x4568E2/0x4568FC/0x456984/0x456A3E` | 799/599 | **未改** | UI 布局常量（docs/64 D 组只改了其中 `0x45696D`） |
| `0x45E741`、`0x46B2AB`、`0x46CF45`、`0x4700DD` | 800 | **未改** | 其它模块（UI/文本/窗口）写死宽；是否影响地图链**未证实** |
| `0x467299`、`0x46795E`、`0x46CF4E`、`0x4700E4` | 600 | **未改** | 同上 |

**症状**：地图本体（§1.3 的 `0x41FF8A`）不经漏斗，所以能铺满 1920 宽；但凡走统一漏斗 `0x4235E5` 的绘制（叠加层、图标、文字框、`[0x663408]` 层）都被 799/599 硬裁 ⇒ x>799 或 y>599 的叠加元素整体消失、鼠标拖影在 x=800 处被切断/拉伸（docs/64 实测：v10b 打上「A 组」放宽裁剪框后，原先被裁掉的工具提示框以三大条品红现身，且 `y≥1056` 与右侧斑驳依旧）。

**补丁已经改掉的地图链尺寸（对照，全部见 `out\cmp_text_diff.txt`，共 87 字节）**：`0x441A79/0x441A7E`（SetDisplayMode→1080/1920）、`0x441FAF/0x441FB6`（画布→1920×1080）、`0x41C4D7/0x41C4DE`（视口/工具栏 rect 571→1052、799→1919）、`0x41EBF2/0x41EBFB/0x41EC75/0x41EC7E/0x41ECA7`、`0x42321A/0x423224/0x42322C/0x423236`、`0x4233E3/0x4233ED/0x4233F4/0x4233FE`、`0x424CD7/0x424CE3`、`0x425B90/0x425B97/0x425BE2/0x425BE9`、`0x43B226/0x43B232/0x43B23C/0x43B248`、`0x43BCB5/0x43BD89/0x43BD95/0x43BD9F/0x43BDAB`、`0x441796/0x44179B`、`0x44C5CD/0x44C5D2`、`0x44C533/0x44C55F/0x44C564/0x44C569/0x44C599/0x44C5B2/0x44C72A/0x44C731/0x44C746/0x44C771/0x44C778/0x44C78E/0x44C863/0x44C86A/0x44C880/0x44C8AA/0x44C8B1/0x44C8C7/0x44CC61/0x44CC68/0x44CC7E/0x44CCA8/0x44CCAF/0x44CCC5` + .data 表 `0x48CFAE`…`0x4A9C1D`。

**假阳性提醒**（`cmp_va scan` 会误报）：`0x4250EC`(=0x257)、`0x47D963`(=0x31F)、`0x42041E`(=0x320) 都是 `jmp/je rel32` 的位移字节，**不是常量**（分别属 `0x4250EB jmp`、`0x47D961 je`、`0x42041C jne`）。

---

## 3. 三个现象的解释

### 3.1 为什么不用 ddraw 包装时地图完全不画（**未证实**，但可排除若干解释）

已证事实：
1. 程序**从不按 DDraw 能力分支**：全程序未出现 `IDirectDraw::GetCaps(+0x2C)`、`GetDisplayMode(+0x30)` 的调用（`vtcalls.py` 全表：`+0x2C` 唯一站点 `0x41FE4C` 是 `Flip([0x61F900])`；`+0x30` 只有 GetAttachedSurface）；也没有 `DDSCL_*` 之外的窗口化回退。
2. 地图表面是**系统内存**（caps `0x840`，`0x441BF3`），不存在「显存不够导致建面失败」。
3. UI 与地图**都画在同一个后台缓冲 `[0x676904]`**（UI 文字经 `GetDC([0x676904])`），且经 `Flip([0x61F900])` 上屏。若 Flip 失败，两者应一起消失 ⇒ 现象只能来自**地图表面内容**或**那一次地图→后台缓冲 BltFast**。
4. 这些顶点失败路径**只写日志、不回退**：`0x42000B push 0x491308; push 0x420; call 0x437420`（地图 blit）、`0x424B09 push 0x491598; call 0x4383FD`（地块 blit）、`0x424C62 push 0x4915D4`（同族）。

因此最可能的机制（按可信度排序）：
- **(A) 源矩形越界导致 BltFast 被原生 DDraw 直接拒绝（首选假设）**：`0x41FF8A` 的源矩形是 `(x, y, x+(right-left)+1, y+(bottom-top)+1)`；产物里视口宽 = 1920（`0x498d40`−`0x4af300`），而地图表面只有 **1920 列** ⇒ 只要滚动 x≠0（或 y>888），`srcRect` 就超出源面。代码**不校验**（`0x41FF8A` 全文无边界检查），失败只记日志。原生 DDraw 对 INVALIDRECT 是拒绝执行（地图全黑），Svens/cnc-ddraw 这类包装层会裁剪/部分拷贝 ⇒ 也就同时解释了 cnc-ddraw 的**黑空洞**与某些**横向拉伸**。
- **(B) SysMem 源面 → VidMem 后台缓冲的 BltFast 在模拟层被降级/拒绝**（与 (A) 同一条指令，不同触发条件）：**未证实**。
- **(C) 键色语义**：与 §3.3 同源，但只影响被抠/未抠的像素，不足以让整幅地图消失，故不是主因。

**决定性验证建议**（不改 exe）：把镜头停在滚动 (0,0) 再观察；或在包装下拖动地图，看黑空洞是否随滚动移动/扩大 —— 若空洞随滚动出现，(A) 成立。

### 3.2 为什么 cnc-ddraw 下有黑色空洞 / y≈595 横黑带

- **主因：增量重绘**。本作不是每帧全屏重绘：`0x4489CC`（受 `0x4489D8 je` 控制）只做「脏区」刷新，`0x4234A0` 更按 `[0x69A2F4]`/`0x69A300` 脏矩形表逐条贴。**同一 exe 只加 B 组补丁（`0x4489D8` 的 `74 1B`→`90 90`，强制每帧整屏重绘）后大面积纯黑即消失**（docs/64 §五 v10b 实测非黑 80.9%，v10d 无 A 组同样改善）——这是本工作区已有的实验证据：黑区来自「该画的地方没被重画」，不是地图数据缺失。
- **次因：色键抠图露出底色**。画布 `[0x675538]`（9210×1080 中的 1920×1080）与各面板都被 `SetColorKey(flags=8=DDCKEY_SRCBLT, [0x6769B0])` 设了品红键（`0x442034`、`0x441E07`、`0x441EF1`、`0x441F8A`）。被抠掉的键色像素下方若从未绘制，就是**纯黑**（cnc-ddraw）或**品红**（Svens，见 §3.3）。
- **y≈595/600 横带**：描述符#1/#2 的 bottom=**599**（`0x4421DE`/`0x442223`，未改）是所有漏斗绘制的硬边界；600 正是母本屏高，而产物把地图/画布放到了 1080 ⇒ 在 y=600 处出现「已重绘/未重绘」的硬落差，表现为横黑带（cnc-ddraw）或横品红带（Svens）。**部分未证实**：该带也可能来自源矩形在 y 方向的越界（§3.1(A)）。
- **1/4 圆形黑斑**：**未证实**。候选：被色键抠掉的圆形元素（发现/视野圈、罗盘、小地图）、圆形区域的增量重绘遗漏、或目标矩形反转后的裁剪残余。

### 3.3 为什么 Svens 下出现品红（色键未生效）

机制（证据充分）：**品红就是色键值本身**。
```
0x441BA1 cmp [ebp-0xDC],0x3E0        ; 主面 dwGBitMask
0x441BAD [0x62666C]=1 ; 0x441BB7 mov word [0x6769B0],0x7C1F   ; RGB555 的品红
0x441BC2 [0x62666C]=0 ; 0x441BCC mov word [0x6769B0],0xF81F   ; RGB565 的品红（默认路径）
0x441DF6 push 8(DDCKEY_SRCBLT); ... ; 0x441E07 call [ecx+0x74]  ; SetColorKey([0x6633FC], 品红)
0x442026 ...; 0x442034 call [ecx+0x74]                          ; SetColorKey([0x675538], 品红)
0x47D61B..0x47D629 push 8; push surf; call [ecx+0x74]           ; 地块/精灵表面同样带键
```
- 实测品红 RGB(240,0,240) 与 `0xF81F`（RGB565 纯品红，屏幕/截图色彩管理后约 240）一致；任务书里 0xF01E 的换算只是同一像素的取值误差。
- **Svens 未按 `DDCKEY_SRCBLT` 抠图**（或键值/像素格式判定不同），于是这些「用键色填充、本应透明」的区域——工具提示框底色、鼠标拖影、y≈600 的横带——直接以品红显示；同一几何在 cnc-ddraw 下被正确抠掉，露出未绘制底色（黑）。这解释了「同一位置，一种包装品红、另一种包装黑」。
- 与 A 组补丁的关系（docs/64 实测）：裁剪框仍是 799/599 时品红框被裁掉；一旦放宽到 1919/1079，被裁掉的品红框立即显现 ⇒ 品红内容一直在画，只是原先被裁剪框盖住。

---

## 4. 预测：只再改 1–2 处，怎样让「地图在 1920×1080 完整且无空洞」

| 优先级 | VA | 现值 | 建议值 | 预期效果 | 风险 |
|---|---|---|---|---|---|
| **1（最低风险）** | `0x4489D8` | `74 1B`（`je 0x4489F5`） | `90 90`（NOP） | 每帧强制整屏重绘，**直接消掉大面积黑空洞/横黑带**；docs/64 实测有效（v10c/v10d） | 帧率略降（≈1080p 全屏重绘）；docs/64 记为「B 组」 |
| **2（针对越界机制）** | `0x441BFA`（dwHeight）/ `0x441C01`（dwWidth） | `0x780`（1920） | `0x1000`（4096）或至少 `0xF00`(3840)/`0x870`(2160) | 让 §1.3 的 `srcRect = (x, y, x+1920, y+1032)` 在滚动 x>0 / y>888 时**仍然合法** ⇒ 若 §3.1(A) 成立，原生 DDraw 下地图不再整屏黑、cnc-ddraw 下空洞随滚动消失 | 系统内存 +24MB（4096²×2B）；若地图世界本身就是 1920×1920，越界部分会显示未初始化填充（黑/杂色）而非地图；`0x43D732/0x43D745` 等按 1920 夹取的坐标逻辑不变（可能仍需同步放大，**未证实**） |
| 备选（与 1 或 2 搭配，不单独用） | `0x4421DA/0x4421E4/0x44221F/0x442229` | `1F 03`/`57 02` ×2 | `7F 07`/`37 04` ×2 | 裁剪框放大到 1919/1079，叠加层/图标不再在 x>799、y>599 被裁 | docs/64 实测（A+B+D 的 v10b）：被裁掉的工具提示框以三大条**品红带**现身，且 `dx>800` 时漏斗 `0x47E0A0/0x47E4E0` 的 `dst.right = 描述符.right − dx` 会变负、目标矩形反转 ⇒ 横向拉伸/错切。**单独改 A 组会让画面更差** |

**推荐组合**：`0x4489D8`（B）+ `0x441BFA/0x441C01`（地图表面放大）。前者消掉「重绘不足」的黑洞（已有实测证据），后者直击「视口 1920 宽 vs 地图面 1920 宽 ⇒ 一滚动就越界」这一结构缺陷；两者都不放宽漏斗裁剪框，因此**不会**引入 v10b 那三条品红/拉伸。若实测证明空洞与滚动无关（(A) 不成立），则第 2 项改为把视口宽度改回 ≤ 地图面宽（即 `0x41C4DE` 的 1919 与 `0x41C4D7` 的 1052 回调），代价是地图不再铺满 1920。

---

## 附：本次新增/复用的可复现命令

```powershell
cd D:\DSH\军事游戏汉化\work\peg
python cmp_va.py diff 0x401000 0x4b0000 > out\cmp_text_diff.txt   # 母本↔产物全部字节差（87 行）
python cmp_va.py scan 0x440000 0x44c000 0x320 0x258 0x31f 0x257   # 余留写死尺寸（注意 jmp rel32 假阳性）
python disasm_range.py 0x441BE0 0x441EC0      # 表面工厂（地图面/画布/面板 + SetColorKey）
python disasm_range.py 0x41FF70 0x420050      # 地图视口 BltFast 0x41FF8A 全文
python disasm_range.py 0x41EAF0 0x41EB90      # 每帧合成调用点
python disasm_range.py 0x41C4A0 0x41C5A0      # 视口刷新例程（0x41C4D7/DE 立即数所在）
python xref_call.py 0x41ff8a                   # 地图 blit 的 19 个调用者
python find_mem.py 0x6769b0 40 --ctx 6         # 色键值的全部引用（读/写）
python vtcalls.py 0x18 0x50 0x54 0x30 0x2c 0x10 0x38   # IDirectDraw 侧调用点（证明无 GetCaps）
```
