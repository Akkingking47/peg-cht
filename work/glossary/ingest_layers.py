#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**分层入库**：把「既有主库 + 本项目各层表」归入四层词库草案（**不改主库**）。

产出（`glossary/layers/`）：
  `common-glossary.tsv`  通用层  地名/人名/国名/部队名/装备名/军语 —— 跨项目复用
  `series-glossary.tsv`  系列层  ⭐**数据判定**：同一英文**同时**出现在前作 PeG 界面层与本作界面层
                                 ⇒ 同引擎家族共用（如 威望/胜利格/辉煌胜利/部署与补给）
  `scope-glossary.tsv`   专项层  单项目自定：保留原文政策·长文本·菜单/面板/技能/编辑器文案
  `short-glossary.tsv`   ⭐ 短名层 槽位受限的长→短对照（对齐 pg-cht 的 glossary_short）
  `common-drift.tsv`     ⭐ 漂移清单（**分级**：政策差异/纯风格差/用词音译差异/待人工裁定）
  `override.tsv`         覆盖登记（专项/系列覆盖上层，带理由）

层文件列（**前 8 列与主库一致**，其后为新增 ⇒ 旧工具照常可用）：
  `en | zh | cat | scope | status | src | conf | zh_in | layer | bytes | slot | note`

判据（确定、可审；**用途标签取自官方 PFS 分段**，对齐 pg-cht 的 `檔類`）：
  · `zh == en` ⇒ 专项（保留原文政策）
  · 长句散文 ⇒ 专项
  · 专名类（PLACE/LEADER/NATION/UNIT/EQUIP/TITLE）⇒ 通用
  · 界面词按 **PFS 用途** 分：单位特性/国名/兵种/地形天气/移动 ⇒ 通用；菜单/面板/技能/战果/编辑器 ⇒ 专项
  · ⭐ 系列层**覆盖**上述判定：同英文同时出现在 **前作 PeG 界面层** 与 **本作界面层** ⇒ 系列
  · ⭐ **长度**：GBK 字节数（本作编码）；`slot=20` = 受 **20 字节定长字段**限制
    （`.scn` 文本字段定长 20 字节 + NUL 填充 ⇒ GBK 下 ≤10 汉字）

