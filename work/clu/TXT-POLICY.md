# EFILE_Clu 场景 `.txt` 层口径（本批子代理必读）

`EFILE_Clu` 的 `SCENARIO\*.txt`（70 个）是**三层混装**：
① `armclu-NN.txt` 等＝**标签清单**（`PzW 811`、`MG/PzW 761` 这类部队/地名标签，由 `.xscn` 表覆盖，
   落到本清单的极少）；② `*-op.txt` ＝**任务简报**；③ `*-all.txt` ＝**战后战报**。
本轮译②③的散文（及少数标签残留）。

输入每行**一个原文串**（`work\clu\txt-chunks\chunk-NN.tsv`），输出**逐行一一对应的中文**
（`work\clu\txt-zh\part-NN.tsv`，`原文<TAB>译文`）。

---

## 一、总则

- **逐行对应**：输出行数 == 输入行数；一行＝一段，**照译成一行，不拆行**。
- **全角标点**（，。！？：；（））；原文 `'X'`/`"X"` → `「X」`。
- 日期：`01/30/1945`（美式 月/日/年）→ `1945年1月30日`。
- ⚠️ **十六进制格坐标原样保留半角**：`(09,07)`、`(12,2)`、`(05,14)` —— 这是玩法数据，不得译、不得改全角。
- 对玩家说话用「您」；不加原文没有的解释、不写译注。
- **保留不动**：`/`、`-` 分隔线、`*` 号、`#N` 编号、罗马数字、装备型号（`PzW 811`、`B-IV`、`StuG`）。

## 二、套语（照此统一）

| 原文 | 译 |
|---|---|
| `Victory conditions:` | `胜利条件：` |
| `You have to hold A (09,07) and B (12,2) for 5 turns.` | `您必须守住 A (09,07) 和 B (12,2) 共 5 回合。` |
| `Then a withdrawal is possible.` | `之后可以撤退。` |
| `New units have strength 8 and experience 25.` | `新单位强度 8、经验 25。` |
| `Reinforcements will come in.` | `增援会到达。` |
| `Wait for the escape unit.` | `等待突围单位。` |
| `No proto.` | `无原型装备。` |
| `Next scenario:` | `下一场景：` |
| `Next scenario: 7 deploy hexes.` | `下一场景：7 个部署格。` |
| `Special note:` | `特别提示：` |
| `Historical background:` | `历史背景：` |
| `Historical outcome:` / `OUTCOME` | `历史结局：` |
| `The Soviets lost approximately 2500 killed in action.` | `苏军阵亡约 2500 人。` |
| `the Wehrkreis III Brandenburg (military district)` | `第3军区（勃兰登堡，军区）` |
| `Ostwall` | `东方壁垒` |

## 三、军事/历史术语

- 编制：`Division`→师 · `Brigade`→旅 · `Regiment`→团 · `Battalion`→营 · `Corps`→军 ·
  `Army`→集团军 · `Army Group`/`Heeresgruppe`→集团军群 · `Volkssturm`→人民冲锋队 ·
  `Festungsfront`→筑垒地域 · `Fortified Area`→筑垒地域 · `bridgehead`→桥头堡 · `VH`→胜利点 ·
  `pocket`→包围圈 · `relief`→解围 · `counteroffensive`→反攻。
- 地名/人名用通行译名（本 efile 常用表见 `CLU-POLICY.md`：`Oder`→奥得河 · `Küstrin`→屈斯特林 ·
  `Seelow Heights`→泽洛高地 · `Halbe`→哈尔贝 · `Frankfurt an der Oder`→奥得河畔法兰克福 ·
  `Wenck`→文克 · `Steiner`→施泰纳 · `Kurmark`→库尔马克 · `Langkeit`→朗凯特 · `Tornio`→托尔尼奥；
  `Gulf of Bothnia`→波的尼亚湾 · `Kemijoki`→凯米约基河 · `Lapland`→拉普兰）。

## 四、格式与回报

- UTF-8 **无 BOM**；行尾 `\n`；每行一条、逐行对应；无序号/表头/空行/代码块。
- **输出必须能被 GBK 编码**（不得含 `ä ö ü ß é ñ å ø` 等；变音符折写或译成汉字）。
- 每行恰好 1 个 TAB，TAB 前与输入**逐字符相同**。
- 完成后**只回复两行**：`part-NN 完成，共 M 行；自检通过` 与 `照抄保留 N 条：<原文列表>`。
