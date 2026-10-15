# GCE `EFILE_GCE` 汉化风格指南（子代理必读）

> **efile 题材＝西班牙内战（1936–1939）＋ 二战东线（蓝色师/CTV）**。原文语言＝**西班牙语**
> （少量德语/意大利语编制名）。efile 名（`equip.cfg`/`efile.xml`）＝ **GCE（Guerra Civil Española）**。
> ⚠️ 本 efile **无任何既有交付件**（0% 起点）⇒ 口径由本文件**首次定义**，不再有「承上游」可依赖。

---

## 一、任务

把一批 **部队番号 / 编成名 / 地名 / 政治组织名** 译成简体中文。输入是 `.xscn` 尾部串区里的串。

## 二、输入 / 输出（严格）

- 输入：`D:\DSH\军事游戏汉化\work\gce\_gce_todo_partNN.txt`
  格式：`  频次|原文`（频次只用于排序，**不要抄进译文**）。
- 输出：`D:\DSH\军事游戏汉化\work\gce\_gce_dst_partNN.txt`
  格式：**每行一条译文**，与输入**逐行对应**（不要带序号、不要带原文）。
- UTF-8 **无 BOM**；**不要**表头、注释、空行、代码块。

## 三、编制名对照表（西语，务必按此译）

| 原文 | 译文 | 说明 |
|---|---|---|
| `ID` / `Div.` | 步兵师 / 师 | `105 ID` → 第105步兵师 |
| `BM` / `BI` / `Bon.` | 营 | `100 BM` → 第100营；`XIV BI` → 第14营 |
| `Bda.` | 旅 | `V Bda.` → 第5旅 |
| `Columna` | 纵队 | `Columna Durruti` → 杜鲁蒂纵队 |
| `Milicias` | 民兵 | `Milicias Vallecas` → 巴列卡斯民兵 |
| `Cen.` | 中队 | （`2 Cen. FET` → 第2中队） |
| `Agrupacion` | 集群 | |
| `Cuerpo` | 军 | |
| `Division` | 师 | `Division Tetuan` → 得土安师 |
| `Regimiento` / `Rgt.` | 团 | |
| `Batallon` | 营 | |
| `Brigada` | 旅 | |
| `Provisional` | 临时 | `12 ID (Provisional)` → 第12步兵师（临时） |
| `5ta` / `1a` / `2a` | 第5 / 第1 / 第2 | 西语序数词尾 |
| `Res.` | 预备 | |
| `Mixta` | 混成 | |

**番号一律用「第 + 阿拉伯数字 + 编制」**；罗马数字转阿拉伯（`XIV BI` → 第14营）。
**方括号里的纯代号原样保留**（`[V]` `[XV]` `[XVIII]` `[I]` `[II]`）——它们是**军团/地域编号**，不是部队番号。

## 四、通名（**必须译**，不得当专名音译）

| 原文 | 译文 |
|---|---|
| `Barricada` | 街垒 |
| `Pista de Aterrizaje` | 机场 |
| `Aerodromo` | 机场 |
| `Trincheras` | 战壕 |
| `Puente` | 桥 |
| `Rio X` | X河 |
| `Estacion` | 车站 |
| `Hospital` | 医院 |
| `Fabrica` | 工厂 |
| `Carretera de X` | X公路 |
| `Camino` | 道路 |
| `Monte X` / `Cerro X` | X山 / X丘陵 |
| `Sierra` | 山脉 |
| `Valle` | 谷地 |
| `Cota N` | N高地 |
| `Ciudad Universitaria` | 大学城 |
| `Castillo de X` | X城堡 |
| `Casa de X` / `Casa X` | X农舍 |
| `Cuartel General` | 司令部 |
| `Fortin` | 碉堡 |
| `Vado` | 渡口 |

> ⚠️ 教训：COMWW2 轮曾把通名 `Alambradas`（铁丝网）音译成「阿兰布拉达斯」——**本 efile 不得重犯**。

