# KAISER `.xscn` 地名/专名层口径（子代理必读）

本轮做 `EFILE_KAISER`（一战多国，1850–1926）`.xscn` 里**剩下的地名、专名、部队名、短语句**。
这些是组 0（地图标签）、组 1（部队/编制名）、组 -1（标题）的残留。

输入每行**一个原文串**（`work\kaiser\_pl_todo_partNN.txt`），
输出**逐行一一对应的中文**（`work\kaiser\_pl_dst_partNN.txt`）。

---

## 一、总体原则

**只有两类要译，其余一律原样照抄。**

1. **地名** → 音译（用中国人熟悉的通行译名；无通行译名的按音译规则）。
2. **普通词语/短语** → 意译。

其余（人名、舰名、舰级、飞机名、厂名、纯番号代号、罗马数字、符号）→ **原样照抄**（不改一个字符）。

> 判据：**拿不准就照抄**。宁可漏，不可错。

## 二、地名（音译；这是本轮的主体）

用**通行中文译名**；没有通行译名的按下表音译。

| 语种 | 音译要点 | 例 |
|---|---|---|
| 法语 | `eau/aud`→奥 · `ou`→乌 · `-court`→库尔 · `-ville`→维尔 · `-mont`→蒙 · `-bois`→布瓦 · `-fort`→福尔 · `Ouvrage de X`→`X 要塞` · `Fort de X`/`Ft de X`→`X 要塞` · `Bois de X`→`X 树林` · `Cote de X`→`X 高地` · `Ruisseau de X`→`X 溪` · `Quatre`→卡特尔（地名中作「四」时用「四」） | `Douaumont`→杜奥蒙 · `Vaux`→沃 · `Fleury`→弗勒里 · `Bezonvaux`→贝宗沃 · `Thiaumont`→蒂奥蒙 · `Verdun`→凡尔登 |
| 佛兰芒/荷兰语 | `-gem`→海姆 · `-beke/-beek`→贝克 · `-hoek`→胡克 · `-kapelle`→卡佩勒 · `-straat`→斯特拉特 · `-hoeve`→霍弗 · `-kerke`→凯尔克 · `-zeele`→泽勒 | `Zonnebeke`→佐内贝克 · `Poelkapelle`→普尔卡佩勒 · `Wytschaete`→维茨哈特 · `Langemarck`→朗热马克 |
| 波兰/俄语 | `-ów/-ow`→夫 · `-ice`→采 · `-sk`→斯克 · `-owo`→沃 · `-ka`→卡 · `ы`→厄 · `я`→亚 | `Zborow`→兹博罗夫 · `Kalety`→卡莱特 · `Radun`→拉敦 |
| 土耳其语 | `ı`→厄 · `ğ`→（前元音后作 y） · `ş`→什 · `ç`→奇 | `Krithia`→克里西亚 · `Tekke Burnu`→泰凯布努 · `Sedd-El-Bahr`→塞德巴赫尔 |
| 德语 | `-berg`→贝格 · `-dorf`→多夫 · `-bach`→巴赫 · `-heim`→海姆 · `ü`→于 · `ö`→厄/佩 · `ß`→斯 | `Langemarck`→朗热马克 · `Festung Frankfurt`→法兰克福要塞 |
| 匈牙利语 | `ö`→厄 · `ü`→于 · `gy`→吉 · `cs`→奇 · `sz`→斯 | `Érsekújvár`→埃尔斯库伊瓦尔 |
| 意大利语 | `-ello`→埃洛 · `-uzzo`→乌佐 | `Cividale`→奇维达莱 |

**带结构词的地名要译结构词**：`Bridge`→桥 · `Station`→车站 · `Railway/RR`→铁路 · `To X`→`通往X` ·
`X Road`→`X公路` · `Fort`/`Ouvrage`→要塞 · `Cote`→高地 · `Bois`→树林 · `Ruisseau`→溪 · `Hoeve`→霍弗（农庄） ·
`Chapel`→礼拜堂 · `Church`→教堂 · `Wood(s)`→树林 · `Crossing`→渡口 · `Junction`→枢纽 · `Dump`→补给站 ·
`Line`→线 · `Position`→阵地 · `Trench`→战壕 · `Spur`→山嘴 · `Ridge`→山脊 · `Valley`→谷地 · `Lake`→湖 ·
`Hill`→山丘 · `Island`→岛 · `Bay`→湾 · `Coast`→海岸 · `Mine`→矿 · `Mill`→磨坊 · `Farm`→农庄 · `Camp`→营地。

**全大写地名照译**：`KRASNAYA GORKA`→红山 · `SERAYA LOSHAD'`→灰马（俄语地名照音译/意译） ·
`MOUNTAIN PASS`→山口 · `JUNGLE`→丛林 · `NO MAN'S LAND`→无人区。

## 三、照抄不译的

- **人名**（含带军衔者）：`Franz Sigel` `Koos de la Rey` `McLeod` `McCormick` `JägBtl. 4` 中的数字保留 →
  ⚠️ 但**人名保留原文**（`Franz Sigel` 照抄）。
- **舰名/舰级/潜舰**：`INFLEXIBLE` `QUEEN ELIZABETH` `BOUVET+SUFFREN` `SM U-14` `HMS E-42` `LZ-39` `UB-15` `V-125` `S-130`。
- **飞机名**：`Albatros` `Fokker` `Nieuport` …
- **纯番号代号**：`III/3Li/3BM/1LA` `[11]` `[HKII]` `BP #5` `JaSta 26` `SPA bi20` `6 SchK` `2 K.A.R` `FFA 9`。
- **罗马数字**、**数字**、**纯符号**。
- **介词/冠词**单独出现时：`de` `of` `la` `du` `van` `von` …

## 四、普通词语（意译）

`Black Flag`→黑旗 · `Improvised Positions`→简易阵地 · `Abandoned Equipment`→废弃装备 ·
`Kimberley besiegers`→金伯利围城部队 · `Tallinn Communists`→塔林共产党人 · `Samara Bolsheviks`→萨马拉布尔什维克 ·
`Barbelé`→铁丝网 · `Bunkeris`→碉堡 · `>> EVACUATE <<`→`>> 撤离 <<` · `Brug over het kanaal`→运河桥。

**部队专名**（国别+兵种/编制）意译：`I.FldArmee Belgisch-Kongo`→比利时刚果第1野战集团军 ·
`Ejército de Operaciones del Norte`→北方作战集团军 · `Asienkorps`→亚洲军（`[AG Yildirim]` 括号内照抄）·
`EisenbahnDivision.10`→铁道兵第10师 · `s.Afrk.UnionsTruppen`→南非联邦部队 · `Hukbong Pilipinong Mapaghimagsik`→菲律宾革命军。

## 五、格式

- UTF-8 **无 BOM**；行间 `\n`；**不要**序号/原文/表头/空行/代码块。
- **输出行数必须 == 输入行数**，**逐行严格对应**。
- 中文里**不要夹拉丁残留**（除照抄项）；不留首尾空格。
- 标点用**半角**（`.xscn` 口径）；分隔符 `/`、`-`、`[ ]`、`+` 的数量与顺序**原样保留**。

## 六、回报

完成后**只回复一行**：`pl-NN 完成，共 M 行；自检通过`（不要贴内容）。
