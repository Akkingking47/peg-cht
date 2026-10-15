# 37 · 全库 `USERSCEN` 盲区量测与 COMWW2 清账（2026-09-30）

> **本文件是排期级发现**：`USERSCEN\`（用户场景目录）**从未进入任何进度报表**。
> `work\audit\progress.py` 只扫 `SCENARIO\` 与 `TEXT-ZH\SCENARIO\`。

---

## 一、为什么以前看不见

| 事实 | 说明 |
|---|---|
| `progress.py` 扫描范围 | `<efile>\SCENARIO\` 与 `<efile>\TEXT-ZH\SCENARIO\` |
| `USERSCEN\` 位置 | `<efile>\USERSCEN\`（与 `SCENARIO\` **平级**） |
| 后果 | 各 efile 的用户场景 `.xscn` / `.ply` / `.txt` 全部不在矩阵里，**0% 也看不出来** |

## 二、全库实测（`work\audit\measure_userscen.py`）

| efile | `.xscn` | 含拉丁条目 | `.ply` 有正文 | `.ply` 字符 | `.txt` | `.txt` 字符 | 状态 |
|---|---:|---:|---:|---:|---:|---:|---|
| COMWW2 | 2（**仅标题**） | 0 | 2 | 2,640 | 2 | 239 | ✅ **已清** |
| GCE | 14 | **1,740** | 10 | 8,304 | 5 | 6,124 | ⬜ |
| KAISER | 31 | **3,955** | 22 | 24,134 | 9 | 8,326 | ⬜ |
| PzLIGA | 150 | **19,564** | 149 | 111,244 | 2 | 200 | ⬜ |
| **合计** | **197** | **25,259** | **183** | **146,322** | **18** | **14,889** | |

> `.xscn` 的「含拉丁条目」＝ 串区里仍含 ASCII 字母的条目数（即待译串的上界）。
> `PzLIGA` 一家就等于**一个正编 efile 的量级**。

## 三、结构（实测，4 个 efile 同型）

| 文件 | 结构 | 落点 |
|---|---|---|
| `.xscn` | 与 `SCENARIO` 同格式（`<N:…>` + `u16 标题长 + 标题` + 组表）。**COMWW2 的组表为 `[0,0]`（只有标题）**；GCE/KAISER/PzLIGA 有串区 | **原地改**（引擎读 `<efile>\USERSCEN\`，无 TEXT-ZH 覆盖层） |
| `.ply` | **纯文本简报**（无二进制头，与 `AG\TEXT-ZH\SCENARIO\*.txt` 同型） | `TEXT-ZH\USERSCEN\` |
| `.txt` | 纯文本说明 | `TEXT-ZH\USERSCEN\` |

## 四、COMWW2 清账明细（全库首个被汉化的 USERSCEN）

| 文件 | 处理 | 结果 |
|---|---|---|
| `khalkin1.xscn` | 标题 `Khalkin Gol 1 : Japanese Attack` → **哈拉哈河1：日军进攻** | 29,744 → 29,732 B；**只动标题槽 33 B**，尾部 4 B 逐字节相同 |
| `khalkin2.xscn` | 标题 `Khalkhin Gol 2 : Zhukov's Strike` → **哈拉哈河2：朱可夫突击** | 37,957 → 37,946 B；**只动标题槽 34 B** |
| `khalkin1_i.ply` | 诺门罕战役简报（CRLF，含前导空行） | → `TEXT-ZH\USERSCEN\`，**308 汉字**，1,417 → 717 B |
| `khalkin2_i.ply` | 朱可夫八月攻势（**无换行的单段**） | **263 汉字**，1,227 → 620 B |
| `readme-khalkin1/2.txt` | 剧本说明（9 行，CRLF） | **13 / 16 汉字** |

**校验**：`.xscn` 结构异常 0；`.ply`/`.txt` GBK 无 BOM、换行沿用原文（4 个全 CRLF）；
备份 `backup\ORIGINAL-EFILE_COMWW2\USERSCEN\`（7 个原件）。

**工具**（可复用于余下 3 个 efile）：
- `work\userscen\userscen_tool.py` —— 复用 `xscn.py` 的 `parse()` / `write_checked()`；
  `titles` 列标题、`verify` 查结构、`apply --map` 写标题（**先写 `.new` → parse 回读对拍组表/条目数 → 才 replace**）
- `work\userscen\deploy_cmww2_userscen.py` —— `.ply`/`.txt` 落 `TEXT-ZH\USERSCEN\`，
  **只给中间文字，前后白空与内部换行从原文继承**（沿用 `.tmsg` 层的教训）

## 五、排期影响（重要）

1. **USERSCEN 必须单列一个层**（记入 `MEMORY.md` §一 与 §七.13），否则永远不在报表里；
2. 它**不能混进各 efile 的「收官」判据**——判据仍按 `SCENARIO\` 定义，但**交付口径要注明**；
3. 三个待办 efile 的体量：**PzLIGA ≫ KAISER > GCE**（PzLIGA 19,564 条串 + 111K 字符简报，
   与 KAISER/LXF 同级）；建议**跟随各自 B 批一起做**，而不是单独插队；
4. GCE 是下一个 B 批（B6）⇒ **GCE 的 USERSCEN（14 `.xscn` / 1,740 条 + 10 `.ply` + 5 `.txt`）
   应与 GCE 主目录同批处理**，工具已就绪。
