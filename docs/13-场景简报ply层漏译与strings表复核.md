# 13 · 场景简报（`.ply`）层漏译 + `strings-zh.txt` 复核

> 2026-09-24 · 起因：用户提供 4 张**实机截图**（OLGWW2 / Canal Albert 战役）
> 结论来源一律为**实测**：文件字节、目录比对、编码检测、反汇编；不采信文档自述。

---

## 一、起因与截图读取结果

用户在游戏里依次截了 4 张图（1920×1040）。逐张放大取证后：

| # | 画面 | 实测结论 |
|---|---|---|
| 1 | 启动闪屏（LG WW2） | 底部标签 `Efile 文件夹: D:\OpenPG2\EFILE_OLGWW2\ (OpenLGWW2 v2.26 Apr.2013)` —— **中文标签，L7 层生效** ✅ |
| 2 | 地图 + 场景简报弹窗 | 标题「**阿尔贝特运河**」中文 ✅；**正文为西班牙语原文** ❌；且 `alemán`→`alem□`、`situación`→`situac□` **重音字母变方块** ❌ |
| 3 | 地图全屏 | 顶栏「**开阔地 (22 9)**」中文 ✅（= 地形名，L1 的地形名表 22–41 行生效） |
| 4 | 单位详情面板 | 番号行「**第 6 Gn营 / - / 第7步兵师 / 第1军**」中文 ✅；底部左侧 `U:42 …`、中间「**工具**」中文 ✅；右下 `S/S Exp 0 Ent 0 Fuel 80 Mov 2 Mnt 10 Ammx 8` —— **英文统计标签**（`Exp/Ent/Fuel/Mov/Mnt/Ammx`）❓ |

> ⚠️ 低分辨率下我曾把标题误读为「阿贝尔河」、顶栏误读为「开始回合」——**放大后全部推翻**。教训：截图取证必须放大到原始像素，不能靠缩略图猜。

---

## 二、发现 A（主要）：`.ply` 场景简报层**全库漏译**

### 是什么

`<efile>\SCENARIO\*.ply` = **场景开场简报正文**（图 2 那个可滚动弹窗）。

```
Canal Albert 
(10-12 mayo 1940)
                       ← 空行
General, el esperado ataque alemán ha comenzado. …（西班牙语段落）
…
Paqueo, Diciembre 2010
------------------------------------------------------   ← 分隔行（≥8 个 '-'）
                       ← 空行
Canal Albert
(10-12 May 1940)
General, the expected German attack has started. …（英文段落）
```

- **单文件可含 1∼2 个语言块**，用一行 `------` 分隔（OLGWW2 的作者是西班牙团队，故 ES+EN 双写）。
- 编码：**ASCII / Latin-1**（`canalalbert_i.ply` 仅 12 个高位字节，全是西语重音）。
- 引擎按 **CP_ACP=936** 解释这些字节 ⇒ 西语重音 `á é í ó ú ñ` 全部落成方块并**吃掉后一个字符**（实机图 2 可见）。

### 全库清点（156 个）

| 分类 | 数量 | 说明 |
|---|---|---|
| `ascii` | **108** | 纯 ASCII 原文（英文/西语无重音），**未翻译** |
| `high-bytes` | **8** | 含重音字符（西语/法语）原文，**未翻译** |
| `empty` | **40** | 501 字节**纯 `\x00` 占位**（`EFILE_PzLIGA` 全部 14 个 + `EFILE_Clu` 22 个 + AO 3 个 + OPENPG 1 个）⇒ **非文本，跳过** |

⇒ **实需翻译 = 116 个**，分布：

| efile | 需译 | efile | 需译 |
|---|---|---|---|
| OPENPG | **43** | OLGWW2 | **5** |
| AO | 25 | OPENAK | 5 |
| BASEKORP | 18 | OLGCW | 5 |
| LUPO | 7 | AG | 1 |
| KAISER | 6 | Clu | 1 |
| | | **合计** | **116** |

