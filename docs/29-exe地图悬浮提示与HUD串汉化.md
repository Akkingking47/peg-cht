# 29 · exe 地图悬浮提示 / HUD 串块汉化（`.rdata` VA `0x911F80` 起）

> 完成日期：2026-09-24 ｜ 补丁脚本：`work\exe\maphud_patch.py`
> exe MD5：`B97C9117…` → `5A179774…` → **`D8D53A0D…`（当前）**
> ⚠️ 全程**未启动游戏**；预览用 PIL 离屏渲染（`work\ag-verify\maphud-preview.png`）。

## 一、目标与边界

上一轮（`docs\28`）改的是 `.rdata` VA `0x9147BC–0x9155xx` 的**单位面板 / 升级对话框**串，
而 MEMORY 里长期挂着另一处未动的块：

| 项 | 值 |
|---|---|
| 串块起点 | `.rdata` VA **`0x911F80`**（FO `0x511180`） |
| 串块终点 | VA `0x9124FC` 附近（FO `0x5116AC`，` ... ` 之后） |
| 紧邻其后 | FO `0x5116B4` 起是资源加载/菜单热键串（`%s <Ctrl+Q>` 等，**属另一族，本轮不动**） |
| 再往后 | VA `0x912AF0` 起是 **FMOD 库错误串**（第三方，不译） |

> ⚠️ **与 `0x9147BC` 块互不重叠**——两者相隔约 `0x2800` 字节。此前更新记忆时曾误覆盖这条待办，已补回。

## 二、⭐ 本块的结构特征：紧凑 + 4 字节对齐

**这是本块与上一批最大的不同，也是踩坑的根源。**

上一批的串之间有较大空隙；本块是**字符串池式紧密排布**，每条串占用的空间
= `ceil((len + 1) / 4) * 4`，即「内容 + NUL，向上对齐到 4 字节」。

```
0x511224  ' %s'              len 3   avail 4
0x511228  '  Ammo:- '        len 9   avail 12
0x511234  '  Ammo:%d/%d '    len 13  avail 16
0x511244  'KeepAir '         len 8   avail 12   ← 译文需要 10B，> len(old)+1=9
0x511250  ' Mov:%d Mnt:%d'   len 14  avail 16   ← 译文需要 17B，> avail
```

⇒ **两条铁律**：

1. **写入窗口必须是 `avail`（下一串起点 − FO），不是 `len(old)+1`。**
2. `avail` 是**原文件的静态属性，必须硬编码**，不能在运行期动态扫描（见 §五）。

## 三、处理结果：49 条

| 方式 | 条数 | 说明 |
|---|---:|---|
| ① 原地替换 | **46** | `len(GBK)+1 ≤ avail` ⇒ 直接覆盖，余量填 NUL |
| ② 空洞 + 改指针 | **3** | `avail` 不够，写入 `.rdata` 空洞并把 `push imm32` 立即数改向新 VA |
| 合计 | **49** | 另有 1 条术语优化（§六） |

### 代表性译文

| 原文 | 译文 |
|---|---|
| `AP:%d  Fort:%d  Port:%d  Station:%d  Bridge:%d pp` | `行动点:%d  要塞:%d  港口:%d  车站:%d  桥梁:%d pp` |
| `VH to take by ` | `VH 占领方：` |
| `EH: Land, Naval & Air` / `EH: Land & Naval` / `EH: Air` | `EH: 陆、海、空` / `EH: 陆、海` / `EH: 空` |
| `Out of map boundaries` | `超出地图边界` |
| `PAUSED .. type P to resume or Ctrl+Q exit game` | `已暂停 .. 按 P 继续，或 Ctrl+Q 退出游戏` |
| `REPLAY .. type P to pause or Enter to break` | `回放中 .. 按 P 暂停，或 Enter 中断` |
| ` Mov:%d Mnt:%d`（空洞） | ` 机动:%d 山地:%d` |
| ` %s%d/%d Exp:%d  Ent:%d`（空洞） | ` %s%d/%d 经验:%d  工事:%d` |
| ` No prestige bonus nor penalty ` | ` 无声望加成或处罚 ` |
| `(%d,%d)  Click mouse in a flag to show details / select option` | `(%d,%d)  点击旗帜查看详情 / 选择选项` |
| ` This option will increase your prestige %d pp ` | ` 此选项将增加你的声望 %d pp ` |
| `Playing DEBUG_AI mode: all units are revealed and F.O.W. is set for active player side` | `正在 DEBUG_AI 模式：所有单位均可见，且战争迷雾设为当前玩家方` |
| `DEBUG_LG mode: can buy for free, can resupply/reinforce and add exp-bars w/t restrictions` | `DEBUG_LG 模式：可免费购买，可自由补给/增援并增加经验条` |

