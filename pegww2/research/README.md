# pegww2/research —— 资产索引（**顶层只放 34 个，其余全在下层**）

> 目标：**打开项目只需读 ≤3 个文件**。顶层 = 真源 + 填表 + 生成器输入 + 人读索引；**派生物在 `_derived/`，历史在 `_superseded/`**。
> 判据与整理记录见 [`../方法/资产治理与索引规范.md`](../方法/资产治理与索引规范.md)。整理：2026-10-20（顶层 217 → **34**）。

---

## 一、真源（改这里才会生效，10）

| 文件 | 作用 |
|---|---|
| `ww2-scn-map.tsv` | **场景层主真源**（值模式整行键控；24,031 行 / 24,025 有效键） |
| `ww2-eqp-map.tsv` · `WW2Gui-map.tsv` · `WW2Misc-map.tsv` · `WW2Tips-map.tsv` · `WW2NAME-map.tsv` | 装备 / 界面三表 / 人名 |
| `_scn-file-overrides.tsv` | **per-file 行级覆盖**——优先级**高于**整串键控（同串多义只能走这里） |
| `unit-abbr-map.tsv` | 编制缩写表（番号 batch 的规则来源） |
| `banned.tsv` · `policy-keep-non-gb2312.tsv` | 禁用译法（生成器拦截）· 非 GB2312 有意保留登记 |

## 二、人工填表（下一次改动会直接编辑，6）
`WW2Gui-fill.tsv` · `WW2Misc-fill.tsv` · `WW2Tips-fill.tsv` · `WW2NAME-fill.tsv` · `ww2-eqp-fill.tsv` · `_desc-authored.tsv`

## 三、生成器输入 / 支撑（改它=改结论，6）
`_scn-国别.tsv`（场景→战役国别）· `_u-position-ladder.tsv`（位次→编制阶梯）· `_场景国籍精确归属-20261020.tsv` · `_场景列表台账.tsv` · `_场景列表分组编号提案.tsv` · `_场景列表_最终序号.md`

## 四、口径资产（被 `方法/` 当定稿样本引用，5）
`_scn-sample.tsv` · `_scn-sample-nations.tsv` · `_scn-sample-west.tsv` · `_scn-sample-west-zh.tsv` · `_scn-sample-zh.tsv`

## 五、人读（4）
`README.md`（本文件）· `进度-场景层.md` · `实机复测清单-场景层.md` · `_审核报告-终态-20261019.md` · `_同类译法问题-审计.md` · `各国军语风格口径.md`

## 六、交付物（1）
`番号展开-对照表-20261020.xlsx`（14 表：总览 / 对照表 / 待判 / 后缀码 / 保留 / 舰名 / 场景国籍 / token 映射 / 收口四表）

---

## 七、下层（需要时才进）

| 目录 | 内容 | 说明 |
|---|---|---|
| `_derived/`（20） | **生成器产出，可复算、勿手改** | `_对照-*.tsv`（gen_text/gen_value）· `_scn-stats.tsv`（make_scn_worksheets）· `_u-*-mined.tsv` + `_番号展开-对照表` + 后缀码/保留/舰名/收口四表（gen_desig_table / apply_desig_closure）· `_番号未展开统计*`（nation_rebucket*） |
| `_superseded/merged/`（2） | 同族同构小表**合并**后的单册 | `_scn-fill-autofix-汇总.tsv`（17→1，75 行）· `_审核-终态-20261019-汇总.tsv`（12→1，1,109 行） |
| `_superseded/rounds/`（177） | 分片/待译中间件 | 含上一轮 136 |
| `_superseded/backups/`（12） | `*.pre-*` 写前快照 | |
| `_superseded/retired/`（67） | 历史审计/裁定留痕（仅被文档提及） | 2026-10-20 迁入 |
| `_superseded/tmp/`（15） | 一次性探针 dump | |
| `evidence/`（81） | 可复算证据（含 PNG） | |
| 留痕 | `_superseded/README.md` · `README-assets.md` · `README-assets-v2.md` | 逐文件原路径 |

> ⚠️ **为什么生成器产出必须进 `_derived/`**：否则下次重跑会把顶层重新弄脏，索引立刻过期。
> 已重定向：`gen_text` · `gen_value` · `make_scn_worksheets` · `split_remaining` · `gen_desig_table` ·
> `nation_rebucket` · `nation_rebucket2` · `classify_desig` · `to_xlsx` · `apply_desig_closure` · `resolve_pending`（11 个脚本）。

---

## 八、三条管线与复算

```
① 根级文本：make_worksheets → add_value_reuse → fix_line_map_align → merge_fill → apply_eqp_fill
           → gen_text/gen_value（四道校验）→ deploy.py --text --apply → verify_deploy
② 场景层  ：gen_scn.py dry（五道校验）→ gen_scn.py → deploy_scn.py --apply → verify_deploy
③ 词库门  ：改真源后必跑 ingest_layers.py --apply → converge_plan.py --apply
           → layer_gate.py --full（缺失 0 / 新增偏离 0）+ check_glossary.py
```

```powershell
$env:PYTHONIOENCODING='utf-8'; $env:PYTHONUTF8='1'
& C:\Python314\python.exe work\pegww2\gen_scn.py dry
& C:\Python314\python.exe work\pegww2\verify_deploy.py
& C:\Python314\python.exe work\glossary\layer_gate.py --full
& C:\Python314\python.exe work\pegww2\reorg_research.py --apply   # 资产整理（幂等）
```

> ⚠️ 生成侧从 `testbed/backup/` 读原文；部署侧绝不读原文。
> ⚠️ 改真源不改词库 ⇒ 构建被拒（层表新键须 `ingest_layers --apply` 入库）。