用法: python ingest_layers.py [--apply]
"""
import collections
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
GL = os.path.join(WS, "glossary")
OUTD = os.path.join(GL, "layers")
EVID = os.path.join(GL, "evidence")
BANK = os.path.join(GL, "standard-glossary.tsv")
PFS = os.path.join(WS, "work", "peg", "pfs", "GUI-Segmented.txt")
RES = os.path.join(WS, "pegww2", "research")
PRES = os.path.join(WS, "peg", "research")
DOCSTERM = os.path.join(WS, "pegww2", "docs-zh", "_翻译须知与术语.md")
SHORTEN = os.path.join(RES, "_eqp-carrier-shorten.tsv")
SLOT_BYTES = 20
# ⭐ 槽位规则（**有据可查**；不搞"一刀切 20 字节"）：见 evidence/slot-rules.tsv
#   适用层/用途 → (规则名, 上限, 单位, 证据)
SLOT_RULES = [
    ("scn20B", 20, "bytes", "`.scn` @11210/@11230/@11329 定长 20B（recon9_scnfields.py 实测）", ("PEGWW2_SCN_FIELD",)),
    ("ui5", 5, "hanzi", "UI 短标签 ≤5 汉字可完整显示（docs/38 §6.5/6.9 实测）",
     ("MISCELLANEOUS INTERFACE LABELS", "MISCELLANEOUS INTERFACE LABELS 2", "MISCELLANEOUS INTERFACE LABELS 3",
      "MISCELLANEOUS INTERFACE LABELS 4", "MISCELLANEOUS INTERFACE LABELS 5", "HOT KEYS HELP")),
]


def hanzi(s):
    return sum(1 for c in s if "\u4e00" <= c <= "\u9fff")

# 官方 PFS 分段 → (类别, 预设层)
#   ⚠️ 踩点：**不要**用"该串在前作与本作都出现"当系列层判据 —— 本作 GUI 文件就是
#      基础 PeG 的 GUI 改的，未改动的行两边必然都有，长提示句也会命中。
#      ⇒ 系列层改按**用途**判：引擎家族的机制类用途 = 系列；本项目自有文案 = 专项。
SEG = {
    "COUNTRY NAMES": ("NATION", "COMMON"),
    "AIR MOBILITY": ("TERM", "COMMON"),
    "UNIT CHARACTERISTICS LABELS": ("TERM", "COMMON"),
    "EQUIPMENT CLASS LABELS": ("UNIT", "COMMON"),
    "GROUND CONDITIONS, DATE & WEATHER LABELS": ("TERM", "COMMON"),
    # 引擎家族机制（PG/PeG/PG2 同族共享）
    "UNIT ATTACHMENT LABELS": ("TERM", "SERIES"),
    "LEADER TYPE NAMES": ("TERM", "SERIES"),
    "WINNING RANKS": ("TERM", "SERIES"),
    "EQUIPMENT SPECIAL ABILITIES": ("TERM", "SERIES"),
    "AIR MISSION LABELS 1": ("TERM", "SERIES"),
    "AIR MISSION LABELS 2": ("TERM", "SERIES"),
    "UNIT BATTLE RECORD LABELS": ("TERM", "SERIES"),
    # 本项目自有文案
    "HOT KEYS HELP": ("TERM", "SCOPE"),
    "INTERNET & LAN PLAY 1": ("TERM", "SCOPE"),
    "INTERNET & LAN PLAY 2": ("TERM", "SCOPE"),
}
for _k in list(SEG):
    if _k.startswith("SCENARIO BUILDER"):
        SEG[_k] = ("TERM", "SCOPE")
# 术语基准表里的「类别」→ 预设层
KIND = {
    "兵种": "COMMON", "编制": "COMMON", "军衔": "COMMON", "移动方式": "COMMON",
    "地形": "COMMON", "天气": "COMMON", "缩写": "COMMON", "数值": "COMMON",
    "阵营": "COMMON", "舰艇": "COMMON", "装备名": "COMMON", "后勤": "COMMON",
    "工事": "COMMON", "装备后缀": "COMMON",
    "菜单": "SCOPE", "游戏机制": "SCOPE", "战果": "SCOPE", "战斗提示": "SCOPE",
    "指挥官技能": "SCOPE", "特种装备": "SCOPE", "属性": "SCOPE", "标签": "SCOPE",
    "战场要素": "SCOPE", "战术": "SCOPE", "武器型号": "COMMON", "类别": "SCOPE",
}


def gbk_len(s):
    try:
        return len(s.encode("gbk"))
    except UnicodeEncodeError:
        return -1


def pfs_sections():
    """GUI 行号 → PFS 分段名。"""
    out, cur = {}, None
    if not os.path.isfile(PFS):
        return out
    for l in io.open(PFS, encoding="cp1252", errors="replace"):
        c = l.split("|")
        if len(c) < 3:
            continue
        num = c[2].strip()
        if not num:
            continue
        if num.replace(".", "").isdigit():
            if cur:
                out[int(float(num))] = cur
        else:
            cur = num
    return out


def load_pairs(path, ecol, zcol):
    out = []
    if not os.path.isfile(path):
        return out
    for l in io.open(path, encoding="utf-8-sig"):
        if l.startswith("#"):
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) <= max(ecol, zcol):
            continue
        en, zh = c[ecol].strip(), c[zcol].strip()
        if not en or not zh or en.lower() in ("行号", "原文", "en", "english") or re.fullmatch(r"\d+", en):
            continue
        out.append((en, zh, c[0].strip()))
    return out


def main():
    apply_ = "--apply" in sys.argv
    segs = pfs_sections()
    raw = []          # (en, zh, cat, scope, src, conf, note)

    def add(en, zh, cat, scope, src, conf="", note=""):
        if en and zh:
            raw.append((en, zh, cat, scope, src, conf, note))

    # ① 既有主库
    n_bank = 0
    for i, l in enumerate(io.open(BANK, encoding="utf-8-sig")):
        if i == 0:
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) >= 8:
            add(c[0], c[1], c[2], c[3], c[5], c[6], "主库:" + c[2])
            n_bank += 1
    # ②本作界面（用途＝PFS 分段）
    # ⚠️ 列位必须按**该表自己**的列序给：界面三表带「行号」列 ⇒ (1, 2)；
    #    单位名表表头是 `原文|译文|来源`（**无行号列**）⇒ 必须 (0, 1)。
    #    踩过（W21）：WW2NAME 曾与界面三表共用 (1, 2) ⇒ 每行都被**转置**入库
    #    （en 存成中文名、zh 存成「新译/词库」来源标签），399 条英文键从未进词库，
    #    而门又没覆盖该表 ⇒ 这个错误**静默存在了整轮**，直到把该表纳入门才暴露。
    for fn, scope, tag in (("WW2Gui-map.tsv", "PEGWW2_UI", "ui"),
                           ("WW2Misc-map.tsv", "PEGWW2_UI", "ui"),
                           ("WW2Tips-map.tsv", "PEGWW2_UI", "ui")):
        for en, zh, no in load_pairs(os.path.join(RES, fn), 1, 2):
            seg = segs.get(int(no)) if no.isdigit() else None
            add(en, zh, SEG.get(seg, ("TERM",))[0], scope, tag, "HIGH", seg or "未分类")
    for en, zh, no in load_pairs(os.path.join(RES, "WW2NAME-map.tsv"), 0, 1):
        add(en, zh, "UNIT", "PEGWW2_NAME", "names", "HIGH", "指挥官/单位名")
    # ②b 前作界面（系列层判定用）
    for en, zh, no in load_pairs(os.path.join(PRES, "gui030-zh.tsv"), 1, 2):
        seg = segs.get(int(no)) if no.isdigit() else None
        add(en, zh, SEG.get(seg, ("TERM",))[0], "PEG_UI", "ui", "HIGH", seg or "未分类")
    # ②c 基准表（带权威类别）
    for en, zh, _ in load_pairs(os.path.join(PRES, "ui-glossary.tsv"), 0, 1):
        pass
    if os.path.isfile(os.path.join(PRES, "ui-glossary.tsv")):
        for l in io.open(os.path.join(PRES, "ui-glossary.tsv"), encoding="utf-8-sig"):
            if l.startswith("#"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 4 and c[0].strip() and c[1].strip():
                add(c[0], c[1], "TERM", "PEG_BASE", "basis", "HIGH", c[2].strip())
    # ②d 装备
    n_eqp = 0
    for en, zh, _ in load_pairs(os.path.join(RES, "ww2-eqp-map.tsv"), 0, 1):
        add(en, zh, "EQUIP", "PEGWW2_EQP", "equip", "HIGH", "装备名")
        n_eqp += 1
    # ②e 场景层
    n_scn = 0
    for en, zh, _ in load_pairs(os.path.join(RES, "ww2-scn-map.tsv"), 0, 1):
        long = len(en.split()) > 6 or bool(re.search(r"[.;!?]\s|,\s", en))
        add(en, zh, "TEXT" if long else "UNIT", "PEGWW2_SCN", "scn", "MID",
            "长句散文" if long else "场景/地名/部队名")
        n_scn += 1
    # ②e-bis per-file 覆盖表（`pegww2/research/_scn-file-overrides.tsv`）
    #   ⚠️ 这是**第三个译法真源**：`gen_scn.py` 里它 **优先于** `ww2-scn-map.tsv` 的整串键控
    #      （per-file 行号级覆盖 > 整串精确匹配 > 原样保留）。
    #   此前从未入库 ⇒ 词库对这些键只能看到映射表的 `Breda -> Breda`，于是把它们判成
    #      「保留原文政策」，而**成品其实已译**（布雷达/法拉格特/柯尼斯堡/努比亚号…）。
    #   纳入范围：只收 **映射表没给中文**（无该键、或该键的 zh == en）的行 ⇒ 落到 COMMON 层，
    #      与映射表留英文的那行（SCOPE 层）不冲突，`layer_gate` 新增偏离为 0。
    #   映射表**另有**中文但与覆盖表不同的键（同 scope 同层双译）、以及**同键在不同文件有不同
    #      译名**的键，层表表达不了（键没有文件维度，压平就是造假）⇒ 只落证据表供人工裁定。
    n_ovf = 0
    n_ovf_div = 0
    n_ovf_clash = 0
    n_ovf_divrow = 0
    n_ovf_clashrow = 0
    ovf_note = []
    ovf_keep_pairs = []          # 入库的 (en, zh)：须同时登记到 override.tsv，否则门判「跨层多译」
    OVF = os.path.join(RES, "_scn-file-overrides.tsv")
    if os.path.isfile(OVF):
        MAP_ZH = {}
        for _en, _zh, _ in load_pairs(os.path.join(RES, "ww2-scn-map.tsv"), 0, 1):
            MAP_ZH[_en] = _zh
        ovf_rows = []
        for l in io.open(OVF, encoding="utf-8-sig"):
            if l.startswith("#"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) < 5:
                continue
            en, zh, fname, sub = c[3].strip(), c[4].strip(), c[1].strip(), c[0].strip()
            if not en or not zh or zh == en or en in ("期望原文", "原文"):
                continue
            ovf_rows.append((en, zh, fname, sub))
        seen_zh = collections.defaultdict(set)
        for en, zh, _fn, _sub in ovf_rows:
            seen_zh[en].add(zh)
        div = {en for en, zs in seen_zh.items() if len(zs) > 1}
        done = set()
        for en, zh, fname, sub in ovf_rows:
            if en in div:
                ovf_note.append((en, zh, sub + "/" + fname, "同键多译"))
                n_ovf_divrow += 1
                continue
            if en in MAP_ZH and MAP_ZH[en] != zh:
                # ⭐ 用户裁定「并入」（m01713-②）：映射表另有中文**不再排除**。
                #    同一英文键在映射表与 per-file 覆盖表各有一个中文，是**两个优先级层**
                #    的真实取值；两者 scope 不同（PEGWW2_SCN / PEGWW2_SCN_OVR），
                #    去重键 (en, 层, scope) 不冲突，可并存。
                #    ⚠️ 但**两侧的值都要登记**到 override.tsv：只登记覆盖表那侧时，
                #       另一侧的映射表中文就成了未登记偏离 ⇒ 门报「跨层多译/通用层内多译」。
                # ⭐ 补登记（2026-10-19）：映射表**留英文**（`MAP_ZH[en] == en`）的键同属此列 ——
                #    层表里 COMMON 拿覆盖表中文、SCOPE 拿映射表原样，值不同 ⇒ 同样是
                #    「跨层多译」新增偏离（实测 88 条番号）。原判据写成
                #    `MAP_ZH[en] != en and ...` 把这一类漏掉，只收「中文不同」的一类。
                n_ovf_clashrow += 1
                ovf_keep_pairs.append((en, MAP_ZH[en]))
            if en in done:
                continue
            done.add(en)
            long = len(en.split()) > 6 or bool(re.search(r"[.;!?]\s|,\s", en))
            # ⭐ scope 用 **PEGWW2_SCN_OVR** 而不是 PEGWW2_SCN：两者是**不同优先级层**
            #    （per-file 行号级覆盖 > 整串精确匹配 > 原样保留）。若并入同一 scope，
            #    `layer_gate` 会把它判成「同 scope 多译」新增偏离 108 条 —— 那是**假冲突**：
            #    同一个键在映射表里留英文、在覆盖表里给中文，是**设计**而非矛盾。
            #    分 scope ⇒ 每 (en, scope) 仍只有一个中文，门保持干净，且两者都可查。
            add(en, zh, "TEXT" if long else "UNIT", "PEGWW2_SCN_OVR", "scn-ovr", "HIGH",
                "按场景定点覆盖:" + fname)
            ovf_keep_pairs.append((en, zh))
            n_ovf += 1
        n_ovf_div = len(div)
        n_ovf_clash = n_ovf_clashrow

    # ②f 文档层
    n_doc = 0
    if os.path.isfile(DOCSTERM):
        for l in io.open(DOCSTERM, encoding="utf-8"):
            m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", l)
            if not m or m.group(1).strip() in ("英文", "---"):
                continue
            en = re.sub(r"[（(][^）)]*[）)]\s*$", "", m.group(1).strip())
            if en and not en.startswith("-"):
                add(en, m.group(2), "TERM", "PEGWW2_DOCS", "docs", "HIGH", "文档")
                n_doc += 1

    # ③ 系列层：按**用途**判定（见 SEG 预设的注释：不用"两边都出现"，该信号不可靠）
    def is_fmt(s):
        return ("%" in s) or len(s) > 28 or s.count(" ") > 4

    ui_prev = {r[0] for r in raw if r[3] == "PEG_UI" and not is_fmt(r[0])}
    ui_cur = {r[0] for r in raw if r[3].startswith("PEGWW2") and not is_fmt(r[0])}
    both = ui_prev & ui_cur          # 仅供报告：本作与前作都有（≈未被本项目改动）

    def layer_of(r):
        en, zh, cat, scope, src, conf, note = r
        if zh == en:
            return "SCOPE", "保留原文政策"
        if cat in ("TEXT",):
            return "SCOPE", "长文本"
        if cat in ("PLACE", "LEADER", "NATION", "UNIT", "EQUIP", "TITLE"):
            return "COMMON", note
        if note in KIND:
            return KIND[note], note
        for seg, (c, lay) in SEG.items():
            if note == seg:
                return lay, seg
        return "SCOPE", note or "未分类"

    best = {}
    for r in raw:
        lay, why = layer_of(r)
        # ⚠️ 去重键必须是 **(en, 层, scope)**：若只用 (en, 层)，同层内不同 scope 的同原文异译
        #    会被合并掉 ⇒ 跨项目/前作差异**看不见**（Profile 概况/轮廓 就是这么消失的）。
        k = (r[0], lay, r[3])
        if k not in best or r[1] == r[0]:
            best[k] = r + (lay, why)
    rows = sorted(best.values(), key=lambda r: (r[7], r[2], r[0].lower()))
    cnt = collections.Counter(r[7] for r in rows)

    print("=== 分层入库草案（输入：主库 %d · 本作装备 %d · 场景 %d · 按场景覆盖 %d · 文档 %d）==="
          % (n_bank, n_eqp, n_scn, n_ovf, n_doc))
    if n_ovf_divrow or n_ovf_clashrow:
        print("   按场景覆盖表：收 %d 键入库 · 只落证据 %d 行（同键多译 %d 键/%d 行）"
              " · 映射表另有中文**已并入** %d 行"
              % (n_ovf, n_ovf_divrow, n_ovf_div, n_ovf_divrow, n_ovf_clashrow))
    print("   原始记录 %d ⇒ 去重后 %d" % (len(raw), len(rows)))
    for k in ("COMMON", "SERIES", "SCOPE"):
        print("   %-8s %6d 条" % (k, cnt[k]))
    over = [r for r in rows if gbk_len(r[1]) > SLOT_BYTES]
    print("   按证据规则判定的超限行（见 slot-rules.tsv）：")

    def slot_of(r):
        """只在**有据可查**的用途上判槽位；其余留空（不假装知道限制）。"""
        note = r[8]
        for name, lim, unit, ev, applies in SLOT_RULES:
            if note in applies:
                val = hanzi(r[1]) if unit == "hanzi" else gbk_len(r[1])
                return name, val > lim
        return "", False

    viol = [(r, slot_of(r)[0]) for r in rows if slot_of(r)[1]]
    for name, lim, unit, ev, _a in SLOT_RULES:
        n = sum(1 for _r, s in viol if s == name)
        print("      %-8s 上限 %s%s ⇒ 超限 %d 条" % (name, lim, unit, n))
    print("   系列层样例：%s" % "、".join(r[0] for r in rows if r[7] == "SERIES")[:110])

    by = collections.defaultdict(lambda: collections.defaultdict(set))
    for r in rows:
        by[r[0]][r[1]].add(r[3])
    drift = []
    prose = 0
    for en, d in by.items():
        zh = [z for z in d if z != en]
        scopes = {s for ss in d.values() for s in ss}
        if len(zh) < 2 or len(scopes) < 2:
            continue
        if len(en) > 60 or any(x in en for x in ("。", "，")):     # 长句=散文，不进术语漂移清单
            prose += 1
            continue
        cat = next((r[2] for r in rows if r[0] == en), "")
        if any(z == en for z in d):
            kind = "政策差异"                       # 一边保留原文（非错误）
        else:
            # 分级：有没有共同汉字 —— 有 ⇒ 同一概念的不同用词/风格；无 ⇒ 可能同形异义
            sets = [set(c for c in z if "\u4e00" <= c <= "\u9fff") for z in zh]
            common = set.intersection(*sets) if len(sets) > 1 else set()
            if not common:
                kind = "同形异义候选"               # 如 Ranger 游骑兵(美军)/突击队(英军)
            else:
                ls = sorted(len(z) for z in zh)
                kind = "纯风格差" if ls[-1] - ls[0] <= 1 else "用词差异"
        drift.append((en, cat, kind, " ｜ ".join("%s(%s)" % (z, "/".join(sorted(ss))) for z, ss in d.items())))
    print("   漂移 %d 条（另有散文差异 %d 条未计入术语表）" % (len(drift), prose))

    if not apply_:
        print("\n（dry-run；加 --apply 写 %s）" % OUTD)
        return 0

    os.makedirs(OUTD, exist_ok=True)
    os.makedirs(EVID, exist_ok=True)
    # per-file 覆盖表里**层表表达不了**的部分（同键多译）落证据，供人工裁定
    with io.open(os.path.join(EVID, "ingest-scn-ovr.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# per-file 覆盖表（pegww2/research/_scn-file-overrides.tsv）中**未进层表**的行\n")
        f.write("# 层表键＝(en, 层, scope)，没有**文件维度** ⇒ 同一英文在不同文件取值不同时压平会造假，故只登记来源。\n")
        f.write("# 注：『映射表另有中文』自 m01713-② 起已**并入**（scope=PEGWW2_SCN_OVR，与映射表并存）。\n")
        f.write("en\t覆盖表中文\t来源文件\t未并入原因\n")
        for en, zh, where, why in sorted(ovf_note):
            f.write("%s\t%s\t%s\t%s\n" % (en, zh, where, why))
    HDR = "en\tzh\tcat\tscope\tstatus\tsrc\tconf\tzh_in\tlayer\tbytes\tslot\tnote\n"
    for lay, fn in (("COMMON", "common-glossary.tsv"), ("SERIES", "series-glossary.tsv"),
                    ("SCOPE", "scope-glossary.tsv")):
        with io.open(os.path.join(OUTD, fn), "w", encoding="utf-8", newline="\n") as f:
            f.write("# 层=%s（`ingest_layers.py` 产出，勿手改；改各层真源后重跑）\n" % lay)
            f.write(HDR)
            for r in rows:
                if r[7] != lay:
                    continue
                f.write("\t".join([r[0], r[1], r[2], r[3], ("POLICY" if r[1] == r[0] else "LOCKED"),
                                   r[4], r[5], r[4], r[7], str(gbk_len(r[1])),
                                   slot_of(r)[0], r[8]]) + "\n")
    with io.open(os.path.join(OUTD, "short-glossary.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# 短名层：槽位受限的长→短对照（对齐 pg-cht glossary_short）\n")
        f.write("# 判据见 slot-rules.tsv；未有据可查的行**不臆断**，只记 bytes\n")
        f.write("en\tzh_long\tzh_short\tbytes_long\tbytes_short\tslot\tnote\n")
        seen = set()
        if os.path.isfile(SHORTEN):
            for i, l in enumerate(io.open(SHORTEN, encoding="utf-8-sig")):
                if i == 0 or l.startswith("#"):
                    continue
                c = l.rstrip("\n").split("\t")
                if len(c) >= 4 and c[1].strip() and c[0].strip() not in ("英文原文", "原文"):
                    f.write("%s\t%s\t%s\t%d\t%d\teqp\t来源:_eqp-carrier-shorten\n"
                            % (c[1], c[2], c[3], gbk_len(c[2]), gbk_len(c[3])))
                    seen.add(c[1])
        for r, sname in viol:                       # 按**适用规则**判定超限的行
            if r[0] not in seen:
                f.write("%s\t%s\t\t%d\t\t%s\t超限,待补短名\n" % (r[0], r[1], gbk_len(r[1]), sname))
    # 槽位规则表（有据可查，作为判据依据留痕）
    with io.open(os.path.join(OUTD, "slot-rules.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# 槽位/长度规则（**每条都有证据**；本工具只对适用行判限，不搞一刀切）\n")
        f.write("规则\t上限\t单位\t适用用途\t证据\n")
        for name, lim, unit, ev, applies in SLOT_RULES:
            f.write("%s\t%d\t%s\t%s\t%s\n" % (name, lim, unit, "|".join(applies), ev))
        f.write("eqp\t-\t-\t装备名(采购列表)\t无硬上限，但括注需压缩（_eqp-carrier-shorten.tsv 有原/新字数）\n")
        f.write("scndisp\t120\tchars\t场景列表显示名(_m.txt 行0)\t超长=缺陷（scan_nameslot.py 判据），须改写成场景名\n")
    with io.open(os.path.join(OUTD, "common-drift.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# 跨层/跨项目漂移（分级）。政策差异=一边保留原文(非错误)｜纯风格差｜用词/音译差异｜待人工裁定\n")
        f.write("en\tcat\t等级\t各层译法\n")
        for d in sorted(drift, key=lambda x: x[2]):
            f.write("\t".join(d) + "\n")
    with io.open(os.path.join(OUTD, "override.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# 覆盖登记：**同原文按用途分工**（专项/系列覆盖上层，必须显式登记，否则校验视为错误）\n")
        f.write("# ⚠️ 第 5 列「用途」= 官方 PFS 分段名（与层表 note 列同词表）；派生层表时**先查本表**，\n")
        f.write("#    否则同一张表里 `Air Defense` 兵种/数值两译会派生不出来。\n")
        f.write("en\t层\t覆盖为\t理由\t用途\n")
        reg = [
            ("Air Defense", "SERIES", "防空", "兵种名用「防空」", "EQUIPMENT CLASS LABELS|MISCELLANEOUS INTERFACE LABELS 4"),
            ("Air Defense", "SERIES", "对空防御", "数值/附件用「对空防御」", "UNIT ATTACHMENT LABELS|UNIT CHARACTERISTICS LABELS|MISCELLANEOUS INTERFACE LABELS 2"),
            ("Air Transport", "SERIES", "空中运输", "兵种名（与地面运输/海上运输对齐）", "EQUIPMENT CLASS LABELS"),
            ("Air Transport", "SERIES", "空运", "按钮/任务", "MISCELLANEOUS INTERFACE LABELS"),
            ("Naval Transport", "SERIES", "海上运输", "兵种名", "EQUIPMENT CLASS LABELS"),
            ("Naval Transport", "SERIES", "海运", "按钮", "MISCELLANEOUS INTERFACE LABELS"),
            ("AT", "COMMON", "反坦克", "兵种名", "EQUIPMENT CLASS LABELS"),
            ("AT", "COMMON", "AT", "型号/后缀保留缩写", "MISCELLANEOUS INTERFACE LABELS"),
        ]
        # ⭐ per-file 覆盖表登记（**必须与 ②e-bis 入库同步**）：
        #   映射表把该键留英文、覆盖表在特定文件给中文 —— 这是**两条不同优先级链路**，
        #   不是一个 scope 里的两个译法。不登记就会被 `layer_gate` 判「跨层多译」新增偏离。
        for _en, _zh in sorted(set(ovf_keep_pairs)):
            reg.append((_en, "PEGWW2_SCN_OVR", _en + "|" + _zh,
                        "映射表保留英文、per-file 覆盖表(_scn-file-overrides.tsv)在该文件翻译；"
                        "per-file > 整串匹配 > 原样保留，属设计而非冲突", "按场景定点覆盖"))
        for en, lay, val, why, use in reg:
            f.write("%s\t%s\t%s\t%s\t%s\n" % (en, lay, val, why, use))
    # 长度报告（只报分布与最长项，不臆断限制）
    lens = sorted(((gbk_len(r[1]), r[0], r[1]) for r in rows), reverse=True)
    rep = ["分层入库报告", "=" * 60,
           "输入：主库 %d · 本作装备 %d · 场景 %d · 文档 %d" % (n_bank, n_eqp, n_scn, n_doc),
           "原始记录 %d ⇒ 去重后 %d（键=en+层）" % (len(raw), len(rows)),
           "输出：" + "  ".join("%s %d" % (k, cnt[k]) for k in ("COMMON", "SERIES", "SCOPE")),
           "漂移 %d 条 · 按适用规则超限 %d 条" % (len(drift), len(viol)), "",
           "按规则判定的超限："] + \
          ["   %-8s 上限 %s%s ⇒ %d 条" % (n, l, u, sum(1 for _r, s in viol if s == n))
           for n, l, u, _e, _a in SLOT_RULES] + \
          ["", "漂移分级："] + ["   %-10s %d" % (k, sum(1 for d in drift if d[2] == k))
                            for k in ("政策差异", "纯风格差", "用词/音译差异", "待人工裁定")] + \
          ["", "最长译文 TOP 10（GBK 字节）："] + \
          ["   %3d B  %-34s %s" % (b, en[:34], zh[:28]) for b, en, zh in lens[:10]]
    io.open(os.path.join(EVID, "ingest-report.txt"), "w", encoding="utf-8").write("\n".join(rep) + "\n")
    print("\n已写 %s（三层 + 短名 + 槽位规则 + 漂移 + 覆盖登记 + 报告）" % OUTD)
    return 0


if __name__ == "__main__":
    sys.exit(main())
