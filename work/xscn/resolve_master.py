# -*- coding: utf-8 -*-
r"""总词库冲突裁定器 —— 把 master-conflicts.tsv 的 1436 条多译法冲突归一为单一权威译法。

用法: python resolve_master.py

裁定优先级（从高到低）:
  R0 人工 override        master-overrides.tsv（我人工裁定的高置信语义/地形订正）
  R1 CEM 规则            任一候选含「摩洛哥军」则强优先（[CEM]=摩洛哥军已 GCE 实证 70 条）
  R2 纯标点/您您 差异     归一化后唯一 ⇒ 按「全角引号 + 您 + 计数」择优
  R3 多数票              某个候选计数严格最高 ⇒ 采用
  R4 平票打分            ①罗马数字方括号保留 ②无日式「师团/联队」③汉字更多(更完整展开)
                        ④标点风格(短键半角/长句全角) ⑤您(散文) ⑥计数 ⑦字典序

产出:
  master-resolve.tsv     src \t dst \t rule（覆盖全部冲突，src 唯一）
  master-resolve-stat.txt
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
CONF = os.path.join(HERE, "master-conflicts.tsv")
OVR = os.path.join(HERE, "master-overrides.tsv")

# 罗马数字（含 [N]=纳瓦拉 这类单字母保留，但 N/V 也可能是缩写；仅作为弱偏好）
ROMAN = re.compile(r"\[[IVXLCDM]+\]")
# 日式编制词（本项目口径用 师/团/军，不用 师团/联队/大队）
IJA = re.compile(r"师团|联队|战车队")
CJK = re.compile(r"[\u4e00-\u9fff]")
FULL_QUOTE = re.compile(r"[“”「」]")
FULL_PUNCT = re.compile(r"[，。！？：；（）【】]")


def norm(s):
    """比较用归一：您→你、全角→半角、引号统一。用于判定「仅标点/敬称差异」的 cosmetic 冲突。"""
    s = s.replace("您", "你")
    for a, b in [("“", '"'), ("”", '"'), ("‘", "'"), ("’", "'"), ("「", '"'), ("」", '"'),
                 ("，", ","), ("。", "."), ("！", "!"), ("？", "?"), ("：", ":"), ("；", ";"),
                 ("（", "("), ("）", ")"), ("【", "["), ("】", "]"), ("…", "...")]:
        s = s.replace(a, b)
    return s


def score(d, src):
    s = 0
    if ROMAN.search(d) and not re.search(r"\[第\d+", d):
        s += 100          # 罗马数字方括号保留
    if not IJA.search(d):
        s += 80           # 不用日式 师团/联队
    s += len(CJK.findall(d))      # 汉字越多=展开越完整
    if len(src) > 40:     # 长句=散文 ⇒ 全角标点、敬称「您」
        s += (20 if FULL_PUNCT.search(d) else 0)
        s += (10 if "您" in d else 0)
    else:                 # 短键=.xscn 层 ⇒ 半角标点
        s += (20 if not FULL_PUNCT.search(d) else 0)
    if FULL_QUOTE.search(d):
        s += 5            # 全角引号（中文排版）
    return s


def main():
    overrides = {}
    if os.path.exists(OVR):
        with io.open(OVR, encoding="utf-8-sig", newline="") as f:
            for ln in f.read().replace("\r\n", "\n").split("\n"):
                c = ln.split("\t")
                if len(c) >= 2 and c[0].strip() and not c[0].startswith("#"):
                    overrides[c[0].strip()] = c[1].strip()

    rows = []
    with io.open(CONF, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) < 2:
                continue
            src = c[0]
            variants = []
            for part in c[1].split(" | "):
                m = re.match(r"^(.*)\((\d+)\)$", part)
                if m:
                    variants.append((m.group(1), int(m.group(2))))
            rows.append((src, variants))

    rule_cnt = {}
    resolved = {}
    for src, variants in rows:
        if not variants:
            continue
        # R0
        if src in overrides:
            resolved[src] = (overrides[src], "R0-override")
            rule_cnt["R0-override"] = rule_cnt.get("R0-override", 0) + 1
            continue
        # R1 CEM
        moka = [v for v in variants if "摩洛哥军" in v[0]]
        bad = [v for v in variants if re.search(r"休达|东方集团军群|\[CEM\]", v[0])]
        if moka and bad:
            resolved[src] = (moka[0][0], "R1-CEM")
            rule_cnt["R1-CEM"] = rule_cnt.get("R1-CEM", 0) + 1
            continue
        # R2 cosmetic
        if len({norm(v[0]) for v in variants}) == 1:
            # 全角引号 + 您 + 计数 择优
            best = max(variants, key=lambda v: (
                FULL_QUOTE.search(v[0]) is not None,
                "您" in v[0],
                v[1],
            ))
            resolved[src] = (best[0], "R2-cosmetic")
            rule_cnt["R2-cosmetic"] = rule_cnt.get("R2-cosmetic", 0) + 1
            continue
        # R3 majority
        cnt = sorted([n for _, n in variants], reverse=True)
        if len(cnt) >= 2 and cnt[0] > cnt[1]:
            best = max(variants, key=lambda v: v[1])
            resolved[src] = (best[0], "R3-majority")
            rule_cnt["R3-majority"] = rule_cnt.get("R3-majority", 0) + 1
            continue
        # R4 tie-break
        best = max(variants, key=lambda v: (score(v[0], src), v[1], -ord(v[0][0]) if v[0] else 0))
        resolved[src] = (best[0], "R4-tiebreak")
        rule_cnt["R4-tiebreak"] = rule_cnt.get("R4-tiebreak", 0) + 1

    with io.open(os.path.join(HERE, "master-resolve.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tdst\trule\n")
        for src in sorted(resolved):
            dst, r = resolved[src]
            f.write("%s\t%s\t%s\n" % (src, dst, r))
    with io.open(os.path.join(HERE, "master-resolve-stat.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("total\t%d\n" % len(resolved))
        for r in sorted(rule_cnt, key=lambda k: -rule_cnt[k]):
            f.write("%s\t%d\n" % (r, rule_cnt[r]))

    print("冲突裁定完成: 共 %d 条" % len(resolved))
    for r in sorted(rule_cnt, key=lambda k: -rule_cnt[k]):
        print("  %-14s %5d" % (r, rule_cnt[r]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
