# work 脚本三态索引（active / one-shot / deprecated）

> **本文件**：`work\` 下 `.py` 脚本的生命周期索引，由 **C-1「脚本生命周期治理」** 建立（2026-10-15）。
> **用途**：回答「哪个是当前流水线 / 哪个跑过一次就没用了 / 哪个已被取代」——
> 新人先看本文件的**§1 活跃清单**，再去 `_scratch\` 之外找脚本；`work\_scratch\` 里的脚本**不得被活跃流水线引用**。

## 三态定义

| 态 | 存放位置 | 判据 | 允许被引用 |
|---|---|---|---|
| **active 活跃** | `work\` 各子目录（**不含 `_scratch\`**） | ① 被回归入口 / D-1 生成链直调，或 ② 被其他活跃件引用，或 ③ 无入引用但列入不可移动白名单 | 是 |
| **one-shot 一次性** | `work\_scratch\`（保留原相对路径） | 全工作区**入引用 = 0** 的一次性审计/迁移脚本 | **否**（新代码不得引用；要复用请先提升回 `work\` 并登记本文件） |
| **deprecated 已废弃** | 原位（不移动） | 有入引用，且引用处**明确写着**已废弃 / 旧版 / 不要再跑 | 仅历史引用 |

## 治理规则

1. **新脚本先写进本文件**：落盘后到 §1（活跃）或 §2（一次性）登记一行，写清用途与归属项目。
2. **一次性脚本一律进 `work\_scratch\`**：跑完即迁，用 `git mv` 保留历史，**不要**「新建 + 删除」。
3. **移动前必须证明零入引用**：在全工作区（含 `docs\`、`peg*\`、`.workbuddy\`、`*.md`、`*.cmd`、`*.ps1`、其他 `.py`）搜**文件名（不带路径）**。
   - 命中 0 处 ⇒ 可移动；
   - 命中 ≥1 处 ⇒ 不移动；**引用来自 `docs\` 也一律不移动**（改文档会与 A-2/D-3 的效力状态栏冲突），只在 §4 登记；
   - **子串误配不算命中**：`_check.py` 被 `bridge_check.py` 命中不构成引用，须逐条人工确认。
4. **移动后回归必须全绿**：`C:\Python314\python.exe work\regression.py`（需 `PYTHONIOENCODING=utf-8`），
   rc=0 且「新增 0 条 / 消失 0 条 / 变化 0 条」。不为 0 ⇒ 立刻 `git mv` 回原位并列入 §4。
5. **`work\_scratch\` 是只读存档区**：允许读、允许 `git mv` 回来复活；**禁止**外部脚本 `import` 或 `subprocess` 调用其中文件。
6. **不许删脚本**：本治理只做「移动 + 注释 + 索引」，任何删除都要单独走流程（历史可追）。

---

## 1. active 活跃清单（不可移动）

### 1.1 门禁 / 机制件 / 生成链骨架（硬约束：不可移动、不可加 DEPRECATED）

| 脚本 | 角色 |
|---|---|
| `work\regression.py` | 回归总入口（门禁编排 + 基线比对） |
| `work\lineage.py` | 溯源机制件（D-1 已接入） |
| `work\lint_zh.py` | 中文体检机制件 |
| `work\lint_rules.tsv` | 体检规则表（数据，非脚本） |
| `work\build-zh.ps1` | 构建入口 |
| `work\glossary\layer_gate.py` | 回归直调：层表门 |
| `work\glossary\audit_authority.py` | 回归直调：译名库权威核对 |
| `work\glossary\build_glossary.py` | D-1 生成器：标准译名库 |
| `work\_sync-audit\verify_naming.py` | 回归直调：命名校验 |
| `work\_sync-audit\residual_scan.py` | 回归直调：残留扫描 |
| `work\audit\progress.py` | 回归直调：全库进度 |
| `work\pegww2\verify_deploy.py` | 回归直调：ww2 部署 sha |
| `work\peg\peg_launcher.py` | 回归直调：启动器自检 |
| `work\peg\gen_scn_zh.py` | D-1 生成器：PeG 场景 |
| `work\pegww2\gen_scn.py` | D-1 生成器：PeG-WW2 场景 |
| `work\pegww2\build_glossary_unified.py` | D-1 生成器：统一译名库 |

### 1.2 被活跃件引用而留在原位的脚本

共 **423** 个（判据：全工作区入引用 ≥1，或引用来自 `docs\`）。
完整清单与逐条命中原文见 §4；`work\out\_c1_notmoved_refs.txt` 是逐行命中明细（含每处引用的文件与行）。

---

## 2. one-shot 一次性清单（已移入 `work\_scratch\`）

**本次移动 288 个**（占候选 711 个的 40.5%）。目录结构与原路径一致，可用 `git mv work\_scratch\<...> work\<...>` 复活。

| 原目录 | 个数 |
|---|---|
| `work\` | 3 |
| `work\_scan-pegbranch\` | 4 |
| `work\_sync-audit\` | 25 |
| `work\ao\` | 2 |
| `work\atomic\` | 12 |
| `work\atomic\scn\` | 1 |
| `work\atomic\zh\` | 17 |
| `work\audit\` | 1 |
| `work\basekorp\` | 34 |
| `work\basekorp\chunks\` | 1 |
| `work\clu\` | 8 |
| `work\comww2\` | 6 |
| `work\crash-20260924\` | 11 |
| `work\efile-nashornpbem\` | 22 |
| `work\efile-poc\` | 26 |
| `work\efile_pzliga\` | 2 |
| `work\gce\` | 7 |
| `work\glossary\` | 18 |
| `work\peg\` | 42 |
| `work\pegww2\` | 40 |
| `work\xscn\` | 6 |

<details><summary>展开全部 288 个（按原目录分组）</summary>

**`work\`**（3）

- `_diag_session_interrupt.py`
- `_verify17.py`
- `gen_part17.py`

**`work\_scan-pegbranch\`**（4）

- `placename_crosscheck.py`
- `scope_check.py`
- `stemfix_measure.py`
- `undetermined_diag.py`

**`work\_sync-audit\`**（25）

- `audit_brief_map2.py`
- `audit_brief_map3.py`
- `audit_place_mistag.py`
- `cand_overrides.py`
- `dbg_bucket.py`
- `explain_residual2.py`
- `explain_residual3.py`
- `fix_brief_faction.py`
- `probe_amur.py`
- `probe_amur_file.py`
- `probe_brief_faction.py`
- `probe_cats.py`
- `probe_dupkeys.py`
- `probe_glossary.py`
- `probe_keep62.py`
- `probe_lodz_lines.py`
- `probe_names.py`
- `probe_pairs.py`
- `probe_src.py`
- `probe_stem_dates.py`
- `probe_struct.py`
- `probe_textzh.py`
- `scan_peg_side.py`
- `triage_ovr_diff.py`
- `verify_place_forks.py`

**`work\ao\`**（2）

- `ao-names-zh.py`
- `ao-scenario-zh.py`

**`work\atomic\`**（12）

- `_verify04.py`
- `atomic-equip-zh.py`
- `atomic-names-zh.py`
- `atomic-nations-strings.py`
- `atomic-xscn-04-zh.py`
- `build_part01.py`
- `build_part06.py`
- `gen07.py`
- `gen_part12.py`
- `gen_part15.py`
- `gen_part19.py`
- `gen_part20.py`

**`work\atomic\scn\`**（1）

- `verify_batches.py`

**`work\atomic\zh\`**（17）

- `_keeplist03.py`
- `_verify.py`
- `_verify03.py`
- `_verify10.py`
- `_verify11.py`
- `_verify14.py`
- `_verify16.py`
- `build_part02.py`
- `build_part03.py`
- `build_part08.py`
- `build_part09.py`
- `build_part10.py`
- `build_part11.py`
- `build_part13.py`
- `build_part14.py`
- `build_part16.py`
- `build_part18.py`

**`work\audit\`**（1）

- `_recount_remaining.py`

**`work\basekorp\`**（34）

- `_check.py`
- `_chk17.py`
- `_cls2.py`
- `_cons.py`
- `_cov.py`
- `_ctx.py`
- `_ctx2.py`
- `_fix_stat.py`
- `_gen09.py`
- `_gen17.py`
- `_incons.py`
- `_mask.py`
- `_peek.py`
- `_probe2.py`
- `_probe3.py`
- `_probe_label.py`
- `_probe_leak.py`
- `_q.py`
- `_resid.py`
- `_suf.py`
- `_tok.py`
- `_toklist.py`
- `build_crossmap.py`
- `build_txt_precedent.py`
- `gen_bn2_zh.py`
- `gen_bom_zh.py`
- `gen_dr_zh.py`
- `gen_equip.py`
- `gen_gg_zh.py`
- `gen_it_zh.py`
- `gen_prose_data.py`
- `gen_rawfix.py`
- `gen_root.py`
- `gen_xsch.py`

**`work\basekorp\chunks\`**（1）

- `gen_title.py`

**`work\clu\`**（8）

- `build_clu_equip.py`
- `build_clu_xscn.py`
- `make_clu_efile_txt.py`
- `make_clu_small_root.py`
- `make_equip_chunks.py`
- `make_txt_chunks.py`
- `measure_clu_root.py`
- `split_clu_equip.py`

**`work\comww2\`**（6）

- `fix_label_keep.py`
- `gen_b6b1.py`
- `gen_b6b2.py`
- `gen_b6b3.py`
- `gen_b6b_words.py`
- `probe_b6.py`

**`work\crash-20260924\`**（11）

- `audit_final.py`
- `bisect2.py`
- `bisect3.py`
- `bisect4.py`
- `bisect5.py`
- `ctx_dump.py`
- `dbgrun.py`
- `dbgrun2.py`
- `diffprobe.py`
- `find_hole.py`
- `pe_map.py`

**`work\efile-nashornpbem\`**（22）

- `analyze_hintblock.py`
- `build_equip_blk3.py`
- `build_intro_blk1.py`
- `build_ui_blk1.py`
- `check_intro.py`
- `clickuntil.py`
- `dump_xscn.py`
- `fix_title.py`
- `goto_loaded.py`
- `make_probes.py`
- `mkprobe_names.py`
- `mkvariants.py`
- `patch_hintblock.py`
- `probe_toolbar.py`
- `readout.py`
- `replay_flow.py`
- `replay_full.py`
- `runtime-verify.py`
- `scan_division2.py`
- `scan_division_trunc.py`
- `setsettings.py`
- `verify_ply.py`

**`work\efile-poc\`**（26）

- `_allrefs.py`
- `_callers.py`
- `_callers2.py`
- `_check.py`
- `_chunk.py`
- `_consist.py`
- `_diag.py`
- `_dump.py`
- `_eqref.py`
- `_findvar.py`
- `_gv8.py`
- `_gvrefs.py`
- `_langfiles.py`
- `_langname.py`
- `_merge.py`
- `_plan.py`
- `_resrefs.py`
- `_strings.py`
- `_style.py`
- `_survey.py`
- `_trace.py`
- `_trackgv.py`
- `_xref.py`
- `_xscnmerge.py`
- `_xscnplan.py`
- `_xscntodo.py`

**`work\efile_pzliga\`**（2）

- `gen_p4_zh.py`
- `gen_p6.py`

**`work\gce\`**（7）

- `audit_gce_dict.py`
- `classify_gce_dict.py`
- `export_userscen_todo.py`
- `make_gce_build.py`
- `make_gce_cov.py`
- `make_gce_txt.py`
- `rebuild_gce_todo.py`

**`work\glossary\`**（18）

- `audit_reference_rate.py`
- `fix_aasc_and_era_probe.py`
- `fix_faction_german.py`
- `fix_faction_kishinev.py`
- `fix_faction_r701_label.py`
- `fix_from_audit.py`
- `fix_last_hint.py`
- `fix_lodz_era.py`
- `fix_map_grounded.py`
- `fix_prose.py`
- `fix_roster_us.py`
- `gen_pending_supplement.py`
- `merge_roster_batch2.py`
- `plan_fixes.py`
- `probe_tarnopol6v.py`
- `probe_tarnopol_side.py`
- `survey_openpg_units.py`
- `sweep_c.py`

**`work\peg\`**（42）

- `_add_mode_flag.py`
- `_add_play_mode.py`
- `_append_memory_61.py`
- `_append_memory_62.py`
- `_append_memory_63.py`
- `_append_memory_64.py`
- `_append_memory_65.py`
- `_append_memory_66.py`
- `_append_memory_67.py`
- `_append_memory_68.py`
- `_append_memory_69.py`
- `_append_memory_70.py`
- `_ddc_blit.py`
- `_ddc_summary.py`
- `_dump2.py`
- `_find_logger.py`
- `_fix_consts.py`
- `_fix_launcher_args.py`
- `_fix_md5.py`
- `_fix_play_settings.py`
- `_fix_write_call.py`
- `_gui_flag_test.py`
- `_make_ddraw_cmds.py`
- `_make_ddraw_play_cmd.py`
- `_make_diag_cmd.py`
- `_measure_figs.py`
- `_test_diag_cmd.py`
- `_tune_play_settings.py`
- `disasm_gui.py`
- `disasm_text.py`
- `patch-month-zh.py`
- `peek_ctrl.py`
- `prob1_strings.py`
- `prob2_enc.py`
- `prob3_67.py`
- `prob4_imm_sites.py`
- `prob_mouse2.py`
- `prob_panel1.py`
- `prob_panel3.py`
- `prob_panel6.py`
- `prob_panel7.py`
- `probe_blt.py`

**`work\pegww2\`**（40）

- `_fill_m_02.py`
- `apply_term_rulings.py`
- `audit_desc.py`
- `audit_shipnames.py`
- `check_nameslot_fp.py`
- `cleanup_tasks.py`
- `deploy_ply.py`
- `extract_eqp_vocab.py`
- `final_audit.py`
- `fix_names_consistency.py`
- `fix_nameslot.py`
- `fix_nameslot_v2.py`
- `fix_redux_consistency.py`
- `fix_shipnames.py`
- `gen_tokens.py`
- `gen_trial.py`
- `m_full_1.py`
- `m_full_2.py`
- `m_full_3.py`
- `m_full_4.py`
- `m_full_5.py`
- `m_place.py`
- `patch-mbcs-ww2.py`
- `rebuild_fill.py`
- `reuse_analysis.py`
- `sample_nations.py`
- `sample_scn.py`
- `sample_west.py`
- `scan_campaign.py`
- `scan_campaign2.py`
- `scan_campaign3.py`
- `scan_campaign4.py`
- `scan_desc_source.py`
- `scan_eqp_damage.py`
- `scan_nameslot2.py`
- `scan_pollution.py`
- `scan_pursuit.py`
- `scan_unitpanel.py`
- `split_scn_todo.py`
- `verify_name.py`

**`work\xscn\`**（6）

- `_analyze2-openpg.py`
- `_analyze3-openpg.py`
- `_analyze4-openpg.py`
- `_analyze5-openpg.py`
- `_gen13.py`
- `audit_dict_quality.py`

</details>

---

## 3. deprecated 已废弃清单

**本次新增 DEPRECATED 头注：0 个。**

判定条件（任务书硬约束 2）：脚本**有入引用**、且**引用处明确写着**「已废弃 / 旧版 / 不要再跑」才加头注、且只加注释不改代码。
本轮对全部 423 个「有引用故未移动」脚本做了两轮独立扫描（`git grep -F` + 33,521 个文本文件全工作区 substring），
只有 5 个脚本的引用行含「一次性 / 遗留 / 作废」类词，且**全部是在说别的东西**（详见 §5「与任务书不符处」），
因此按「宁可不动、不可误标」原则**一个头注都没加**。

| 脚本 | 引用行 | 为什么不算废弃声明 |
|---|---|---|
| `work\basekorp\gen_tmsg.py` | `work\_scratch\basekorp\_fix_stat.py:2` 「一次性：修正 **gen_tmsg.py** 末尾的汉字统计行」 | 「一次性」形容的是 `_fix_stat.py`，`gen_tmsg.py` 是被修正的对象 |
| `work\tmsg\tmsg.py` | 同上（`gen_tmsg.py` 子串误配） | 同上，且命中是子串 |
| `work\comww2\gen_prose_zh.py` | `work\comww2\fix_prose_rest.py:82` 「基础表**遗留**的等级串」 | 「遗留」形容的是数据串，不是脚本生命周期 |
| `work\peg\gen_gui030_zh.py` | `work\lint_rules.tsv:43` 「第32轮试行版面板名已**作废**」 | 「作废」形容的是某个**译文取值**，脚本本身仍在规则表里被引用 |
| `work\pegww2\merge_fill.py` | `pegww2\research\WW2Gui-fill.tsv:2` 「@KEEP 表示原样保留，@订正 表示覆盖前作**遗留**值」 | 「遗留」形容的是前作数值，且该行是**用法说明**（正在用它） |

---

## 4. 有引用故未移动的脚本（全部 423 个）

**不移动的三条理由**：① 被活跃流水线真引用；② 引用来自 `docs\`（改文档会与 A-2/D-3 冲突）；③ 引用来自历史记忆 `.workbuddy\memory\`（改它不是本任务边界）。

| 脚本 | 入引用处数 | 主要引用来源（前 3） |
|---|---|---|
| `work\_audit_skills.py` | 3 | `.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\MEMORY.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md` |
| `work\_cleanup_apply.py` | 3 | `.workbuddy\memory\2026-10-10.md`<br>`docs\39-冗余扫描报告-2026-10-10.md`<br>`docs\39-冗余扫描报告-2026-10-10.md` |
| `work\_cleanup_scan.py` | 3 | `.workbuddy\memory\2026-10-10.md`<br>`docs\39-冗余扫描报告-2026-10-10.md`<br>`docs\39-冗余扫描报告-2026-10-10.md` |
| `work\_scan-pegbranch\decode_cwgen.py` | 1 | `work\_scan-pegbranch\README.md` |
| `work\_scan-pegbranch\gate_keycheck.py` | 1 | `docs\44-地名三维规则纳入词库方案.md` |
| `work\_scan-pegbranch\placename_verdict.py` | 6 | `docs\43-地名经验吸收裁定-方法与译名分层.md`<br>`glossary\SOURCES.tsv`<br>`glossary\SOURCES.tsv` |
| `work\_split_sd25.py` | 2 | `.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md` |
| `work\_split_skills.py` | 3 | `.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\MEMORY.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md` |
| `work\_sync-audit\apply_naming.py` | 9 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`docs\51-残留专名定名与词库重建.md` |
| `work\_sync-audit\apply_naming_peg.py` | 6 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`docs\52-词库更新铺设到PeG及PeG-WW2.md` |
| `work\_sync-audit\audit_brief_map.py` | 1 | `docs\68-汉化工程系统性审查与改进建议报告.md` |
| `work\_sync-audit\audit_brief_map4.py` | 1 | `work\_sync-audit\dbg_bucket.py` |
| `work\_sync-audit\audit_brief_map5.py` | 4 | `docs\47-词库升级与两作成品同步评估.md`<br>`docs\47-词库升级与两作成品同步评估.md`<br>`docs\47-词库升级与两作成品同步评估.md` |
| `work\_sync-audit\audit_faction_places.py` | 4 | `docs\49-按场景定点覆盖与词库第三真源入库.md`<br>`docs\49-按场景定点覆盖与词库第三真源入库.md`<br>`glossary\SOURCES.tsv` |
| `work\_sync-audit\audit_shipped_vs_lib.py` | 3 | `docs\47-词库升级与两作成品同步评估.md`<br>`docs\47-词库升级与两作成品同步评估.md`<br>`work\_sync-audit\probe_keep62.py` |
| `work\_sync-audit\cmp_authority.py` | 3 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`docs\50-cat误标治理与覆盖表并入词库.md` |
| `work\_sync-audit\cmp_gloss_postnaming.py` | 2 | `docs\52-词库更新铺设到PeG及PeG-WW2.md`<br>`docs\52-词库更新铺设到PeG及PeG-WW2.md` |
| `work\_sync-audit\explain_residual.py` | 1 | `docs\50-cat误标治理与覆盖表并入词库.md` |
| `work\_sync-audit\list_residual_names.py` | 2 | `docs\51-残留专名定名与词库重建.md`<br>`docs\51-残留专名定名与词库重建.md` |
| `work\_sync-audit\plan_place_cat_fix.py` | 1 | `docs\50-cat误标治理与覆盖表并入词库.md` |
| `work\_sync-audit\probe_align.py` | 1 | `docs\51-残留专名定名与词库重建.md` |
| `work\_sync-audit\probe_bon76.py` | 7 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`docs\52-词库更新铺设到PeG及PeG-WW2.md` |
| `work\_sync-audit\probe_keep_source.py` | 2 | `docs\49-按场景定点覆盖与词库第三真源入库.md`<br>`docs\49-按场景定点覆盖与词库第三真源入库.md` |
| `work\_sync-audit\probe_null.py` | 2 | `docs\47-词库升级与两作成品同步评估.md`<br>`work\_sync-audit\audit_brief_map4.py` |
| `work\_sync-audit\probe_occ_state.py` | 1 | `docs\51-残留专名定名与词库重建.md` |
| `work\_sync-audit\probe_stem.py` | 1 | `docs\47-词库升级与两作成品同步评估.md` |
| `work\_sync-audit\probe_ternopil.py` | 2 | `docs\47-词库升级与两作成品同步评估.md`<br>`docs\47-词库升级与两作成品同步评估.md` |
| `work\_sync-audit\promote_regen.py` | 2 | `docs\49-按场景定点覆盖与词库第三真源入库.md`<br>`docs\49-按场景定点覆盖与词库第三真源入库.md` |
| `work\_sync-audit\scan_residue_all.py` | 4 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`docs\52-词库更新铺设到PeG及PeG-WW2.md` |
| `work\_sync-audit\verify_name_converge.py` | 4 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`docs\48-地名收敛与两作成品同步执行记录.md` |
| `work\ag-scenario\deploy.py` | 5441 | `requirements.txt`<br>`.workbuddy\memory\2026-09-28.md`<br>`.workbuddy\memory\2026-09-28.md` |
| `work\ag-verify\fonttest.py` | 3 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\MECHANICS.md`<br>`docs\27-实机验收-AG单位面板与字体字距修复.md` |
| `work\ag-verify\zoom.py` | 79 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\MECHANICS.md`<br>`.workbuddy\tmp\research-remake-ui-scaling.md` |
| `work\atomic\build_map.py` | 5 | `work\glossary\scn_player_probe.py`<br>`work\glossary\scn_player_probe.py`<br>`work\glossary\scn_player_probe.py` |
| `work\atomic\deploy_scenario.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\atomic\scn\fix_cr.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\atomic\scn\fix_titles.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\atomic\scn\unify.py` | 11 | `.workbuddy\memory\2026-09-28.md`<br>`pgforever\work\brf-all\index.json`<br>`pgforever\work\brf-all\index.json` |
| `work\atomic\split_chunks.py` | 2 | `.workbuddy\memory\2026-10-11.md`<br>`work\pegww2\split_chunks.py` |
| `work\audit\_xscn_untranslated_probe.py` | 3 | `.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\MECHANICS.md`<br>`docs\34-BASEKORP-label层收官与COMWW2开工量测.md` |
| `work\audit\measure_efile.py` | 3 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md` |
| `work\audit\measure_userscen.py` | 3 | `.workbuddy\memory\2026-09-30.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md`<br>`docs\37-全库USERSCEN盲区量测与COMWW2清账.md` |
| `work\basekorp\_cls.py` | 1 | `work\glossary\fix_from_audit.py` |
| `work\basekorp\_dump_xscn_leak.py` | 2 | `docs\34-BASEKORP-label层收官与COMWW2开工量测.md`<br>`docs\34-BASEKORP-label层收官与COMWW2开工量测.md` |
| `work\basekorp\_measure_comww2.py` | 1 | `docs\34-BASEKORP-label层收官与COMWW2开工量测.md` |
| `work\basekorp\build_map.py` | 6 | `work\atomic\build_map.py`<br>`work\glossary\scn_player_probe.py`<br>`work\glossary\scn_player_probe.py` |
| `work\basekorp\deploy_prose.py` | 6 | `.workbuddy\memory\2026-09-28.md`<br>`.workbuddy\memory\2026-09-28.md`<br>`.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\det.py` | 14870 | `.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\MECHANICS.md`<br>`backup\ORIGINAL-EFILE_AG\TEXT-DE\SCENARIO\hog_4_i.txt` |
| `work\basekorp\extract_block_todo.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_ac80_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_ac81_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_ac82_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_akdtr_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_akge_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_bc_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_bk_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_bn_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_buzprg_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_cas_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_dragrom_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_efile_meta.py` | 7 | `.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\2026-10-08.md` |
| `work\basekorp\gen_gaw_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_ge_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_german_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_jh11_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_jh12_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_jh_residue_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_label_zh.py` | 14 | `.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\MECHANICS.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\basekorp\gen_lah_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_misc_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_oldiron_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_other_zh.py` | 1 | `.workbuddy\memory\2026-09-29.md` |
| `work\basekorp\gen_panther_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_r_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_sealion_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_small_blocks_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_spzbrg_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_ssbdm_zh.py` | 1 | `.workbuddy\memory\2026-09-29.md` |
| `work\basekorp\gen_tiger_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\gen_tmsg.py` | 2 | `work\basekorp\_fix_stat.py`<br>`work\basekorp\_fix_stat.py` |
| `work\basekorp\gen_xbk_zh.py` | 1 | `.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\tokdict.py` | 1 | `work\basekorp\det.py` |
| `work\basekorp\translate_prose.py` | 41 | `.workbuddy\memory\2026-09-28.md`<br>`.workbuddy\memory\2026-09-28.md`<br>`.workbuddy\memory\2026-09-28.md` |
| `work\basekorp\txt_workbench.py` | 20 | `.workbuddy\memory\2026-09-28.md`<br>`.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\2026-09-29.md` |
| `work\basekorp\unify.py` | 11 | `.workbuddy\memory\2026-09-28.md`<br>`pgforever\work\brf-all\index.json`<br>`pgforever\work\brf-all\index.json` |
| `work\clu\gen_txt_zh.py` | 22 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md` |
| `work\clu\make_clu_names.py` | 1 | `glossary\SOURCES.tsv` |
| `work\comww2\apply_tmsg_zh.py` | 1 | `.workbuddy\memory\2026-09-30.md` |
| `work\comww2\audit_map_quality.py` | 7 | `.workbuddy\memory\MECHANICS.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md`<br>`.workbuddy\memory\MEMORY-OpenPG-archive-2026-10-10.md` |
| `work\comww2\audit_pollution.py` | 6 | `.workbuddy\memory\MECHANICS.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md`<br>`.workbuddy\memory\MEMORY-OpenPG-archive-2026-10-10.md` |
| `work\comww2\build_prose_zh.py` | 5 | `.workbuddy\memory\2026-09-30.md`<br>`.workbuddy\memory\MECHANICS.md`<br>`docs\35-COMWW2-prose层收官与txt100%.md` |
| `work\comww2\build_xscn_map.py` | 13 | `.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\2026-09-29.md` |
| `work\comww2\dump_xscn_leak.py` | 1 | `.workbuddy\memory\2026-09-29.md` |
| `work\comww2\export_prose_dst.py` | 2 | `.workbuddy\memory\2026-09-30.md`<br>`docs\35-COMWW2-prose层收官与txt100%.md` |
| `work\comww2\fix_prose_rest.py` | 4 | `.workbuddy\memory\2026-09-30.md`<br>`docs\00-工作空间导航.md`<br>`docs\35-COMWW2-prose层收官与txt100%.md` |
| `work\comww2\fix_scenario_lines.py` | 4 | `.workbuddy\memory\2026-09-30.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md`<br>`docs\00-工作空间导航.md` |
| `work\comww2\gen_efile_meta.py` | 6 | `.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\2026-10-08.md` |
| `work\comww2\gen_label_zh.py` | 12 | `.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\MECHANICS.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\comww2\gen_prose_zh.py` | 14 | `.workbuddy\memory\2026-09-30.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\MECHANICS.md` |
| `work\comww2\gen_residual_comp.py` | 1 | `.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\comww2\gen_root_zh.py` | 26 | `.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md` |
| `work\comww2\gen_xscn_batch.py` | 7 | `.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\MECHANICS.md` |
| `work\comww2\gen_xscn_batch2.py` | 2 | `.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\MECHANICS.md` |
| `work\comww2\make_tmsg_map.py` | 1 | `.workbuddy\memory\2026-09-30.md` |
| `work\comww2\measure_comww2.py` | 1 | `.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\comww2\measure_root.py` | 2 | `.workbuddy\memory\2026-09-29.md`<br>`docs\34-BASEKORP-label层收官与COMWW2开工量测.md` |
| `work\comww2\measure_xscn_cov.py` | 10 | `.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\MECHANICS.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\comww2\measure_xscn_reuse.py` | 1 | `.workbuddy\memory\2026-09-29.md` |
| `work\comww2\merge_prose_block.py` | 6 | `.workbuddy\memory\2026-09-30.md`<br>`.workbuddy\memory\2026-09-30.md`<br>`.workbuddy\memory\MECHANICS.md` |
| `work\comww2\merge_prose_rest.py` | 3 | `.workbuddy\memory\2026-09-30.md`<br>`.workbuddy\memory\2026-09-30.md`<br>`docs\35-COMWW2-prose层收官与txt100%.md` |
| `work\comww2\probe_equip_icons.py` | 5 | `.workbuddy\memory\MECHANICS.md`<br>`.workbuddy\memory\MECHANICS.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\comww2\probe_residual_reuse.py` | 3 | `.workbuddy\memory\MEMORY-archive-2026-10-10.md`<br>`.workbuddy\memory\MEMORY-OpenPG-archive-2026-10-10.md`<br>`.workbuddy\tmp\ctx-b5-raw.md` |
| `work\comww2\propagate_dup_txt.py` | 10 | `.workbuddy\memory\2026-09-30.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\comww2\rebuild_todo.py` | 1 | `.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\comww2\split_prose_rest.py` | 2 | `.workbuddy\memory\2026-09-30.md`<br>`docs\35-COMWW2-prose层收官与txt100%.md` |
| `work\comww2\txt_workbench.py` | 18 | `.workbuddy\memory\2026-09-28.md`<br>`.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\2026-09-29.md` |
| `work\comww2\verify_pollution_hits.py` | 3 | `.workbuddy\memory\MECHANICS.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md`<br>`docs\34-BASEKORP-label层收官与COMWW2开工量测.md` |
| `work\crash-20260924\bisect.py` | 4 | `.workbuddy\memory\2026-10-10.md`<br>`docs\39-冗余扫描报告-2026-10-10.md`<br>`docs\39-冗余扫描报告-2026-10-10.md` |
| `work\crash-20260924\boottest.py` | 7 | `work\crash-20260924\bisect.py`<br>`work\crash-20260924\bisect.py`<br>`work\crash-20260924\bisect2.py` |
| `work\crash-20260924\rebuild.py` | 219 | `backup\before-brief-faction\scenario-long-zh.tsv`<br>`backup\before-brief-faction\scenario-long-zh.tsv`<br>`backup\before-cat-fix\glossary\standard-glossary.tsv` |
| `work\efile-nashornpbem\apply_residual.py` | 35 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\MECHANICS.md` |
| `work\efile-nashornpbem\apply_unify.py` | 3 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\MECHANICS.md`<br>`docs\19-OLGWW2-xscn译名统一订正执行报告.md` |
| `work\efile-nashornpbem\audit_residual.py` | 3 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-24.md`<br>`docs\14-实机三图复核与四层新发现.md` |
| `work\efile-nashornpbem\bridge_check.py` | 15 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\MECHANICS.md` |
| `work\efile-nashornpbem\classify_residual.py` | 1 | `.workbuddy\memory\2026-09-24.md` |
| `work\efile-nashornpbem\cmp_mirror.py` | 2 | `.workbuddy\memory\2026-09-24.md`<br>`docs\13-场景简报ply层漏译与strings表复核.md` |
| `work\efile-nashornpbem\cmp_strings.py` | 2 | `.workbuddy\memory\2026-09-24.md`<br>`docs\13-场景简报ply层漏译与strings表复核.md` |
| `work\efile-nashornpbem\context_cards.py` | 3 | `.workbuddy\memory\2026-09-24.md`<br>`docs\15-OLGWW2残留条目清理.md`<br>`docs\15-OLGWW2残留条目清理.md` |
| `work\efile-nashornpbem\crop2.py` | 2 | `.workbuddy\memory\2026-09-24.md`<br>`docs\13-场景简报ply层漏译与strings表复核.md` |
| `work\efile-nashornpbem\crop3.py` | 1 | `.workbuddy\memory\2026-09-24.md` |
| `work\efile-nashornpbem\crop_shots.py` | 2 | `.workbuddy\memory\2026-09-24.md`<br>`docs\13-场景简报ply层漏译与strings表复核.md` |
| `work\efile-nashornpbem\dump_arm_context.py` | 2 | `.workbuddy\memory\2026-09-24.md`<br>`docs\22-译名库权威核对执行报告.md` |
| `work\efile-nashornpbem\dump_scene.py` | 3 | `.workbuddy\memory\2026-09-24.md`<br>`docs\18-OLGWW2-xscn与场景清单译名一致性普查.md`<br>`docs\19-OLGWW2-xscn译名统一订正执行报告.md` |
| `work\efile-nashornpbem\export_residual.py` | 3 | `.workbuddy\memory\2026-09-24.md`<br>`docs\15-OLGWW2残留条目清理.md`<br>`docs\15-OLGWW2残留条目清理.md` |
| `work\efile-nashornpbem\find_nengli.py` | 2 | `.workbuddy\memory\2026-09-24.md`<br>`docs\13-场景简报ply层漏译与strings表复核.md` |
| `work\efile-nashornpbem\fix_alias_dup.py` | 5 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\MECHANICS.md` |
| `work\efile-nashornpbem\fix_arm_inf.py` | 4 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-24.md`<br>`docs\22-译名库权威核对执行报告.md` |
| `work\efile-nashornpbem\fix_division.py` | 6 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\MECHANICS.md`<br>`docs\22-译名库权威核对执行报告.md` |
| `work\efile-nashornpbem\fix_g0_authority.py` | 4 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-24.md`<br>`docs\22-译名库权威核对执行报告.md` |
| `work\efile-nashornpbem\inv_scenario.py` | 2 | `.workbuddy\memory\2026-09-24.md`<br>`docs\13-场景简报ply层漏译与strings表复核.md` |
| `work\efile-nashornpbem\list_place_ascii.py` | 2 | `.workbuddy\memory\2026-09-24.md`<br>`docs\17-OLGWW2待考地名核对报告.md` |
| `work\efile-nashornpbem\lookup_via_txt.py` | 4 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-24.md`<br>`docs\17-OLGWW2待考地名核对报告.md` |
| `work\efile-nashornpbem\make_unify_plan.py` | 3 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\MECHANICS.md`<br>`docs\19-OLGWW2-xscn译名统一订正执行报告.md` |
| `work\efile-nashornpbem\match_txt_names.py` | 6 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-24.md`<br>`docs\17-OLGWW2待考地名核对报告.md` |
| `work\efile-nashornpbem\memscan.py` | 8 | `work\exe\mem-scan.ps1`<br>`work\exe\mem-scan.ps1`<br>`work\exe\mem-scan.ps1` |
| `work\efile-nashornpbem\mk_ply_all.py` | 1 | `work\efile-nashornpbem\verify_ply.py` |
| `work\efile-nashornpbem\mk_ply_olgww2.py` | 3 | `.workbuddy\memory\2026-09-24.md`<br>`docs\16-ply场景简报层盘点与OLGWW2落地.md`<br>`docs\16-ply场景简报层盘点与OLGWW2落地.md` |
| `work\efile-nashornpbem\ogsnap.py` | 5 | `work\efile-nashornpbem\clickuntil.py`<br>`work\efile-nashornpbem\goto_loaded.py`<br>`work\efile-nashornpbem\probe_toolbar.py` |
| `work\efile-nashornpbem\pending_context.py` | 4 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-24.md`<br>`docs\17-OLGWW2待考地名核对报告.md` |
| `work\efile-nashornpbem\ply_struct.py` | 3 | `.workbuddy\memory\2026-09-24.md`<br>`docs\13-场景简报ply层漏译与strings表复核.md`<br>`docs\16-ply场景简报层盘点与OLGWW2落地.md` |
| `work\efile-nashornpbem\scan_arm_inf_conflict.py` | 2 | `.workbuddy\memory\2026-09-24.md`<br>`docs\22-译名库权威核对执行报告.md` |
| `work\efile-nashornpbem\scan_g1_vs_txt.py` | 5 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\MECHANICS.md` |
| `work\efile-nashornpbem\scan_xscn_latin.py` | 2 | `docs\52-词库更新铺设到PeG及PeG-WW2.md`<br>`work\_sync-audit\apply_naming_peg.py` |
| `work\efile-nashornpbem\triage_mismatch.py` | 5 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\MECHANICS.md`<br>`docs\18-OLGWW2-xscn与场景清单译名一致性普查.md` |
| `work\efile-nashornpbem\verify_residual.py` | 4 | `.workbuddy\memory\2026-09-24.md`<br>`docs\15-OLGWW2残留条目清理.md`<br>`docs\15-OLGWW2残留条目清理.md` |
| `work\efile-nashornpbem\verify_unify.py` | 3 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\MECHANICS.md`<br>`docs\19-OLGWW2-xscn译名统一订正执行报告.md` |
| `work\efile-nashornpbem\verify_xscn.py` | 6 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-24.md`<br>`docs\14-实机三图复核与四层新发现.md` |
| `work\efile-poc\_addrrefs.py` | 1 | `docs\00-工作空间导航.md` |
| `work\efile-poc\_dirtrace.py` | 6 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-24.md`<br>`docs\00-工作空间导航.md` |
| `work\efile-poc\_dis.py` | 1 | `docs\00-工作空间导航.md` |
| `work\efile-poc\_plyrefs.py` | 2 | `.workbuddy\memory\2026-09-24.md`<br>`docs\13-场景简报ply层漏译与strings表复核.md` |
| `work\efile_pzliga\gen_root_zh.py` | 26 | `.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md` |
| `work\efile_pzliga\gen_titles.py` | 2 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\efile_pzliga\gen_txt_zh.py` | 22 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md` |
| `work\efile_pzliga\gen_userscen_xscn.py` | 1 | `glossary\SOURCES.tsv` |
| `work\efile_pzliga\make_pzliga_root.py` | 2 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\efile_pzliga\make_pzliga_txt.py` | 2 | `.workbuddy\memory\2026-10-09.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\efile_pzliga\translate_miss.py` | 2 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\efile_pzliga\translate_short.py` | 1 | `.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\exe\exe_zhfix.py` | 20 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-24.md` |
| `work\exe\maphud_patch.py` | 9 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-28.md`<br>`.workbuddy\memory\2026-09-28.md` |
| `work\exe\pelib.py` | 9 | `.workbuddy\memory\2026-09-28.md`<br>`work\crash-20260924\audit_final.py`<br>`work\exe\ledger.md` |
| `work\exe\poke_holes.py` | 5 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-28.md`<br>`.workbuddy\memory\MECHANICS.md` |
| `work\exe\unitdlg_patch.py` | 11 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-28.md`<br>`docs\28-exe单位面板与升级对话框串汉化.md` |
| `work\exe\unitpanel_patch.py` | 21 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-28.md`<br>`.workbuddy\memory\2026-09-28.md` |
| `work\gce\build_xscn_map.py` | 13 | `.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\2026-09-29.md` |
| `work\gce\fix_gce_parts.py` | 2 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\gce\gen_efile_meta.py` | 6 | `.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\2026-10-08.md` |
| `work\gce\gen_root_zh.py` | 26 | `.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md` |
| `work\gce\gen_txt_zh.py` | 22 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md` |
| `work\gce\gen_userscen_text.py` | 4 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\gce\make_gce_root.py` | 2 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\gce\make_gce_root_manual.py` | 2 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\gce\measure_xscn_cov.py` | 10 | `.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\MECHANICS.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\gce\merge_gce_parts.py` | 4 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\gce\merge_txt_parts.py` | 2 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\gce\merge_userscen_parts.py` | 1 | `.workbuddy\memory\2026-10-08.md` |
| `work\gce\normalize_gce_map.py` | 2 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\gce\normalize_txt_zh.py` | 1 | `.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\gce\split_txt_miss.py` | 1 | `.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\gce\txt_workbench.py` | 18 | `.workbuddy\memory\2026-09-28.md`<br>`.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\2026-09-29.md` |
| `work\glossary\ag_xscn.py` | 18 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-28.md`<br>`.workbuddy\memory\2026-09-28.md` |
| `work\glossary\audit_layers.py` | 1 | `glossary\SOURCES.tsv` |
| `work\glossary\cat_fix_rules.py` | 11 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.md` |
| `work\glossary\check_glossary.py` | 29 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-28.md`<br>`docs\20-标准译名库建设报告.md` |
| `work\glossary\converge_plan.py` | 36 | `requirements.txt`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md` |
| `work\glossary\deploy_tarnopol_6v.py` | 4 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`docs\46-阵营维度补视角与修键实测结论.md` |
| `work\glossary\era_dimension_pilot.py` | 3 | `docs\44-地名三维规则纳入词库方案.md`<br>`docs\44-地名三维规则纳入词库方案.md`<br>`glossary\SOURCES.tsv` |
| `work\glossary\faction_audit.py` | 4 | `glossary\SOURCES.tsv`<br>`work\glossary\fix_faction_german.py`<br>`work\glossary\fix_faction_kishinev.py` |
| `work\glossary\faction_place_audit.py` | 38 | `requirements.txt`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.md` |
| `work\glossary\faction_wire.py` | 20 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md` |
| `work\glossary\fix_batch_A_F.py` | 1 | `.workbuddy\memory\2026-09-24.md` |
| `work\glossary\fix_era_lodz.py` | 1 | `glossary\SOURCES.tsv` |
| `work\glossary\fix_faction_history.py` | 1 | `work\glossary\fix_tarnopol_6v.py` |
| `work\glossary\fix_map_segments.py` | 9 | `glossary\SOURCES.tsv`<br>`glossary\SOURCES.tsv`<br>`glossary\SOURCES.tsv` |
| `work\glossary\fix_mojibake.py` | 3 | `.workbuddy\memory\2026-09-24.md`<br>`docs\22-译名库权威核对执行报告.md`<br>`docs\22-译名库权威核对执行报告.md` |
| `work\glossary\fix_name_converge.py` | 4 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`docs\48-地名收敛与两作成品同步执行记录.md` |
| `work\glossary\fix_peg_sync.py` | 2 | `glossary\SOURCES.tsv`<br>`glossary\分层架构-实施记录.md` |
| `work\glossary\fix_self_identity_rows.py` | 3 | `glossary\SOURCES.tsv`<br>`glossary\梳理-实施记录.md`<br>`glossary\梳理-实施记录.md` |
| `work\glossary\fix_side_override.py` | 2 | `glossary\SOURCES.tsv`<br>`glossary\SOURCES.tsv` |
| `work\glossary\fix_tarnopol_6v.py` | 4 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`work\glossary\deploy_tarnopol_6v.py` |
| `work\glossary\fix_two_leftovers.py` | 2 | `glossary\梳理-实施记录.md`<br>`glossary\梳理-实施记录.md` |
| `work\glossary\glossary.py` | 10909 | `README.md`<br>`README.md`<br>`README.md` |
| `work\glossary\ingest_layers.py` | 91 | `requirements.txt`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md` |
| `work\glossary\make_ag_equip.py` | 2 | `.workbuddy\memory\2026-09-24.md`<br>`docs\25-B1-EFILE_AG根级汉化执行报告.md` |
| `work\glossary\make_ag_names.py` | 2 | `.workbuddy\memory\2026-09-24.md`<br>`docs\25-B1-EFILE_AG根级汉化执行报告.md` |
| `work\glossary\make_ag_root.py` | 2 | `.workbuddy\memory\2026-09-24.md`<br>`docs\25-B1-EFILE_AG根级汉化执行报告.md` |
| `work\glossary\make_ag_xscn_map.py` | 3 | `.workbuddy\memory\2026-09-24.md`<br>`docs\26-B1-EFILE_AG-xscn层汉化执行报告.md`<br>`docs\30-后续汉化推进方案.md` |
| `work\glossary\make_b_decide.py` | 10 | `docs\22-译名库权威核对执行报告.md`<br>`docs\22-译名库权威核对执行报告.md`<br>`glossary\README.md` |
| `work\glossary\make_orig_charset_fix.py` | 5 | `.workbuddy\memory\2026-09-24.md`<br>`glossary\README.md`<br>`glossary\SOURCES.tsv` |
| `work\glossary\make_pegww2_glossary.py` | 9 | `glossary\README.md`<br>`glossary\README.md`<br>`glossary\SOURCES.tsv` |
| `work\glossary\make_scenario_zh.py` | 2 | `.workbuddy\memory\2026-09-24.md`<br>`glossary\README.md` |
| `work\glossary\make_utf8_fix.py` | 4 | `.workbuddy\memory\2026-09-24.md`<br>`glossary\README.md`<br>`glossary\SOURCES.tsv` |
| `work\glossary\materialize.py` | 22 | `glossary\SOURCES.tsv`<br>`glossary\SOURCES.tsv`<br>`glossary\SOURCES.tsv` |
| `work\glossary\regen_glossary_catfix.py` | 2 | `docs\50-cat误标治理与覆盖表并入词库.md`<br>`docs\50-cat误标治理与覆盖表并入词库.md` |
| `work\glossary\restore_b_unify.py` | 4 | `.workbuddy\memory\2026-09-24.md`<br>`docs\22-译名库权威核对执行报告.md`<br>`docs\22-译名库权威核对执行报告.md` |
| `work\glossary\restore_orig_encoding.py` | 3 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\MECHANICS.md`<br>`glossary\README.md` |
| `work\glossary\scan_mojibake.py` | 2 | `.workbuddy\memory\2026-09-24.md`<br>`docs\22-译名库权威核对执行报告.md` |
| `work\glossary\scan_orig_charset.py` | 2 | `.workbuddy\memory\2026-09-24.md`<br>`glossary\README.md` |
| `work\glossary\scn_player_probe.py` | 1 | `work\glossary\faction_place_audit.py` |
| `work\glossary\scn_side_probe.py` | 1 | `glossary\阵营视角-约定.md` |
| `work\glossary\seg_canon_build.py` | 11 | `glossary\SOURCES.tsv`<br>`glossary\SOURCES.tsv`<br>`glossary\SOURCES.tsv` |
| `work\glossary\seg_ruling_plan.py` | 6 | `glossary\SOURCES.tsv`<br>`glossary\SOURCES.tsv`<br>`glossary\SOURCES.tsv` |
| `work\glossary\sweep_docs.py` | 2 | `glossary\梳理-实施记录.md`<br>`glossary\梳理-实施记录.md` |
| `work\glossary\sweep_drift.py` | 2 | `glossary\SOURCES.tsv`<br>`glossary\SOURCES.tsv` |
| `work\glossary\sweep_nonascii_untranslated.py` | 3 | `glossary\梳理-实施记录.md`<br>`glossary\梳理-实施记录.md`<br>`glossary\梳理-实施记录.md` |
| `work\glossary\sweep_quality.py` | 2 | `glossary\梳理-实施记录.md`<br>`glossary\梳理-实施记录.md` |
| `work\glossary\sweep_rules.py` | 2 | `glossary\梳理-实施记录.md`<br>`glossary\梳理-实施记录.md` |
| `work\glossary\sweep_seg_filecheck.py` | 3 | `glossary\梳理-实施记录.md`<br>`glossary\梳理-实施记录.md`<br>`glossary\梳理-实施记录.md` |
| `work\glossary\sweep_ui5.py` | 3 | `glossary\SOURCES.tsv`<br>`glossary\梳理-实施记录.md`<br>`glossary\梳理-实施记录.md` |
| `work\glossary\sweep_untranslated.py` | 3 | `glossary\梳理-实施记录.md`<br>`glossary\梳理-实施记录.md`<br>`glossary\梳理-实施记录.md` |
| `work\glossary\unify_b.py` | 4 | `.workbuddy\memory\2026-09-24.md`<br>`docs\22-译名库权威核对执行报告.md`<br>`docs\22-译名库权威核对执行报告.md` |
| `work\glossary\verify_b_unify.py` | 4 | `.workbuddy\memory\2026-09-24.md`<br>`docs\22-译名库权威核对执行报告.md`<br>`docs\22-译名库权威核对执行报告.md` |
| `work\glossary\verify_xscn_after.py` | 4 | `.workbuddy\memory\2026-09-24.md`<br>`docs\22-译名库权威核对执行报告.md`<br>`docs\22-译名库权威核对执行报告.md` |
| `work\kaiser\export_xscn_uniq.py` | 3 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\kaiser\gen_root_zh.py` | 26 | `.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md` |
| `work\kaiser\gen_txt_zh.py` | 22 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md` |
| `work\kaiser\gen_userscen_text.py` | 4 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\kaiser\gen_xscn_zh.py` | 4 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\kaiser\make_kaiser_root.py` | 2 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\kaiser\make_kaiser_root_manual.py` | 2 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\kaiser\measure_xscn_cov.py` | 10 | `.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\MECHANICS.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\kaiser\merge_place_parts.py` | 3 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\peg\_dr_test.py` | 5 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`docs\67-PeG宽屏方案（分层策略与实施路线）.md` |
| `work\peg\_dump_debugevent.py` | 1 | `work\peg\peg_trace.py` |
| `work\peg\_find_map_sites.py` | 3 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`work\peg\_append_memory_70.py` |
| `work\peg\_gen_panel_table.py` | 3 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`work\peg\_append_memory_64.py` |
| `work\peg\_make_forensics_cmd.py` | 3 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`work\peg\_append_memory_67.py` |
| `work\peg\_plan_vs_780.py` | 4 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`work\peg\peg_launcher.py` |
| `work\peg\analyze_pe.py` | 4 | `docs\38-PeG中文化可行性评估.md`<br>`docs\38-PeG中文化可行性评估.md`<br>`peg\research\evidence\exe-tables.md` |
| `work\peg\build_long2_zh.py` | 3 | `.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\MEMORY-PeG-archive-2026-10-10.md`<br>`peg\方法\PeG汉化经验总结.md` |
| `work\peg\build_long_zh.py` | 4 | `.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\MEMORY-PeG-archive-2026-10-10.md`<br>`peg\方法\PeG汉化经验总结.md` |
| `work\peg\build_scn_list_doc.py` | 8 | `.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md` |
| `work\peg\build_scn_number.py` | 11 | `.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\2026-10-10.md` |
| `work\peg\build_v10.py` | 15 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md` |
| `work\peg\build_v5.py` | 6 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`docs\56-PeG高分辨率-v5变体（代码驱动布局验证版）.md` |
| `work\peg\census_text.py` | 6 | `docs\38-PeG中文化可行性评估.md`<br>`docs\38-PeG中文化可行性评估.md`<br>`peg\research\observations.tsv` |
| `work\peg\cmp_va.py` | 5 | `.workbuddy\tmp\research-map-composition.md`<br>`.workbuddy\tmp\research-map-composition.md`<br>`.workbuddy\tmp\research-map-composition.md` |
| `work\peg\crack_rle.py` | 1 | `docs\38-PeG中文化可行性评估.md` |
| `work\peg\crop_shot.py` | 3 | `docs\55-PeG高分辨率-v4实机取证与运行时重算根因.md`<br>`docs\57-PeG高分辨率-v6面板基准620到844.md`<br>`docs\58-PeG高分辨率-工具列绘制公式与锚点751修正（v8）.md` |
| `work\peg\d.py` | 47235 | `env.cmd`<br>`README.md`<br>`README.md` |
| `work\peg\diag_ddraw.py` | 24 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md` |
| `work\peg\diag_run.py` | 3 | `work\peg\diag_ddraw.py`<br>`work\peg\_make_diag_cmd.py`<br>`work\peg\out\_diag_cmd_test.cmd` |
| `work\peg\diff_res_canvas.py` | 5 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`docs\54-PeG高分辨率-S1补丁重建与S2花屏根因.md` |
| `work\peg\diff_shot.py` | 2 | `docs\57-PeG高分辨率-v6面板基准620到844.md`<br>`docs\61-PeG-UI显示系统重构方案.md` |
| `work\peg\disasm_range.py` | 13 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`.workbuddy\tmp\research-display-pipeline.md` |
| `work\peg\dump_pfs.py` | 3 | `requirements.txt`<br>`docs\38-PeG中文化可行性评估.md`<br>`docs\38-PeG中文化可行性评估.md` |
| `work\peg\extract_research.py` | 5 | `README.md`<br>`.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\2026-10-10.md` |
| `work\peg\find_bytes.py` | 9 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`.workbuddy\tmp\research-display-pipeline.md` |
| `work\peg\find_calls.py` | 4 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`docs\58-PeG高分辨率-工具列绘制公式与锚点751修正（v8）.md` |
| `work\peg\find_imm.py` | 8 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`docs\57-PeG高分辨率-v6面板基准620到844.md` |
| `work\peg\find_mem.py` | 15 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md` |
| `work\peg\fix_scn_intro_flag.py` | 7 | `.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-PeG-archive-2026-10-10.md` |
| `work\peg\gen_gui030_zh.py` | 61 | `requirements.txt`<br>`.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\2026-10-10.md` |
| `work\peg\gen_name030_zh.py` | 5 | `.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\MEMORY-PeG-archive-2026-10-10.md`<br>`docs\38-PeG中文化可行性评估.md` |
| `work\peg\gen_observations.py` | 3 | `.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\MEMORY-PeG-archive-2026-10-10.md`<br>`peg\research\README.md` |
| `work\peg\gen_peg_text.py` | 12 | `requirements.txt`<br>`.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\2026-10-10.md` |
| `work\peg\gen_ply_zh.py` | 10 | `requirements.txt`<br>`.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\2026-10-10.md` |
| `work\peg\gen_scn_desc_txt.py` | 10 | `.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\2026-10-10.md` |
| `work\peg\hint_pe.py` | 28 | `requirements.txt`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.md` |
| `work\peg\imm_range.py` | 3 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`work\peg\hint_pe.py` |
| `work\peg\imp_list.py` | 1 | `.workbuddy\tmp\research-display-pipeline.md` |
| `work\peg\patch-date-lcid-zh.py` | 10 | `.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md` |
| `work\peg\patch-lc-time-zh.py` | 9 | `.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-PeG-archive-2026-10-10.md` |
| `work\peg\patch_fullrepaint.py` | 3 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`work\peg\_append_memory_70.py` |
| `work\peg\patch_res_wh.py` | 21 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md` |
| `work\peg\patch_resolution.py` | 33 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md` |
| `work\peg\patch_scn_extra.py` | 3 | `.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\MEMORY-PeG-archive-2026-10-10.md`<br>`peg\方法\PeG汉化经验总结.md` |
| `work\peg\patch_ui_layout.py` | 5 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md` |
| `work\peg\patch_v6_panelref.py` | 4 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`docs\57-PeG高分辨率-v6面板基准620到844.md` |
| `work\peg\patch_v7_bisect.py` | 3 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`docs\57-PeG高分辨率-v6面板基准620到844.md` |
| `work\peg\patch_v8_anchor.py` | 3 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`docs\58-PeG高分辨率-工具列绘制公式与锚点751修正（v8）.md` |
| `work\peg\peek_table.py` | 3 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`docs\63-PeG-16比9界面重构：崩溃事故、v9a判读与v9b设计.md` |
| `work\peg\peek_va.py` | 8 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.md` |
| `work\peg\peg_trace.py` | 15 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md` |
| `work\peg\prob0_sechdr.py` | 1 | `work\peg\hint_pe.py` |
| `work\peg\prob_b14_ctx.py` | 1 | `work\peg\out\report-secondary-ui.md` |
| `work\peg\prob_hexconst.py` | 2 | `work\peg\out\report-input-mapping.md`<br>`work\peg\out\report-input-mapping.md` |
| `work\peg\prob_mouse1.py` | 1 | `work\peg\out\report-input-mapping.md` |
| `work\peg\prob_panel2.py` | 1 | `work\peg\out\report-panel-table.md` |
| `work\peg\prob_panel4.py` | 1 | `work\peg\out\report-panel-table.md` |
| `work\peg\prob_panel5.py` | 1 | `work\peg\out\report-panel-table.md` |
| `work\peg\prob_panel8.py` | 1 | `work\peg\out\report-panel-table.md` |
| `work\peg\prob_sec1.py` | 1 | `work\peg\out\report-secondary-ui.md` |
| `work\peg\prob_sec2.py` | 1 | `work\peg\out\report-secondary-ui.md` |
| `work\peg\prob_sec3.py` | 1 | `work\peg\out\report-secondary-ui.md` |
| `work\peg\prob_sec4.py` | 2 | `work\peg\out\report-secondary-ui.md`<br>`work\peg\out\report-secondary-ui.md` |
| `work\peg\probe_btn.py` | 12 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md` |
| `work\peg\probe_dialog2.py` | 2 | `docs\38-PeG中文化可行性评估.md`<br>`docs\38-PeG中文化可行性评估.md` |
| `work\peg\probe_dialog_dat.py` | 1 | `docs\38-PeG中文化可行性评估.md` |
| `work\peg\probe_res_coverage.py` | 2 | `docs\54-PeG高分辨率-S1补丁重建与S2花屏根因.md`<br>`docs\55-PeG高分辨率-v4实机取证与运行时重算根因.md` |
| `work\peg\probe_row.py` | 2 | `docs\55-PeG高分辨率-v4实机取证与运行时重算根因.md`<br>`docs\58-PeG高分辨率-工具列绘制公式与锚点751修正（v8）.md` |
| `work\peg\probe_runs.py` | 2 | `docs\55-PeG高分辨率-v4实机取证与运行时重算根因.md`<br>`docs\58-PeG高分辨率-工具列绘制公式与锚点751修正（v8）.md` |
| `work\peg\probe_shot.py` | 1 | `docs\55-PeG高分辨率-v4实机取证与运行时重算根因.md` |
| `work\peg\probe_stale.py` | 1 | `docs\55-PeG高分辨率-v4实机取证与运行时重算根因.md` |
| `work\peg\probe_strings.py` | 1 | `docs\38-PeG中文化可行性评估.md` |
| `work\peg\probe_widgets.py` | 3 | `docs\55-PeG高分辨率-v4实机取证与运行时重算根因.md`<br>`docs\57-PeG高分辨率-v6面板基准620到844.md`<br>`docs\61-PeG-UI显示系统重构方案.md` |
| `work\peg\regen_scn_name_converge.py` | 17 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md` |
| `work\peg\render_s16.py` | 2 | `docs\38-PeG中文化可行性评估.md`<br>`docs\38-PeG中文化可行性评估.md` |
| `work\peg\render_s16b.py` | 1 | `docs\38-PeG中文化可行性评估.md` |
| `work\peg\show_bytes.py` | 8 | `docs\56-PeG高分辨率-v5变体（代码驱动布局验证版）.md`<br>`docs\56-PeG高分辨率-v5变体（代码驱动布局验证版）.md`<br>`docs\57-PeG高分辨率-v6面板基准620到844.md` |
| `work\peg\vtcalls.py` | 13 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.md` |
| `work\peg\xr.py` | 454 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md` |
| `work\peg\xref_call.py` | 7 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md`<br>`.workbuddy\tmp\research-display-pipeline.md` |
| `work\peg\xref_data.py` | 3 | `docs\55-PeG高分辨率-v4实机取证与运行时重算根因.md`<br>`docs\57-PeG高分辨率-v6面板基准620到844.md`<br>`work\peg\find_imm.py` |
| `work\pegww2\_todo_tokens.py` | 1 | `work\pegww2\gen_tokens.py` |
| `work\pegww2\add_value_reuse.py` | 4 | `.workbuddy\memory\2026-10-11.md`<br>`pegww2\README.md`<br>`pegww2\research\进度-场景层.md` |
| `work\pegww2\apply_eqp_fill.py` | 3 | `.workbuddy\memory\2026-10-11.md`<br>`pegww2\README.md`<br>`pegww2\research\ww2-eqp-fill.tsv` |
| `work\pegww2\apply_scn_numbers.py` | 4 | `.workbuddy\memory\2026-10-11.md`<br>`pegww2\research\进度-场景层.md`<br>`pegww2\research\进度-场景层.md` |
| `work\pegww2\apply_value_fill.py` | 5 | `.workbuddy\memory\2026-10-11.md`<br>`.workbuddy\memory\2026-10-11.md`<br>`pegww2\research\进度-场景层.md` |
| `work\pegww2\audit_namefix_safety.py` | 1 | `pegww2\README.md` |
| `work\pegww2\audit_names.py` | 1 | `pegww2\README.md` |
| `work\pegww2\audit_three_way.py` | 3 | `.workbuddy\memory\2026-10-11.md`<br>`.workbuddy\memory\2026-10-11.md`<br>`.workbuddy\memory\2026-10-11.md` |
| `work\pegww2\author_desc.py` | 1 | `pegww2\README.md` |
| `work\pegww2\autofill_docs.py` | 2 | `pegww2\docs-zh\_批D1-留痕.md`<br>`pegww2\方法\DOCS汉化经验.md` |
| `work\pegww2\backup_originals.py` | 2 | `docs\40-PeG-WW2中文化可行性评估.md`<br>`pegww2\README.md` |
| `work\pegww2\build_all.py` | 3 | `glossary\分层架构-实施记录.md`<br>`glossary\分层架构-实施记录.md`<br>`work\glossary\layer_gate.py` |
| `work\pegww2\build_file_overrides.py` | 2 | `glossary\SOURCES.tsv`<br>`glossary\SOURCES.tsv` |
| `work\pegww2\build_perspective.py` | 1 | `pegww2\research\进度-场景层.md` |
| `work\pegww2\check_glossary.py` | 31 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-28.md`<br>`docs\20-标准译名库建设报告.md` |
| `work\pegww2\crosscheck_names.py` | 3 | `.workbuddy\memory\2026-10-11.md`<br>`pegww2\README.md`<br>`pegww2\research\进度-场景层.md` |
| `work\pegww2\deploy.py` | 5437 | `requirements.txt`<br>`.workbuddy\memory\2026-09-28.md`<br>`.workbuddy\memory\2026-09-28.md` |
| `work\pegww2\deploy_docs.py` | 6 | `requirements.txt`<br>`glossary\分层架构-实施记录.md`<br>`glossary\分层架构-实施记录.md` |
| `work\pegww2\deploy_scn.py` | 10 | `glossary\梳理-实施记录.md`<br>`glossary\梳理-实施记录.md`<br>`glossary\梳理-实施记录.md` |
| `work\pegww2\doc_rtf.py` | 10 | `pegww2\docs-zh\_批D1-留痕.md`<br>`pegww2\docs-zh\_批D1-留痕.md`<br>`pegww2\方法\DOCS汉化经验.md` |
| `work\pegww2\doc_translate.py` | 7 | `pegww2\docs-zh\_批D1-留痕.md`<br>`pegww2\方法\DOCS汉化经验.md`<br>`pegww2\方法\DOCS汉化经验.md` |
| `work\pegww2\drop_empty_shells.py` | 1 | `pegww2\research\进度-场景层.md` |
| `work\pegww2\dump_text.py` | 4 | `work\pegww2\check_glossary.py`<br>`work\pegww2\check_glossary.py`<br>`work\pegww2\check_glossary.py` |
| `work\pegww2\dup_check.py` | 11 | `.workbuddy\memory\2026-10-11.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY.pre-compress-2026-10-15.md` |
| `work\pegww2\export_scn_group_proposal.py` | 1 | `pegww2\research\进度-场景层.md` |
| `work\pegww2\fix_eqp_carrier.py` | 5 | `.workbuddy\memory\2026-10-11.md`<br>`glossary\SOURCES.tsv`<br>`glossary\SOURCES.tsv` |
| `work\pegww2\fix_eqp_typewords.py` | 3 | `.workbuddy\memory\2026-10-11.md`<br>`pegww2\README.md`<br>`pegww2\research\进度-场景层.md` |
| `work\pegww2\fix_glossary_basis.py` | 1 | `pegww2\方法\术语统一-治本.md` |
| `work\pegww2\fix_line_map_align.py` | 3 | `.workbuddy\memory\2026-10-11.md`<br>`pegww2\README.md`<br>`pegww2\README.md` |
| `work\pegww2\fix_markers.py` | 5 | `pegww2\research\_scn-fill-m-r2-01-fix.tsv`<br>`pegww2\research\_scn-fill-m-r3-01-fix.tsv`<br>`pegww2\research\_scn-fill-m-r4-01-fix.tsv` |
| `work\pegww2\fix_override_filename_case.py` | 3 | `.workbuddy\memory\2026-10-11.md`<br>`pegww2\research\进度-场景层.md`<br>`pegww2\research\进度-场景层.md` |
| `work\pegww2\fix_profile_class.py` | 1 | `pegww2\research\_同类译法问题-审计.md` |
| `work\pegww2\gen_text.py` | 9 | `requirements.txt`<br>`.workbuddy\memory\2026-10-11.md`<br>`glossary\分层架构-实施记录.md` |
| `work\pegww2\gen_value.py` | 15 | `requirements.txt`<br>`.workbuddy\memory\2026-10-11.md`<br>`.workbuddy\memory\2026-10-11.md` |
| `work\pegww2\make_chunks.py` | 3 | `pegww2\docs-zh\_fill\_chunks-index.tsv`<br>`pegww2\方法\DOCS汉化经验.md`<br>`work\pegww2\merge_tasks.py` |
| `work\pegww2\make_scn_worksheets.py` | 1 | `pegww2\research\进度-场景层.md` |
| `work\pegww2\make_worksheets.py` | 2 | `.workbuddy\memory\2026-10-11.md`<br>`pegww2\README.md` |
| `work\pegww2\merge_d5_remain.py` | 1 | `pegww2\方法\DOCS汉化经验.md` |
| `work\pegww2\merge_fill.py` | 3 | `.workbuddy\memory\2026-10-11.md`<br>`pegww2\README.md`<br>`pegww2\research\WW2Gui-fill.tsv` |
| `work\pegww2\merge_tasks.py` | 6 | `glossary\分层架构-实施记录.md`<br>`glossary\分层架构-实施记录.md`<br>`pegww2\docs-zh\_批D1-留痕.md` |
| `work\pegww2\patch_scn_fields.py` | 1 | `pegww2\README.md` |
| `work\pegww2\prune_fills.py` | 4 | `pegww2\docs-zh\_批D1-留痕.md`<br>`pegww2\方法\DOCS汉化经验.md`<br>`pegww2\方法\DOCS汉化经验.md` |
| `work\pegww2\recon2.py` | 2 | `docs\40-PeG-WW2中文化可行性评估.md`<br>`pegww2\README.md` |
| `work\pegww2\recon3.py` | 2 | `docs\40-PeG-WW2中文化可行性评估.md`<br>`pegww2\README.md` |
| `work\pegww2\recon4_scn.py` | 2 | `docs\40-PeG-WW2中文化可行性评估.md`<br>`pegww2\README.md` |
| `work\pegww2\recon5_workload.py` | 2 | `docs\40-PeG-WW2中文化可行性评估.md`<br>`pegww2\README.md` |
| `work\pegww2\recon6_bitmap.py` | 2 | `docs\40-PeG-WW2中文化可行性评估.md`<br>`pegww2\README.md` |
| `work\pegww2\recon7_fullscreen.py` | 2 | `docs\40-PeG-WW2中文化可行性评估.md`<br>`pegww2\README.md` |
| `work\pegww2\recon8_render.py` | 2 | `docs\40-PeG-WW2中文化可行性评估.md`<br>`pegww2\README.md` |
| `work\pegww2\recon9_scnfields.py` | 10 | `backup\before-cat-fix\layers\slot-rules.tsv`<br>`backup\before-name-converge\layers\slot-rules.tsv`<br>`backup\before-naming\layers\slot-rules.tsv` |
| `work\pegww2\recon_engine.py` | 2 | `docs\40-PeG-WW2中文化可行性评估.md`<br>`pegww2\README.md` |
| `work\pegww2\regen_scn_name_converge.py` | 17 | `.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-15.md` |
| `work\pegww2\restore.py` | 547 | `.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\2026-10-10.md`<br>`.workbuddy\memory\2026-10-10.md` |
| `work\pegww2\resync_src.py` | 1 | `pegww2\方法\全程复盘-踩坑与问题汇总.md` |
| `work\pegww2\rollback_namefix.py` | 1 | `pegww2\README.md` |
| `work\pegww2\run_dup_check.py` | 2 | `pegww2\README.md`<br>`pegww2\research\进度-场景层.md` |
| `work\pegww2\scan_address.py` | 1 | `pegww2\research\各国军语风格口径.md` |
| `work\pegww2\scan_fix.py` | 18 | `pegww2\research\_scn-fill-autofix-aircorps.tsv`<br>`pegww2\research\_scn-fill-autofix-br.tsv`<br>`pegww2\research\_scn-fill-autofix-dic1.tsv` |
| `work\pegww2\scan_nameslot.py` | 7 | `backup\before-cat-fix\layers\slot-rules.tsv`<br>`backup\before-name-converge\layers\slot-rules.tsv`<br>`backup\before-naming\layers\slot-rules.tsv` |
| `work\pegww2\split_chunks.py` | 2 | `.workbuddy\memory\2026-10-11.md`<br>`work\atomic\split_chunks.py` |
| `work\pegww2\split_remaining.py` | 1 | `pegww2\research\进度-场景层.md` |
| `work\pegww2\sweep_map_residue.py` | 1 | `glossary\梳理-实施记录.md` |
| `work\pegww2\sweep_map_segments.py` | 5 | `glossary\SOURCES.tsv`<br>`glossary\梳理-实施记录.md`<br>`glossary\梳理-实施记录.md` |
| `work\pegww2\tsv_esc.py` | 8 | `.workbuddy\memory\2026-10-11.md`<br>`pegww2\research\进度-场景层.md`<br>`pegww2\方法\全程复盘-踩坑与问题汇总.md` |
| `work\pegww2\verify_eqp.py` | 2 | `.workbuddy\memory\2026-10-11.md`<br>`pegww2\README.md` |
| `work\pegww2\verify_scn_fill.py` | 1 | `pegww2\research\进度-场景层.md` |
| `work\tmsg\tmsg.py` | 41 | `README.md`<br>`.workbuddy\memory\2026-09-28.md`<br>`.workbuddy\memory\2026-09-28.md` |
| `work\userscen\deploy_cmww2_userscen.py` | 3 | `.workbuddy\memory\2026-09-30.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md`<br>`docs\37-全库USERSCEN盲区量测与COMWW2清账.md` |
| `work\userscen\userscen_tool.py` | 12 | `.workbuddy\memory\2026-09-30.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md` |
| `work\xsch\xsch.py` | 22 | `README.md`<br>`.workbuddy\memory\2026-09-28.md`<br>`.workbuddy\memory\2026-09-28.md` |
| `work\xscn-openpg\build-map.py` | 3 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\MECHANICS.md`<br>`docs\12-OPENPG场景汉化完成报告.md` |
| `work\xscn-openpg\dump-one.py` | 2 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\MECHANICS.md` |
| `work\xscn-openpg\verify.py` | 222 | `.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-24.md`<br>`.workbuddy\memory\2026-09-28.md` |
| `work\xscn\_analyze-openpg.py` | 1 | `docs\68-汉化工程系统性审查与改进建议报告.md` |
| `work\xscn\apply_master.py` | 20 | `requirements.txt`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md` |
| `work\xscn\audit_number_segments.py` | 5 | `.workbuddy\memory\MECHANICS.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md`<br>`.workbuddy\memory\MEMORY-OpenPG-archive-2026-10-10.md` |
| `work\xscn\build_dict.py` | 22 | `.workbuddy\memory\2026-09-29.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md` |
| `work\xscn\build_master.py` | 22 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md` |
| `work\xscn\build_prose_dict.py` | 13 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md` |
| `work\xscn\build_rawfix.py` | 8 | `.workbuddy\memory\2026-10-09.md`<br>`.workbuddy\memory\2026-10-09.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\xscn\build_root_dict.py` | 16 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md` |
| `work\xscn\find_slot.py` | 3 | `.workbuddy\memory\2026-10-09.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md`<br>`.workbuddy\memory\MEMORY-OpenPG-archive-2026-10-10.md` |
| `work\xscn\fix_number_segments.py` | 2 | `.workbuddy\memory\MECHANICS.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\xscn\list_residual.py` | 11 | `.workbuddy\memory\2026-10-09.md`<br>`.workbuddy\memory\2026-10-09.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md` |
| `work\xscn\lookup_residual.py` | 5 | `.workbuddy\memory\2026-10-09.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md`<br>`.workbuddy\memory\MEMORY-OpenPG-archive-2026-10-10.md` |
| `work\xscn\resolve_master.py` | 14 | `.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-08.md`<br>`.workbuddy\memory\2026-10-09.md` |
| `work\xscn\union_residual.py` | 4 | `.workbuddy\memory\2026-10-09.md`<br>`.workbuddy\memory\MEMORY-archive-2026-10-10.md`<br>`.workbuddy\memory\MEMORY-OpenPG-archive-2026-10-10.md` |
| `work\xscn\xscn.py` | 284917 | `out-diag.txt`<br>`out-diag.txt`<br>`out-diag.txt` |

> 逐条命中原文：`work\out\_c1_notmoved_refs.txt`（每个脚本最多列 6 处，含文件与行内原文）。

---

## 5. 与任务书不符处 / 不确定的地方

1. **任务书假设「确实无人引用的一次性脚本」占多数，实测零入引用只有 288 / 711 = 40.5%。**
   剩余大部分脚本被 `docs\` 报告、`.workbuddy\memory\` 记忆或彼此引用钉住；按硬约束 2 一律不移动。
2. **任务书要求「对『被引用但已被取代』的脚本加 DEPRECATED 头注」，实跑结果新增 0 个**——
   工作区里没有任何一处引用明确声明某个脚本「已废弃 / 不要再跑」。不做无证据的标注（§3）。
3. **没有「已废弃」态的既有样本**，所以 §3 目前是空态定义 + 一条实测否证，不是清单；
   一旦出现首个真废弃脚本，按 §3 的判定条件补登记。
4. **移动粒度是「文件」而非「目录」**：`work\basekorp\` 等处三态脚本混在同一个目录里，
   因此只搬走零引用文件、不搬目录（避免把活跃件一起搬进 `_scratch\`）。
5. **子串误配已逐条人工确认**：10 个（`_check.py` / `_cov.py` / `_ctx.py` / `_peek.py` / `_probe2.py` / `_dump.py` / `_plan.py` / `_strings.py` / `_trace.py`），
   全部是「更长文件名里的子串」（如 `bridge_check.py` ⊃ `_check.py`），不构成引用，故仍移动。

---

## 6. 复现命令

```powershell
$env:PYTHONIOENCODING='utf-8'
# ① 重扫入引用（全工作区 substring，最保守）
C:\Python314\python.exe work\out\_c1_scan_refs.py     # 重扫候选 + 入引用 → _c1_inventory.json
C:\Python314\python.exe work\out\_c1_verify_zero.py    # 二次核对零引用 → _c1_zero_verify.txt
# ② 生成/更新本文件
C:\Python314\python.exe work\out\_c1_scripts_md.py
# ③ 移动后回归门禁（必须 rc=0 且新增/消失/变化 全为 0）
C:\Python314\python.exe work\regression.py
```
