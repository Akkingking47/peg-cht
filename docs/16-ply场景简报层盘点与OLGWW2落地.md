# 16 · `.ply` 场景简报层：全库盘点与 OLGWW2 落地

日期：2026-09-24　作者：汉化工程

---

## 一、修正 `docs\13` 的规模判断

`docs\13` 说"`.ply` 全库 116 个待译"。**逐文件读内容后修正**：

| 类别 | 数量 | 说明 |
|---|---|---|
| 纯 `\x00` / 0 字节空文件 | **40** | 无语义 |
| **占位模板**（`Intro for X` + `* Intro text *`） | **53** | 作者未填写，**无正文可译** |
| **有真实正文** | **63** | ← **真正需要翻译的** |
| 合计 | 156 | |

> ⇒ 待译规模从 116 **下修到 63**（已完成 5，**剩 58**）。
> **OPENPG 的 43 个 `.ply` 全部是占位模板**（`anvil_i.ply` = `Intro for Anvil\n* Intro text *`），
> 只有 `*sp_i.ply`（16 个）与 `game101_i.ply` 有正文 —— 与 `docs\13` 的判断完全相反。

### 有正文的 63 个分布

| efile | 个数 | efile | 个数 |
|---|---|---|---|
| OPENPG | 17 | OLGWW2 | **5 ✅ 已完成** |
| AO | 16 | OLGCW | 5 |
| BASEKORP | 11 | LUPO | 4 |
| OPENAK | 3 | Clu | 1 |
| KAISER | 1 | 合计 | 63 |

---

## 二、文件结构与显示行为

- **结构**：纯文本，`标题行` + 空行 + `正文段落`。
- **编码**：原文 ASCII / Latin-1（西语重音字节会被按 GBK 误解码 ⇒ 方块＋吃字）。
- **双语言块**：一行 `------`（≥8 个 `-`）分隔 1∼2 个语言块。OLGWW2 的西班牙团队写了
  `canalalbert_i.ply` / `getteriver.ply` 两个文件是 **ES + EN 双块**。
- ★ **引擎只显示第一个语言块** —— 依据：实机弹窗（`docs\14` 图 2）显示的正是 ES 块全文，
  且弹窗可滚动、后续没有出现 EN 块。

> **据此定的写法**：把双块**合并为单一中文块**（不保留原 EN 块）。
> 理由：无论引擎读第一块还是全部，显示结果都是中文，且**不会出现重复**。
> 比"只译第一块、留 EN 第二块"更彻底，比"两块都写中文"更干净。

---

## 三、部署位置

`.ply` 走 **LangDir 优先**（`docs\14 §发现1`：`%sSCENARIO\%s.ply` 的两个 `push` 站点
分别用 `0x11951B0`(LangDir) 与 `[ecx+0x400]`，**不是** EfileRoot）。

但为消除路径歧义，**两处同时写**：

```
<efile>\SCENARIO\<name>.ply            ← 原文位置（覆盖，先备份）
<efile>\TEXT-ZH\SCENARIO\<name>.ply    ← LangDir（首选）
```

> 与 `.xscn` 不同：`.xscn` 只认 EfileRoot，**本次不需要动它**；`.ply` 两处都写。

**编码纪律**：GBK(936)、**无 BOM**、**纯 CRLF**（已验证：0 孤立 LF、0 BOM）。

---

## 四、已完成：OLGWW2 的 5 个（含用户截图里的那个弹窗）

| 文件 | 原 | 现 | 汉字 |
|---|---|---|---|
| `canalalbert_i.ply` | 1989 B（ES+EN） | **532 B** | 210 |
| `getteriver.ply` | 1675 B（ES+EN） | **415 B** | 168 |
| `nice_sfb.ply` | 1221 B | **845 B** | 291 |
| `barceint.ply` | 477 B | **362 B** | 93 |
| `chaco1.ply` | 476 B | **360 B** | 91 |

`canalalbert_i.ply` 正是 `docs\14` 截图里那个"标题中文、正文西班牙语且重音变方块"的弹窗
—— 现已整篇中文，**乱码根因（Latin-1 字节按 GBK 解码）随原文替换一并消除**。

备份：`backup\olgww2-ply-before\`（10 个文件 = 2 处 × 5 个，两处 md5 逐一致）。

工具：`work\efile-nashornpbem\mk_ply_olgww2.py`（写 → 回读校验 → 落盘）。

---

## 五、剩余 58 个（待译）

OPENPG 16（`*sp_i.ply` 场景简介：标题+日期+一段描述+"Converted and Openized by MG43"署名）·
AO 16 · BASEKORP 11（`panther*/tiger*` 完整简报：战役背景＋任务＋Tip＋胜利条件，**单篇最长 1.6 KB**）·
OLGCW 5 · LUPO 4 · OPENAK 3 · Clu 1 · KAISER 1。

**内容类型**：
- **场景简介**（OPENPG `*sp_i.ply`、AO、KAISER、OLGCW）—— 一二百字节，含元信息标签
  （`MAP:` / `EFILE:` / `TYPE:` / `SOUND:`）与作者署名网址。
- **战役简报**（BASEKORP、OPENAK、LUPO、Clu）—— 数百至 1.6 KB，含任务、提示、胜利条件。

**翻译口径补充**（本层新增）：
- 元信息标签译中文：`地图:` / `资料库:` / `类型:` / `音效:`（`EFILE:` 保留标签名亦可）。
- 作者署名、机构名、网址**原样保留**。
- 引语（如 `nice_sfb.ply` 的巴多里奥/罗斯福名言）按通行译文处理。
- 胜利条件术语：`BV/V/TV` → 大胜 / 小胜 / 战术胜利；`VH` → 胜利点。

---

## 六、产物

| 文件 | 说明 |
|---|---|
| `work\efile-nashornpbem\mk_ply_olgww2.py` | OLGWW2 5 个中文 `.ply` 写入器 |
| `backup\olgww2-ply-before\` | 10 个改动前快照（含 `TEXTZH-` 前缀版） |
| `work\efile-nashornpbem\ply_struct.py` | `.ply` 结构解析（语言块/分隔行/编码） |
