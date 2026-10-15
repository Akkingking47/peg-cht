# `Bon.`/`Bn` → 「第76营」对位表与修法候选（P1-4 / E-1 前半 · 只读取证）

> 本文件为**取证产出**。未修改任何译文、词库、映射表、生成器。
> **修法选择是用户裁定项**——本文只列事实与候选利弊，不作推荐、不代替决策。

---

## 一、取值方法与实际命令行

工作目录：`D:\DSH\军事游戏汉化`

```powershell
$env:PYTHONIOENCODING='utf-8'
python work\_sync-audit\probe_bon76.py
```

- 退出码 0，**无报错**。控制台须设 `PYTHONIOENCODING=utf-8`，否则中文显示为 mojibake（不影响判定，但会影响人工核对）。
- 探针只读，不写文件。

**探针实现要点**（`work\_sync-audit\probe_bon76.py`）：
- `sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\efile-nashornpbem")` → `from apply_residual import parse`
- `ORIG = <WS>\backup\ORIGINAL-EFILE_OLGWW2\SCENARIO`（英文原文）
- `CUR  = D:\OpenPG2\EFILE_OLGWW2\SCENARIO`（当前交付中文）
- `FILES = ["GCN0.xscn","GCN2.xscn","GCN3.xscn","GCN4.xscn","GCN7.xscn"]`
- 过滤条件：`"Bon" in EN or "76" in ZH` → **两个子串或**

### 探针输出摘要（38 行 / 4 个文件段）

| 文件 | 输出行数 | 其中「EN 有 Bon 且 ZH 含 76」 | 其中「EN 有数字 Bon，ZH 正确」 |
|---|---|---|---|
| GCN0.xscn | 4 | 2（g1#34、g1#35） | 2（g1#37、g1#38） |
| GCN2.xscn | 27 | 27 | 0 |
| GCN3.xscn | 1 | 1（g1#1） | 0 |
| GCN4.xscn | 9 | 1（g1#78） | 8（g1#57/79/97/162-166） |
| GCN7.xscn | 0 | —（无匹配或文件缺失） | — |

**对照证据（英文带数字时译文正确）**：

```
GCN0.xscn g1#38  EN=6 Bon./2 MBda./2 Bda.   ZH=第6营/第2 MBda./第2旅
GCN4.xscn g1#57  EN=8 Bon./1 Bda./[1Agrp.]  ZH=第8营/第1旅/[1Agrp.]
GCN4.xscn g1#79  EN=80 Bon./-/[XIV]         ZH=第80营/-/[XIV]
GCN4.xscn g1#162 EN=78 Bon./-/[XIV]         ZH=第78营/-/[XIV]
```

⇒ 故障只在 `Bon.` **前面没有数字**时出现；此时被填入一个**凭空**的「76」。

---

## 二、全量对位表

> 统计口径用全量重扫（脚本内联遍历 `ORIG` 下全部 **187** 个 `.xscn`，与 `CUR` 逐文件对齐；`CUR` 同目录亦为 187 个 `.xscn`）。
> 组别判定：`Bon.`/`Bn` 前 3 字符内**无数字** ⇒ 不该有番号。

### A 组 — 西语裸 `Bon.`（Batallón）被填「第76营」：**37 槽 / 33 个不同键 / 6 个文件**