**OLGWW2（5）与 OPENPG（43）属于我们已宣称"完成 L2–L9"的两个 efile** —— 即：**宣称完成的两套 efile 里各有一整层没翻**。

### 与 `.txt` 简报层的区别（别搞混）

同一场景有两种载体，**互不替代**：

| 载体 | 例子 | 我们翻了没 |
|---|---|---|
| `.txt` 名称清单（地图地名 + 部队番号，`.xscn` 的文本投影） | `canalalbert.txt`（4389 B，汉字 1133） | ✅ 已翻 |
| `.txt` 简报族 `*i/*int/*v/*l/*bv/*tv` | `18days0i.txt`（汉字 188）、`dak1int.txt`（汉字 111）、`dak1v.txt`（汉字 40） | ✅ 已翻 |
| **`.ply` 简报** | `canalalbert_i.ply` | ❌ **从未触碰** |

CanalAlbert 的简报**只有 `.ply`** 一种载体（没有 `canalalberti.txt`），所以整个场景的介绍就是西语。

### 修法（建议）

1. 译文转 **GBK、无 BOM、CRLF**；
2. **两个目录同时写**：`SCENARIO\*.ply` **和** `TEXT-ZH\SCENARIO\*.ply` —— 见发现 B，不要只写一处；
3. 双语块文件：若引擎只显示第一块，则只需译第一块（待实机确认取块规则）；
4. 先备份：`canalalbert_i.ply` 等 5 个 OLGWW2 原件已有 2018 时间戳副本，可直接用作还原源。

---

## 三、发现 B（高风险）：`TEXT-ZH\SCENARIO\` 是镜像，且藏着**英文原版 `.xscn`**

### 实测

| efile | SCENARIO vs TEXT-ZH/SCENARIO | 相同 | **不同** | 差异文件的扩展名 |
|---|---|---|---|---|
| OLGWW2 | 各 1033 个文件（双向零差异 = 完整镜像） | 846 | **187** | `.xscn` × 187 |
| OPENPG | — | 239 | **54** | `.xscn` × 54 |

**187 / 54 恰好等于我们 L9 汉化的全部 `.xscn` 数量。**

### 内容判定（英文残留计数，ASCII 词长 ≥4）

| 文件 | SCENARIO（L9 成品） | TEXT-ZH（镜像） |
|---|---|---|
| `CanalAlbert.xscn` | 17 个英文词 | **194 个英文词** |
| `18days3.xscn` | 31 | **208** |
| `anvil.xscn`（OPENPG） | 4 | **73** |
| `ardennes.xscn`（OPENPG） | 4 | **78** |

