# OpenGeneral exe 硬编码汉化 —— P0 可行性验证

- 日期：2026-10-16
- 效力：**现行** ｜ 对象：`D:\OpenGeneral\OpenGen.exe`（ver 25.02.26.0）
- 补丁脚本：`work\exe\og_p0_exit_patch.py`（幂等 · 默认干跑 · `--apply` 才写盘）
- 前置评估：`docs\05-exe硬编码汉化可行性评估.md`（一作 OpenPG2 的方法论与风险清单）
- 同族先例：`docs\28`（单位面板/升级对话框）· `docs\29`（地图悬浮提示/HUD）
- **本报告未自行启动游戏**（`MEMORY.md` 硬纪律第 7 条）；实机验证由用户执行，见 §六。

---

## 一、结论

**这条路在 OpenGeneral 上同样走得通，而且第一批比一作更简单。**

`Do you really want to exit ? ... ` 这条串在 OpenGeneral 的 exe 里满足**最强的一档条件**：
唯一引用、纯显示、目标槽位够长 ⇒ **原地等长替换**，
**不需要空洞、不需要改任何指针、` .text ` 零改动**。

| 项 | 一作既有 4 个补丁 | 本批 P0 |
|---|---|---|
| 手段 | 原地替换 + **空洞 + 改 `push imm32` 立即数** | **仅原地替换** |
| 改 `.text`？ | 是（改立即数） | **否（0 字节）** |
| 主要风险 | 空洞安全性（曾有 LoadConfig 写坏事故） | **无空洞 ⇒ 该类风险不存在** |

---

## 二、对象与指纹

| 项 | 值 |
|---|---|
| 文件 | `D:\OpenGeneral\OpenGen.exe` |
| 原始态 | 6,310,400 B · md5 `5b0eb96efae364ae68d119828a3d830f` |
| 补丁后 | 6,310,400 B · md5 `4841a46d7beeb683b8d38c7757a2fce2` |
| 大小 | **完全不变** |

> ⚠️ 这是**二作**的 exe。一作的 `unitpanel_patch.py` / `unitdlg_patch.py` / `maphud_patch.py`
> 针对 `D:\OpenPG2\OpenGen.exe`（26.03.30.0，6,316,032 B，比本 exe 大 5,632 B）。
> **两者偏移不可照搬**，本报告全部数据均在本 exe 上现扫得到。

---

## 三、为什么这条能安全改（四项判据）

| # | 判据 | 实测值 |
|---|---|---|
| 1 | 全 exe 内该 VA 的立即数引用数 | **1 处**（唯一） |
| 2 | 该引用的指令形态 | FO `0x3F94C3` / VA `0x007FA0C3`，字节 `68 f4 ed 90 00` ⇒ 前导 `0x68` = **`push imm32`** |
| 3 | 语义是否可能兼作查找键 | **否**。是退出确认框的消息文本，`docs\05` 的 R1 风险（strcmp key）不适用 |
| 4 | 目标槽位是否放得下 GBK 译文 | 原文 33 B + NUL，其后另有 2 个 `0x00`，下一串 `LAST COMBAT ` 起于 **FO+36** ⇒ 可用 **36 B**；译文 GBK 21 B + NUL = **22 B** ⇒ 富余 14 B |

| 参数 | 值 |
|---|---|
| 目标串 | `Do you really want to exit ? ... ` |
| FO | `0x50DDF4` |
| VA | `0x0090EDF4` |
| 槽位长度 | 36 B（FO `0x50DDF4` .. `0x50DE18`） |
| 唯一引用指令 | FO `0x3F94C3` / VA `0x007FA0C3` |
| 译文 | `你真的想退出吗 ? ... ` |

---

## 四、执行过程（六项自证，全部由脚本机检）

脚本在写入前后各跑一遍下列检查，任一项不过就 `SystemExit` 拒绝写盘：

| # | 自证 | 结果 |
|---|---|---|
| 1 | 文件大小不变 | ✅ 6,310,400 B |
| 2 | 逐字节审计：差异**全部落在槽位内** | ✅ 差异 33 处，范围 `0x50DDF4..0x50DE15` |
| 3 | `.text`（FO `0x400..0x476000`）差异为 0 | ✅ **0 字节** |
| 4 | GBK 回读 | ✅ `'你真的想退出吗 ? ... '`（21 B + NUL） |
| 5 | 下一串完好 | ✅ FO `0x50DE18` 起 `b'LAST COMBAT '` |
| 6 | 唯一引用指令未被改动 | ✅ `68 f4 ed 90 00`（仍 `push` 本串 VA） |