| 文件 | 槽位 | 英文原文 | 当前中文译文 | 词库当前值 |
|---|---|---|---|---|
| GCN0.xscn | g1#34 | `Bon. Thaelmann` | 第76营 台尔曼 | 台尔曼营 ✅ |
| GCN0.xscn | g1#35 | `Bon. Commune de Paris` | 第76营 巴黎公社 | 巴黎公社营 ✅ |
| GCN1.xscn | g1#45 | `Bon. CNT No.4` | 第76营 CNT 第4号 | 全国劳工联盟第4营 ✅ |
| GCN1.xscn | g1#47 | `Bon. CNT No.5` | 第76营 CNT 第5号 | 全国劳工联盟第5营 ✅ |
| GCN1.xscn | g1#50 | `Bon. Caz. Asturias No.1` | 第76猎兵营 阿斯图里亚斯 第1号 | 阿斯图里亚斯猎兵第1营 ✅ |
| GCN1.xscn | g1#51 | `Bon. Caz. Gijon No.2` | 第76猎兵营 希洪 第2号 | 希洪猎兵第2营 ✅ |
| GCN1.xscn | g1#52 | `Bon. Caz. Langreo No.3` | 第76猎兵营 兰格雷奥 第3号 | 兰格雷奥猎兵第3营 ✅ |
| GCN2.xscn | g1#40 | `Bon. CNT No.5` | 第76营 CNT 第5号 | 全国劳工联盟第5营 ✅ |
| GCN2.xscn | g1#42 | `Bon. Caz. Asturias No.1` | 第76猎兵营 阿斯图里亚斯 第1号 | 阿斯图里亚斯猎兵第1营 ✅ |
| GCN2.xscn | g1#43 | `Bon. Caz. Gijon No.2` | 第76猎兵营 希洪 第2号 | 希洪猎兵第2营 ✅ |
| GCN2.xscn | g1#44 | `Bon. Caz. Langreo No.3` | 第76猎兵营 兰格雷奥 第3号 | 兰格雷奥猎兵第3营 ✅ |
| GCN2.xscn | g1#48 | `Bon. CNT No.1` | 第76营 CNT 第1号 | 全国劳工联盟第1营 ✅ |
| GCN2.xscn | g1#49 | `Bon. Muniz` | 第76营 Muniz | 穆尼斯营 ✅ |
| GCN2.xscn | g1#50 | `Bon. IR Azana` | 第76营 IR Azana | 伊尔·阿萨尼亚营 ✅ |
| GCN2.xscn | g1#51 | `Bon. Cienfuegos` | 第76营 西恩富戈斯 | 先丰营 ✅ |
| GCN2.xscn | g1#52 | `Bon. Jose Florez` | 第76营 Jose Florez | 何塞·弗洛雷斯营 ✅ |
| GCN2.xscn | g1#53 | `Bon. Llaneza` | 第76营 Llaneza | 利亚内萨营 ✅ |
| GCN2.xscn | g1#54 | `Bon. Dutor No.1` | 第76营 Dutor 第1号 | 杜托尔第1营 ✅ |
| GCN2.xscn | g1#55 | `Bon. A. de la Fuente` | 第76营 A. de la Fuente | A.德拉富恩特营 ✅ |
| GCN2.xscn | g1#56 | `Bon. CNT No.2` | 第76营 CNT 第2号 | 全国劳工联盟第2营 ✅ |
| GCN2.xscn | g1#58 | `Bon. M. Fernandez/[Sograndio]` | 第76营 M. 费尔南德斯/[索格兰迪奥] | **第76营 M. 费尔南德斯/[索格兰迪奥]** ⛔ |
| GCN2.xscn | g1#59 | `Bon. CNT No.9/[Sograndio]` | 第76营 CNT 第9号/[索格兰迪奥] | **第76营 CNT 第9号/[索格兰迪奥]** ⛔ |
| GCN2.xscn | g1#60 | `Bon. F. Lopez/[Sograndio]` | 第76营 F. Lopez/[索格兰迪奥] | **第76营 F. Lopez/[索格兰迪奥]** ⛔ |
| GCN2.xscn | g1#61 | `Bon. D. Rodriguez/[Sograndio]` | 第76营 D. 罗德里格斯/[索格兰迪奥] | **第76营 D. 罗德里格斯/[索格兰迪奥]** ⛔ |
| GCN2.xscn | g1#66 | `Bon. Chuno/[Manjoya]` | 第76营 Chuno/[曼霍亚] | **第76营 Chuno/[曼霍亚]** ⛔ |
| GCN2.xscn | g1#67 | `Bon. J. Naves/[Manjoya]` | 第76营 J. Naves/[曼霍亚] | **第76营 J. Naves/[曼霍亚]** ⛔ |
| GCN2.xscn | g1#68 | `Bon. D.G. Castro/[Manjoya]` | 第76营 D.G. Castro/[曼霍亚] | **第76营 D.G. Castro/[曼霍亚]** ⛔ |
| GCN2.xscn | g1#69 | `Bon. Galicia/[Manjoya]` | 第76营 加利西亚/[曼霍亚] | **第76营 加利西亚/[曼霍亚]** ⛔ |
| GCN2.xscn | g1#72 | `Bon. Sama/[S.Esteban]` | 第76营 Sama/[圣埃斯特班] | **第76营 Sama/[圣埃斯特班]** ⛔ |
| GCN2.xscn | g1#73 | `Bon. A. Naves/[S.Esteban]` | 第76营 A. Naves/[圣埃斯特班] | **第76营 A. Naves/[圣埃斯特班]** ⛔ |
| GCN2.xscn | g1#75 | `Bon. Daniel Secades/[Lugones]` | 第76营丹尼尔·塞卡德斯/[卢戈内斯] | **第76营丹尼尔·塞卡德斯/[卢戈内斯]** ⛔ |
| GCN2.xscn | g1#77 | `Bon. Sotrondio/[Cayes]` | 第76营索特龙迪奥/[卡耶斯] | **第76营索特龙迪奥/[卡耶斯]** ⛔ |
| GCN2.xscn | g1#78 | `Bon. Larranaga` | 第76营 Larranaga | 拉腊尼亚加营 ✅ |
| GCN2.xscn | g1#79 | `Bon. Meabe` | 第76营 Meabe | 梅亚贝营 ✅ |
| GCN3.xscn | g1#1 | `Bon./[Col. Iglesias]` | 第76营/[伊格莱西亚斯上校] | **第76营/[伊格莱西亚斯上校]** ⛔ |
| GCN4.xscn | g1#78 | `Bon. G. Hernandez/-/[XIV]` | 第76营 G. 埃尔南德斯/-/[XIV] | **第76营 G. 埃尔南德斯/-/[XIV]** ⛔ |
| GCN6.xscn | g1#17 | `Bon. IdM/''A'' Div./[XIV]` | 第76营 IdM/''A''师/[XIV] | **第76营 IdM/''A''师/[XIV]** ⛔ |

