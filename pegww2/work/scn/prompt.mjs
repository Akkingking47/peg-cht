export const RULES = `你在做「个人研究用途」的二战老游戏 MOD「PeG-WW2」汉化（People's General 引擎）。全程只做语言转换，绝对不改原文的世界观、阵营划分与叙事措辞。一律简体中文。

【工作区】D:\\DSH\\军事游戏汉化

【第一步 · 必做】完整读这两个文件，它们定义本批的全部口径：
1. D:\\DSH\\军事游戏汉化\\pegww2\\research\\各国军语风格口径.md
2. D:\\DSH\\军事游戏汉化\\pegww2\\research\\_scn-sample-zh.tsv
3. D:\\DSH\\军事游戏汉化\\pegww2\\research\\_scn-sample-west-zh.tsv
（后两个是已获用户认可的定稿样本，照这个水准与风格写。）

【你的输入】read 工具读取：<CHUNK_SRC>
文件格式：首行注释，之后每行「全局编号<TAB>原文」。逐条译。

【你的产出】write 工具写：<CHUNK_OUT>
严格按输入逐行对应：全局编号<TAB>译文。行数、顺序、编号与输入完全一致，不得增删行。

### 铁律
1. 译文列零空值。译文内绝不能含 TAB，也不能含换行。
2. 元数据行原样保留（译文＝原文）：以 Version / Gameset / Equipment / Note / Source / BTW 开头的文件头元数据行，以及整行就是 dummy 的行，以及纯 --------- 分隔线。
3. 控制字符转义序列原位保留：原文里的 \\x00 \\x01 \\x11 \\x12 等字面反斜杠转义序列，译文必须在相同位置带上同样的序列（原文以 \\x00 结尾 ⇒ 译文也以 \\x00 结尾）。原文 \\x00 前的空格数也照抄。
4. 先判文体再定语域，不要一律作战命令体。六种文体：任务交代体（平实交代）｜战况通报体（通报态势+要求）｜嘉奖体（Outstanding work⇒干得漂亮）｜训斥体/败报（you have done poorly!⇒你打得很差！）｜战史复述体（第三人称、过去完成⇒中文用「已」＋平实叙事）｜政治公报体（苏联/南斯拉夫/西班牙共和军）。
   原文限制译文的军事化程度：原文平实就别改成命令体，原文有比喻就照译比喻。
5. 称呼（全库只有两个可靠锚点）：
   - 原文有 Herr ⇒ 阁下（Herr General⇒将军阁下；Herr Feld-Marschall⇒元帅阁下）
   - 原文有 Comrade/comrade ⇒ 同志（Comrade General X⇒X 将军同志；句末 Comrade⇒同志）
   - 两个都没有 ⇒ 不得凭空添加敬语：General⇒将军、Sir⇒长官、Commander⇒指挥官
   - ⚠️ 德军视角文件里混用了英语 Sir（作者笔误）：德军视角的 Sir 译「阁下」，美军视角的 Sir 译「长官」。
6. 各国语域：美军＝去文言、直白效率优先；英/加＝克制含蓄；苏/共＝公报语汇（重申/一贯/坚决/务必）；德军＝军语精确克制；党卫军＝照译原文语气强度，不自行强化也不淡化其意识形态措辞。
7. 人名/地名：历史人物用约定译名（Rommel⇒隆美尔、Zhukov⇒朱可夫、Konev⇒科涅夫、Guderian⇒古德里安、Model⇒莫德尔、Patton⇒巴顿、Montgomery⇒蒙哥马利、Mannerheim⇒曼纳海姆、Tito⇒铁托、Stalin⇒斯大林、STAVKA⇒最高统帅部）。行内地名/人名加半角 (原文)，如 斯特拉斯堡(Strasbourg)、朱可夫(Zhukov)；部队番号与装备型号不加；已有中文固有译名的（顿河、华沙、莫斯科、柏林）可不加。
8. 不增删词句十条铁律：不加呼语（原文没叫「将军」就不加）· 不加说明性括注 · 不删从句 · 不合并并列项 · 不改语气强度（never, never⇒绝不、绝不；!!!⇒！！！）· 不过度口语化也不过度文言化 · 数据不动（番号/日期/坐标/(#1)/(#7d10)/PeG:WW2 原样）· 标点随原文（--⇒——）· 代词随原文 · 语境优先于词表。
9. 机翻味诊断：knife through⇒如利刃般直插（不是「快速穿过」）· As you can see,⇒如你所见 · 不写「进行了一次攻击」⇒写「发起攻击」· 补足目的句 · 不堆「的」· 不倒英文语序 · 被动句汉化。
10. 禁用词：國力/佔領/光榮勝利/前進觀測官/改良裝備 及其简体形式（作 Prestige/Overrun/Brilliant Victory 等义时）；Prestige 统一作「威望」，禁用「声望」。
11. 这批文本同时来自 `_m`/`_u`/`_i`/`txt`/`bv`/`tx`/`log` 等载体：短语料可能只是部队名或地图格名（如 "7th Panzer Division / [X]"、"Divisionnaire Headquarters 101st Airborne"），按常规军语译，不加解释、不加原文括号。

【完成后自检】再 read 一次你的产出文件，数行数：必须等于输入行数，且每行都不为空。若不符，重写该文件。
只回报一行：<CHUNK_OUT> 与行数。不要回报译文内容。`;

export function promptFor(chunk) {
  const nn = String(chunk).padStart(2, '0');
  return RULES
    .replaceAll('<CHUNK_SRC>', `D:\\DSH\\军事游戏汉化\\pegww2\\work\\scn\\chunks\\chunk_${nn}.tsv`)
    .replaceAll('<CHUNK_OUT>', `D:\\DSH\\军事游戏汉化\\pegww2\\work\\scn\\out\\chunk_${nn}.tsv`);
}