> 📌 自证 2 第一版断言写错（要求「差异范围恰好等于槽位」），被机检拦下：
> 槽位尾部 3 B 原文本就是 `0x00`，写入后仍是 `0x00` ⇒ **不产生差异**，并非数据异常。
> 已把断言改为「差异必须完全落在槽位内」+ 新增 `.text` 零差异的**真检查**（不再只是声称）。

**硬纪律①执行**（绝不直接覆盖）：构造新内容到内存 → 写 `OpenGen.exe.p0.tmp` →
**重新打开临时件回读**，逐字节比对 → 一致才 `os.replace` 换名 → 落盘后**再回读**比对。

---

## 五、结果与回滚

```
备份：D:\DSH\军事游戏汉化\backup\OpenGen.exe.before-p0
      md5 5b0eb96efae364ae68d119828a3d830f（= 原始态，与正式件不同名，不覆盖已有备份）

回滚：copy 'D:\DSH\军事游戏汉化\backup\OpenGen.exe.before-p0' 'D:\OpenGeneral\OpenGen.exe'
```

**幂等已验证**：改后复跑脚本，报告 `当前状态：patched —— 已是汉化版：'你真的想退出吗 ? ... '`
并 **跳过，无任何写入**。

**只读复核**：`python work\exe\og_p0_exit_patch.py --verify`

---

## 六、✅ 实机验证（**已通过**，2026-10-16）

**User said (m00769)**：「汉化成功，成功显示 你真的想退出吗 ?」

| 判据 | 结果 |
|---|---|
| 退出确认框显示中文 | ✅ `你真的想退出吗 ? ... ` |
| 能正常返回游戏、不崩 | ✅（用户确认「汉化成功」） |

⇒ **本 exe 的「原地等长替换」方法已实机证明可行**，据此铺开 P1（见 §十）。

---

## 七、OpenGeneral exe 内已定位的其它候选串（现扫）

用户截图里出现的英文，逐条在本 exe 上定位（VA / `push` 引用数）。**`push=1` 才属低风险可改档**：

| 串 | VA | push 引用 | 判定 |
|---|---|---|---|
| `Do you really want to exit ? ... ` | `0x0090EDF4` | **1** | ✅ **本批已改** |
| `Campaigns' catalog` | `0x009114B0`（另有 `0x009115EC`） | **1** | ✅ 低风险 |
| `OG Mode` | `0x009180A0` | **1** | ✅ 低风险 |
| `dry - ice - mud - terrain` | `0x008F5034` | **1** | ✅ 低风险（运动力表头整条） |
| `No RTP pool` | `0x008F2B28` | **1** | ✅ 低风险 |
| 同族 `Can't use RTP` / `No RTP available in pool` / `No RTP matching front/weight` / `Can use: RTP` | `0x008F2B00` / `0x008F2B34` / `0x008F2B50` / `0x008F2BA0` | **1** | ✅ 低风险 |
| `%s * Mode: %d x %d x %d bpp (Click to show Credits)` | `0x009108AC` | **1** | ⚠️ 含 4×`%d` + 1×`%s`，**必须逐字保留** |
| `   File: %s   [%d scenarios]` | `0x008F63E8` | **1** | ⚠️ 含格式符 |
| `Weather is: %s  *  Ground condition: %s`（3 个变体） | `0x008F0A90` / `0x008F1BDC` / `0x008F353C` | **1** | ⚠️ 含格式符 |
| `Weather can change ground condition` | `0x008EFEE0` | **1** | ✅ |
| `Ground condition changed! ... ` | `0x008F4ED8` | **1** | ✅ |
| `Frozen ground condition supply: %+d%%` / `Mud ground condition supply: %+d%%` | `0x008F9C20` / `0x008F9C48` | **1** | ⚠️ 含 `%+d%%` |
| `*** can't use RTP ***` / `%3d - %3d - %3d   (when using RTP)` | `0x008F508C` / `0x008F5050` | **1** | ⚠️ |
| `Toggles terrain labels` | `0x008F6F98` | **0** | ⚠️ 无 push 引用（走指针表/资源），暂缓 |
| `Show Terrain labels and data` / `Show terrain labels and roads` | `0x0098E2A0` / `0x009A47A0` | **0** | ⚠️ 同上 |

