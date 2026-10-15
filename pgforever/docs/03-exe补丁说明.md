# PG Forever — exe 补丁说明（L6/L7）

> 本文记录对 `PGForever.exe` 的三处修改。全部为**字节级原地替换**，文件大小恒定 `753664` 字节。
> 每次改动前均已备份，可独立回滚。

---

## 补丁总览

| # | 名称 | 位置 | 改动 | 解决的问题 |
|---|---|---|---|---|
| **P1** | 嵌入 manifest 改为 UTF-8 代码页 | 文件偏移 `0xAC27C`（资源区 XML，Size=346） | 用 246 字节精简 XML 等长替换 | 让进程内 `CP_ACP` = 65001，中文不再被按 GBK→UTF-8 误转 |
| **P2** | `WideCharToMultiByte` 缓冲区计算修正 | 文件偏移 `0x6CA3E`（`.text`，2 字节） | `D1 F8`(sar eax,1) → `D1 E0`(shl eax,1) | 缓冲区按"字符数"分配，但 UTF-8 汉字占 3 字节 → 截断/越界 |
| **P3** | 硬编码 UI 文案汉化（L7） | `.rdata` 等数据区，77 处 | 译文 UTF-16LE 原地写入，不足补 `\0\0` | 单位类别、战斗结算、提示、错误信息等仍是英文 |

---

## P1 — manifest：`activeCodePage=UTF-8`

**为什么需要外部改**：exe 已内嵌 `RT_MANIFEST`，Windows 会**忽略**同名外部 `.manifest` 文件，所以只能改内嵌那份。

**空间来源**：manifest 资源 `Size=346`，原 XML 恰好 346 字节。去掉只声明 `asInvoker`（本就是默认行为）的 `trustInfo` 段后，精简 XML 为 **246 字节**，可等长塞回原资源槽，不动任何资源结构。

```xml
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <application><windowsSettings>
    <activeCodePage xmlns="http://schemas.microsoft.com/SMI/2019/WindowsSettings">UTF-8</activeCodePage>
  </windowsSettings></application>
</assembly>
```

**效果**：进程内 `GetACP()` 返回 65001，引擎 `WideCharToMultiByte(CP_ACP,…)` 产出 UTF-8 字节，HTMLayout（按 UTF-8 解析窄字符串）正确渲染。

> 注意：这是**逐进程**生效，不改系统全局设置；删掉内嵌 manifest 里的 `activeCodePage` 即还原。

---

## P2 — UTF-8 缓冲区溢出修正（核心）

### 症状
- 主菜单战役列表最后一条损坏：`1943 东线` → `1943 东缃`，描述位置露出 `body>`
- 战役简报长文本被截断
- **htm 界面的中文却完全正常**

### 定位
区别在于数据源路径：
- `*.htm` → HTMLayout 直接从文件读 UTF-8 → **不经过 exe 转换** → 正常
- `*.pgcam` / `*.pgscn` / `*.pgbrf` → exe 读成 UTF-16 → 再转 UTF-8 交给 HTMLayout → **出问题**

反汇编 `WideCharToMultiByte` 调用点（VA `0x46D64A`，文件偏移 `0x6CA4A`）：

```asm
lea   ecx,[ebp-0x1410]
push  ecx               ; lpMultiByteStr = 缓冲区
lea   ecx,[ebp-0x6B8]
sub   eax,ecx
cdq
sub   eax,edx
sar   eax,1             ; ← eax = (end-start)/2 = 宽字符数 N
push  eax               ; ← cbMultiByte = N      ★ 元凶
push  esi
push  65001             ; CP_UTF8
call  [WideCharToMultiByte]
```

`cbMultiByte` 收到的是**字符数 N**，但 UTF-8 下一个汉字需要 **3 字节**：

| 文本 | 需要字节 | 实际传入 | 结果 |
|---|---|---|---|
| 英文 N 字符 | N | N | ✅ 刚好 |
| 中文 N 字 | **3N** | N | ❌ 只够 1/3 → 截断 + 越界读相邻内存 |