**A 组计数复核**：GCN0 2 + GCN1 5 + GCN2 27 + GCN3 1 + GCN4 1 + GCN6 1 = **37 槽**。
33 个不同键（GCN1 与 GCN2 共享 4 键：`Bon. CNT No.5`、`Bon. Caz. Asturias No.1`、`Bon. Caz. Gijon No.2`、`Bon. Caz. Langreo No.3`）。

### B 组 — 法语裸 `Bn`/`Bon` 同族错译：**7 槽 / 7 键 / 6 个文件**（探针**完全未覆盖**）

| 文件 | 槽位 | 英文原文 | 当前中文译文 | 词库当前值 |
|---|---|---|---|---|
| 18days2.xscn | g1#20 | `Bn CyFr Limbourg / I CA` | 第76工兵营 塞法尔·林堡 / 第1军 | **第76工兵营 塞法尔·林堡 / 第1军** ⛔ |
| 18days3.xscn | g1#7 | `Bn Moto ChA / Gpt K` | 第76摩托化营 ChA / K集群 | **第76摩托化营 ChA / K集群** ⛔ |
| 18days6.xscn | g1#18 | `Bn Pon` | 第76工兵营 | **第76工兵营** ⛔ |
| 18days7.xscn | g1#0 | `Bn Mo ChA / CC` | 第76工兵营 Mo ChA / 骑兵军 | **第76工兵营 Mo ChA / 骑兵军** ⛔ |
| 18days8.xscn | g1#102 | `Bn Gn / 1 DChA / VI CA` | 第76工兵营 Gn / 第1DChA / 第6军 | **第76工兵营 Gn / 第1DChA / 第6军** ⛔ |
| 18days11.xscn | g1#203 | `Bon Pontonniers d'Armée` | 第76架桥工兵营 | 集团军架桥营 ✅ |
| CanalAlbert.xscn | g1#51 | `Bon CyFr Limbourg / - / I CA` | 第76工兵营 塞法尔·林堡 / - / 第1军 | **第76工兵营 塞法尔·林堡 / - / 第1军** ⛔ |

