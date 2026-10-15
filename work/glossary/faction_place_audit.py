#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**地名/作战名的历史称法审计**（以史料为准，**不看原文拼写**）。

用户口径（2026-10-12）：
  「不要看原文本，要看**历史上双方如何称呼同一个地名**的分歧，这样才能有历史代入感，
    这也是加强游戏体验的一环。」「作战行动也是，例如库尔斯克会战是苏联的叫法，
    德国称呼『堡垒』行动。」

判据：
  ① 先从**译文口吻**判定"这段文本属于哪一方"（三层：口吻标记 → 同场景继承 → 战役族多数票）
  ② 再看该地/该战役**历史上那一方怎么叫**（`faction-places.tsv` / `faction-ops.tsv`）
  ③ 若译文用了**别方**的称法 ⇒ 报出（警告级，附主张与依据）

关键改进（相对上一版）：
  · **不以英文拼写为键**：同一个地方按"地名ID"聚合，各方称法并列 ⇒
    英文写 `Kishinev`（俄式）但文本是罗马尼亚视角时，仍应写「基希讷乌」
  · **识别命中不限拼写**：文本里出现任何一方的写法（含英文常见写法/原语）都算提到该地

用法: python faction_place_audit.py [--sample N]
"""
import collections
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
GL = os.path.join(WS, "glossary")
LAY = os.path.join(GL, "layers")
EVID = os.path.join(GL, "evidence")
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
GAME = r"D:\Program Files\PeG-WW2\SCENARIO"

MARK = {
    # ⚠️ 只收**说话人口吻**（对上级/下属的称呼、自称）。
    #    剔除过「红军」「方面军」「最高统帅部」「法西斯入侵者」——这些是**提到**敌/我，
    #    德方简报里满篇「红军」「俄军」，据此判成苏方 ⇒ 实测把 3 份德方简报判错。
    "苏": ("将军同志", "同志，", "斯大林同志", "最高统帅部同志"),
    "德": ("将军阁下", "元首", "德意志", "我们德国"),
    "盟": ("指挥官，", "盟军将", "艾森豪威尔", "蒙哥马利", "巴顿将军", "美国陆军"),
    "罗": ("罗马尼亚军队", "安东内斯库", "Conducator", "我们罗马尼亚"),
    "芬": ("芬兰军队", "曼纳海姆", "Mannerheim", "我们芬兰"),
    "波": ("家乡军", "华沙起义", "波兰流亡政府", "我们波兰"),
    "意": ("意大利军队", "墨索里尼", "意军指挥官"),
}
# 展示位后缀：`_i`/`_m`/… 之外，本作还有**不带下划线**的写法（`110bv.TXT`/`110l.TXT`/`110tv.TXT`）。
# ⚠️ 2026-10-13 修：旧正则 `(_i|_m|…)$` **要求下划线**，导致 `110bv` 没被剥成 `110` ⇒
#    `110` 的同场景继承与 `.scn` 查找**双双失效**（实测 640 个未判定里 330 个卡在这条）。
#    新规则：`_后缀` **或** 「数字紧跟后缀」都算展示位后缀。
SUFFIX = r"(?:i|m|u|l|bv|tv|v)"
STEM_TAIL = re.compile(r"(?i)(?:_%s$|(?<=[0-9])%s$)" % (SUFFIX, SUFFIX))
STEM_TAIL_OLD = re.compile(r"(?i)(_i|_m|_u|_l|_bv|_tv|_v)$")
NO_VOICE = re.compile(r"(?i)(?:_m$|(?<=[0-9])m$|_u$|(?<=[0-9])u$)")

# 作战名识别时要剔除的**通用词/泛地理词**（不然 `Unternehmen`/`Battle`/`Bulge` 会到处命中）
# ⚠️ `bulge` 必须剔：`Orel Bulge`（奥廖尔突出部）会撞上 `Battle of the Bulge`（阿登），
#    实测这一条就造出 10+ 假阳。
OPS_STOP = {"unternehmen", "operation", "operacja", "battle", "offensive", "campaign",
            "bulge", "the", "and"}


def era_of(text):
    """从场景文本取年代 → (年, 月)；取不到返回 None（**78% 场景取不到**，故年代检查只作提示）。"""
    m = re.search(r"(19[3-5]\d)\s*年\s*(\d{1,2})?\s*月", text)
    if m:
        return int(m.group(1)), int(m.group(2) or 0)
    mon = "(?i)(january|february|march|april|may|june|july|august|september|october|november|december)"
    m = re.search(mon + r"\s+\d{1,2},?\s+(19[3-5]\d)", text)
    if m:
        idx = ["january", "february", "march", "april", "may", "june", "july",
               "august", "september", "october", "november", "december"].index(m.group(1).lower()) + 1
        return int(m.group(2)), idx
    m = re.search(r"\b(19[3-5]\d)\b", text)
    return (int(m.group(1)), 0) if m else None


def parse_era(field):
    """解析「时期」判据列 → [(op, (年,月), 译名)]；无判据返回 []。

    写法示例：`>=1940-04 → 利茨曼施塔特 ； <1940-04 → 罗兹`
    """
    out = []
    for part in re.split(r"[；;]", field):
        m = re.search(r"(<=|>=|<|>)\s*(\d{4})(?:-(\d{2}))?\s*→\s*([^|；;]+)", part)
        if m:
            out.append((m.group(1), (int(m.group(2)), int(m.group(3) or 0)), m.group(4).strip()))
    return out


def era_ok(rules, era):
    """给定年代，返回该年代的合法译名集合；无法判定返回 None。"""
    if not rules or not era:
        return None
    y, mo = era
    cur = (y, mo or 0)
    for op, ym, zh in rules:
        if (op == ">=" and cur >= ym) or (op == ">" and cur > ym) or \
           (op == "<=" and cur <= ym) or (op == "<" and cur < ym):
            return {zh}
    return None


def load_registry(fn, idc, facc, zhc, enc):
    """返回 {ID:{阵营:译名}} · {ASCII:ID} · {中文:ID} · {ID:[该方称法]} · {(ID,阵营):[年代判据]}。"""
    per, en2id, zh2id, native = collections.defaultdict(dict), {}, {}, collections.defaultdict(list)
    era = {}
    p = os.path.join(LAY, fn)
    if not os.path.isfile(p):
        return per, en2id, zh2id, native, era
    for l in io.open(p, encoding="utf-8"):
        if l.startswith("#") or l.startswith("地名ID") or l.startswith("作战ID"):
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) < 4 or not c[idc].strip():
            continue
        pid, fac, zh = c[idc].strip(), c[facc].strip(), c[zhc].strip()
        if len(c) > 2 and c[2].strip() and c[2].strip() != "—":
            native[pid].append(c[2].strip())
        # 中文译名允许**多个合法称法**，用 `|` 分隔（如盟方 `阿登战役|突出部之战`）
        for one in zh.split("|"):
            one = one.strip()
            if one and one != "—":
                per[pid][fac] = per[pid].get(fac, "") + ("|" if per[pid].get(fac) else "") + one
                zh2id[one] = pid
        for form in (c[enc] if len(c) > enc else "").split(",") + [c[idc]]:
            f = form.strip()
            if f and re.fullmatch(r"[A-Za-z' \-\.]+", f):
                en2id.setdefault(f.lower(), pid)
        # ⭐ 年代维度（试点）：第 6 列「时期」若含 `op YYYY[-MM] → 译名` 即视为**年代判据**
        #    ⚠️ 必须**累积**（同一 (ID,阵营) 可有多条年代规则，如苏方 Königsberg: ≤1945 柯尼斯堡 / ≥1946 加里宁格勒）
        if len(c) > 5 and "→" in c[5]:
            rr = parse_era(c[5])
            if rr:
                era.setdefault((pid, fac), []).extend(rr)
    return per, en2id, zh2id, native, era


def norm(s):
    """归一化：剥掉书名号/引号/空格 —— 游戏惯用「火炬」行动，登记表写 `火炬行动` ⇒ 必须能匹配。"""
    return re.sub(r"[「」“”\"'·\s]", "", s)


def perspective(text):
    sc = {f: sum(text.count(m) for m in ms) for f, ms in MARK.items()}
    best = max(sc, key=lambda f: sc[f])
    return best if sc[best] > 0 else None


def stem_of(fn):
    s = STEM_TAIL_OLD.sub("", os.path.splitext(fn)[0])
    s = STEM_TAIL.sub("", s)
    return re.sub(r"(?i)(?<=[0-9v])e$", "", s)


def is_list_file(fn):
    """名单类文件（`_m`/`_u`，含无下划线写法）——**只接收视角、不当视角来源**（规则 3）。"""
    return bool(NO_VOICE.search(os.path.splitext(fn)[0]))


def family_of(fn):
    m = re.match(r"(?i)^([A-Za-z]{2,})", os.path.splitext(fn)[0])
    return m.group(1).lower() if m else ""


# ⚠️ 2026-10-13 补：`family_of` 要求**首字符是字母** ⇒ `7Pzra717v_i` 这类以数字开头的族名
#    （实测 7 个文件）永远进不了「战役族」。放宽版允许「数字+字母」前缀。
#    仅作**最后一层兜底**使用，故不改变任何既有归属。
FAMILY2 = re.compile(r"(?i)^(\d*[A-Za-z][A-Za-z]*)")


def family2_of(fn):
    m = FAMILY2.match(os.path.splitext(fn)[0])
    return m.group(1).lower() if m else ""


# ⭐ 第四层兜底：**`.scn` 的国别字段**（2026-10-12 用已知视角做字节相关性搜索定位）
#   `@22`（单字节/u16 LE 均可）＝该场景的国别索引，实测准确率 **77.7% / 80.3%**（样本 256）
#   值→阵营（经验表，仅取纯度 ≥70% 的取值，其余**不猜**）：
#     3→德 · 4→苏 · 10→盟 · 13→盟 · 18→罗(德)
#   ⚠️ 语义是"**场景的国别**"，未必等于"**谁的文本**"（罗场景里 @22=罗、@23=德 二者并列）
#   ⇒ 只当**兜底**，且来源标为 `scn国别(值N)`，供人工权衡。
SCN_SIDE = {3: "德", 4: "苏", 10: "盟", 13: "盟", 18: "罗"}


def scn_side(fn, scndir):
    stem = stem_of(fn)
    for cand in (stem + ".scn", "zz" + stem + ".scn"):
        p = os.path.join(scndir, cand)
        low = [x for x in os.listdir(scndir) if x.lower() == cand.lower()]
        if low:
            p = os.path.join(scndir, low[0])
        if os.path.isfile(p):
            try:
                b = open(p, "rb").read()
                if len(b) > 22:
                    return SCN_SIDE.get(b[22])
            except Exception:
                pass
    return None


def load_scenarios():
    """{文件名: (原文 cp1252, 成品 gbk)}。"""
    data = {}
    for fn in sorted(os.listdir(BK)):
        if not fn.lower().endswith(".txt"):
            continue
        gp = os.path.join(GAME, fn)
        if not os.path.isfile(gp):
            continue
        try:
            data[fn] = (io.open(os.path.join(BK, fn), encoding="cp1252", errors="replace").read(),
                        io.open(gp, encoding="gbk", errors="replace").read())
        except Exception:
            continue
    return data


def load_pin():
    """人工视角钉：{stem(小写): 阵营}。"""
    pin = {}
    pp = os.path.join(LAY, "side-override.tsv")
    if os.path.isfile(pp):
        for l in io.open(pp, encoding="utf-8"):
            if l.startswith("#") or l.startswith("stem\t"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 2 and c[0].strip():
                pin[c[0].strip().lower()] = c[1].strip()
    return pin


def _propagate(data, side, origin, sources, pin, scndir, tag):
    """用 `sources`（{文件名: 阵营}）建 stem/战役族计数，给仍未判定的文件补视角。

    `tag` 空串＝第一遍（来源＝口吻）；`(二遍)`＝第二遍（来源＝全部已判定的**非名单**文件）。
    返回本次新增判定的数量。
    """
    bs, bf = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    bf2 = collections.defaultdict(collections.Counter)
    for fn, f in sources.items():
        bs[stem_of(fn).lower()][f] += 1
        fa = family_of(fn)
        if fa:
            bf[fa][f] += 1
        fb = family2_of(fn)
        if fb:
            bf2[fb][f] += 1
    added = 0
    for fn in sorted(data):
        if fn in side:
            continue
        key = stem_of(fn).lower()
        if key in pin:                            # ⓪ 人工视角钉（最高优先）
            side[fn], origin[fn] = pin[key], "人工钉"
            added += 1
            continue
        c = bs.get(key)
        if c:
            side[fn], origin[fn] = c.most_common(1)[0][0], "同场景" + tag
            added += 1
            continue
        c = bf.get(family_of(fn))
        if c and sum(c.values()) >= 3 and c.most_common(1)[0][1] * 10 >= sum(c.values()) * 6:
            side[fn], origin[fn] = c.most_common(1)[0][0], "战役族" + tag
            added += 1
            continue
        # ④ 兜底：`.scn` 国别字段
        f2 = scn_side(fn, scndir)
        if f2:
            side[fn], origin[fn] = f2, "scn国别" + tag
            added += 1
            continue
        # ⑤ 兜底二（2026-10-13 补）：放宽族名的战役族多数票。放在**最后一层**，
        #    只在 ①~④ 全部落空时生效 ⇒ 不改变任何既有归属。
        c = bf2.get(family2_of(fn))
        if c and sum(c.values()) >= 3 and c.most_common(1)[0][1] * 10 >= sum(c.values()) * 6:
            side[fn], origin[fn] = c.most_common(1)[0][0], "战役族2" + tag
            added += 1
    return added


def resolve_sides(data, pin, scndir=None):
    """视角判定链：口吻 → 人工钉 → 同场景继承 → 战役族多数票 → `.scn` 国别兜底（**跑两遍**）。

    返回 (side, origin, voice)。**主流程与 `scn_player_probe.py` 共用同一套标签**，
    避免探针自己重写一份判定链而与审计器漂移。

    第二遍（2026-10-13 随 `stem_of` 修正一起加）：第一遍的"同场景"来源**只有口吻文件**；
    但本作大量展示位文件（`_bv`/`_l`/`_tv`/`_v`，以及无下划线的 `110bv`）**天生没有口吻**，
    必须先靠 `战役族`/`.scn 国别` 把同族的"主文件"判出来，再回头传播一次。
    ⚠️ 第二遍的来源**排除名单类**（`_m`/`_u`）—— 规则 3：名单只接收视角、不当来源。
    """
    scndir = scndir or GAME
    voice = {}
    for fn, (_e, zh) in data.items():
        if is_list_file(fn):
            continue
        f = perspective(zh)
        if f:
            voice[fn] = f
    side, origin = dict(voice), {fn: "口吻" for fn in voice}
    _propagate(data, side, origin, voice, pin, scndir, "")
    src2 = {fn: f for fn, f in side.items() if not is_list_file(fn)}
    _propagate(data, side, origin, src2, pin, scndir, "(二遍)")
    return side, origin, voice


def main():
    per_p, en2p, zh2p, nat_p, era_p = load_registry("faction-places.tsv", 0, 1, 3, 4)
    per_o, en2o, zh2o, nat_o, era_o = load_registry("faction-ops.tsv", 0, 1, 3, 4)
    print("历史称法登记：地名 %d 处 · 作战 %d 处" % (len(per_p), len(per_o)))
    if not os.path.isdir(BK) or not os.path.isdir(GAME):
        print("  ⚠️ 缺备份或游戏目录")
        return 0
    data = load_scenarios()
    pin = load_pin()
    side, origin, voice = resolve_sides(data, pin)
    # ⭐ 接线（第一步）：把「未判定」显式计数，不再静默跳过（详见 docs/44 §三·缺口 3）
    era_files = sum(1 for _fn, (_e, zh) in data.items() if era_of(zh))
    origin_n = collections.Counter(origin.values())
    undet_side = len(data) - len(side)
    ORDER = ("口吻", "人工钉", "同场景", "同场景(二遍)", "战役族", "战役族(二遍)",
             "scn国别", "scn国别(二遍)", "战役族2", "战役族2(二遍)")
    keys = [k for k in ORDER if origin_n.get(k)] + \
           [k for k in origin_n if k not in ORDER]
    print("扫描 %d 个场景文件 · 判定视角 %d 个（%.0f%%）· ⚠️ 未判定 %d 个（%.0f%%）"
          % (len(data), len(side), 100.0 * len(side) / max(1, len(data)),
             undet_side, 100.0 * undet_side / max(1, len(data))))
    print("   来源：" + " · ".join("%s %d" % (k, origin_n[k]) for k in keys))
    print("年代可判 %d / %d 个文件（%.0f%%）· ⚠️ 年代不可判 %d 个（年代检查对有年代的才生效）"
          % (era_files, len(data), 100.0 * era_files / max(1, len(data)), len(data) - era_files))

    hits = []
    for fn, (en, zh) in data.items():
        f = side.get(fn)
        era = era_of(zh)                      # ⭐ 年代维度：整篇取一次（78% 取不到 ⇒ 取不到就不查年代）
        if not f:
            continue
        for i, (a, b) in enumerate(zip(en.split("\n"), zh.split("\n")), 1):
            a, bl = a.strip(), b.strip()
            if not a and not bl:
                continue
            low = a.lower()
            nbl = norm(bl)
            for pid, table in per_p.items():
                ok = {x for x in table.get(f, "").split("|") if x}
                if not ok:
                    continue
                names = {x for v in table.values() for x in v.split("|") if x}
                used = sorted({v for v in names if norm(v) in nbl}, key=len, reverse=True)
                if not used:
                    continue
                # ⭐ 年代维度（试点）**必须先判**：通用 `ok` 是**各年代名的并集**，
                #    若先判并集就会把"用了别年代的名"当成合法而短路（实测踩过：1945-02 场景写「罗兹」未被报出）。
                eok = era_ok(era_p.get((pid, f)), era)
                if eok:
                    if norm(used[0]) in {norm(x) for x in eok}:
                        continue
                    hits.append(("年代错配", fn, i, pid, used[0], f, "|".join(sorted(eok)), origin.get(fn, "")))
                    continue
                # ⚠️ 中文名是**子串匹配**，会误命中更长的地名：
                #    「罗兹」命中「格罗兹尼」(Grozny) —— 实测造成 2 处假阳。
                #    规则：若命中名后面紧接**汉字**（说明它只是更长词的一部分），
                #    则要求英文行也出现该地的任一写法来佐证。
                nm = used[0]
                pos = bl.find(nm)
                tail = bl[pos + len(nm):pos + len(nm) + 1]
                if tail and "\u4e00" <= tail <= "\u9fff":
                    forms = {k for k, v in en2p.items() if v == pid}
                    if not any(f in a.lower() for f in forms) and norm(pid) not in a.lower():
                        continue
                if norm(used[0]) in {norm(x) for x in ok}:
                    continue
                hits.append(("地名", fn, i, pid, used[0], f, "|".join(sorted(ok)), origin.get(fn, "")))
            for pid, table in per_o.items():
                ok = {x for x in table.get(f, "").split("|") if x}
                if not ok:
                    continue
                names = {x for v in table.values() for x in v.split("|") if x}
                used = sorted({v for v in names if norm(v) in nbl}, key=len, reverse=True)
                # 识别写法：单 token 的专名直接用；**多 token 的须整串命中**
                # （否则 `Wacht am Rhein` 的 `rhein` 会撞上军舰名 `VK Rheine`——实测假阳）
                forms = set()
                for nm in nat_o.get(pid, ()):
                    toks = [t.lower() for t in re.split(r"[^\w]+", nm)
                            if re.fullmatch(r"[A-Za-z][A-Za-z'\-]{3,}", t) and t.lower() not in OPS_STOP]
                    if len(toks) >= 2:
                        forms.add(" ".join(toks))
                    else:
                        forms.update(toks)
                if not forms or not any(fm in low for fm in forms):
                    continue
                if used and norm(used[0]) in {norm(x) for x in ok}:
                    continue
                hits.append(("作战", fn, i, pid, used[0] if used else "（未用专名）",
                             f, "|".join(sorted(ok)), origin.get(fn, "")))
    print("\n⚠️ 与史料称法不符：%d 处" % len(hits))
    for kind, fn, i, pid, used, f, want, org in hits[:int(os.environ.get("SAMPLE", "20"))]:
        print("   [%s] %-16s 行%-4d %-16s 现用「%s」 视角=%s（%s） 史称「%s」"
              % (kind, fn, i, pid[:16], used[:14], f, org, want[:14]))
    os.makedirs(EVID, exist_ok=True)
    with io.open(os.path.join(EVID, "faction-place-audit.txt"), "w", encoding="utf-8", newline="\n") as w:
        w.write("# 地名/作战名 · 与史料称法不符（警告级）\n")
        w.write("类\t文件\t行号\tID\t现用\t视角\t史称\t视角来源\n")
        for h in hits:
            w.write("\t".join(str(x) for x in h) + "\n")
    # ⭐ 接线：给上层（layer_gate / faction_wire）一份机器可读摘要
    with io.open(os.path.join(EVID, "faction-audit-summary.txt"), "w", encoding="utf-8", newline="\n") as w:
        w.write("scanned=%d\n" % len(data))
        w.write("side_determined=%d\n" % len(side))
        w.write("side_undetermined=%d\n" % undet_side)
        w.write("side_pct=%.0f%%\n" % (100.0 * len(side) / max(1, len(data))))
        for k in keys:
            w.write("origin_%s=%d\n" % (k, origin_n.get(k, 0)))
        w.write("era_determined=%d\n" % era_files)
        w.write("era_undetermined=%d\n" % (len(data) - era_files))
        w.write("era_pct=%.0f%%\n" % (100.0 * era_files / max(1, len(data))))
        w.write("hits=%d\n" % len(hits))
    print("\n报告 → glossary/evidence/faction-place-audit.txt")
    print("摘要 → glossary/evidence/faction-audit-summary.txt（供 layer_gate/faction_wire 读取）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