越界读到的相邻内存正好是 HTML 模板片段，于是把 `</body>` 的 `body>` 当正文显示出来 —— 这就是标签泄漏的来源。

### 修复
```
0x6CA3E:  D1 F8  (sar eax,1  → eax = N)
       ↓
          D1 E0  (shl eax,1  → eax = (end-start)*2 = 4N)
```
`4N ≥ 3N`，纯中文也够用；**2 字节等长替换**，文件大小与所有偏移不变。

实测（列表区"文字墨迹"像素数，数值含截图噪声，仅作定性参考）：

| 状态 | 墨迹 |
|---|---|
| 补丁前 | 1540 |
| +P2 | 2458 |
| +P2+P3 | 2458 ~ 3573 |

### 残余
列表中存在**第二个同类调用点**（VA `0x473347` 附近），其 `cbMultiByte` 与 `cchWideChar` 复用同一个 `[ebp+0x10]`，无法用等长替换修正（改大会让源长度越界读），需要 code cave 才能动。当前 P2 已覆盖主要路径，该点暂留。

---

## P3 — 硬编码 UI 文案（77 处）

从 `.rdata`/`.text`/`.data` 提取 UTF-16LE 宽字符串 **815 条**，筛出用户可见文案 **188 条**，最终翻译 **77 处**。

**已汉化**（示例）：

| 原文 | 译文 |
|---|---|
| `Aircraft Carrier` / `Capital Ship` / `Level Bomber` | 航空母舰 / 主力舰 / 重型轰炸机 |
| `Air Defense Fire` / `Defensive Artillery` | 防空火力 / 防御炮兵 |
| `Effective Attack: %d` / `Effective Defense: %d` | 有效攻击: %d / 有效防御: %d |
| `Rugged defense chance: %d%%` | 顽强防御概率: %d%% |
| `carpet bombing` / `strategic bombing` | 地毯式轰炸 / 战略轰炸 |
| `Turns per Day` / `Current Weather` / `Weather Zone` | 每日回合数 / 当前天气 / 天气区域 |
| `Some units have not moved yet. End turn?` | 尚有单位未移动。是否结束回合? |
| `[ERROR] Failed to load equipment table.` | [错误] 装备表加载失败。 |

**铁律（脚本强制）**
1. 译文字符数 ≤ 原文字符数，不足补 `\0\0` 终止
2. 写入前校验该偏移字节 == 原文 UTF-16LE，不符即跳过（防错位）
3. 白名单保护，以下**一律不碰**：
   - 命令协议：`purchase %d %d %d` / `move %d %d` / `load pg %d %d` 等
   - 文件名与内部键：`SCENSTAT.BIN` / `unittypes.pgeqp` / `PANZER.EXE` / `PG Forever`
   - 格式符与标签：`%d` `%s` `%u` `%%` `&nbsp;` `<tr>` `<div>`

---

## 回滚

| 目标 | 操作 |
|---|---|
| 撤掉 P3（保留 P1/P2） | 用 `backup\PGForever.before-L7.exe` 覆盖 |
| 撤掉 P2（保留 P1） | 用 `backup\PGForever.before-w2m-patch.exe` 覆盖 |
| 撤掉全部，回到原版 | 用 `backup\origin\PGForever.exe` 覆盖 |

> ⚠️ 覆盖顺序：`origin` 是最原始；`before-w2m-patch` = origin+P1；`before-L7` = origin+P1+P2。

---

## 待实机验证

GUI 自动化在本机不可用（`SetForegroundWindow` 恒定失败，即使最小化全部其它窗口，合成鼠标/键盘也到不了游戏窗口），因此以下需人工确认：

1. **战役简报长文本**是否完整显示（P2 的主要目标）
2. 主菜单战役列表最后一条是否不再出现 `body>` 泄漏
3. 单位面板/战斗结算中的 77 条文案是否正常
4. 游戏运行是否稳定（P2 改变了缓冲区长度，建议跑几个回合）