### 明确不译（清单写进脚本 `SKIP_NOTE`，便于审计）

- **键名**：`ESC` / `Ctrl+Q` / `Enter` / `Shift+E` / `Tab` / `F1`（内联保留，不拆）
- **大写缩写**：`U:%d`（单位编号）· `pp`（声望点）· `EH` · `SH` · `VH` · `F.O.W.`（内联译为「战争迷雾」）
  · `P1`–`P4`（玩家位编号）
- **纯格式串 / 符号**：` %s ` ` %s` ` %s (%s)` ` {Sab}` ` OH(%d,%d)` ` OH(%d,%d)>U:%d`
  ` * ` `  ***  ` ` ... ` `><` ` [S:%d H:%d]`
- **非文本**：`s2` `:` `>` `.jpg` `.png` `.bmp` `.gif`
- **资源/菜单族**：FO `0x5116B4` 之后（`%s <Ctrl+Q>`、`Visit OpenGen Forum`、`menu_attachments12`…）属另一批

## 四、空洞（方式②）

| 项 | 值 |
|---|---|
| FO / VA | `0x4ECB39` / `0x8ED939` |
| 长度 | 64 字节 |
| 占用 | 52 字节（余 12） |
| 安全三查 | ① 区间全 NUL ✅ ② **逐 VA 搜索 4 字节小端模式 ⇒ 0 引用** ✅ ③ 三条原串引用唯一且均为 `push imm32` ✅ |

写入布局：

```
VA 0x8ED939   机动:%d 山地:%d          17B   ← 原 VA 0x912050
VA 0x8ED94A   机动:%d                   9B   ← 原 VA 0x912060
VA 0x8ED953   %s%d/%d 经验:%d  工事:%d   26B   ← 原 VA 0x912068
```

三条引用点（全是 `68 xx xx xx xx` = `push imm32`）：

| 原串 VA | 引用 FO |
|---|---|
| `0x912050` | `0x4038A0` |
| `0x912060` | `0x4038E1` |
| `0x912068` | `0x40391D` |

> **原地遗留的旧英文串不清理**（`0x511250`/`0x511260`/`0x511268` 处仍是 ` Mov:%d Mnt:%d` 等死字节）。
> 与上一批一致：清理会扩大差异面且无收益，只要无指针指向即安全。

## 五、⭐ 两个必须记住的坑

### 5.1 Python 切片赋值会「静默撑长」bytearray

首版实现用了 `d[fo:fo+len(old)] = new + b"\x00" * pad`，其中 `pad = len(old) - len(new)`。

`KeepAir ` 的 `len(old)=9`、`len(new)=10` ⇒ **`pad = -1`** ⇒ 右侧长度 10 ≠ 左侧切片长度 9
⇒ **`bytearray` 切片赋值自动扩容，之后所有字节整体后移 1 字节**，全文件错乱（干跑阶段发现：后续 42 条全部报「原文不符」，因为读到的每个 FO 都多了个前导 `\x00`）。

**正解**：`d[fo:fo+lim] = new + b"\x00" * (lim - len(new))`，`lim = avail`，写满固定窗口 ⇒ 长度恒定。

### 5.2 `avail` 不能运行期动态扫描

首版 `scan_avail()` 把「串」定义为**可打印 ASCII 段**（`0x20 ≤ b < 0x7F`）。
这在英文原文件上正确，但**汉化之后失效**：GBK 汉字字节范围是 `0xA1–0xFE`，**不在该区间内** ⇒ 中文串不被识别为串 ⇒ 算出的边界全错（幂等重跑误报 16 条「原文不符」）。

**正解**：`avail` 是**原始文件的静态属性**，直接**硬编码为 `AVAIL` 字典**（本脚本已这样做）。
若确需重扫，扫描条件必须同时接受 ASCII 与 `b >= 0x81`。

### 5.3 幂等检查的窗口也要用 avail

若检查窗口取 `len(old)`，当译文比原文长时，读到的 `cur` 会被截短到比 `chk` 还短 ⇒ 永远比不上 ⇒ 重跑误报。窗口必须与写入窗口一致。

