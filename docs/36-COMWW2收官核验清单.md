# 36 · COMWW2 收官核验清单（2026-09-30）

> COMWW2 本轮新增交付：`.txt` 层 100%（1,032 文件）＋ `.tmsg` 层（15 个有正文）。
> **本文件只列「怎么自己核」与「还剩什么」，不含新改动。**
> ⚠️ 硬纪律：**需要截图时必须停下**，由用户手动截取；**严禁自行启动/点击游戏**。

---

## 一、本轮交付清单（可直接核）

| 项 | 位置 | 规模 | 可核方式 |
|---|---|---|---|
| 场景 `.txt` | `D:\OpenPG2\EFILE_COMWW2\TEXT-ZH\SCENARIO\` | **1,032 / 1,032** | 与 `SCENARIO\` 同名文件逐个比对：行数、换行类型、GBK 可解、无 BOM |
| `.tmsg` | `D:\OpenPG2\EFILE_COMWW2\SCENARIO\*.tmsg` | **20 个（15 个有正文）** | `python work\tmsg\tmsg.py --efile COMWW2 verify` |
| 根级四件套 | `TEXT-ZH\{equip,names,nations,strings_efile}.txt` | 2,333 行 | 逐行对齐原文 |
| `efile.txt` | `TEXT-ZH\efile.txt` | 211 B | 原文侧 md5 未变 |
| `.xscn` | `SCENARIO\*.xscn`（原地） | 18,030 条 / 98.0% | `python work\xscn\xscn.py --efile COMWW2 verify` |

**回滚**：删 `TEXT-ZH\SCENARIO\` 整目录即回退场景文本；`.tmsg` 从
`backup\ORIGINAL-EFILE_COMWW2\*.tmsg` 还原；`.xscn` 从 `backup\ORIGINAL-EFILE_COMWW2\SCENARIO\` 还原。
**原文侧零改动**（`SCENARIO\*.txt` mtime 仍 2018/2019）。

---

## 二、实机核验建议（切到 COMWW2 后）

改 `Settings.cfg`：`EFolder=efile_comww2\`（**确认目录名大小写**）、`UI_Lang=strings-zh`、
`Font1/2=simhei.ttf`、`SzFont1/2=12`。

一次进城看这几处（**都属本轮或本轮改动的层**）：

| # | 看哪一屏 | 期望 |
|---|---|---|
| 1 | 主界面 → 战役选择 | 战役/场景名中文（`.xcam` 内的名称是引用，正常可能仍为原文） |
| 2 | 进任一剧本的**开局简报** | 应显示中文（prose 层） |
| 3 | **战斗简报 / 胜负结算屏** | 应显示中文，且等级用词为「决定性胜利 / 胜利 / 险胜 / 失败」 |
| 4 | 胜利条件提示（`konrad` / `nordwind` 等剧本） | 应显示中文（`.tmsg` 层，**首尾空行排版不变**） |
| 5 | 地图胜利点提示 / 部署提示 | 「胜利点」「部署格」用词一致，**不应再出现 `VH`/`DH`** |
| 6 | 单位面板、地图悬浮提示 | 沿用已交付的 exe 补丁（无需本轮复核） |

> ⚠️ 第 4 项特别值得看：`.tmsg` 的**首尾空行段**是屏幕定位指令，若排版位置跑偏即为异常。

---

## 三、COMWW2 仍余（按优先级）

| # | 项 | 规模 | 性质 |
|---:|---|---|---|
| 1 | `USERSCEN\` | 2 `.xscn`（29/37 KB）+ 2 `.ply` + 2 `readme-*.txt` | ❌ **全英文、0 汉字**，且**从未纳入任何统计**（`progress.py` 只扫 `SCENARIO\`）。落点：`.xscn` 原地改，`.ply`/`.txt` → `TEXT-ZH\SCENARIO\` |
| 2 | label 保留集里的英文编制名 | **43 条唯一**（`216th Battery`、`4th Anti-tank Brig.`、`10th Sapernii Brig.`…） | ❌ 游戏内仍显示英文；根因＝保留集整批继承 `.xscn` 残留，残留混进普通英文词 |
| 3 | `readme.doc` | 1 个（45 KB OLE2 Word） | 🟡 战役说明，玩家可见但非引擎渲染 ⇒ **待批** |
| 4 | `.front`(199) / `.xcam`(10) | — | ✅ **判性结论：无文本可译**（`.front` 非零字节 3–4 个；`.xcam` 是文件名引用表） |
| 5 | `L8` 位图 | efile 自有 `hex_text.png` 3,105 B（原件 1,880 B） | ✅ 已重绘；`mouse_*` 无自有版本 ⇒ 走根级已汉化版 |

---

## 四、下一批建议（`docs\24` 优先级）

COMWW2 主体已收官，按 `docs\24` 的 B 类顺序，下一批是 **B6 GCE**（`.xscn` 唯一 1,649 · 根级 4 件套 · 144 个场景 `.txt`，
判为「小」档）。开工前按纪律做**全 efile 量测**，并复用本轮已泛化的工具链：

```
根级四件套（gen_root_zh.py 参数化）→ .xscn（xscn.py + build_dict.py + gen_xscn_batch.py）
→ 场景 .txt（txt_workbench.py → label 层 gen_label_zh.py / prose 层 split+merge+gen_prose_zh.py）
→ .tmsg/.xsch（tmsg.py / xsch.py）→ 位图
```

⚠️ **两个必须带过去的工具修正**（本轮踩到）：
1. `gen_prose_zh.py` 的 `detect_nl()`（纯 LF 判定）与「`plan` 元组携带 `nl`」—— 否则 LF 文件部署中断；
2. 生成器只写 **rep** ⇒ 必须再跑 `propagate_dup_txt.py` 按原文 md5 铺满同组重复文件。
