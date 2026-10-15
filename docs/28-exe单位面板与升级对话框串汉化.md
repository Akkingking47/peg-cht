# exe 硬编码串汉化：单位信息面板 + 升级/指挥官对话框（48 条）

> 日期：2026-09-24 ｜ 目标：`D:\OpenPG2\OpenGen.exe`
> 起因：实机截图（`hog_4`）中单位面板顶部仍有 `Gnd unit - Target:` 等英文
> 结果：**48 条玩家可见串全部汉化**，文件长度不变，PE 结构完好
> exe MD5：`1640811C…` → **`B97C9117…`**
> ⚠️ **全程未启动游戏**；预览用 PIL 离屏渲染

---

## 一、定位

截图里的 `Gnd unit - Target:` 来自 `.rdata` 内一段**连续的格式串块**，范围
VA `0x9147BC – 0x9155xx`（FO `0x5139BC – 0x5146xx`）。

先查现有流水线是否覆盖：

| 文件 | 是否含这批串 |
|---|---|
| `work\exe\dialogs-all.txt`（1007 行） | 仅 `Main country` 偶然命中 |
| `dialogs-todo-en.txt` / `dlg.tsv` / `patches.tsv` | 无 |

⇒ **`rtdialog` 流水线不覆盖**（那套走 RT_DIALOG 资源，这批是 SDL 自绘的运行时文本）。

`STOP` 另查：全库无此字符串，是 `OpenIcons.dat` 里的**图像**，无需也无法汉化。

---

## 二、三类改法

| 方式 | 条数 | 说明 |
|---|---:|---|
| ① 原地等长/缩容替换 | 40 | GBK 字节数 ≤ 原文 ASCII 长度+1，余量填 NUL |
| ② 空洞 + 改指针 | 7 | 3–4 字节短串放不下，写入 `.rdata` 空洞并改 4 字节立即数 |
| ③ 多行块整块替换 | 6 | 原串含 `\n` 且互相嵌套，按「FO→下一串起点」整块改写 |

### 关键前提：显示宽度

中文全角字符 = **2 字节 GBK，显示宽度 ≈ 2 个半角**。
所以「英文单词数 → 中文汉字数」大致减半时，**显示宽度基本持平**：

| 原串 | 显示宽 | 译串 | 显示宽 |
|---|---:|---|---:|
| `%s unit - Target: %s` | 20 | `%s 单位 - 目标：%s` | 19 |
| `Range Air Defense: %d` | 21 | `防空射程：%d` | 11 |
| `Upgrading to this new equipment, will remove the leader,` | 56 | `升级到此新装备将移除指挥官，` | 28 |

⇒ 排版不会溢出（离屏预览已确认，见 `work\ag-verify\unitpanel-preview.png`）。

---

## 三、方式①：原地替换（40 条）

