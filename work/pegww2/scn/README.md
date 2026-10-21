# work\pegww2\scn —— 场景层「番号/国籍/年代」分析工具集

> **2026-10-20 脚本树合并留痕**：本目录全部内容原在 `pegww2\work\scn\`，
> 为消除「两处脚本树」，一次性迁入 `work\pegww2\`（与全工作区约定 `work\<项目>\` 对齐）。
> 迁移方式：`.py` 本未被 git 跟踪 ⇒ 普通移动；`.mjs` 已跟踪 ⇒ `git mv`（保留历史）。
> **数据未随迁**：`pegww2\work\scn\chunks\`（21 个 `chunk_*.tsv` + `manifest.json`，4,021 行 prose 原英文）
> 是**原版英文参照资产**且被 `research\_scn-file-overrides.tsv` 当证据引用，按 `.gitignore`
> 「`work/` 只留脚本，`pegww2/work/` 留给数据」的白名单**留在原位**。
> 原 `pegww2\work\scn\out\`（切片派生物，已被 `**/out/` 忽略）已删除。

## 目录内容

| 组 | 文件 | 用途 |
|---|---|---|
| 番号展开 | `gen_desig_table.py` | ⭐ **主生成器**：产出 `research\_derived\_番号展开-对照表-*.tsv` 等四表（幂等可复跑） |
| 番号展开 | `classify_desig.py` · `pend_breakdown.py` · `pos_stats.py` · `pos_stats2.py` | 按形态/位次统计未展开番号 |
| 国籍归属 | `nation_probe.py` · `nation_probe2.py` · `nation_rebucket.py` · `nation_rebucket2.py` | `.SCN` 单位块（S0=11350/65B）→ 逐单位精确国籍 |
| 年代维度 | `era_diag.py` | 场景年代分桶诊断 |
| 挖掘 | `mine_pairs.py` | 原版备用 `_u` ↔ 已译部署 `_u` 同比对，挖实测映射 |
| 校验 | `verify_scn.py` · `verify2.py` · `verify3.py` · `check_fmt.py` · `check_orphan.py` | 场景/单位/格式/孤儿核对 |
| 抽样 | `review_sample.py` · `sample_table.py` | 人工复核取样 |
| 出表 | `to_xlsx.py` | 对照表 → xlsx（交付物） |
| 归档 | `reorg_rounds.py` | 轮次片归档到 `research\_superseded\rounds\` |
| 审计 | `audit_ws.py` · `audit_ws2.py` | 工作区重复/引用审计 |
| JS（一次性）| `scn_prose_make.mjs` · `scn_prose_extract.mjs` · `scn_prose_assemble.mjs` · `prompt.mjs` | prose 批次切分/组装/提示词；**输入 `research\_scn-todo-prose.tsv` 已归档 ⇒ 除 `prompt.mjs` 外均已失效** |

## 口径（勿改）

- `.SCN` 单位块：起始 `S0=11350`，65 字节/单位，`+34`=阵营、`+36`=国籍 id；国籍 id = `WW2Gui.txt` 行号 + 1。
- `_u.txt` 行 i ↔ 单位 i；行 0 为 `Dummy` 时行 i ↔ 单位 i-1。
- **年代维度**：`.SCN` 头部无年份 ⇒ 取场景自身日期，否则取所属战役年代众数；分桶 `1939-41 / 1942-43 / 1944-46 / ?`。
- 生成物一律落 `pegww2\research\_derived\`（**勿手改**）。

## 跑法

```powershell
$env:PYTHONIOENCODING='utf-8'; $env:PYTHONUTF8='1'
C:\Python314\python.exe work\pegww2\scn\gen_desig_table.py     # 重算番号四表
C:\Python314\python.exe work\pegww2\scn\to_xlsx.py             # 出交付 xlsx
```

> ⚠️ 本目录脚本一律用**绝对路径**常量（`RES` / `BK` / `SCN` / `DEP`），与所在目录无关，迁址不影响运行。
> 新脚本请按 `work\SCRIPTS.md` 治理规则先行登记。
