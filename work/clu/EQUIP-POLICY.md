# EFILE_Clu `equip97.txt` 口径（本批子代理必读）

## 任务
把 `EFILE_Clu` 的装备/编制名表（2,036 行）中**不是型号**的条目译成简体中文。
题材＝**芬兰**（冬战/继续战争/拉普兰战争）＋**德国**（1945 奥得河前线）＋苏联 ＋
少量罗马尼亚/西班牙/意大利/匈牙利/瑞典/挪威/丹麦 装备。

先读：`D:\DSH\军事游戏汉化\work\xscn\POLICY.md`（番号/缩写硬规则）与
`D:\DSH\军事游戏汉化\work\clu\CLU-POLICY.md`（本 efile 已定口径）。

## 输入 / 输出
- 输入：`D:\DSH\军事游戏汉化\work\clu\equip-chunks\chunk-NN.tsv`（**单列**，每行一条原文，UTF-8 无 BOM）
- 输出：`D:\DSH\军事游戏汉化\work\clu\equip-zh\part-NN.tsv`（`原文<TAB>译文`，行数与顺序逐行一致，
  UTF-8 无 BOM，不要表头/注释/空行）

## 硬规则

1. **装备型号一律保留原文**：`Bf-109G-2` `Ju-88A-4` `T-34/85` `Renault FT17` `Vickers 6t`
   `Brewster Mod. 239` `MS.406C1` `G.50` `AB-41` `45mm M1938` `76.2mm M1936` `20 pst kiv/39`
   —— **含口径/型号数字的整条通常就是型号 ⇒ 原样照抄**（除非其中夹着可译的兵种词，见第 3 条）。
2. **括号标记与图标码原样保留**：`[A]` `[AM]` `[CS AA]` `[S H]` `[D]` `[AA]` `(wi)` `(su)`；
   但 `(wi)`＝芬兰语 **talvi 冬**、`(su)`＝**suvi 夏** ⇒ 译作 `(冬)` / `(夏)`；`(mot)`→`(摩托化)`；
   `capt.`→`缴获`；`zbV`/`z.b.V.`→保留。
3. **兵种/编制/装备通用名译中文**（这是本层主体）：

| 芬兰语 | 中文 | 芬兰语 | 中文 |
|---|---|---|---|
| Jalkaväki / Jalkavaki | 步兵 | Pioneeri | 工兵 |
| Siltapioneeri | 桥梁工兵 | Jaakari / Jääkäri | 猎兵 |
| Ratsuväki / Ratsuvaki | 骑兵 | Polkupyorajoukot | 自行车部队 |
| Tiedustelijat | 侦察兵 | Tarkka-ampuja | 狙击手 |
| Krenatööri | 掷弹兵 | Bunkkerin miehistö | 掩体班组 |
| Varuskunta | 驻防部队 | Rannikkopatteri | 海岸炮台 |
| Kevyt kk | 轻机枪 | Maxim kk | 马克沁机枪 |
| pst kiv | 反坦克步枪 | kenttätykki | 野战炮 |
| Atelaj | 驮畜 | Ilmatorjunta | 防空 |
| Lentokone | 飞机 | Pommittaja | 轰炸机 |
| Hävittäjä | 战斗机 | Valkoinen Kaarti | 白卫队 |

| 德语 | 中文 | 德语 | 中文 |
|---|---|---|---|
| Infanterie / Inf. | 步兵 | Panzer / Pz. | 装甲 |
| Grenadier / Gren. | 掷弹兵 | Fallschirmjäger | 伞兵 |
| Gebirgsjäger | 山地猎兵 | Pionier / Pi. | 工兵 |
| Artillerie / Art. | 炮兵 | Flak | 高射炮 |
| Panzerjäger | 反坦克 | Aufklärung | 侦察 |
| Sicherung | 警卫 | Volkssturm | 人民冲锋队 |
| Festung | 要塞 | Marine | 海军 |
| Kavallerie | 骑兵 | Nachschub | 补给 |
| Sanität | 卫生 | Sturmgeschütz | 突击炮 |
| Mörser / Moerser | 臼炮 | Haubitze | 榴弹炮 |

| 英/苏/其他 | 中文 | 英/苏/其他 | 中文 |
|---|---|---|---|
| Guards / Gds | 近卫 | Rifle | 步兵 |
| Tank / Tk | 坦克 | Cavalry | 骑兵 |
| Machine Gun / MG | 机枪 | Mortar | 迫击炮 |
| Anti-tank / AT | 反坦克 | Engineer | 工兵 |
| Recon | 侦察 | Transport | 运输 |
| Sub / Destroyer / Cruiser | 潜艇/驱逐舰/巡洋舰 | Class | 级 |
| Rannikkopatteri(SV) | 海岸炮台 | Semovente(IT) | 自行火炮 |

4. **编号一律「第+阿拉伯数字」**（`20 pst kiv/39`→`20 反坦克步枪/39`，年份 `39` 保留原样不加「第」）；
   `/`、`-`、`[ ]`、`( )`、空格数量与顺序**逐字保留**；括号一律半角。
5. ⚠️ **拿不准就照抄原文**（尤其整条是型号或未知缩写时），并在回复里点名。

## 交付前自检（必须做，并在回复里报告）
1. 行数 == 输入行数；2. 每行恰好 1 个 TAB 且 TAB 前与输入逐字符相同；
3. `/ [ ] ( )` 计数逐行一致；4. 译文非空、无首尾空格、无 BOM。

## 回复格式（只两行）
`part-NN 完成，共 M 行；自检通过`
`照抄保留 N 条：<逗号分隔的原文列表>`