| 原串 | 译文 | FO |
|---|---|---|
| `%d/%d hangars full` | `%d/%d 机库已满` | 0x513A14 |
| `Embark: %s [%s]` | `搭载：%s [%s]` | 0x513A28 |
| `%s in U:%d hangar` | `%s 在 U:%d 机库` | 0x513AF4 |
| `%s %d/%d hangars full` | `%s %d/%d 机库已满` | 0x513B08 |
| **`%s unit - Target: %s`** | **`%s 单位 - 目标：%s`** | 0x513B38 |
| `dry - ice - mud - terrain` | `干燥 - 结冰 - 泥泞 - 地形` | 0x513B80 |
| `%3d - %3d - %3d   (when using RTP)` | `%3d - %3d - %3d   (使用RTP时)` | 0x513B9C |
| `Range Air Defense: %d` | `防空射程：%d` | 0x513BD8 |
| `Range Air Attack: %d` | `空袭射程：%d` | 0x513BF0 |
| `Hangar cap=%d` | `机库容量=%d` | 0x513C10 |
| ` *** can't use RTP ***` | ` *** 无法使用 RTP ***` | 0x513C3C |
| `%s:  cost:%d  %s`（×2） | `%s:  花费:%d  %s` | 0x513C54 / 0x513C70 |
| `*%s*   %s   Cost:  %d + %d%% unit's cost ` | `*%s*   %s   花费:  %d + %d%% 单位成本 ` | 0x513CE8 |
| ` >> (disabled)` | ` >> (已禁用)` | 0x513D14 |
| `*%s*   %s   Cost: %dpp (%d + %d)` | `*%s*   %s   花费: %d点 (%d + %d)` | 0x513D24 |
| `%s * idx:%d - Fronts: %d Factns: %d - %s` | `%s * 序号:%d - 战线:%d 阵营:%d - %s` | 0x514104 |
| `Unit: %s` | `单位：%s` | 0x514184 |
| `Unit: %s  (%s)` | `单位：%s  (%s)` | 0x514190 |
| `Main country: %s` | `主国：%s` | 0x5141A0 |
| `Support country %d: %s` | `支援国 %d：%s` | 0x5141B4 |
| `  .. E:%04d  Fronts: %d  Factns: %d` | `  .. E:%04d  战线:%d  阵营:%d` | 0x51430C |
| ` -- Avail:%s -> %s` | ` -- 可用:%s -> %s` | 0x514330 |
| `Upgrading will remove %d attachments. Do you want to continue` | `升级将移除 %d 个附属单位。是否继续？` | 0x514344 |
| `Cannot reassign unit!` | `无法重新分配单位！` | 0x514388 |
| `%s  Bomb Size:%d` | `%s  载弹量:%d` | 0x51458C |
| `No hangars` | `无可用机库` | 0x514600 |
| `Number of hangars: %d` | `机库数量：%d` | 0x51461C |
| `Units matching hangar's weight` | `符合机库载重的单位` | 0x5146BC |
| `Hangar cap=%d` | `机库容量=%d` | 0x5146E0 |
| `%s not found, neither external nor in DatFile.dat\n` | `%s 未找到，外部与 DatFile.dat 中均无\n` | 0x5139C0 |
| `Leader's random attribute is not valid…changed or removed` | `该指挥官的随机属性无效，将被更改或移除` | 0x514200 |

---

## 四、方式②：空洞 + 改指针（7 条）

| 空洞 | FO | VA | 长 | 占用 |
|---|---|---:|---:|---|
| 空洞 1 | `0x51CB31` | `0x91D931` | 59B | 33B |
| 空洞 2 | `0x4B1C86` | `0x8B2A86` | 76B | 65B |

| 原串 | 译文 | 新 VA | 引用处 FO |
|---|---|---|---|
| `TBD` | `待定` | 0x91D931 | 0x412D26 |
| `OTP` | `他方` | 0x91D936 | 0x419A3E |
| `Gnd` | `地面` | 0x91D93B | 0x41ADCF |
| `Air` | `空中` | 0x91D940 | 0x41ADC6 |
| `%s (Mv=%d)` | `%s (机动=%d)` | 0x91D945 | 0x41801D |
| `U:%d  %s  [Exp:%d] - %s * %s` | `U:%d  %s  [经验:%d] - %s * %s` | 0x8B2A86 | 0x422EF1 |
| `U:%d  %s  [Exp:%d] <%s> - %s * %s` | `U:%d  %s  [经验:%d] <%s> - %s * %s` | 0x8B2AA4 | 0x422E91 |

**安全前提（每条均已核验）**：
1. 空洞区间**全 NUL**；
2. 对空洞内**每一个 VA** 逐一搜 4 字节小端模式 ⇒ **0 处引用**；
3. 原串引用**各仅 1 处**，且都是 `push imm32`(`68`) 或 `mov [ebp-x], imm32`(`C7 45 xx`) ⇒ **改立即数即生效**。

⇒ 「`Gnd unit - Target:`」现在是「**地面单位 - 目标：**」。

---

## 五、方式③：多行块（6 处）

原串含 `\n`，且块与块内子串**互相嵌套**（例：`0x514258` 三行块里同时"是"
`0x514294`、`0x5142CA` 两个更短的串）。**若只改块头，子指针会指向中文串中间 ⇒ 乱码。**

核查结论：所有内部子指针（`0x514294`/`0x5142CA`/`0x51444D`/`0x5144E1`/`0x514527`/`0x51454A`）
**0 引用** ⇒ 只是块内子串，**可整块覆盖**。

