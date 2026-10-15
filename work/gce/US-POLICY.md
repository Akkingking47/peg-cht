# GCE `USERSCEN` 层翻译口径（子代理必读）

> efile＝`EFILE_GCE`（**西班牙内战 1936–39 ＋ 意大利志愿军团 CTV**）。
> 本层＝**用户场景**目录：`.xscn` 的地图标签与部队番号、`.ply`/`.txt` 的场景简报。
> **先读 `TXT-POLICY.md`（上一层的口径，绝大多数规则照用）**，本文只写本层特有的。

---

## 一、任务与输入输出（严格）

- 输入：`D:\DSH\军事游戏汉化\work\gce\_us_todo_partNN.txt`
  格式：`   频次|原文`（**频次不要抄进译文**）。
- 输出：`D:\DSH\军事游戏汉化\work\gce\_us_dst_partNN.txt`
  **每行一条译文，与输入逐行对应**；不要序号、原文、表头、空行、代码块。
- UTF-8 **无 BOM**，行间 `\n`。一个输入行＝一条输出行（长段落**不要拆行**）。

## 二、本层的三类内容

| 类 | 样子 | 怎么译 |
|---|---|---|
| **地图标签 / 部队番号**（占大多数） | `Salas` · `Rio Navia` · `22 BM/39 Div./[XIII]` · `-/-/XV CE` · `Guarnicion` | 地名→通行中文；番号按 `POLICY.md` 三；**`/` 与 `-` 分隔符数量原样** |
| **`.ply`/`.txt` 简报正文** | `Tras la batalla del Ebro, el ejército nacional avanza…` | 同 `TXT-POLICY.md`：**西语段与英译段都要译**，用词一致；上级对将军用「您」 |
| **简报字段行** | `Efile: GCE` · `Mapa: Barcelona` · `Map design: Santiago Fuertes` | 见下表 |

## 三、简报字段行对照（**必按此译**）

| 西语 | 英语 | 中文 |
|---|---|---|
| `Efile: X` | `Efile: X` | `装备文件：X` |
| `Mapa: X` | `Map: X` | `地图：X` |
| `Diseño Mapa: X` | `Map design: X` | `地图设计：X` |
| `Diseño escenario: X` | `Scenario design: X` | `场景设计：X` |
| `Duración máxima de escenario: N Turnos` | `Maximum scenario lenght: N Turns` | `场景最长回合数：N 回合` |

⚠️ **设计者人名保留原文**（`Santiago Fuertes` · `Guille` · `SSI` · `Von Adler`）——
先例：ATOMIC 的 `Scenario Designer: randowe` 就保留 `randowe`。

## 四、本层特有口径

1. **`CE` ＝ `Cuerpo de Ejército`（军）**：`XV CE` → `第15军`（**罗马数字转阿拉伯**，同 `POLICY.md` 三）。
   `EM/53 Div./[V]` → `EM/第53师/[V]`（`EM` ＝ Estado Mayor 参谋部，**保留缩写**）。
2. **`[方括号]` 内的罗马数字代号原样保留**（`[XIII]` `[V]` `[XVIII]`）；
   方括号内的**地名/人名要译**（`[Sograndio]` → `[索格兰迪奥]`）。
3. **未知缩写不要猜，原样保留**（`G.A.` `CRS` `DECA` `CRS` `Bia` `Cia.` `Esc.` `R.` `Vol.` `Bon.` `Grupo` `Grp.`）。
   ⚠️ 例外：`Guarnicion`＝驻军、`Milicias`＝民兵、`Flota del Mediterraneo`＝地中海舰队、
   `Columna`＝纵队、`Tabor`＝塔博尔、`Centuria`＝百人队、`Division`/`Div.`＝师、
   `Brigada`/`Bda.`＝旅、`Batallon`/`Ban.`＝营（Falange 建制则作「旗队」）。
4. **地名**：先在 `work\gce\gce-xscn-map.tsv` 里**精确查一遍**（两列 `src<TAB>dst`）；
   查到**必须用它的 dst**——那份表已经落进游戏 `.xscn`，两处不一致玩家会直接看出来。
   查不到的按通行译名。
5. 分隔线 `¯¯¯¯¯` / `-----` / `-÷-÷-` **原样保留**；标点用**全角**（`（）` `、`）；
   `''X''` → `「X」`；日期 `1936年11月13日`。
6. 不加原文没有的解释、不写译注、不加 emoji。

## 五、交付前自检（必须做，并在回复里报告）

1. 输出行数 == 输入行数；2. 每行非空、无 TAB、无换行符、无 BOM；
3. 原文的数字/番号/方括号代号在译文里对得上。

## 六、只回复一行

`part-NN 完成，共 N 行；自检通过`（**不要**贴译文内容）