## 五、政治组织 / 派系（**保留原文缩写**，不加中文）

`CNT` `FAI` `UGT` `POUM` `PNV` `JSU` `PCE` `PSOE` `FAL` `FET` `Requete(s)` `Falange` `CEDA` `UGT`
—— 这些是**政党/工会的专有缩写**，中文里也通行用原文缩写，**原样保留**。
`FARE` 同为组织缩写，**保留原文**（不作音译、不展开猜测）。

## 六、方括号地名（**译中文，保留方括号**）

`[Madrid]`→`[马德里]` · `[Zaragoza]`→`[萨拉戈萨]` · `[Aragon]`→`[阿拉贡]` · `[Belchite]`→`[贝尔奇特]` ·
`[Africa]`→`[非洲]` · `[Ebro]`→`[埃布罗]` · `[Ceuta]`→`[休达]` · `[Norte]`→`[北部]` · `[Vitoria]`→`[维多利亚]` ·
`[Navarra]`→`[纳瓦拉]` · `[Teruel]`→`[特鲁埃尔]` · `[Brunete]`→`[布鲁内特]` · `[Jarama]`→`[哈拉马]` ·
`[Guadalajara]`→`[瓜达拉哈拉]` · `[Euzkadi]`→`[巴斯克]` · `[Varela]`→`[巴雷拉]`（人名，通行译名）

## 七、地名（通行中文译名优先）

`Madrid` 马德里 · `Barcelona` 巴塞罗那 · `Zaragoza` 萨拉戈萨 · `Aragon` 阿拉贡 · `Teruel` 特鲁埃尔 ·
`Belchite` 贝尔奇特 · `Brunete` 布鲁内特 · `Jarama` 哈拉马 · `Guadalajara` 瓜达拉哈拉 · `Ebro` 埃布罗河 ·
`Bilbao` 毕尔巴鄂 · `Oviedo` 奥维耶多 · `Toledo` 托莱多 · `Sevilla` 塞维利亚 · `Malaga` 马拉加 ·
`Vitoria` 维多利亚 · `Navarra` 纳瓦拉 · `Ceuta` 休达 · `Tetuan` 得土安 · `Manzanares` 曼萨纳雷斯河 ·
`Cinca` 辛卡河 · `Extremadura` 埃斯特雷马杜拉 · `Vallecas` 巴列卡斯 · `Perales` 佩拉莱斯 ·
`Mosquito` 莫斯基托 · `Villafranca` 比利亚弗兰卡 · `Pablo Iglesias` 巴勃罗·伊格莱西亚斯

## 八、硬规则

1. **结构与分隔符逐字保留**：`/`、`-`、`[ ]`、`( )` 的数量与顺序不变；原文空格位置尽量保留。
2. **人名**用通行译名（`Durruti` 杜鲁蒂 · `Varela` 巴雷拉 · `Miaja` 米亚哈 · `Rojo` 罗霍 ·
   `Modesto` 莫德斯托 · `Lister` 利斯特 · `Campesino` 坎佩西诺 · `Franco` 佛朗哥 · `Mola` 莫拉 ·
   `Yague` 亚圭 · `Cabanellas` 卡瓦内利亚斯）。
3. **拿不准一律保留原文，不要猜**；未知缩写（`T.O.C.E.` `FARE` `PNV`）原样保留。
4. 装备/飞机/舰船型号**保留原文**（`Bf-109` `CR.32` `T-26` `SB-2`）。
5. 不使用蔑称、旧称；不添加原文没有的解释性文字（**方括号内已有内容不得改写**）。
6. 中文内部不加多余空格。

## 九、交付前自检（必须做，并在回复里报告）

1. 输出行数 == 输入行数；
2. 每行译文非空、无 TAB、无换行、无 BOM；
3. `/`、`[`、`]`、`(`、`)` 的数量与输入对应行一致。

## 十、只回复一行

`part-NN 完成，共 N 行；自检通过`（**不要**贴译文内容）
