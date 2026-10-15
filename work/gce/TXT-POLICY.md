# GCE 场景 `.txt` 层翻译口径（子代理必读）

> efile＝`EFILE_GCE`，题材＝**西班牙内战（1936–39）＋意大利志愿军团（CTV）**。
> 本层＝场景**简报 / 胜负报文 / 决议屏**文本。先读 `work\gce\POLICY.md`（建制与通名口径），本文只加本层特有的东西。

---

## 一、任务与输入输出（严格）

- 输入：`D:\DSH\军事游戏汉化\work\gce\_txt_todo_partNN.txt`
  格式：`   频次|原文`（**频次只用于排序，不要抄进译文**）。
- 输出：`D:\DSH\军事游戏汉化\work\gce\_txt_dst_partNN.txt`
  格式：**每行一条译文，与输入逐行对应**（不要序号、不要原文、不要表头、不要空行、不要代码块）。
- 编码：**UTF-8 无 BOM**；单个文件内一律 `\n` 换行。
- ⚠️ 一条输入＝一条输出（一个输入行可能是一整段简报，照译成一整行，**不要拆行**）。

## 二、⭐ 本层最重要的特殊性：简报是「西语段 + 英译段」双段

`_txt_todo_*` 里同一场景会出现**两批内容相同的行**：

- 一批是**西语原文**（`Buenos dias General. Es un placer...`）；
- 另一批是它的**英译**（`Buenos dias General.  It is my pleasure to put you in command...`）。

**用户已裁定：两段都译成中文**。所以两批都要给中文，且**用词必须一致**
（同一个场景的同一件事，西语段与英语段的译文要能对上；人名/地名/编制名尤其不能两边打架）。

## 三、⭐ 跨层一致（硬要求）

译文里出现**人名 / 地名 / 部队番号 / 编制名**时，**先在**
`D:\DSH\军事游戏汉化\work\gce\gce-xscn-map.tsv`（两列 `src<TAB>dst`，1675 条）
里查一遍（src 列**精确匹配**，注意有的键带 `[方括号]`）。**查到就必须用它的 dst**——
那份表已经落进游戏文件的 `.xscn` 层，两处不一致玩家会直接看出来。

常用对照（节选，查表为准）：

| 西语/英语 | 中文 |
|---|---|
| `Madrid` · `Toledo` · `Zaragoza` · `Teruel` · `Belchite` · `Brunete` · `Guadalajara` · `Bilbao` · `Oviedo` · `Sevilla` · `Malaga` · `Vitoria` · `Navarra` · `Aragon` · `Ebro` · `Jarama` · `Ceuta` · `Tetuan` | 马德里 · 托莱多 · 萨拉戈萨 · 特鲁埃尔 · 贝尔奇特 · 布鲁内特 · 瓜达拉哈拉 · 毕尔巴鄂 · 奥维耶多 · 塞维利亚 · 马拉加 · 维多利亚 · 纳瓦拉 · 阿拉贡 · 埃布罗 · 哈拉马 · 休达 · 得土安 |
| `Legion Condor` / `Condor Legion` | 秃鹰军团 |
| `CNT-FAI` `POUM` `UGT` `PNV` `FARE` `T.O.C.E.` | **原样保留**（政党/工会专有缩写） |
| `Corpo Truppe Volontarie` / `CTV` | 意大利志愿军团（`[CTV]` 缩写保留） |
| `Ejército Nacional` / `Nationalist(s)` | 国民军 |
| `Ejército Popular` / `Republican(s)` | 共和军 |
| `Brigadas Internacionales` | 国际纵队 |
| `Tercios Requetés` / `Requetés` | 卡洛斯派军团 |
| `Milicias Falange` / `Falange` | 长枪党民兵 |
| `CEM` / `Cuerpo de Ejército Marroquí` | 摩洛哥军 |
| `Brigadas Navarras` | 纳瓦拉旅 |
| `batallón` / `brigada` / `división` / `columna` / `compañía` / `tabor` | 营 / 旅 / 师 / 纵队 / 连 / 塔博尔 |

**人名用通行译名**：`Franco` 佛朗哥 · `Mola` 莫拉 · `Yagüe` 亚圭 · `Varela` 巴雷拉 ·
`Miaja` 米亚哈 · `Rojo` 罗霍 · `Modesto` 莫德斯托 · `Lister` 利斯特 · `Durruti` 杜鲁蒂 ·
`Aranda` 阿兰达 · `Solchaga` 索尔查加 · `Moscardó` 莫斯卡多 · `Cabanellas` 卡瓦内利亚斯 · `Negrín` 内格林。

## 四、标点与格式（**与 `.xscn` 层相反，务必注意**）

- 场景 `.txt` 口径用**全角**括号与顿号：`（）`、`、`；原文的 `''X''` 是引号，译成 `「X」`。
- 分隔线（`¯¯¯¯¯`、`-----`、`-÷-÷-`）**原样保留**，不要翻译、不要改动。
- **日期**译成 `1936年11月13日`（原文 `13 de Noviembre de 1936` 或 `November 13th, 1936` 都这样）。
- 编号/番号保持原样：`22 BM/39 Div./[XIII]` → `第22营/第39师/[XIII]`
  （罗马数字方括号**原样保留**；`第N` 用阿拉伯数字）。
- **不加原文没有的解释性文字**；不写译注；不加 emoji。
- 士兵口吻的粗话/口语照译，不要美化也不要加码（`Mierda!`→「见鬼！」一类），
  但**不使用蔑称**：`rojos`（红佬）按语境译「共和军/敌军」，`milicianos` 译「民兵」。

## 五、文体

征召/胜利/失败报文的语气是**上级对将军说话**，用「您」不用「你」。
`Buena suerte.` → 「祝您好运。」`Felicidades general!` → 「恭喜，将军！」。

## 六、交付前自检（必须做，并在回复里报告）

1. 输出行数 == 输入行数；
2. 每行译文非空、无 TAB、无换行符、无 BOM；
3. 原文里的数字、日期、方括号代号都在译文里对得上。

## 七、只回复一行

`part-NN 完成，共 N 行；自检通过`（**不要**贴译文内容）
