# ATOMIC 场景散文 .txt 翻译规格（每批子代理必读）

## 任务
读入 `in-NN.txt`，输出 `out-NN.txt`。

**输出格式**：与输入**逐行同构** —— 每个 `@@FILE <名字> <bytes> <nfiles>` 头行后，紧跟该文件的**中文全文**（UTF-8、保留原有 `\r\n` 换行、不添加/删除任何行）。

⚠️ 头行的 `\r\n` 必须按原文原样保留；**不要**把 `@@FILE` 行也翻译。

## 文件结构（三类）

1. **结算/晋升语**（短，1 行）：`Well done Herr General!` / `Great job Kommodore!!!` / `What a disaster!` → 译
2. **简报正文**：若干段散文 → 译
3. **可选附属块**：
   - `PICTURE:` 块 —— **标签本身保留 `PICTURE:` 不译**，其后的图片说明散文 → 译
   - `¯¯¯¯¯¯` 行（下划线装饰）→ **原样保留，字数和个数都别动**
   - 元数据块（`Scenario Version:` / `Scenario Type:` / `Player Countries:` / `AI Version:` / `Turns:` / `Scenario Designer:` / `Player Turn Prestige` / `Campaign Version:` / `Number of Scenarios:` / `Campaign Difficulty:` / `Campaign Designer:` / `Playtesters:` / `Core Countries:` / `Historical Info:` / `Original Campaign by:` / `Converted to OG by:` / `Sa-kuva. Photo number` 等）→ **键与值都译**，冒号后保留一个空格

## 分节标签译法（固定口径）

| 原文 | 译 |
|---|---|
| `SITUATION:` | `态势：`|
| `ORDERS:` / `Orders` | `命令：`|
| `NOTE:` / `NOTES:` / `NOTE` | `注意：`|
| `NOTES & RULES` | `注意与规则` |
| `Your troops:` | `你的部队：`|
| `Enemy troops:` | `敌军部队：`|
| `Historical Info:` | `历史附注：`|
| `Please notice:` | `请注意：`|
| `Please remember:` | `请记住：`|
| `Attention please:` | `请注意：`|
| `Upgrades` | `升级` |

⚠️ 标签后的 `: ` 若原文是**半角冒号+空格**，译文用**全角冒号**（`：`）后不加空格（这是场景 .txt 层的分层约定：全角）；若原文无空格则同样处理。

## 术语口径（沿用既有 efile，不得自创）

- `BV` / `V` / `TV` → **保留缩写**（`BV`/`V`/`TV`）
- `Brilliant Victory` → `辉煌胜利`；`Tactical Victory` → `战术胜利`；`Victory` → `胜利`
- `VHs` / `VH`（胜利点）→ `胜利点`
- `pp`（威望）→ **保留 `pp`**（硬纪律）；`Prestige` → `威望`
- 装备型号保留原文：`M4A1`、`Bf-109G2`、`Ju 87`、`Pz IV`
- 军舰舰名/舰级保留原文：`USS Iowa`、`Admiral Hipper`
- 大写军事缩写保留：`AT` `FlaK` `BB` `ZOC` `LOS` `LOF` `VH` `AAR` `RAF` `Luftwaffe`（→`德国空军`）`USAF` `RADAR`（→`雷达`）`SS` `NKVD`
- 部队番号：`6. Japanese army` → `日本第6军`；`12th SS Panzer Division` → `党卫军第12装甲师`
- 军衔：`Herr General` → `将军阁下`；`Herr Feldmarschall` → `元帅阁下`；`Kommodore` → `海军准将`；`Kapitan zur See` → `海军上校`；`Herr Leutnant` → `少尉阁下`；`Fregattenkapitan` → `海军中校`；`Korvettenkapitan` → `海军少校`；`Herr Oberleutnant` → `中尉阁下`；`Kapitanleutnant` → `海军上尉`
  ⚠️ 结算语里 `Herr X` 一律译 `X阁下`（保留军衔汉译）。
- 日期：`June 1942` → `1942年6月`
- 地名译通行中文名；无通行译名的用音译+通名后缀

## 立场原则
按扮演方视角用其代号与编制名。禁用蔑称与旧称。

## 严禁
1. 译文出现 `src == dst` 的恒等映射（除非该串是**纯型号/纯缩写/纯数字**，且被本规格明确要求保留）
2. 改动 `¯¯¯` 装饰行
3. 增删任何行、合并或拆分段落
4. 输出 BOM
5. 用半角括号（本层用全角 `（）`）—— 例外：原文内已有的英文书名/番号括号保留原样

## 输出
`out-NN.txt`（UTF-8 无 BOM，LF 行分隔以承载 `\r\n` 内容的行 —— 见下）

**⚠️ 换行约定**：由于原文内含 `\r\n`，导出时以 `\n` 作为"行分隔符"写出，因此译文中的 `\r\n` 会原样嵌在行内。你只需保证：
- `@@FILE` 头行 + 换行 `\n` + 译后全文（其中保留原 `\r\n`）
- 文件之间以 `\n` 分隔，最后**不要**额外补 `\n`（除非原文件本身以 `\r\n` 结尾，则译文同样以 `\r\n` 结尾）
