# OpenPG（EFILE_OPENPG）efile 汉化说明

- 目标 efile：`D:\OpenPG2\EFILE_OPENPG`
- 完成日期：本次会话
- 状态：**已部署并实测通过**

---

## 一、完成情况

| 文件 | 内容 | 条目 | 状态 |
|---|---|---|---|
| `TEXT-ZH\nations.txt` | 阵营（轴心国/盟军）+ 26 国国名 | 28 | ✅ **实测生效** |
| `TEXT-ZH\strings_efile.txt` | 覆盖 `[results]` `[classes]` `[requisition]` `[terrain]` 四段 | 约 95 | ✅ 已部署 |
| `TEXT-ZH\tips1.txt` | 游戏机制提示 | 13 | ✅ 已部署 |
| `TEXT-ZH\SCENARIO\*.txt` | 场景文本：简报 41 + 决定性胜利 37 + 胜利 37 + 战术胜利 37 + 失败 37 + 战役简介 1 | **190** | ✅ **实测生效** |
| `TEXT-ZH\equip.txt` | 单位名称：装备型号保留原文，兵种/编制/后勤名译中文 | 331 处 | ✅ 已部署 |
| `TEXT-ZH\names.txt` | 将领姓名（24 国 × 31 名）；前 31 行贡献者保留 | 744 处 | ✅ 已部署 |

### 附：`equip.txt` 与 `.xeqp` 的关系（已查明）

`equip.xeqp` 为定长二进制记录（`261328 = 4 + 2142×122` 字节），记录序号 = `equip.txt` 行号 − 1，偏移 74 起 8 字节是 IconID —— **122 字节装不下名称字符串，所以单位名称必然来自 `equip.txt`**。两者配合：`.xeqp` 供属性与图标，`.txt` 供名称。故翻译 `equip.txt` 有效。

反过来，用 `.xeqp` 的 IconID 查 `D:\OpenPG2\OpenIcons.csv`（`IconID;Description;Color;IconClass;Nation;Chassis;IconStyle`，17908 条）可以反查每个单位的类别与国别，用于校对译名。本次即据此交叉校验了 330 条译名（核对表：`work\openpg\equip-核对表.csv`）。

### 实测证据

| 界面 | 显示 |
|---|---|
| 战役简介框 | `1939 战役 v1.0` / `德国在东部发动一场闪电战，最终打败波兰。` / `由 MG43 改编，转换并移植为 Open Panzer General 版本` / `01/2014` |
| 场景选择对话框 | `EFile 文件夹:`、`41 个场景`、`检查地图（不下载）`、`检查并下载缺失`、`按文件名排序` |
| 对战方标签 | `P1 盟军-苏联`、`P2 轴心国-德国` |
| 底部提示条 | `EFile 文件夹` |

---

## 二、为什么必须做 `TEXT-ZH\`

OPENPG 的 `strings_efile.txt` **覆盖**了 UI 主字符串的四个段（`[results]` `[classes]` `[requisition]` `[terrain]`）。

这意味着：**即使 UI 已经汉化，只要不提供 efile 级中文版，这些类别名仍会显示 efile 里的英文原值。**

举例：UI 已把 `Battleship` 译为 `BB`，但 OPENPG 的 `[classes]` 会覆盖为它自己的 `Battleship`；不做 `TEXT-ZH\strings_efile.txt`，玩家看到的还是英文。

---

## 三、机制与技术要点