⇒ **`TEXT-ZH\SCENARIO\*.xscn` 是未汉化的英文原版**，与 `SCENARIO\` 下的汉化成品并存。

### 为什么这是风险

反汇编已证实引擎拼场景路径时**先试 LangDir、再回退 EfileRoot**：

```
0x007E8C7A  push 0x90e1f8   ; "%sSCENARIO\%s"   …含 0x11951B0(LangDir=TEXT-ZH)
0x007E8CF1  push 0x90e254   ; "%sSCENARIO\%s"   …0x11951AC(EfileRoot)  ← 回退
```

若 `.xscn` 也走这条解析，则**从"场景列表/战役"正常加载时读到的是英文原版**，L9 的 241 个场景全部白干。
本次用户是通过 `Settings.cfg` 的 `LastOpen=EFILE_OLGWW2\SCENARIO\CanalAlbert.xscn` **显式路径**进入的，所以读到了成品 —— **不能据此判定安全**。

### 待做的验证（一次即可定性）

> 在游戏里用**场景列表**（而不是"继续最近存档"）打开一个已汉化场景，
> 看地图上悬浮显示的地名是**中文还是英文**。
> 中文 ⇒ 镜像不被读，可忽略；英文 ⇒ 镜像必须清理/同步。

### 修法（不论验证结果，都该做）

- 让 `TEXT-ZH\SCENARIO\*.xscn` 与 `SCENARIO\*.xscn` **同步为汉化版**（或直接删掉 TEXT-ZH 下这 241 个 `.xscn`，让它回退到 EfileRoot）；
- **凡"覆盖原文"的策略，必须检查是否有同名镜像在 TEXT-XX 下遮蔽**。

---

## 四、发现 C：`strings-zh.txt` 两处漏译

与官方西语版 `strings-es.txt` **逐行对齐**（819–900 行全部对应，**无串位** ✅）。
`strings-zh.txt` 共 917 行（es=916 / de=917 / hu=915 / pl=916 ⇒ 模板本身行数就有 ±2 浮动，917 合法）。

| 行 | 英文/西语 | 中文现状 | 判定 |
|---|---|---|---|
| **834** | `* Special attributes`（西语版**也是英文**） | `* Special attributes` | 模板级漏译 |
| **879** | 西语版已译 `* Lideres` | `* Leaders`（英文） | **我们的漏译** |

> 其余"纯 ASCII 行"经逐行核对，绝大多数是 `*` 开头的模板结构注释（`* Menu Main`、`* [terrain]` 等），**设计上不翻译、不显示**；`AT`/`FlaK`/`BB`/`AI` 等缩写按既定口径保留，**均非缺陷**。

**已排除的伪问题**：`\n` / `\r\n` 字面转义出现 40+ 处 —— 那是**引擎约定的换行转义**（整表统一使用，含 `\r\n` 组合），不是错误。

---

## 五、发现 D：`EFILE_OLGWW2\names.txt` 换行不一致

`LF=2263 / CRLF=2260` ⇒ **有 3 个孤立 LF**，与其余 2260 行的 CRLF 混用。
（该文件 21429 B、278 个高位字节，非纯 ASCII，属官方原版特性还是我们部署时引入，**待查**。）

---

## 六、待确认项

1. **单位面板标题「能力 AEZ+-=:#」**（图 4）。`能力` = `strings-zh.txt` 第 835 行，与西语 `Habilidades` 对齐；后随的 `AEZ+-=:#` 疑为**紧凑属性代码**（`AEZ` 与 `equip.txt` 的 `Sturmpioniere [AEZ]` 同源）或**符号字体丢失后的回退字形**。需再取一张更清晰的图或在实机悬停确认。
2. 图 4 右下 `S/S Exp 0 Ent 0 Fuel 80 Mov 2 Mnt 10 Ammx 8` 的**统计标签未汉化**（`Exp/Ent/Fuel/Mov/Mnt/Ammx`）—— 属 `strings-zh.txt` 之外的另一处表，需定位。

---

## 七、复核后确认**没问题**的部分（避免误判）

- `strings-zh.txt` 与官方译文**逐行对齐，无串位**；
- L1 地形名（顶栏「开阔地」）、L7 面板标签（`Efile 文件夹:`）、L6 弹窗标题（「阿尔贝特运河」）、
  L9 番号（「第 7步兵师 / 第1军」）、底部按钮（「工具」）**全部正确中文**；
- `.xscn` 汉化成品**结构未损**（英文残留 17∼31 个词，属番号/型号保留项）。

---

## 附：本次新增工具（`work\efile-nashornpbem\`）

| 脚本 | 用途 |
|---|---|
| `crop_shots.py` / `crop2.py` | 从实机截图裁剪 + 放大取证（Pillow，**系统 `C:\Python314` 有 Pillow 12.3**） |
| `ply_struct.py` | 解析 `.ply` 结构（语言块 / 分隔行 / 编码） |
| `inv_scenario.py` | 全库 `SCENARIO\` 扩展名清点 + `.ply` 三态分类 |
| `cmp_mirror.py` | `SCENARIO\` vs `TEXT-XX\SCENARIO\` 镜像逐文件 md5 比对 |
| `cmp_strings.py` | `strings-zh.txt` vs 官方 `strings-es/de/hu/pl` 逐行对照 |
| `find_nengli.py` | 定位串表具体行并对照 exe 内置表 |
| `_plyrefs.py` | 定位 exe 中 `.ply` 路径模板与其引用点 |
