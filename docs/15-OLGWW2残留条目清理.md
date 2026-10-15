# OLGWW2 残留条目清理报告（`.xscn` 层补译）

日期：2026-09-24　对象：`D:\OpenPG2\EFILE_OLGWW2\SCENARIO\*.xscn`（187 个）

---

## 一、背景：为什么会有这一轮

`docs\14` 的直接读文件审计发现：OLGWW2 对外宣称的"全量完成"**虚高 4.7%**。

根因是映射表里 **2,679 条 `src==dst` 恒等映射（16.5%）**，而写入脚本有条规则
"译文不含 CJK 就保留原字节" ⇒ **"没译"被静默算成"已处理"**。

收紧口径后确认**硬漏译 392 条**＝ 7 标题 ＋ 277 地名 ＋ 108 番号。

---

## 二、方法（五步，可复用）

| 步 | 动作 | 脚本 |
|---|---|---|
| 1 | **直接读文件**导出全部"未含汉字"条目，按 TITLE / PLACE / UNIT_W / ABBR / BRACKET / SHIP / ACRO 分类 | `export_residual.py` |
| 2 | 为每个含漏译的文件生成**语境卡**（已译邻居 + 未译条目），据战役/地区定译名 | `context_cards.py` |
| 3 | 建**译名表**（唯一真源）：`src → dst → 分类`，政策保留项显式写 `KEEP`、待考项写 `PENDING` | `olgww2-glossary.tsv` |
| 4 | **字节级定点写回**：只改命中条目的「2 字节长度字段＋内容」，其余字节一个不动 | `apply_residual.py` |
| 5 | **重建复核**：用「备份＋译名表」重新序列化，必须与现文件**逐字节相同** | `verify_residual.py` |

### 关键设计

- **写回器天然可重入**：匹配的是"当前文件内容"。已改成中文的条目解码 `ascii` 失败 ⇒ 自动跳过；
  同时用 `dst → src` 反查表把"已改过"也计入命中，避免误报"未命中"。
- **只改长度字段＋内容**，不动任何偏移/其它字节 ⇒ 结构不可能被破坏。
- **重建复核是最强校验**：它同时覆盖了"译名是否正确""是否多改了字节""组表/条目顺序是否保持"。

---

## 三、结果

| 指标 | 改动前 | 改动后 | 变化 |
|---|---|---|---|
| 含汉字条目 | 13,532 | **13,856** | **+324** |
| 硬漏译（TITLE+PLACE+UNIT_W） | 392 | **106** | **−286** |
| 未译标题 | 7 | **0** | −7 |
| 宽口径"疑似漏译" | 754 | 437 | −317 |

> **+324 与改动数 324 精确一致**（三批：274 + 38 + 12），是"零副作用"的直接证据。

### 已译 324 条的分布

| 类 | 译出 | 例 |
|---|---|---|
| TITLE | 7 | `Manouevres 1938`→1938年演习、`Invasion!`→入侵！、`Headquarters`→司令部 |
| PLACE | 232 | `Beda Fomm`→贝达富姆、`Axel`→阿克塞尔、`Balaton`→巴拉顿湖、`Kaping`→… |
| UNIT_W | 47 | `Barrages Cointet Ligne KW`→柯因特障碍 KW防线、`U.62 / 1.Unterseebootsflotilla`→U.62 / 第1潜艇支队 |
| ABBR | 38 | `Luft`→空军、`''UN'' Task Force`→联合国特遣部队、`DCA/[Ebro]`→防空/[Ebro] |

涉及 **119 个文件**，全部通过重建复核（119/119 逐字节一致）。

---

## 四、剩余 106 条：**不是漏译，是两类"不该动"**

### ① 政策保留 54 条（舰名/船名，项目既定口径"军舰舰名保留原文"）

`Achilles` `Andrea Doria` `Admiral Hipper` `Asakaze` `Harukaze` `Matzukaze` `Nagatsuki`
`Arashi` `Nowaki` `Maikaze` `Minegumo` `Almirante Cervera` `RM Alpino` `RM Andrea Doria`
`RM Duca degli Abruzzi` `RM C.Mirabello` `RM L.Malocello` `SMG Squalo` `HMNZ Achilles`
`HMNZ Leander` `HMNoS Eidsvold` `Niciloso Da Recco` `Antonio Pigafetta` `Tazzoli`
`Il Mitragliere` `Il Corazziere` `Il Granatiere` `Aquila` `Luca Tarigo` `Lanciere` `Aviere`
`Ascari` `Nubian` `Richard Beitzen` `Alvise da Mosto` `Bartolomeo Colleoni` `''Ciriza''` 等