**另一套机制（本报告未覆盖，需单独评估）**：`CREDITS`、`DISCLAIMER`、
`Files in folder`、`Check campaigns & DL missing maps` 在 **`.rsrc` 的 Win32 DIALOG 模板（UTF-16）**里，
不是 `push imm32` 的字符串表。好消息是 UTF-16 下中文与拉丁字母**同为 2 字节**，
中文译文通常更短 ⇒ 大概率塞得进原槽；但要动资源段，**不能打包票**。

**禁区**（`docs\05` §五，绝不修改）：文件路径串、printf 格式符本身、`settings.cfg` 键名、
疑似 strcmp key（战役名/场景名/efile 名）、`.text` 代码本体（除经确认的 `push` 立即数）、调试/日志串。

---

## 八、下一步建议（P1+）

1. **等 P0 实机结论**再铺开。P0 过 ⇒ 本 exe 的字节级改动方法已证；P0 不过 ⇒ 先查字体/编码路径。
2. **P1 候选**（收益最直观、风险最低）：`Campaigns' catalog`（底栏悬停）、`OG Mode`（关卡详情）、
   `dry - ice - mud - terrain`（运动力表头）、`No RTP pool` 同族。**全部 `push=1`**。
3. **含格式符的串**（`%d`/`%s`）单列一批，译文逐字保留格式符，改后**统计格式符个数必须一致**。
4. **`push=0` 的串**（`Toggles terrain labels` 等）先探明承载方式（指针表 or `.rsrc` STRING TABLE）再动。
5. **`.rsrc` 对话框**（`CREDITS`/`DISCLAIMER`/`Files in folder`）另立子课题评估。

---

## 九、产出清单

| 文件 | 说明 |
|---|---|
| `work\exe\og_p0_exit_patch.py` | 本批补丁脚本（幂等 · 默认干跑 · `--apply`） |
| `backup\OpenGen.exe.before-p0` | 原始态整份备份 |
| `docs\72-OpenGeneral-exe硬编码汉化P0验证.md` | 本报告 |

---

## 十、P1：一批 UI 串汉化（13 条 / 17 槽位）

P0 实机通过后铺开。脚本 `work\exe\og_p1_ui_patch.py`，方法**完全同 P0**（原地等长替换、
不挖空洞、不改指针、不碰 `.text`）。

### 10.1 本批清单

| # | 原文 | VA | 槽位 | 译文 | 出处（哪里能看到） |
|---|---|---|---:|---|---|
| 1 | `Campaigns' catalog` | `0x009114B0` | 20 | `战役目录` | 底栏按钮悬停提示 |
| 2 | `Campaigns' catalog` | `0x009115EC` | 20 | `战役目录` | 同上（第二份副本） |
| 3 | `OG Mode` | `0x009180A0` | 8 | `OG 模式` | 关卡详情面板右下 |
| 4–7 | `dry - ice - mud - terrain` | `0x008F5034` / `0x00913790` / `0x00914310` / `0x00914DB8` | 28 | `干燥 - 结冰 - 泥泞 - 地形` | 单位面板「消耗移动力」表头（4 份副本） |
| 8 | `No RTP pool` | `0x008F2B28` | 12 | `无 RTP 池` | 单位面板铁路运输行 |
| 9 | `Can't use RTP` | `0x008F2B00` | 16 | `无法使用 RTP` | 同上 |
| 10 | `No RTP available in pool` | `0x008F2B34` | 28 | `运输池中无 RTP` | 同上 |
| 11 | `No RTP matching front/weight` | `0x008F2B50` | 32 | `无匹配阵营/重量的 RTP` | 同上 |
| 12 | `Can use: RTP` | `0x008F2BA0` | 16 | `可用: RTP` | 同上 |
| 13 | `Weather can change ground condition` | `0x008FA550` | 36 | `天气会改变地面状况` | 单位面板天气提示 |
| 14 | `Ground condition changed! ... ` | `0x008F4ED8` | 32 | `地面状况已改变! ... ` | 同上 |
| 15 | `No file loaded` | `0x00907B04` | 16 | `未载入文件` | 设置对话框右侧字段 |
| 16 | `Keep current` | `0x008FBC98` | 16 | `保持当前` | 设置对话框分辨率下拉 |
| 17 | `Normal` | `0x00888B80` | 8 | `普通` | 设置对话框字体面板标签 |

### 10.2 md5 链

| 阶段 | md5 |
|---|---|
| 出厂原始态 | `5B0EB96EFAE364AE68D119828A3D830F` |
| P0 后 | `4841A46D7BEEB683B8D38C7757A2FCE2` |
| **P1 后（当前）** | `EA30ABEFEF1905A3A3696B91DDB62835` |