| 块 FO | 原 | 译 | 字节 |
|---|---|---|---|
| 0x5141D4 | `The new unit cannot attack any target!` | `新单位无法攻击任何目标！` | 42→27 |
| 0x514258 | `The current leader is useless for the new unit, so you can:` + 两条选项 | `当前指挥官对新单位无用，你可以：` + 两条选项 | 178→115 |
| 0x5143A0 | `Leader's random attribute changed. Unit's exp-bars reduced to: %d` | `指挥官随机属性已更改，单位经验条降至：%d` | 67→42 |
| 0x5143E8 | `Upgrading to this new equipment, will result in losing 1 exp-bar…` | `升级到此新装备将损失 1 条经验条，以更改指挥官的随机属性` | 128→71 |
| 0x514468 | `Unit set exp-level: %d and exp-bar:%d, after losing its leader` | `失去指挥官后单位经验等级设为 %d，经验条 %d` | 64→44 |
| 0x5144A8 | `Upgrading to this new equipment, will remove the leader,`（4 行） | `升级到此新装备将移除指挥官，`（4 行） | 190→126 |

---

## 六、验收

| 项 | 结果 |
|---|---|
| 文件长度 | `6316032` **不变** ✅ |
| PE 头前 16B | 与补丁前**相同** ✅ |
| PE 签名 / 节数 | `PE\0\0` / 4 ✅ |
| 差异区间 | 25 段：`.text` 6 处（**全是 6 个指针立即数**）+ `.rdata` 19 处 ✅ |
| 回读校验 | 48 条译文逐条回读**全部通过** ✅ |
| 脚本幂等 | 两脚本重跑**零错误**（已生效自动跳过）✅ |
| 离屏预览 | `work\ag-verify\unitpanel-preview.png` 排版正常、无重叠 ✅ |

**保留（不译）**：`U:%d`（单位编号缩写，符合「大写缩写保留」口径）· `RTP` ·
`DatFile.dat` · `%sSCENARIO\%s.buy` 路径模板 · 调试/日志串（`atlTrace*`、SDL 初始化失败提示，玩家看不到）。

---

## 七、工具

| 脚本 | 作用 |
|---|---|
| `work\exe\unitpanel_patch.py` | 第一批 20 条（面板格式串 + 5 条改指针） |
| `work\exe\unitdlg_patch.py` | 第二批 28 条（升级/指挥官 + 6 处多行块 + 2 条改指针） |
| `work\exe\poke_holes.py` | 扫 PE 节表 + 连续 NUL 空洞 |

两脚本均为 **dry-run 默认 / `--apply` 写盘 / 幂等可重跑**，并含：
原文逐字节校验、GBK 可编码校验、超长拒绝、引用唯一性校验、空洞全 NUL 校验、
写后回读校验、长度不变断言。

**备份**：`backup\OpenGen.exe.before-unitpanel`（`1640811C`）→ 回滚一条 `cp` 即可。

---

## 八、仍待处理

1. ⬜ **exe 地图悬浮提示串块**（本次**未动**）：`.rdata` **VA `0x911F80` 起**（FO `0x511180`），
   约 60 条玩家可见文本 —— `Odds: %d-%d` · `AP:%d  Fort:%d  Port:%d  Station:%d  Bridge:%d pp` ·
   `Fuel:%d` · `Ammo:%d/%d` · `Mov:%d Mnt:%d` · `Exp:%d  Ent:%d` · `VH to take by` ·
   `Friends` / `Enemy` / `Both sides` · `Out of map boundaries` ·
   `PAUSED .. type P to resume or Ctrl+Q exit game` · `REPLAY ..` …
   > 该块**紧邻**本次改的块（`0x911F80` < `0x9147BC`），但**互不重叠**，本次未触碰。
   > 再往后（`0x912AF0` 起）是 **FMOD 库错误串**，属第三方库，**不译**。
2. `EFILE_AG` 的 `SCENARIO\*.txt` 286 个 / 142 KB 英文散文、`.ply` 1、`.xcam` 4。
3. `work\exe\todo-p*.txt` 里 P1–P4 若干 UI 微调（已译未应用）。
4. 其余 17 个 efile（按 `docs\24` 顺序；B1 已完成根级 + `.xscn`）。
