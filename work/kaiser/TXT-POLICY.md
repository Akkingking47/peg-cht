# KAISER 场景 `.txt` 层口径（子代理必读）

`EFILE_KAISER`（一战多国，1850–1926）的 `SCENARIO\*.txt`（含大写 `.TXT`）是**场景简报**，
多数为英文散文，个别文件开头含德语段落（信件/口号）。本轮译这些散文。

输入每行**一个原文串**（`work\kaiser\_kt_todo_partNN.txt`），输出**逐行一一对应的中文**
（`work\kaiser\_kt_dst_partNN.txt`）。

---

## 一、总则

- **逐行对应**：输出行数 == 输入行数；一行就是一段简报，**照译成一行，不拆行**。
- **全角标点**（，。！？：；（））；原文 `'X'` / `"X"` → `「X」`；原文 `` ''X'' `` → `「X」`。
- 日期：`March 12th 1915`→`1915年3月12日`；`September, 25th 1916`→`1916年9月25日`。
- 上级对将军说话用「您」；不加原文没有的解释、不写译注。
- **保留原文不动的东西**：`/` 与 `-` 分隔线、`*` 号、编号 `#N`、罗马数字 `XIV`、专有型号。

## 二、简报常见套语（照此统一）

| 原文 | 译 |
|---|---|
| `Victory conditions:` | `胜利条件：` |
| `Victory conditions: Take all VHs.` | `胜利条件：夺取所有胜利点。` |
| `HISTORICAL EVENTS:` / `Historical events:` | `历史事件：` |
| `HISTORICAL OUTCOME:` / `Historical outcome` / `OUTCOME` | `历史结局：` |
| `Historical background:` | `历史背景：` |
| `Brief to Anzac Commander.` | `致澳新军团指挥官的简报。` |
| `- Take all the VHs.` | `- 夺取所有胜利点。` |
| `- Your MSU core unit must survive.` | `- 你的主力核心单位必须存活。` |
| `Dear Sir,` | `尊敬的先生，` |
| `Special note:` | `特别提示：` |
| `In other news:` | `其他消息：` |
| `Equipment File: Kaiser General` | `装备文件：凯撒将军` |
| `(from the memoirs of Lt. Gen. Bruce W. Dickinson)` | `（摘自布鲁斯·W·迪金森中将回忆录）` |
| `----{secret telegraph depeche to general}-----` | `----{致将军的机密电报}----` |
| `-----{end of secret telegraph depeche}----` | `-----{机密电报结束}----` |
| `THE WHITE HOUSE; WASHINGTON,` | `白宫；华盛顿，` |
| `THE PRESIDENT OF THE UNITED STATES` | `美利坚合众国总统` |

## 三、德语段落照译

如 `Liebe Anna,`→`亲爱的安娜，` · `Ich küsse Dich,`→`吻你，` · `Dein Hugo`→`你的 雨果`。

## 四、军事/历史术语

- 编制：`Division`→师 · `Brigade`→旅 · `Regiment`→团 · `Battalion`→营 · `Corps`→军 · `Army`→集团军 ·
  `Alpenkorps`→阿尔卑斯军 · `Entente`→协约国 · `Central Powers`→同盟国 · `VH`→胜利点 ·
  `BV`→大捷 · `TV`→小捷 · `MSU`→主力单位 · `core unit`→核心单位。
- 地名/人名：用通行译名（`Neuve Chapelle`→新沙佩勒 · `Transylvania`→特兰西瓦尼亚 · `Piave`→皮亚韦河 ·
  `Kitchener`→基钦纳 · `Falkenhayn`→法尔肯海因 · `Haig`→黑格 · `Charles IV`→查理四世 · `Hugo Bauernschmitt`→胡戈·鲍恩施密特）。

## 五、格式与回报

- UTF-8 **无 BOM**；行间 `\n`；**每行一条，逐行对应**；无序号/原文/表头/空行/代码块。
- **输出必须能被 GBK 编码**（不得含 `é á ö ñ ü ß ş` 等；变音符折写或意译成汉字）。
- 完成后**只回复一行**：`kt-NN 完成，共 M 行；自检通过`。