## 六、`exe_zhfix.py`：exe 侧的「二次修正」入口（新增工具）

补丁脚本靠**英文原文**匹配，一旦该处已是中文，重跑只会报「原文不符」⇒ 改译名/统一术语无从下手。
本轮就遇到这个需求：宽度量测显示 `SH for Owner` → `SH 归属：拥有方` 比原文宽 **+18px**（其余 5 条仅 +6~12px）。

新增 `work\exe\exe_zhfix.py`（对应 `.xscn` 侧的 `ag_xscn.py zhfix`）：

```bash
python exe_zhfix.py --tsv fix.tsv                      # 列: FO<tab>旧译文<tab>新译文[<tab>limit]
python exe_zhfix.py --tsv fix.tsv --apply
python exe_zhfix.py --fo 0x511408 --old "…" --new "…" --limit 0x10   # 变长替换
```

- 默认**只允许缩短**（`len(new) ≤ len(old)`）⇒ 天然不越界；
- 需变长时必须显式 `--limit`（该串可用空间），脚本校验 `len(new)+1 ≤ limit`；
- 幂等、干跑/`--apply`、回读校验齐备。

本轮用它把 `SH for Owner` 由 `SH 归属：拥有方`（90px）改为 **`SH 归属方`（51px，比原文 72px 还窄）**。

## 七、验收

| 项 | 结果 |
|---|---|
| 文件长度 | `6316032` → `6316032` **不变** ✅ |
| PE 头前 16 B / 签名 `PE\0\0` / 节数 4 | 全部一致 ✅ |
| **逐字节差异审计** | 10 个区间：`.text` **恰好 3 段**（= 3 条 `push imm32` 立即数）、`.rdata` 7 段（译文 + 空洞）；`.data`/其它 **0 段** ✅ |
| 回读校验 | 49 条逐条通过 ✅ |
| **三脚本幂等** | `maphud_patch.py` / `unitpanel_patch.py` / `unitdlg_patch.py` 重跑均**零错误** ✅ |
| 残留扫描 | 本块仅剩 11 条含英文的串，**全部是有意保留**（键名 / 调试模式名 / `{Sab}` 符号）＋ 3 条已搬家的死字节 ✅ |
| GBK 可编码 | 0 失败 ✅ |
| 显示宽度 | 26 条关键译文对比：**20 条不宽于原文**，6 条短标签 +6~18px（优化后 +6~12px）✅ |
| 游戏启动 | **未启动**（PIL 离屏渲染预览） |

## 八、产物

| 文件 | 说明 |
|---|---|
| `work\exe\maphud_patch.py` | 本块补丁（46 原地 + 3 空洞），幂等，含硬编码 `AVAIL` 表 |
| `work\exe\exe_zhfix.py` | **新增**：exe 已汉化串二次修正（缩短默认 / `--limit` 变长 / `--tsv` 批量） |
| `work\exe\zhfix-maphud.tsv` | 本轮术语优化清单（1 条） |
| `work\ag-verify\maphud-preview.png` | PIL 离屏渲染预览（三组：HUD / 暂停回放提示 / 调试模式） |
| `backup\OpenGen.exe.before-maphud` | 本轮前备份（`B97C9117…`） |

## 九、仍待处理

1. **`EFILE_AG` 的 `SCENARIO\*.txt`** 286 个 / 142 KB 英文散文（`csr` 39 = 《高卢战记》英译、`spa` 112、`kk` 86、`hog` 31）＋ `.ply` 1 ＋ `.xcam` 4。
2. FO `0x5116B4` 起的**资源/菜单热键族**（`%s <Ctrl+Q>`、`Visit OpenGen Forum`、`Campaigns' catalog`、`Reset Foe spotting`…）——同法可做，但多为菜单标签，优先级低。
3. 其余 17 个 efile（按 `docs\24` 顺序）。
4. ⚠️ **待实机复验**：本轮 49 条 + 上一轮 48 条 + 字体，共 3 项需重启游戏确认。

## 十、回滚

```bash
cp -f "backup/OpenGen.exe.before-maphud" "D:/OpenPG2/OpenGen.exe"   # 退到本轮之前（B97C9117）
cp -f "backup/OpenGen.exe.before-unitpanel" "D:/OpenPG2/OpenGen.exe" # 退到面板批次之前（1640811C）
```
