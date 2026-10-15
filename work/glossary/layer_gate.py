#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**词库门**：层表是否符合分层词库 + 版本戳（治本件的第 3–4 步）。

三件事：
  1. **校验**：逐层表逐行判 —— 译文能否由词库复现、是否属"未登记的偏离"
  2. **分级**：
       缺失            = 词库没有该原文（必须入库）                      → ❌ 错误
       通用层内多译     = 同一原文在**通用层**有多种译法（跨项目漂移）      → ❌ 错误（除非登记）
       跨层多译(未登记) = 同一原文在不同层/scope 有不同译法且未登记        → ❌ 错误
       跨层多译(已登记) = `override.tsv` 里登过                            → ⚠️ 提示
       同形异义已登记   = 登记为"语境不同、不算错"                          → ⚠️ 提示
  3. **版本戳** `GLOSSARY.lock`：记词库各层与各层表的 sha/条数 + **偏离基线**
     ⇒ 冻结基线（`--baseline`）后，本门**只拦新增偏离**，不追究历史遗留。
       这解决"历史遗留一大片、一开门就全红"的问题，同时保证**新改动必须合规**。

用法:
  python layer_gate.py                 # 校验（对基线，只报新增偏离）
  python layer_gate.py --baseline      # 冻结当前状态为基线（写 GLOSSARY.lock）
  python layer_gate.py --full          # 连历史遗留一起列（审计用，退出码仍按"新增"）
