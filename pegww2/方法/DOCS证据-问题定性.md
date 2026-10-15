# PeG-WW2 问题定性：DOCS 证据（合成 MOD 原生缺陷，非汉化引入）

> 生成：2026-10-11 深夜 · 目的：回答用户「这些问题是这个合成 mod 版本本来就有的，还是不应该产生的」
> 依据目录：`D:\Program Files\PeG-WW2\DOCS\`（**只读**，未改动任何游戏文件）

## 一、DOCS 结构说明：本作是**多个第三方战役 MOD 的合成包**

| 证据 | 出处 |
|---|---|
| 主包 = Redball（Mark Kirby / Robert Mary）的 PeG-WW2 2.7c | `PeG-WW2 2.7 Read Me.txt`：「PEG-WW2 VERSION 2.7c (beta) · modifications by REDBALL · BETA RELEASE 22 September 2004」 |
| 每个战役是**独立第三方 MOD**，各自 zip 解到 `SCENARIO\` | 各 `PeG-WW2 XX Campaign Install.rtf`：「The scenarios and the campaign file (\*.scen, \*.txt, \*.cam) : Unzip all files included in the "XXX_v1.zip" in the SCENARIO directory of PeG WWII」 |
| 战役由**不同作者**制作/移植 | `Band of Brothers`（BoB）· `Deutsches Afrika Korps`（DAK）· `1st SS Leibstandarte Division`（LSSAH/LAH）· `Red Alert`（RA）· `Red Menace`（RM/RG）· `Reich Defence`（B7）· `Road to Berlin`（RTB）· `Romanian Struggle`（R7）· `Red World Order`（s00）· `Operation Sealion`（SL）· `For Stalin and Motherland`（ZS）· `The 7 PzrArmee…`（7Pzr）· `Mediterranean 46`（LH_ger46med）… |
| **场景名已被各 MOD 加前缀**以避免混淆 | `Band of Brothers\PeG-WW2 BoB Campaign Install.rtf`：「**Names of scenarios and campaign have been renamed and begin now with BOB**, this allows the player to uni[quely identify]…」 |

## 二、⭐ 直接解答用户疑问的两条「作者自述」

### 证据 A：「**所有场景都可以单独当独立场景玩**」—— 这是设计约定

- `British Campaign in Europe\BCampaign Information.rtf`：
  「**All scenarios can be played individually as "gray" scenarios, similarly to what is done in the original SSI campaigns.**」
- `Reich Defence\PG2_RDCampaign Information.rtf` · `Road to Berlin\PG2 RTB Campaign Information J Gabitto.rtf` ·
  `Romanian Struggle\PG2_RomCampaign Information.rtf`：**同样一句话**（原版 PG2 时代就有的约定）

⇒ 所以「每个战役场景另存一份、并让它进『进行场景』列表（`.SCN@0=0`）」**不是我们加的**，是**各 MOD 作者按 PG2 惯例刻意做的**。
本次出问题的 `lah_it_ngran`（列表版）↔ `LAH_IT_Gran`（战役版）正是这一约定的产物。

### 证据 B：⭐ **「我没有更新每一份会显示的注释文件」—— 作者自己承认文本未同步**

- `Waffen SS\PG2 Readme.txt`（John McNulty 原文，Robert Mary 移植）：
  > 「When creating this campaign **I didn't update every possible comments file displayed during the game** and
  > I couldn't create the voices that go along with the games "feedback"…」
- 同文件：「Note: these scenarios are **not designed to be played individually**, at least not in this version (1.1).」

⇒ **「文本文件与场景实际内容不同步」正是原作者承认的做法**。这与我们实测到的
「`lah_it_ngran_m.txt` 装的是卡朗唐/101 空降师简报、`_u.txt` 装的是海格力斯操作提示」
**完全吻合** —— 合成包里多来源资料被就地复用，注释/格名文件没跟着改。

## 三、实测复核：**英文原版就是坏的**（10 个格名表）

英文备份里这 10 个进列表场景的 `_m.txt`（引擎用它当**地图格名表**）**不含任何地名**：

| 场景 | 英文 `_m.txt` 非空行 | 内容（英文原文） |
|---|---:|---|
| `Red` | 1 | `Unfortunately, sir, you have not quite met the expec…` |
| `lah_it_ngran` | 20 | `Message from:-` / `Divisional Headquarters 101st Airborne.` / … |
| `malta` | 1 | `The Germans have pushed us back to our starting poin…` |
| `prok1-R` | 1 | `Wonderful victory General !!! You have defeated the …` |
| `saturn-R` | 3 | `Herr General, this defeat is out of the question…` |
| `savannah-R` | 1 | `Excellent work, Commander. You've got the Krauts hig…` |
| `thermopy` | 4 | `Welcome to Sevilla, General.` / `Your task is to lead…` |
| `viipuri` | 1 | `Superb performance, Herr General!  You have again br…` |
| `viipuri-R` | 1 | `Kyiv has been captured, and your SS PanzerKorps has …` |
| `windsor1-R` | 2 | `Kiev encirclement - Romny September1941 V` / `You have successfully…` |

⇒ **英文玩家进这些场景，地图同样没有地名。** 与汉化无关。

## 四、排除「汉化导致偏移」的四重证据

| # | 证据 |
|---|---|
| 1 | `.scn` 的文本字段是**定长 20 字节 + NUL 填充**，**无偏移量概念**，长度变化不会挤到别的字段 |
| 2 | 全库**只有 2 个 `.scn` 被改**（`ATM_scn29`/`ATM_scn34`），**各 1 字节**、位置 0（`@0` 进列表标志） |
| 3 | 这 10 条的 `@11210 地图` / `@11329 说明` / `@11349 标志` **全为原值**，`.scn` 未改（无 `.orig-backup`） |
| 4 | `_m.txt` **英文与中文行数逐条一致**（1/1、26/26、2/2、4/4…），我们只替换行内文字，**未增删行、未改结构** |

## 五、结论（一句话）

> **这些问题是「合成 MOD 版本本来就有的」** —— 由多个第三方 PG2 战役移植而来，原作者按 PG2 惯例额外导出「独立场景版」，
> 但（作者自述）**没有同步每一份注释/格名文件**，导致这批「独立场景版」的**格名表/单位表装的是别的战斗的文本**。
> **不是汉化产生的，也不是汉化应当修复的**；汉化只做语言转换，忠实保留了原状。
> 若我们修正它，属于**改良**（而且比只换语言更进一步），须显式记账并声明偏离原版。