**合计（A + B）＝ 44 槽 / 40 键 / 13 个 `.xscn`**。

### C 组 — 同含「76」但**不属于** Bon 族：2 槽（另案，勿并入本修法）

| 文件 | 槽位 | 英文原文 | 当前中文译文 |
|---|---|---|---|
| RSBUR03.xscn | g1#61 | `HQ/LVXI Army` | HQ/第76集团军 |
| RSCHI06.xscn | g1#40 | `HQ/LVXI Army` | HQ/第76集团军 |

`LVXI` 不是合法罗马数字，疑为 `LXI`(61) 的另一次错位 ⇒ 属**不同 bug 族**，仅在统计时区分。

---

## 三、词库侧现状分档（决定修法工作量）

`glossary\standard-glossary.tsv` 与 `glossary\layers\common-glossary.tsv` 实测：

| 分档 | 键数 | 含义 |
|---|---|---|
| 词库**已正确**（无「76」），仅交付 `.xscn` 未同步 | **19** | A 组 18 + B 组 1（`Bon Pontonniers d'Armée`） |
| 词库与交付**双错** | **21** | A 组 15 + B 组 6 |
| 合计 | 40 | |

- A 组「双错」的 15 键**全部**是含 `/[地名]` 后缀的键。
- 主词库中 `第76营`/`第76猎兵营` 命中 **15 键**，`scope` 全为 `EFILE_OLGWW2`，**`PEGWW2` 命中 0 行** ⇒ 本缺陷目前是 **OLGWW2 单 efile 问题**。
- 例：`glossary\standard-glossary.tsv` 中 `Bon. Thaelmann → 台尔曼营`（UNIT/LOCKED/txt+xscn），而交付 xscn 仍是 `第76营 台尔曼`。
- 冲突留痕：`work\glossary\_regen-catfix\glossary-conflicts.tsv:798  Bon. Thaelmann  EFILE_OLGWW2  台尔曼营  台尔曼营×1 | 第76营 台尔曼×1  REAL  PLACE  2`
- **漂移登记缺口**：以 `key\t` 前缀在 `glossary\layers\common-drift.tsv` 中检索这 40 键，命中 **0 行** ⇒ docs §五 的「漂移 196 条」表未覆盖本族，修复后不能靠该表验收。

---

## 四、根因与传播链（取证所得，非推测）

| 层 | 事实 |
|---|---|
| 词素层**正确** | `work\xscn\master-words.tsv:195  Bon.	营`；`work\xscn\master-words.tsv:185  Bn	营` |
| 词库层**部分已修正** | `glossary\standard-glossary.tsv`（19 键正确）；`glossary\layers\common-glossary.tsv`（15 键仍错） |
| **「76」首次出现处** | `work\xscn\zh\part-14.tsv:137  Bon. Thaelmann	第76营 台尔曼`；同文件 `:72`～`:76`、`:104`～`:105` 承载 B 组 6 键 |
| 汇聚 | `work\xscn\master-glossary.tsv:39532  Bon.	营`（词素正常）、`:39645  Bon. Thaelmann	第76营 台尔曼	xscn	3` |
| 原子映射 | `work\atomic\atomic-xscn-map.tsv:5818…`（`Bon. Thaelmann	第76营 台尔曼	cross`）、`work\atomic\_xscn-crossmap.json:5818…` |
| 下游副本 | `work\gce\gce-xscn-map.tsv:798`、`work\gce\userscen-zh.tsv:1032`、`work\basekorp\_xscn-crossmap.json:13601` |
| 交付 | `D:\OpenPG2\EFILE_OLGWW2\SCENARIO\*.xscn` |
| 正确参照 | `work\basekorp\txt-precedent.tsv:9364  Bon. Thaelmann	台尔曼营	1	OLGWW2` |