"""
import collections
import hashlib
import io
import json
import os
import sys
import time

WS = r"D:\DSH\军事游戏汉化"
GL = os.path.join(WS, "glossary")
LAY = os.path.join(GL, "layers")
EVID = os.path.join(GL, "evidence")
BANK = os.path.join(GL, "standard-glossary.tsv")
LOCK = os.path.join(GL, "GLOSSARY.lock")

# ── 阵营/年代维度 · 接线（第一步：只报不判）────────────────────────────────
#   `faction_wire` 把「地名ID × 阵营 × 年代」这套登记**显示**到门里，但
#   **不参与** ok/bad/退出码 —— 判定结果与接线前逐字一致（见 docs/44）。
#   设 `GLOSSARY_NO_WIRE=1` 可整体跳过（流水线提速用）。
try:
    import faction_wire
except Exception:                                          # 缺模块时门照常工作
    faction_wire = None


def wire_brief():
    """返回 (摘要字符串 or None, 计数 dict)；任何异常都不得影响门。

    · 被 `GLOSSARY_NO_WIRE` 关掉 ⇒ 返回 None（调用方原样回退到接线前行为）
    · 接线失败 ⇒ 返回一行说明，不改判定
    """
    if faction_wire is None or os.environ.get("GLOSSARY_NO_WIRE"):
        return None, {}
    try:
        s = faction_wire.summary()
    except Exception as e:
        return "（接线失败：%s）" % e, {}
    # ⭐ 2026-10-13：放宽数一律以**真实门**为准。简化口径（只含 faction 两表、按 ID 建键）
    #    实测报「1 条」，真实门是「0 条」—— 它漏算了 override/scope-diff/faction-terms/词库本身。
    eff = s.get("effect") or {}
    real = eff.get("loosened")
    loose = ("修键后放宽 %d 条（真实门）" % real) if real is not None \
            else ("修键后放宽 %d 条（简化口径·偏乐观）" % s["flip_unreg"])
    return ("登记 %d ID（未解析 %d）· 唯一阵营 %d / 多阵营 %d / 简称 %d / 复合标题 %d"
            " · %s"
            % (s["ids"], s["unresolved"], s["only1"], s["many"], s["short"],
               s["compound"], loose), s)
RES = os.path.join(WS, "pegww2", "research")
PRES = os.path.join(WS, "peg", "research")

# 层表 → 该表所属项目 scope（判断"本项目层"用）
TABLES = [
    ("pegww2/research/WW2Gui-map.tsv", os.path.join(RES, "WW2Gui-map.tsv"), 1, 2, "PEGWW2_UI"),
    ("pegww2/research/WW2Misc-map.tsv", os.path.join(RES, "WW2Misc-map.tsv"), 1, 2, "PEGWW2_UI"),
    ("pegww2/research/WW2Tips-map.tsv", os.path.join(RES, "WW2Tips-map.tsv"), 1, 2, "PEGWW2_UI"),
    ("pegww2/research/ww2-eqp-map.tsv", os.path.join(RES, "ww2-eqp-map.tsv"), 0, 1, "PEGWW2_EQP"),
    ("pegww2/research/ww2-scn-map.tsv", os.path.join(RES, "ww2-scn-map.tsv"), 0, 1, "PEGWW2_SCN"),
    # ⭐ 单位名层（401 行）此前**不在门内**（覆盖缺口）：它被 `gen_value.py`/`ingest_layers.py`/
    #    `check_glossary.py` 引用，译文能进游戏，却没有任何一致性拦截。ingest 侧早已按
    #    scope=`PEGWW2_NAME` 入库（见 ingest_layers.py:162），此处补齐门侧。
    ("pegww2/research/WW2NAME-map.tsv", os.path.join(RES, "WW2NAME-map.tsv"), 0, 1, "PEGWW2_NAME"),
    ("peG/research/gui030-zh.tsv", os.path.join(PRES, "gui030-zh.tsv"), 1, 2, "PEG_UI"),
]
SKIP = ("原文", "行号", "en", "english", "檔類", "档类")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()[:16]


def load_glossary():
    by = collections.defaultdict(list)
    for fn in ("common-glossary.tsv", "series-glossary.tsv", "scope-glossary.tsv"):
        p = os.path.join(LAY, fn)
        if not os.path.isfile(p):
            continue
        for l in io.open(p, encoding="utf-8"):
            if l.startswith("#") or l.startswith("en\t"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 9:
                by[c[0]].append((c[1], c[8], c[3]))
    return by


def load_overrides():
    """登记表：`override.tsv`（本项目内的分工）+ `scope-diff.tsv`（跨项目/同形异义/前作未同步）。

    ⚠️ 两张表**列序不同**，取值列要分别指定：
       · `override.tsv`   ：`en | 层 | 覆盖为 | 理由`     ⇒ 值在第 **3** 列（索引 2）
       · `scope-diff.tsv` ：`en | 各译法 | 类别 | 理由`   ⇒ 值在第 **2** 列（索引 1）
       （踩过：统一读第 2 列 ⇒ 把"层"当成允许译法，5 条明明是已登记的却报未登记）
    """
    ov = {}
    for fn, vcol in (("override.tsv", 2), ("scope-diff.tsv", 1), ("faction-terms.tsv", 2),
                     ("faction-places.tsv", 3), ("faction-ops.tsv", 3),
                     ("scn-place-override.tsv", 3)):
        p = os.path.join(LAY, fn)
        if not os.path.isfile(p):
            continue
        for l in io.open(p, encoding="utf-8"):
            if l.startswith("#") or l.startswith("en\t"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) > vcol and c[0].strip():
                vals = [x for x in c[vcol].replace("|", "\t").split("\t") if x]
                ov.setdefault(c[0].strip(), set()).update(vals)
                # ⭐ 别名回填（缺口：登记 ID 与层表键拼写不同 ⇒ 登记在门里失效）。
                #    两张阵营表的列是 `地名ID|阵营|该方称法|中文译名|其它常见写法|时期|依据`，
                #    第 5 列（索引 4）就是"同一地方的另一拼法"（Chisinau↔Kishinev、
                #    Citadel_ND↔Nordwind…）。不按它回填，这些登记就只对审计器有效、
                #    对**门**完全无效（门只按 en 键查）。
                if fn in ("faction-places.tsv", "faction-ops.tsv") and len(c) > 4:
                    for al in c[4].replace("，", ",").replace("、", "|").replace("/", "|") \
                                   .replace(";", "|").replace(",", "|").split("|"):
                        al = al.strip()
                        if al:
                            ov.setdefault(al, set()).update(vals)
    return ov


def compute(by, ov):
    """返回 (层表统计, 偏离集合)。偏离集合是**冻结基线**与"新增偏离"的比较对象。"""
    tables = {}
    for tag, path, ec, zc, scope in TABLES:
        if not os.path.isfile(path):
            continue
        n = ok = multi = miss = 0
        for l in io.open(path, encoding="utf-8-sig"):
            if l.startswith("#"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) <= max(ec, zc) or not c[ec].strip():
                continue
            en, zh = c[ec].strip(), c[zc].strip()
            if not zh or en.lower() in SKIP:
                continue
            n += 1
            cands = by.get(en, ())
            if not cands:
                miss += 1
                continue
            exact = {z for z, _la, sc in cands if sc == scope}
            if zh in exact:
                ok += 1
            elif zh in {z for z, _la, _sc in cands}:
                multi += 1                     # 能复现，但来自别的层/scope ⇒ 跨层偏离
            else:
                miss += 1
        tables[tag] = {"n": n, "ok": ok, "multi": multi, "miss": miss, "sha": sha(path)}
    # 偏离集合：同一原文有多种译法
    div = []
    for en, lst in by.items():
        zs = sorted({z for z, _la, _sc in lst})
        if len(zs) < 2:
            continue
        layers = sorted({la for _z, la, _sc in lst})
        scopes = sorted({sc for _z, _la, sc in lst})
        if en in ov and set(zs) <= ov[en]:
            cls = "已登记"
        elif len(layers) == 1 and layers[0] == "COMMON":
            cls = "通用层内多译"
        elif len(scopes) == 1:
            cls = "同 scope 多译"
        else:
            cls = "跨层多译"
        div.append({"en": en, "zh": zs, "layers": layers, "scopes": scopes, "cls": cls})
    div.sort(key=lambda d: (d["cls"], d["en"]))
    return tables, div


def quick_check(verbose=True):
    """给流水线用的**静默门**：返回 (ok, 摘要)。供 gen_text/gen_value/build_all/deploy 前置调用。"""
    try:
        by, ov = load_glossary(), load_overrides()
        tables, div = compute(by, ov)
    except Exception as e:                                  # 词库缺失时不要卡死流水线
        return True, "词库门跳过（%s）" % e
    miss = sum(s["miss"] for s in tables.values())
    lock = json.load(io.open(LOCK, encoding="utf-8")) if os.path.isfile(LOCK) else {}
    base = {tuple(d["zh"]) + (d["en"],) for d in lock.get("divergence", [])} if lock else None
    new = []
    for d in div:
        if d["cls"] == "已登记":
            continue
        if base is not None and tuple(d["zh"]) + (d["en"],) in base:
            continue
        new.append(d)
    # 版本戳：自基线以来哪些层表变了 ⇒ 哪些成品需重建
    changed = [t for t, s in tables.items()
               if lock.get("tables", {}).get(t, {}).get("sha") not in (None, s["sha"])]
    ok = (miss == 0 and not new)
    msg = "词库门 %s：缺失 %d · 新增偏离 %d · 自基线变动层表 %d" % ("通过" if ok else "未过", miss, len(new), len(changed))
    # ⚠️ 阵营/年代维度**只加进消息**，不参与 ok（接线第一步：只报不判）
    brief, _ws = wire_brief()
    if brief:
        msg = msg + " ｜ 阵营维度：" + brief
    if verbose:
        print("  " + msg)
        for t in changed:
            print("     ⚠️ 层表已变（对应成品需重建）：%s" % t)
        for d in new[:5]:
            print("     ❌ 新偏离：%-14s %-22s %s" % (d["cls"], d["en"][:22], " ｜ ".join(d["zh"])[:50]))
    return ok, msg


def main():
    args = sys.argv[1:]
    by = load_glossary()
    ov = load_overrides()
    tables, div = compute(by, ov)
    lock = {}
    if os.path.isfile(LOCK):
        lock = json.load(io.open(LOCK, encoding="utf-8"))
    base = {tuple(d["zh"]) + (d["en"],) for d in lock.get("divergence", [])} if lock else None

    print("=== 词库门 ===")
    print("词库候选原文 %d 条（三层合并）· override 登记 %d 条" % (len(by), len(ov)))
    for tag, s in tables.items():
        print("   %-34s 行 %-6d 本项目层 %-6d 跨层 %-5d 缺失 %d" % (tag, s["n"], s["ok"], s["multi"], s["miss"]))
    err = [s for s in tables.values() if s["miss"]]
    print("\n偏离（同原文多译）共 %d 条：" % len(div))
    for cls, n in collections.Counter(d["cls"] for d in div).most_common():
        print("   %-14s %d" % (cls, n))

    # ── 阵营/年代维度 · 接线（只报不判，**不影响判定与退出码**）──
    brief, ws = wire_brief()
    if brief:
        print("\n阵营/年代维度（接线·只报不判）：")
        print("   " + brief)
    if ws:
        print("   明细 → glossary/evidence/faction-wire.txt"
              "（python work/glossary/faction_wire.py）")
        if ws.get("unresolved"):
            print("   ⚠️ %d 个登记 ID 未对齐到层表 en 键 ⇒ **不参与门侧 allow-list**" % ws["unresolved"])
            print("      （不是失效：登记的主要消费者是阵营审计器，按「该方称法/其它写法」"
                  "在文本里匹配，照常生效；门侧只在真出现偏离时按**实际 en 键**登记。"
                  "分类见 glossary/阵营视角-约定.md §十一）")
        for k, v in (ws.get("und") or {}).items():
            print("   · %s = %s" % (k, v))

    new = []
    if base is None:
        print("\n（首次运行：无基线 ⇒ 只报告，不判新增）")
    else:
        for d in div:
            k = tuple(d["zh"]) + (d["en"],)
            if k not in base and d["cls"] != "已登记":
                new.append(d)
        print("\n⭐ 相对基线**新增**的偏离 %d 条（这些才是要拦的）：" % len(new))
        for d in new[:20]:
            print("   %-14s %-24s %s" % (d["cls"], d["en"][:24], " ｜ ".join(d["zh"])[:70]))

    bad = bool(err) or bool(new)
    if "--full" in args:
        print("\n（--full：全部偏离）")
        for d in div:
            print("   %-14s %-24s %s" % (d["cls"], d["en"][:24], " ｜ ".join(d["zh"])[:70]))

    if "--baseline" in args:
        doc = {
            "frozen_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "bank_sha": sha(BANK),
            "layers": {fn.split("-")[0]: {"n": sum(1 for i, _l in enumerate(io.open(os.path.join(LAY, fn), encoding="utf-8")) if i > 1),
                                          "sha": sha(os.path.join(LAY, fn))}
                       for fn in ("common-glossary.tsv", "series-glossary.tsv", "scope-glossary.tsv")},
            "tables": tables,
            "overrides": ov and {k: sorted(v) for k, v in ov.items()},
            "divergence": div,
        }
        io.open(LOCK, "w", encoding="utf-8").write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        print("\n✅ 基线已冻结 → %s（%d 条偏离入库）" % (LOCK, len(div)))
        return 0

    os.makedirs(EVID, exist_ok=True)
    rep = ["词库门报告  " + time.strftime("%Y-%m-%d %H:%M:%S"), "=" * 60,
           "词库候选 %d 条 · override %d 条" % (len(by), len(ov)), ""]
    for tag, s in tables.items():
        rep.append("%-34s 行 %-6d 本项目层 %-6d 跨层 %-5d 缺失 %d" % (tag, s["n"], s["ok"], s["multi"], s["miss"]))
    rep += ["", "偏离分级："] + ["   %-14s %d" % (c, n) for c, n in collections.Counter(d["cls"] for d in div).most_common()]
    rep += ["", "相对基线新增：%d 条" % len(new)] + ["   %-14s %-24s %s" % (d["cls"], d["en"][:24], " ｜ ".join(d["zh"])[:70]) for d in new]
    if brief:
        rep += ["", "阵营/年代维度（接线·只报不判，不影响判定）：", "   " + brief]
    io.open(os.path.join(EVID, "layer-gate.txt"), "w", encoding="utf-8").write("\n".join(rep) + "\n")
    print("\n判定：%s" % ("❌ 有错误（缺失 %d 处 / 新增偏离 %d 条）" % (sum(s["miss"] for s in tables.values()), len(new)) if bad else "✅ 通过"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