1. **目录约定**：`<EFILE>\TEXT-ZH\`（与官方自带的 `TEXT-DE` / `TEXT-ES` 同构），场景文本放 `TEXT-ZH\SCENARIO\`
2. **加载优先**：引擎**优先**从 `TEXT-ZH\` 读取，找不到才回落到 efile 根目录 —— 所以原文件保持不动，**完全可回滚**
3. **编码**：GBK(936) / 无 BOM / CRLF（与 UI 语言文件一致）
4. **语言识别**：由 `Settings.cfg` 的 `UI_Lang=strings-zh` 决定（引擎由此取语言代码 `zh` 去拼 `TEXT-ZH`）

---

## 四、未翻译的文件及理由

| 文件 | 体量 | 理由 |
|---|---|---|
| `TerrainEx.txt` | 169 行 | 地形数值表（工事加成/先手上限/补给系数），**非显示文本** |
| `weather.txt` | 149 行 | 天气概率表（数字），**非显示文本** |
| `fronts.txt` | 534 行 | 战线/派系定义，官方明确注明**仅供 OpenSuite 使用** |
| `colors.txt` / `pg1mode.cfg` / `efile.xml` | 极小 | 颜色定义 / 兼容模式开关 / efile 元信息 |

> `equip.txt`（331 处）与 `names.txt`（744 处）已按用户选择完成汉化，见第一节。

### 装备名的统一口径

| 类别 | 处理 | 例 |
|---|---|---|
| 型号代码 | **保留原文** | `M4A4`、`Bf-109G2`、`Hs-129B-2`、`Pz IVD Tauchfahig`→`Pz IVD 潜水坦克` |
| 有通行译名的著名装备 | 译中文 | `Sherman II LL`→谢尔曼 II LL、`Churchill IV LL`→丘吉尔 IV LL |
| 军舰/飞机名 | **保留原文** | `Hood`、`Exeter`、`Lancaster`、`Beaufighter` |
| 舰级 | 译「X 级」 | `Espana Class`→西班牙级、`O Class`→O 级 |
| 通用兵种/编制/后勤 | 译中文 | `Pioneeri`→工兵、`Feld Befehl`→战地指挥部、`Versorgung-LKW`→补给卡车 |

将领姓名的处理：按各国语言音译，历史名将强制使用中文圈通行译名（`Rommel`→隆美尔、`Chuikov`→崔可夫、`Montgomery`→蒙哥马利），并修正了 efile 原作者的拼写手误（`Eissenhower`→艾森豪威尔、`Garriboldi`→加里波第、`Bruntland`→布伦特兰）。

---

## 五、质量校验结果

| 检查项 | 结果 |
|---|---|
| 覆盖率 | **190 / 190，0 缺译** |
| 编码 | 全部 无 BOM / CRLF / 合法 GBK |
| 乱码 | 无 U+FFFD |
| 汉字比例 | 190 个文件**全部 ≥ 30%**（无「直接拷贝英文」的情况） |
| 行结构 | 场景文本按原文结构保留（含 `kiev_l` / `poland_l` / `warsaw_l` 的真实换行与分段） |

### 并行翻译的组织方式

190 个文件按文件名排序均分 5 组，由 5 个译者并行处理；**同一场景的简报与各结局文本由同一译者负责**，以保证地名/番号/人称/语气一致。

因两组在边界处重叠，产生了 4 个双版本文件（`berlinwest_bv` `berlinwest_i` `berlinwest_l` `earlymoscow_bv`）。已逐对比对后统一采用质量更好的版本，另一版备份在 `work\openpg\_dup\`。

---

## 六、译名与立场审查（依用户原则：通行译名优先 + 按扮演方立场用词）

### 作战代号：通行译名 + 阵营归属

| 场景 | 代号 | 阵营 | 译文 | 判定 |
|---|---|---|---|---|
| poland | Fall Weiss | 德军 | 白色方案行动 | ✅ 通行 |
| norway | Weserübung | 德军 | **威悉演习行动** | ✅ 已修正（原译「威瑟堡行动」把 -übung 误作 -burg） |
| sealion40 / sealionplus | Operation Sea Lion | 德军 | 海狮行动 | ✅ 通行 |
| sealion40_bv | Barbarossa | 德军 | 巴巴罗萨行动 | ✅ 通行 |
| kursk | Unternehmen Zitadelle | 德军 | 堡垒行动 | ✅ 通行 |
| ardennes | Wacht am Rhein | 德军 | 莱茵守望行动 | ✅ 通行 |
| d-day | Operation Overlord | 盟军（德军视角提及敌方） | 「霸王」行动 | ✅ 通行 |
| cobra | Operation Cobra | 盟军（德军视角提及敌方） | 「眼镜蛇」行动 | ✅ 通行 |

> 立场处理正确：**德军视角的场景一律用德军自己的代号**；德军视角提到敌方行动时用盟军代号（`Overlord`/`Cobra`）。这与「淮海战役 / 徐蚌会战」同理。

### 苏联称谓：按立场区分

| 用词 | 处理 | 理由 |
|---|---|---|
| **俄国**（20 处） | **保留** | 均为德军视角的国家/地理称谓（"对俄国的入侵""深入俄国""俄国战场"），符合扮演方立场，中文亦自然 |
| 俄军 / 俄国人（原 14 处） | **统一为「苏军」** | 军队名称混用会让人困惑；中文军事读物通行「苏军」 |
| 苏军 / 苏联 / 苏联人 | 保留 | 通行译名 |

### 日期与术语格式

- 日期统一为中文出版规范的无空格形式：`8月6日`、`12月31日`、`3月底`（原混用 `8 月 6 日` / `11月26日`）
- 集团军群、突出部、合围、迟滞作战等军语统一

---

## 七、曾经的小瑕疵（已全部处理）

1. ~~组间同义词不一致~~（`最近一次战役` / `最近这次战役` 等，已随术语审查统一）
2. ~~行动代号译名不规范~~（`威瑟堡行动` → **威悉演习行动**）
3. ~~军队名称混用~~（`俄军`/`俄国人` → **苏军**）
4. ~~日期格式混用~~（已统一为无空格）

> 仍可选的细化项：`RAF` 现译「皇家空军」而非保留缩写；运输单位译「运输船」而类别名译「海上运输」。如需改动请告知。

---

## 七、待你决定的两项

### 1. `equip.txt`（2142 行，单位名称）

内容构成：

```
40mm ItK/36  Bf-109G2  M4A1(76)W  StuG IIIG  Fokker D.XXI   ← 装备型号（占多数）
Pioneeri     Ratsuvaki  Cavalerie  Ingénieur  44 Infanterie  ← 各国原语言兵种名
```

- **A. 全部保留原文** —— 最省事，军迷都能认；但 `Pioneeri`/`Ratsuvaki`（芬兰语）普通玩家看不懂
- **B.（推荐）型号保留、兵种名译中文** —— 既符合惯例又看得懂
- **C. 全部翻译** —— 型号也译（不推荐）

### 2. `names.txt`（775 行，将领姓名）

- **A.（推荐）保留原文** —— 避免音译不一致或译错
- **B. 译成中文** —— 用通行译名，但量大且易错

---

## 八、部署与维护

### 部署脚本

```powershell
# 把 work\openpg\scenario\*.utf8.txt 批量转 GBK 并部署到 TEXT-ZH\SCENARIO\
& 'D:\DSH\军事游戏汉化\work\openpg\deploy-scenario.ps1'

# 非场景的 TEXT-ZH 文件（strings_efile / tips1 / nations）用通用工具转换：
& 'D:\DSH\军事游戏汉化\tools\txt-tool.ps1' -Action to-gbk `
    -File 'work\openpg\nations.utf8.txt' -Out 'D:\OpenPG2\EFILE_OPENPG\TEXT-ZH\nations.txt'
```

### 目录结构

```
work\openpg\
  ├─ nations.utf8.txt          ← UTF-8 工作稿（编辑入口）
  ├─ strings_efile.utf8.txt
  ├─ tips1.utf8.txt
  ├─ scenario\*.utf8.txt       ← 190 个场景文本工作稿
  ├─ _dup\                     ← 重叠版本备份
  └─ deploy-scenario.ps1       ← 部署脚本
```

> **注意**：`deploy-scenario.ps1` 含中文路径，必须保存为 **UTF-8 with BOM**，否则 PowerShell 5.1 会按 GBK 误读路径（本次已修复）。

---

## 九、下一步可选方向

1. 决定 `equip.txt` / `names.txt` 的处理方式（第七节）
2. 统一第六节的术语小瑕疵
3. 汉化其他 efile（机制完全复用：建各自的 `TEXT-ZH\` 即可）
