# OpenGus Zx efile —— 场景文本汉化规则（务必逐条遵守）

## 任务性质
把六边形战棋游戏 **Open General** 的 efile `EFILE_GUS_Zx` 的场景文本（波兰语 / 英语混排）
翻译成**简体中文**。这些字符串会**直接显示在游戏里**：战役名、场景简报、胜/败文本、
地图上的地名、以及每个作战单位的番号名。它**不是**给人读的文档，是 UI 字符串。

## 输入输出
- 输入目录：`D:\DSH\军事游戏汉化\work\gus_zx\src\`
- 输出目录：`D:\DSH\军事游戏汉化\work\gus_zx\zh\`（**文件名必须与输入完全一致**）
- 编码：**UTF-8 无 BOM**（上游会统一转成 GBK 落盘，你不要自己转）
- 换行符：**与输入文件逐字节一致**（有的文件是 CRLF，有的只有 LF，有的**行尾没有换行符**）。
  用 Python 读写并保留原始换行：读 `open(p, encoding="utf-8", newline="")`，
  写 `open(q, "w", encoding="utf-8", newline="")`，**只替换行内文字，不要动任何换行符**。

## 硬性约束
1. **行数绝对不变**，第 N 行对第 N 行。空行保持空行。一行内如果有多段，也保持在同行。
2. **不要合并、不要拆行、不要加/删空行**。简报常见的「一整段挤在一行」要保持一行。
3. 不要添加任何解释、注释、译注、括号补充、Markdown。
4. 纯数字、纯符号、表格对齐用的空格、列宽——**原样保留**。
   `H02__flow.txt`、`G06__flow.txt` 这类是**引擎自己生成的报表**（列对齐），
   只翻译其中的**场景标题词**（如 `Mokra` `Sedan` `Klin`、`Operacja "Merkury"`、`Zitadelle`），
   **列宽和空格不要重新排版**，翻译后长度尽量贴近原文。
5. 文件里出现的 `<M:0010>`、`<U:0007>`、`<N:0001>` 之类**内部标记原样保留**。
6. 数字、日期、番号数字、罗马数字原样保留：`1 IX 1939` → `1939年9月1日`（可），
   但 `Sep  1, 1939` 这种在 `__flow` 报表里的就保持 `Sep  1, 1939` 不动。

## 风格
- 军事史书语气，简洁、克制、不用口语和网络语。
- 德军战役里上级对玩家的称呼 `Herr General` → **「将军阁下」**；`Herr Feldmarschall` → **「元帅阁下」**。
- 祈祷/口号类保留气势，例如 `For the Third Reich` → 「为了第三帝国」。
- 脏话（波兰语 `Dupa zbita.` = 打输了）用干净的对应语：「一败涂地。」「全线崩溃。」

## 地名（用通行中文译名）
华沙 Warszawa / Warsaw · 莫斯科 Moskwa / Moscow · 克林 Klin · 沃洛科拉姆斯克 Volokolamsk ·
诺夫哥罗德 Novgorod · 基什尼奥夫 Kishinev · 塞当 Sedan · 敦刻尔克 Dunkirk ·
利勒哈默尔 Lillehammer · 托布鲁克 Tobruk · 萨莱诺 Salerno · 卡昂 Caen ·
斯大林格勒 Stalingrad · 库尔斯克 Kursk / Zitadelle·堡垒行动 · 普罗霍罗夫卡 Prokhorovka ·
列宁格勒 Leningrad · 斯特拉斯堡 Strasbourg · 布达佩斯 Buda-Pest · 莫克拉 Mokra ·
彼得库夫 Piotrków · 罗兹 Łódź · 琴斯托霍瓦 Czestochowa · 布祖拉河 Bzura · 瓦尔塔河 Warta ·
别尔斯科 Kamieńsk · 拉多姆斯科 Radomsko · 普热梅希尔 Przemyśl · 利沃夫 Lwów/Lviv ·
扎莫希奇 Zamość · 埃尔宾/埃尔布隆格 Elbląg · 格鲁琼兹 Grudziądz · 格但斯克 Gdańsk ·
格丁尼亚 Gdynia · 马尔堡 Malbork · 特切夫 Tczew · 维尔纽斯 Wilno/Vilnius ·
塞萨洛尼基/萨洛尼卡 · 梅塔克萨斯防线 Linia Metaksasa · 克里特 Kreta/Crete ·
马来 Maleme?（无则忽略）· 汉堡 · 鲁尔 · 默兹河 Moza/Meuse · 阿尔登 Ardeny/Ardennes ·
法莱斯 Falaise · 尚布瓦 Chambois · 卡昂 Caen · 亚琛 · 埃菲尔

## 番号与缩写
**保留数字与结构，把说明词译成中文**。常用对照：

波兰军（H02_Blitz 前三个、G27、G06 里的波军）：
- `DP` / `Dywizja Piechoty` → 步兵师；`DK` → 骑兵师；`BK` → 骑兵旅
- `PU` = Pułk Ułanów → 枪骑兵团；`PSK` = Pułk Strzelców Konnych → 骑乘步枪团
- `pp` = pułk piechoty → 步兵团；`ppL`/`pp Legionów` → 波兰军团步兵团
- `PAL` = Pułk Artylerii Lekkiej → 轻炮兵团；`DAK` → 骑炮营；`PAM` → 摩托化炮兵团
- `b ckm` = batalion ckm → 重机枪营；`sam bat km` → 独立重机枪营
- `Dywizjon Panc.` → 装甲营；`BatArtPlotMot` → 摩托化高炮营；`Sztab Brygady` → 旅部
- `GO` = Grupa Operacyjna → 战役集群；`ON` = Ośrodek Oporu? / 据点

德军：`InfDiv`→步兵师 · `PzDiv`→装甲师 · `ArtReg`→炮兵团 · `Pio Bat`→工兵营 ·
`PzJagAbt`→反坦克营 · `SchutzenReg`/`Schützen-Regiment`→装甲步兵? （1939–40 用「摩托化步兵团」）·
`GrenReg`→掷弹兵团 · `AufklAbt`→侦察营 · `GebJag`→山地兵 · `Fallschirm`→伞兵

英/盟军：`TB`→坦克旅 · `AB`/`Abn`/`Airborne`→空降 · `GIR`→滑翔机步兵团 ·
`A&SH`=Argyll & Sutherland Highlanders→阿盖尔-萨瑟兰高地团 ·
`Black Watch`→黑卫士 · `Y&L`=York & Lancaster→约克-兰开斯特团 ·
`Leicesters`→莱斯特团 · `Hussars`→骠骑兵团 · `NZ`→新西兰 · `Maori`→毛利营 ·
`Commandos`→突击队 · `RM`=Royal Marine→皇家海军陆战队

> 遇到本表没列的缩写：**保持缩写原样**（宁可留英文缩写，也不要瞎猜译错）。
> 若能从上下文确定含义，就译；拿不准就保留原文缩写。

## 关键：不要做的事
- 不要"顺手"改写源文里本身是英语的段落成波兰语或反之。
- 不要遗漏任何一个文件。分批给你的文件名，**一个都不能少**。
- 不要因为原文很短（如 `Dupa zbita.`）就跳过。