文件大小三态均为 **6,310,400 B 不变**。

**备份**：`backup\OpenGen.exe.before-p1`（＝P0 后状态，回滚 P1 用）；
彻底回出厂态用 `backup\OpenGen.exe.before-p0`。

```
回滚 P1  : copy 'D:\DSH\军事游戏汉化\backup\OpenGen.exe.before-p1' 'D:\OpenGeneral\OpenGen.exe'
回滚全部 : copy 'D:\DSH\军事游戏汉化\backup\OpenGen.exe.before-p0' 'D:\OpenGeneral\OpenGen.exe'
```

### 10.3 五项自证（脚本机检，任一不过拒绝写盘）

| # | 判据 | 结果 |
|---|---|---|
| 1 | 文件大小不变 | ✅ 6,310,400 B |
| 2 | 差异 **316 处全部落在 17 个槽位内**（越界 0 处） | ✅ |
| 3 | `.text`（FO `0x400..0x476000`）差异 **0 字节** | ✅ |
| 4 | 17 个槽位 GBK 回读全一致 + 槽外后继字节逐字节未动 | ✅ |
| 5 | 17 个 `push imm32` 引用指令原样保留 | ✅ |

**幂等已验证**：复跑 → `全部已是汉化版，跳过（幂等）。无任何写入。`
**只读复核**：`python work\exe\og_p1_ui_patch.py --verify`

> 📌 **干跑时自证 4 抓到一处真问题**：RTP 同族串在 `.rdata` 里**首尾相邻**——
> `No RTP pool` 的槽尾正好是 `No RTP available in pool` 的起点 ⇒
> 「槽位之后 8 B 未动」会把自己有意写入的**邻串**误报成越界改动。
> 判据已改为**跳过落在本批其它槽位内的位置**，其余位置仍逐一比对。
> （这与 P0 那次「槽尾本就是 0x00 故无差异」是同一类教训：**自证判据本身也会写错，必须让它能证伪**。）

### 10.4 ❓ 待用户实机验证

| # | 怎么触发 | 应看到 |
|---|---|---|
| 1 | 底栏图标悬停 | `战役目录` |
| 2 | 打开任一关卡详情 | `OG 模式` |
| 3 | 选中单位 → 查看移动力表头 | `干燥 - 结冰 - 泥泞 - 地形`（**重点看列对齐**） |
| 4 | 选中带铁路运输的单位 | `无 RTP 池` / `无法使用 RTP` / `可用: RTP` 等 |
| 5 | 打开设置对话框 | `未载入文件` / `保持当前` / `普通` |

> ⚠️ **第 3 项需重点目视**：该表头是**一整条固定字符串**，中文像素宽于 ASCII，
> 列宽可能与下方数字**不再对齐**。若明显错位，回滚 P1 后我把这 4 个槽位拆出单独处理
> （例如改用更短的词或保留 `dry/ice/mud/terrain` 原文）。

### 10.5 未纳入本批

- **含 printf 格式符的串**（P2）：`%s * Mode: %d x %d x %d bpp (Click to show Credits)`
  （槽 52）· `   File: %s   [%d scenarios]`（槽 32）· `Frozen/Mud ground condition supply: %+d%%`
  · `%3d - %3d - %3d   (when using RTP)` · `*** can't use RTP ***`
  ⇒ 译文须逐字保留格式符，并机检**格式符个数与种类一致**。
- **`push` 引用 = 0 的串**（P3）：`Toggles terrain labels`（`0x008F6F98` / `0x008F73CC`）、
  `Show Terrain labels and data`（`0x0098E2A0`）、`Show terrain labels and roads`（`0x009A47A0`）
  ⇒ 走指针表/Dialog 资源，需先探明承载方式。
- **`.rsrc` UTF-16 对话框模板**（另一套机制）：`Disable Campaigns Dialog at start` ·
  `Hide windows' task bar` · `Change to` · `Tables` · `Files in folder` ·
  `Check campaigns & DL missing maps` · `CREDITS` · `DISCLAIMER`
  ⇒ ASCII 扫描全部找不到，需按资源段解析（中文与拉丁同为 2 B，槽位大概率够）。

**现扫工具**：`work\exe\og_hardcode_probe.py [exe路径]` —— 对一批候选串报出
每次出现的 FO/VA/段/可用槽位、`push imm32` 引用数与任意 4 B 引用数。
**判据：`push = 1` 且「其它 4 B 引用」也是 1，才属最低风险可改档。**