⇒ 错值由**句级译文层**（`work\xscn\zh\part-*.tsv`）注入，被当成「正确译文」一路固化到交付。
⇒ 因此「改词库」不足以修复：**19 键的词库早已是对的，是交付侧没重铺**。

英文原文出处（`backup\ORIGINAL-EFILE_OLGWW2\SCENARIO`，GBK，行号实测）：
`gcn0.txt:22,49,50` · `gcn1.txt:39,41,42,43,44` · `gcn2.txt:39,42,43,44,48～56,58～61,65～68,72,73,76,78,105,106` ·
`gcn3.txt:51` · `gcn4.txt:61,62,203,204,205,209` · `gcn6.txt:36`

---

## 五、候选修法对比（**修法选择是用户裁定项**；以下只列事实与利弊）

### 候选 1 — 一律改「营」：按词库既有值逐键回填（`Bon.`=营 / `Bn`=营）

| 项 | 内容 |
|---|---|
| 影响槽位 | A 组 37 + B 组 7 = **44 槽**（若只做 A 组则 37 槽） |
| 影响 efile/文件 | 交付层 13 个：`GCN0/GCN1/GCN2/GCN3/GCN4/GCN6/18days2/18days3/18days6/18days7/18days8/18days11/CanalAlbert`（均在 `D:\OpenPG2\EFILE_OLGWW2\SCENARIO\`） |
| 影响词库 | 仅 21 个双错键需改；19 个已正确键无须动 |
| 影响中间层 | `work\xscn\zh\part-*.tsv`（源头）· `work\xscn\master-glossary.tsv` · `work\atomic\atomic-xscn-map.tsv` · `work\atomic\_xscn-crossmap.json` · `work\gce\gce-xscn-map.tsv` · `work\gce\userscen-zh.tsv` · `work\basekorp\_xscn-crossmap.json` |
| 风险点 | ① xscn 槽**定长**，须等长替换或走既有 materialize 管线；② 「词干残留拉丁文」（`Muniz`/`Lopez`/`Chuno`/`Naves`…）不在本族修复范围，改后仍为「穆尼斯营」等；③ 属**已交付内容回改**，需重新出包；④ `scn20B`(20 bytes)／`ui5`(5 汉字) 门须复跑（本修法中文变**短**，方向有利，但仍需实测确认） |
| 参考优点 | 与词库 19 个正确键一致；与「英文带数字」参照例（`8 Bon.`→`第8营`）风格统一 |
| 参考代价 | 中文侧丢失「缩写字面」信息；需改动 13 个已交付场景文件 |

### 候选 2 — 按上下文区分：`Bon.`（西语 Batallón）＝营 vs `Bn`（法语 Bataillon）＝营

| 项 | 内容 |
|---|---|
| 影响槽位 | 与候选 1 **相同**（44 槽），差异仅在分组处理 |
| 影响文件 | 同候选 1 |
| 风险点 | 本仓实测**两者已同族同错**（`master-words.tsv` 中 `Bon.`→营、`Bn`→营 均为「营」），且 A 组（西语 GCN 系）与 B 组（法语 18days/CanalAlbert）本就分属不同文件 ⇒ 区分后**中文结果完全相同** |
| 事实结论（非推荐） | 现有仓库数据**不支持**「必须区分」这一前提；该分支不产生额外收益，只增加一次分类判断 |

### 候选 3 — 保留可追溯性并加注（如 `第76营(Bon. Thaelmann)` / `营(Bon.)` / `X营（Bon.）`）

| 项 | 内容 |
|---|---|
| 影响槽位 | 44 槽（同） |
| 影响文件 | 同候选 1，另需决定注记格式的统一规则 |
| 风险点 | ① **槽位超限**：中文侧显著变长，`scn20B`(20 bytes) 阈值几必被击穿（docs §五 记现有超限 0 条），`ui5`(5 汉字) 现有 73 条会进一步增加；② xscn 槽定长 ⇒ 超限可能截断/溢出；③ 与全仓风格不一致（全仓仅 `Raemcke` 那类有散文双语注特例） |
| 参考优点 | 保留原文可追溯性，便于后续复核 |
| 参考代价 | 超限与截断风险，且需为 44 槽逐一定制注记 |

> **以上三选一（或组合）由用户裁定。** 本文不给出推荐排序。

---

## 六、与 docs\52 §六-3 记录的差异（逐条）

| docs\52 原文 | 实测 | 判定 |
|---|---|---|
| 「GCN0/GCN2/GCN3/GCN4 共 **25 槽**」 | A 组 **37 槽 / 6 文件**；仅这 4 个文件也已是 2+27+1+1 = **31 槽** | ❌ **低估**，且漏 GCN1(5 槽)、GCN6(1 槽) |
| 「GCN2.xscn g1#34  EN='Bon. Thaelmann'」 | `Bon. Thaelmann` 在 **GCN0.xscn g1#34**；GCN2 无 Thaelmann | ❌ 文件归属错误（槽号对、文件错） |
| 「GCN2.xscn g1#42 EN='Bon. Caz. Asturias No.1'」 | 实测一致 | ✅ |
| 「GCN4.xscn g1#78 EN='Bon. G. Hernandez/-/[XIV]'」 | 实测一致 | ✅ |
| 「GCN3.xscn g1#1 EN='Bon./[Col. Iglesias]'」 | 实测一致 | ✅ |
| 「GCN4.xscn g1#57 / g1#79 带数字正确」 | 实测一致（另测得 g1#97、g1#162-166 亦正确） | ✅ |
| 「词库里落成 **20 个** `…/[地名]` 键」 | 主词库含 `第76营` 的键 **15 个**，且**全部**含 `[…]` | ❌ 数量不符（15 ≠ 20） |
| 未提及 `Bn`（无数字）同族错译 | **7 槽**（18days×6 + CanalAlbert×1） | ➕ docs 漏记 |
| 未提及 `HQ/LVXI Army` → `第76集团军` | **2 槽**（RSBUR03/RSCHI06） | ➕ docs 漏记，但**属另案** |
| 「修法＝用词库 .txt 层的正确写法逐槽改写」 | 该路径对 19 键可行（词库已正确）；对 21 个双错键需**先改词库再重铺** | ⚠️ 改为**分组**处理更准确 |

---

## 七、「另外 4 项家族级译名分歧」定位（验收项 5）

**结论：不在 `probe_bon76.py` 覆盖范围内。**
探针过滤条件是 `EN 含 "Bon"` 或 `ZH 含 "76"`；下列 4 族的关键词（`African D` / `Saharian` / `Imperiali` / `Raemcke`）与「76」无关，故探针**产出 0 行**，须另起探针。

| # | 分歧族 | 分歧内容 | 定位（文件 : 行号 / 命中行数） |
|---|---|---|---|
| 1 | `African D` | `第N非洲师`（12 键）vs `第N南非师`（6 键）；史实＝South African Division ⇒ 南非师 | `glossary\layers\common-glossary.tsv`(34 行) · `glossary\layers\common-drift.tsv`(10 行) · `glossary\layers\scope-diff.tsv`(16 行) · `glossary\layers\converge-list.tsv`(10 行) · `glossary\standard-glossary.tsv`(18 行) · `glossary\evidence\regen-ww2-scn-map.tsv:4674,8735,8737,8738,8739,8740,8743,8744,8745,8746,8747,8748` |
| 2 | `Saharian Grouping` | `撒哈拉战斗群`(1 键) vs `撒哈拉集群`(4 键，含裸键) | `glossary\layers\common-glossary.tsv:9738`(`Saharian Grouping`→撒哈拉集群/PLACE) · `:19515`(`290 R/…`→第290团/撒哈拉战斗群) · `:19516`(→第290团/撒哈拉集群) · `:20844`/`:20845`(`350 R/…`) · `:25878`/`:25879`(`atB/…`) · `glossary\layers\common-drift.tsv:278` · `glossary\layers\scope-diff.tsv`(1 行) · `glossary\layers\converge-list.tsv`(1 行) · `glossary\standard-glossary.tsv`(6 行) · `regen-ww2-scn-map.tsv:4779,4780,4781,8926` |
| 3 | `Imperiali D/XXX/V` | `第5集团军`(1 键) vs `第5军`(2 键)；另 `帝国师` vs `因佩里亚利师` | `glossary\layers\common-glossary.tsv:16181`/`:16182`(`15 B/…`→第15营/因佩里亚利师/第30军/第5集团军) · `:19866`/`:19867`(`3 G/…`→第3团/因佩里亚利师) · `:23048`/`:23049`(`6 R/…`→第6团/帝国师 vs 第6团/因佩里亚利师) · `glossary\layers\common-drift.tsv:53` · `glossary\layers\scope-diff.tsv:409` · `glossary\layers\converge-list.tsv:408` · `glossary\standard-glossary.tsv`(3 行) · `regen-ww2-scn-map.tsv:3101,3102,3103` |
| 4 | `Raemcke` | `拉姆克旅`(.txt 层) vs `雷姆克旅`(.xscn 层) | `glossary\layers\common-glossary.tsv`(16 行) · `glossary\layers\common-drift.tsv:298`(`5 R/Raemcke Bde./[DAK]`：雷姆克旅 vs 拉姆克旅) · `:312`(`Burkhardt/…`) · `:315`(`Heyte/…`) · `:316`(`Huebner/…`) · `glossary\layers\scope-diff.tsv`(7 行) · `glossary\layers\converge-list.tsv`(6 行) · `glossary\standard-glossary.tsv`(10 行) · `regen-ww2-scn-map.tsv:1771,2293,3091,3092,4565,8469` |

---

## 八、工作区纪律证据

- 本任务**只读**运行既有脚本；**未**修改任何译文 / 词库 / 映射表 / 生成器；**未**执行 `git commit` / `checkout` / `reset`；**未**启动游戏。
- 本任务唯一新增文件：`D:\DSH\军事游戏汉化\work\_sync-audit\bon76-对位表.md`（本文件）。
- `.gitignore:22` 为 `!/work/**/*.md` ⇒ `work/` 下 `.md` 入版本，故本文件会以 `??` 出现在 `git status --short`；`work/` 下 `.tsv`/`.log` 等默认被忽略。
- ⚠️ **工作区在取证期间已被并发会话改动**（非本任务产出）：15:22 时 `git status` 为 `M .gitignore` + `M docs/59-…md`；15:28 前后出现新提交 `9251dba docs(68-A-2/D-3): …`，`git status` 一度变为 `M glossary/evidence/layer-gate.txt` 等 7 项，再变为 `M glossary/evidence/layer-gate.txt` + `?? requirements.txt`。
  ⇒ 判定「只新增了允许的产出文件」时**不能只看一次 status**，须以本任务的文件清单为准。本任务未触碰上述任何条目。

## 九、复算命令（本文件全部数据）

```powershell
$env:PYTHONIOENCODING='utf-8'
cd D:\DSH\军事游戏汉化

# 探针（本任务书指定）
python work\_sync-audit\probe_bon76.py

# 全量重扫（本文 A/B/C 组统计口径＝遍历 ORIG 下 187 个 .xscn 与 CUR 逐槽对齐）
#   判定：EN 含 "Bon"/"Bn" 且前 3 字符内无数字
#   依赖：work\efile-nashornpbem\apply_residual.py 的 parse()
# 词库侧分档（对 40 键逐一查 glossary\standard-glossary.tsv 与 glossary\layers\common-glossary.tsv）
```

> 本文的 A/B/C 组统计由**内联全量重扫**得出（非探针输出），探针仅覆盖其 `FILES` 名单中的 5 个文件。
