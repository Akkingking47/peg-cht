# KAISER `.xscn` 词表口径（子代理必读）

`EFILE_KAISER` 的 `.xscn` 场景文件里，**组 1 是部队/编制名、组 0 是地图标签、组 -1 是场景标题**。
这些串是**多语言**的（英/德/俄/波/捷/法/意/西/土/芬/匈/塞/保/希/日…），大量使用**编制缩写**。

本轮任务＝把**高频 token** 译成中文，供生成器做「词级组合」翻译。

---

## 一、要输出的（编制/兵种/类别/描述词）

| 类别 | 例 |
|---|---|
| 编制等级 | `Div.`/`Div`/`div.`→师 · `Brig.`/`Bryg.`→旅 · `Reg.`/`Rgt.`→团 · `Bat.`/`Bn`/`Bon.`→营 · `Corps`/`Korps`→军 · `Army`/`Armée`/`Armee`/`Armiya`→集团军 · `Group`/`Gr.`→集群 |
| 兵种 | `Inf.`→步兵 · `Art.`→炮兵 · `Cav.`→骑兵 · `MG`→机枪 · `Eng.`/`Pion.`→工兵 · `Cossacks`→哥萨克 · `Rifle`→步枪兵/步兵 · `Garrison`→卫戍部队 · `Reserve`→预备役 |
| 类别 | `Line`→线 · `Trench`→战壕 · `Position`→阵地 · `Fort`→要塞 · `Bunker`→碉堡 · `Village`→村庄 · `LAKE`→湖 · `RAILROAD`→铁路 · `Airfield`→机场 · `Farm`→农庄 · `Bridge`→桥 · `River`→河 |
| 国别/民族 | `Turkish`→土耳其 · `Bulgarian`→保加利亚 · `Romanian`→罗马尼亚 · `Serbian`→塞尔维亚 · `German`→德国 · `British`→英国 · `French`→法国 · `Russian`→俄罗斯 · `Italian`→意大利 · `Spanish`→西班牙 · `Persian`→波斯 · `Herero`→赫雷罗 · `Senussi`→赛努西 |
| 描述词 | `Tribes`/`tribe`→部落 · `kabilas`→部落 · `harka`→民团部队 · `Commando`→突击队 · `Remnants`→残部 · `Front`→方面军/前线 · `Detachment`/`Dtch`→支队 · `Do not kill this unit!`→勿杀此单位！ |

**缩写规则**：本工程的黑体缩写（`MG` `FA` `AK` …）**按史料译中文**（`MG`→机枪、`FA`→野战炮兵）；
但**纯编号型代号**（`2KOSB` `8RIR` `4KD` `[HKII]` `[IIIR]`）**不要输出**。

## 二、绝对不要输出的

- **地名**：`Lida` `Pilkem` `Langemarck` `Zonnebeke` `Ouvrage de Thiaumont` `Ft de Douaumont` …
- **人名**：`Wrangel` `Semenov` `Halil-Bei` `Stange Bey` `Djavdet Pasha` `MacArthur` `Cristescu` …
- **部队专名**（姓/地+编制）：`Kuban` `Transvaalers` `Kroonstad Commando` `Zach. Dyw. Strzelców` …
- **罗马数字**（`I` `II` `XIV` `XXI`）、**数字**、**纯符号**、**纯代号**（`Nr.` `Di` `[3]`）。
- **介词/冠词**：`de` `of` `la` `le` `du` `des` `di` `da` `van` `von` `der` `und` `and` `et` …

> 判据：**拿不准就不输出**。宁可漏，不可错。

## 三、格式

输入：`work\kaiser\_xtok_partNN.txt`，每行 `token \t 槽数 \t 样例串`。
输出：`work\kaiser\_xtok_dst_partNN.txt`，每行 `token \t 中文`。

- UTF-8 **无 BOM**；行间 `\n`；**不要表头/序号/空行/代码块**；token 与输入逐字一致。
- **只输出你要译的**；不译的**完全不要出现**。

## 四、回报

完成后**只回复一行**：`xtok-NN 完成，共 M 条`（不要贴内容）。
