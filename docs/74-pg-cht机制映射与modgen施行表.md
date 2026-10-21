# 74 · pg-cht（PG2）机制 → modgen（People's General / PeG030）施行表

> 路线依据：**不做全量反编译**，改走「机制级外科补丁」。
> `docs\73` 的模块作业图降级为备案（只在我们将来要彻底脱离原 exe 时启用）。
> 外部依据：[wicanr2/pg-cht](https://github.com/wicanr2/pg-cht) 的
> [pg2/CLAUDE-PG2-TEMPLATE.md](https://raw.githubusercontent.com/wicanr2/pg-cht/main/pg2/CLAUDE-PG2-TEMPLATE.md)
> —— 该手册开头即写明「首要目標兄弟作 = **解放軍之怒 (People's General, SSI 1998, 同引擎)**」，
> 且全案 **无源码、无全量反编译**，只有 9 道 EXE patch 链。
>
> 两条纪律（双方一致）：
> 1. **机制可移植，绝对地址不可移植** —— 每个地址都要在本机 PeG030.exe 上重新量。
> 2. **一次只加一处补丁，改完先 `--dry-run`/`--selftest`，随时一键回退。**

---

## 一、引擎确认（pg-cht §1 Phase-0 四步 ↔ modgen 实测）

| pg-cht 步骤 | PG2 答案 | modgen / PeG030 实测 | 判定 |
|---|---|---|---|
| ① import table | MSVCRT + DDRAW + mss32 + smackw32 + dplayx + clubdll→gamechat→chatsock | WINMM(5) / KERNEL32(98) / USER32(40) / GDI32(7) / comdlg32(2) / ole32(3) / **mss32(26)** / **DDRAW(1)** / DPLAYX(2)，**无 MSVCRT** | VC++ / DirectDraw ✓；**静态 CRT**（与 PG2 不同）；**无 smackw32、无 clubdll 链** |
| ② 建置路径串（项目代号） | `C:\pz97\main\Src\Scenario.c` ⇒ 代号 `pz97` | `C:\modgen\main\Src\*.c` ⇒ 代号 **`modgen`**，37 个模块 | ✓ 同法命中 |
| ③ 字型格式逐 byte 核对 | TFONT（header 16B + offset table + `[width][px]`，前景 0x00/背景 0xFF） | **本机副本已经是中文版**（`PeG030zh.exe` 等 8 个同尺寸变体 + 已显示中文），CJK 文本管线**已存在**，不必重建 | 目标不同：文本中文化已有人做过，我们只做**画面/坐标/呈现** |
| ④ 语言槽 | 英文（默认）槽注入，不 flip 语言 byte | 同副本已是 zh 变体 | 无需处理 |

结论：**文本管线不是我们的工作量**；我们的战场是「视口几何 / 重绘 / 坐标换算 / 控件呈现」，对应 pg-cht 的 §5⑥⑨ 与 §6.4 那一族。

---

## 二、9 道 patch 链的映射

| # | pg-cht（PG2）机制 | 对 modgen 的适用性 | 我们的对应物 |
|---|---|---|---|
| ① | atlas 字库烘焙（face_index=3 TC、`is_cjk = ord>=0x80`、dense 2-byte 编码） | **不适用**（中文版已存在） | — |
| ② | 主 hook + word-wrap hook + gw-clamp + ww-safe（追加 `.cjk` 节） | **暂不适用** | 若日后要换字级/字体，再回来 |
| ③ | `_pctype` 指针 repoint（不覆写原表；建 `.ctyp` 影子表） | **手法可移植**：任何「共用表被多处读取」的问题都该 repoint 而非覆写 | 我们的 `[0x498D74]` 共享刷新标志（62 处引用）是同类结构，但语义不同（见 §五） |
| ④ | `_output` NULL guard（hook 底层格式化函数 + 塞进既有节 slack） | 手法可移植 | 未遇到 |
| ⑤ | GWCLAMP 2-byte 感知（一处修好 28+ 个量测 caller） | **思路可移植**：先找量测/换算的**唯一收敛点**再改，不要逐点打 | 我们的坐标换算收敛点：`0x43D5AE`/`0x43D5F2`（六角→像素，各 7 个 caller）、`0x40E741`(600)、`0x414646`(800) |
| ⑥ | status-bar / 采购标题清框（**descriptor 表数据 patch**：`bottom = top + fontH + 1`） | **高度适用**：这是「固定几何值按旧尺寸写死」的同类 | 我们的底栏 `0x467297/0x46795E`(+600)、`0x467066/0x4675A0`(+550)、`0x467088/0x4675C4`(+700)；坐标夹取 `0x40E741`(600)、`0x414646`(800) |
| ⑦ | 简报 wrap/line-count **clone**（不同 caller 需求相反 ⇒ 复制函数、只让需要的 caller 走 clone） | **核心纪律，直接采用** | 我们的 `0x43F7E4`（清层+整块重绘）有 11 个 caller，`0x42D0F2`（范围重算）有 6 个 ⇒ 任何改动前先枚举 caller |
| ⑧ | 简报专属 12px + 框高倍率与行距脱钩 | 不适用（字级不改） | — |
| ⑨ | 采购格裁剪 view（`y1 = cellTop + 2 + FONT_H`） | **适用**：与我们「清框/裁剪欠高」同族 | 我们的画面黑块/残影（截图 6/8）与此族相邻（更接近「未绘制区域」） |
| — | **动态插桩 backtrace**（§8 第 5 法：用游戏自身 IAT 的 `CreateFileA`/`WriteFile` 写日志） | **必须采用** | 我们已被反调试打死过断点路线（带断点 2 秒后被踢）；**改 IAT 写日志是零断点方案** |

---

## 三、会重演的雷（pg-cht §6）与我们的对照

| pg-cht 雷 | 我们的状态 |
|---|---|
| 6.2 Chesterton fence：共用表/函数有 blast radius，改前枚举全部 caller | **已撞**：B 组（每帧强制整屏刷新）抢清 `[0x498D74]` ⇒ 更糟 ⇒ 已回退 |
| 6.3 全域"根本解"遇到需求相反的 caller 要 clone | 待用（`0x43F7E4` 有 11 caller） |
| 6.4 清框/框高/裁剪 view 全按原生 8px 字设计，**是一整族** | **正是我们的族**：底栏 y=600/夹取 800x600/黑块残影都属"按 800x600 写死的固定几何值" |
| 6.9 静态归因先用最小 A/B 验证再大改 | **已撞**：M 组（地图面 1920→4096）先上后回退，最终靠 N 组才成立 |
| 6.10 静态分不清 emboss vs 裁切 ⇒ 动态定案 | 待用（阴影只闪一帧已属"静态推理到顶"） |
| 6.13 DirectDraw 独占模式键盘事件进不去 | **已撞**：borderless 下鼠标死、trace 日志饿死输入轮询 |

---

## 四、工具对照

| pg-cht | 我们（`work\_scratch\peg\`、`work\peg\`） |
|---|---|
| `pg2/build/pe_inspect.py`（PE 节表 + 反汇编指定 VA） | `_sections.py`、`work\peg\d.py` |
| capstone | 已用（同库） |
| `pe_imports.py`/`rsrc.py`/`scan_calls.py`/`xref.py`（未进 repo 的 scratchpad） | `_callers.py`、`_callers_range.py`、`_jumps.py`、`_refs.py`、`_dword.py`、`_ptrs.py`、`_prologues.py`、`_func.py`、`_modgen_modules.py` |
| 动态插桩 backtrace（改 IAT 写日志） | **待建**（`diag_watch2.py` 是只读轮询，够用于内存取样，不够用于调用链回溯） |

---

## 五、当前阻塞与已定位地址（本轮之后的施工面）

| 症状 | 机制（已定位） | 候选补丁 |
|---|---|---|
| 选中单位后移动范围阴影只闪一帧 / 移动鼠标才稳定 | 写层已定位（`0x42D0F2` 每帧重算范围 → `0x43D67F` 写两张 1bpp 遮挡层 `0x4CCE40`/`0x53D640`，每帧都在跑）；**真正卡住的是上屏时机**：`0x42D464`（地图屏每帧处理器，同表一格）里 `0x42D509 movsx edx,word[0x4af32c]`（当前视口槽）→ `0x42D510 movsx eax,word[edx*2+0x498d34]` 与 `0x42D518 movsx ecx,word[0x4af2f8]` 比较、`0x42D52A/0x42D532` 对 Y 同样比较（`0x498d38` vs `0x4af2fc`）；`0x42D53B je 0x42D581` ⇒ **滚动没变就跳过**；只有走到 `0x42D579 call 0x41FF8A` 才把地图面 BltFast 上屏 | **R 组已实测无效**（`0x42CF8B 75 11 → 90 90` 只重绘不上屏，用户 m05005 反馈"还是和之前一样"）⇒ 改用 **S 组**：`0x42D53B 74 44 → 90 90`，滚动不变也上屏。**S 组实测也无效**（用户：「鼠标不动时不显示，移动一下屏幕就能显示出来了；黑块拖影照旧；无掉帧」）⇒ 两者**默认关闭**，`--present` / `--maprepaint` 才打开 |
| 地图上零散黑块 / 未绘制区域 | 地图面 1920×1920 < 视口所需；extent 上界之外从未绘制；M 组已放大到 4096 | 待定：给未绘制区填底衬，或让引擎认为地图 ≥ 视口 |
| 鼠标拖影 / 简报页超出 800×600 的永久残留 | 重绘/擦除记账仍按 800×600（顶栏/底栏硬编码 600/800/572） | ⑥⑨ 族：先枚举"画字前先清背景"与"裁剪 view"的固定几何值 |
| 单位坐标漂移 / 点选不准（>800×600 区） | 屏幕↔游戏坐标换算与命中判定仍按 800×600；命中测试唯一读缓存者在 `0x455CA8`，缓存写入者 `0x410E66`（**静态 0 调用者** ⇒ 需动态定案） | 动态插桩 backtrace 定位调用链 |
| 底栏仍在中部 | 调用方按 `i+600`/`i+550`/`i+700` 摆位（`0x4672xx`、`0x4670xx`），绘制例程里的常量曾改到游戏无法启动 ⇒ **必须改调用方的基准常量** | ⑥ 族 |

---

## 六、下一步（按顺序）

1. **实机采样定案**（`work\peg\_sample_shadow.py`，只读）：游戏里选中单位、鼠标别动，采 30 秒 —— 看 `maskA/maskB`（两层 1bpp 遮挡层 0x4CCE40 / 0x53D640 的置位数）是否 > 0。
   - `>0` ⇒ 阴影**算出来了**，缺的只是"烘焙/上屏"，要去找把 1bpp 层涂进地图面 16bpp 的那一步（0x43F64E / 0x43F9E8 / 0x43FC09 三个函数，调用点见 `_find_layer_refs.py` 输出）；
   - `=0` ⇒ 扫描器在鼠标静止时**根本没跑**，要去找它的触发门（`byte[0x498d78]`）。
2. **退出卡死 A/B**（本轮新增异常：「退出游戏会程序锁死」）：S/R 已改为默认关闭，请先按默认（275 条）跑一次、正常退出 —— 若不再卡死 ⇒ 元凶是 R/S 之一（R 的每帧整块重绘会用 `Lock` 拿地图面，S 的每帧 `BltFast(...,0x10)` 带 `DDBLTFAST_WAIT`，两者在退出清理期都可能等死）；若仍卡死 ⇒ 与补丁无关，另查。
2. **建动态插桩器**（pg-cht §8 第 5 法）：改 IAT（`CreateFileA`/`WriteFile`）写 backtrace 日志，专门解决 `0x410E66`/`0x43D680` 静态 0 caller 的谜团（这直接关系「坐标漂移 / 点选不准」）。
3. **清扫固定几何值**：按 6.4 的找法，枚举"清框/裁剪/步进"附近接近原生屏幕尺寸的立即数，产出清单后再逐条 A/B。
4. 每完成一条：写入本表 + `docs\72` 的坐标普查 + 一次实机回归。

---

### R 组补丁记录（第一个"转向后"的补丁）

```
站点：0x42CF8B   原字节 75 11   →  90 90    （jne 0x42CF9E → nop nop）
含义：地图屏每帧都执行 0x43F7E4（清三层 + 按 extent 整块重绘）
位置：work\peg\peg_launcher.py  MAPREPAINT
验证：--dry-run 276 条（274 游戏路径 + 1 R + …）、--selftest「276 条已写入并回读一致（exe 文件未改动）」
回退：在启动命令后加 --no-maprepaint，或让 diag_run.py 传 maprepaint=False
实测：无效（用户 m05005「还是和之前一样，超出800X600部分显示有问题，卡顿倒是没有，黑块/拖影还是之前那样。」）
```

### S 组补丁记录（第二个"转向后"的补丁）

```
站点：0x42D53B   原字节 74 44   →  90 90    （je 0x42D581 → nop nop）
含义：地图屏每帧处理器 0x42D464 里"滚动没变就跳过上屏"的门被去掉 ——
      每帧都走到 0x42D579 call 0x41FF8A（把地图面 BltFast 上屏）
理由：R 只重绘地图面（0x42CF96 → 0x43F7E4）但不改变上屏时机，
      所以遮挡层算得再对也上不了屏 ⇒ "阴影只闪一帧、鼠标不动就没了"、
      "静止区残留黑块/拖影"都是同一机制。
位置：work\peg\peg_launcher.py  PRESENT
验证：--dry-run 显示「S 地图每帧上屏：1 处」；
      --selftest「277 条已写入并回读一致（exe 文件未改动）」（276 + S 1）
回退：在启动命令后加 --no-present
实测：无效（用户：「鼠标完全不动，移动范围不会显示，但是移动一下屏幕，移动范围就能显示出来了；黑块和拖影照旧；没有新的闪烁和掉帧；**退出游戏会程序锁死**」）
```

### 新增静态证据（S 组无效后）

- `0x41FF8A` = **纯 BltFast**：`create rect` → `mov edx,[0x676904]`（显示面）→ `mov ecx,[eax]` → `call [ecx+0x1c]`（IDirectDrawSurface::BltFast）→ `push 0x10`（DDBLTFAST_WAIT），源面 `[0x655574]`（地图面），不碰任何遮罩层；返回后若参数 `[ebp+0x10] != 0` 再 `call 0x423CD6`。⇒ **上屏路径不合成遮罩**，所以 S 组即使每帧上屏也看不见阴影。
- 遮罩层引用普查（`work\_scratch\peg\_find_layer_refs.py`，只读）：`0x4CCE40` / `0x53D640` 各 17 处引用，**只落在 4 个函数**：`0x43D67F`（单格写/清）、`0x43F64E`、`0x43F9E8`、`0x43FC09`。调用点：`0x43D67F` ← 18 处（`0x42CC93 0x42D17C 0x42D192 0x42D38A 0x42DACE 0x42E270 0x43EAF4 0x43EBE2 0x43EC55 0x43EC8D 0x43ECA3 0x43F70D 0x43F78A 0x43F7D6 0x43FBE0 0x43FBF6 0x468D21 0x46A47E`）；`0x43F64E` ← `0x41F10A 0x42E0A7`；`0x43F9E8` ← `0x4255C5 0x4255E2 0x42C152 0x441163 0x448A61`；`0x43FC09` ← `0x42F3AF 0x42F532 0x42F563 0x42F594 0x42F5C5 0x42F63F 0x42F6B1 0x4313C3 0x4313EE`。
- 新工具：`work\peg\_probe_hung.py`（Wow64GetThreadContext 探针；本轮实测发现 PeG030 在退出期有一段时间处于"线程已全部结束、进程对象还在"的僵尸态，故"锁死"未必是死循环）、`work\peg\_sample_shadow.py`（只读采样：dirty/f78/f324/滚动与缓存/视口/范围表命中数/两层遮罩置位数）。