> 另：`BRACKET` 184 条（`[XX]` `[XIV]` `[DAF]` `[V]` 等军级/编队标记）、
> `SHIP` 270 条（`HMS xxx` 带前缀的船名）、`ACRO` 1,336 条 + `ABBR` 147 条中的番号数字与
> 武器型号（`101 [30]` `T-34/41[1]` `105mm M2/45` `BA-10[1]` `17 Pdr/78`）——**一律按政策保留**。

### ② 待考 52 条（原文拼写混乱/存疑，**不硬猜**）

**地名 45 条**：多为日军侵华/朝鲜战役地图上的 Wade-Giles 旧拼或明显错拼，
以及南萨哈林日语地名、部分北非/中东音译。

```
Amatsu  Aohima  Badu  Basou  Bayiashan  Belebzika  Chang Cheng  Chang-Chung-Miao
Changan  Chanji  Chiang Ching  Chihsi  Ching Li ou  Chingkulingmiao  Chingyong
Chio  Chiwagai  Chokchidon  Chon-ni  Chongpyong  Chynsandon  Harzy  Hatsutai
Homuku  Hotel Eucliffe  Hudong-ni  Jlesni  Lishan  Mao-Tsu-Fan  Qingguang  Qingyu
Rehrbaon  Renvez  Ruydun-Gova-khe River  Samnagjnin  Sangchihtung  Sarreinsberg
Tondugch'on  Tongjoson mam  Tumuhop  Vzvatl  [DAF]
```

**番号 7 条**：`Reggia`、`Victoria/[Col. A.Vega]`、`Uad Martin`、
`F.Mateos No.9/2 Col.`、`F.Perzagua No.10/2 Col.`、`Gordetxola No.16/2 Col.`、`4/7 Shenshashidan/[14A]`

**外加写明"原数据缺陷"的 1 条**：`Name Error`（出现在 GCN1/GCN2/GCN6_2/GCN9 —— 原作者的
`names.txt` 缺名，引擎显示占位串）。**保留原文**，译成中文反而会掩盖数据问题。

---

## 五、口径结论（提交审阅）

1. **硬漏译已清 286/392（73%）**；余下 106 条中，54 条属**政策保留**、52 条属**待考**。
   ⇒ 若口径认可"舰名保留、待考不硬译"，则 **OLGWW2 `.xscn` 层实质完成**。
2. 待考 45 个地名若要推进，需要**逐条查证原战役地图**（例如 `Chongpyong` 疑为朝鲜定平/井坪、
   `Kaechong` 已按价川处理、`Chonwon` 已按铁原处理）。**这一批建议单独一轮专门做**，
   不做批量音译——音译出来的名字和地图对不上，等于没译。
3. `Name Error` 属**原数据缺陷**，建议保持原样并在 efile 说明里注明。

---

## 六、产物

| 文件 | 说明 |
|---|---|
| `work\efile-nashornpbem\export_residual.py` | 导出未译条目（按类） |
| `work\efile-nashornpbem\context_cards.py` | 生成语境卡 |
| `work\efile-nashornpbem\olgww2-glossary.tsv` | **译名表（真源）** |
| `work\efile-nashornpbem\apply_residual.py` | 字节级定点写回（`--files` / dry-run / `--apply`） |
| `work\efile-nashornpbem\verify_residual.py` | **重建复核** |
| `work\efile-nashornpbem\olgww2-pending.tsv` | 剩余待考/保留清单 |
| `backup\olgww2-xscn-residual-before\` | 119 个改动文件的**改动前**快照（6 MB） |

> ⚠️ `.xscn` **只从 `<efile>\SCENARIO\` 读取**（`docs\14 §发现1` 反汇编定论），
> `TEXT-ZH\SCENARIO\` 下的同名副本是**引擎永不读的死文件** ⇒ 本次**不需要**同步镜像。
