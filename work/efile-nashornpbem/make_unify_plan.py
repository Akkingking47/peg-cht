# -*- coding: utf-8 -*-
"""生成 OLGWW2 .xscn 组0「全量统一」计划。

输入: out/bridge-mismatch.tsv  (file, idx, orig_en, xscn_now, txt_want)
输出: out/unify-plan.tsv       (file, idx, action, xscn_now, new_value, reason)
      action = CHANGE | KEEP

KEEP 规则（保留 .xscn）：
  A. 括号别名政策（项目既定口径）：.xscn 含圆括号别名 且 .txt 完全没有别名括号，且
     - 括号内容不是「类别标记」（港口/森林/FOREST/PORT…）；
     - 括号内容不是纯数字/罗马数字/海拔测量（527 m、VI.）；
     - 括号外文本不含连续 >=3 个拉丁字母（即主名已汉化）。
     例：埃斯科河 (斯海尔德河) / 根特 (Gand) / 卡普赖克 (Caprijcke)
     （若 .txt 也有括号 ⇒ 只差括号全/半角或别名写法 ⇒ 采 .txt，不保留）
  B. 手工反例清单：.xscn 明显优于 .txt（阿尔贝特运河 / 砥平里 / 海参崴 / 萨尔姆河…）
  C. .txt 自身损坏（如 哈拉哈河（哈拉哈河）自重复）⇒ 保留 .xscn
  D. .txt 侧根本没译（新值不含汉字而 .xscn 有）⇒ 保留 .xscn，避免「中文换英文」倒退
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

CLS_ZH = ["港口", "机场", "火车站", "森林", "丘陵", "山地", "崎岖", "陡崖", "沙地", "河流",
          "溪流", "沼泽", "要塞", "工事", "筑垒", "起伏地", "海洋", "沙漠", "城市", "村庄",
          "范围之外", "建设中", "铁路", "车站", "原住民村落", "农田", "湖泊", "平原"]
CLS_EN = ["FOREST", "PORT", "RIVER", "HILL", "MOUNTAIN", "ROUGH", "SWAMP", "STREAM",
          "SAND", "ESCARPMENT", "FORTIFICATION", "OCEAN", "LAKE", "FORT", "AIRFIELD",
          "CITY", "TOWN", "VILLAGE", "RAILROAD", "CANAL", "SEA", "ROAD", "OUT"]
PAREN = re.compile(r"[（(]([^（()）]*)[)）]")
LAT = re.compile(r"[A-Za-z]{3,}")

# B. 手工反例：按「英文原名」保留 .xscn
MANUAL = {
    "Canal Albert": "阿尔贝特运河为标准名（.txt 作「阿尔贝运河」）",
    "Chip'yong-ni": "砥平里为朝鲜战争标准地名（.txt 作「稷洞里」）",
    "Vladivostok": "海参崴为中国传统名（.txt 作「符拉迪沃斯托克」）",
    "Salm River": "萨尔姆河为 Salm 完整音译（.txt 作「萨姆河」）",
}


def is_class_marker(s):
    s = s.strip()
    if s in CLS_ZH:
        return True
    u = s.upper()
    return any(u == m or u.startswith(m + " ") or u.startswith(m + ".") for m in CLS_EN)


def outside_paren(s):
    return PAREN.sub("", s)


def txt_broken(w):
    """检测 .txt 自损：形如 A（A）/ A（A 或 A A 末尾重复"""
    for pre, body in [("（", "）"), ("(", ")")]:
        if pre in w:
            a, b = w.split(pre, 1)
            b = b.split(body, 1)[0] if body in b else b
            if a.strip() and a.strip() == b.strip():
                return True
    return False


def is_alias(s):
    """括号内容是否为「真别名」：非空、非类别标记、非纯数字/罗马数字/海拔测量。"""
    s = s.strip()
    if not s:
        return False
    if is_class_marker(s):
        return False
    if re.match(r"^\d+$", s):
        return False
    if re.match(r"^\d+\s*m$", s, re.I):
        return False
    if re.match(r"^[IVXLC]+\.?$", s):
        return False
    return True


def manual_hit(se):
    """手工反例按英文原名匹配：允许原名带括号后缀（如 `Canal Albert (I CA)`）。"""
    base = se.split("(")[0].split("[")[0].strip()
    for k in MANUAL:
        if se == k or base == k or se.startswith(k + " "):
            return k
    return None


def has_cjk(s):
    return any("\u4e00" <= c <= "\u9fff" for c in s)


def keep_reason(sc, want, se):
    m = manual_hit(se)
    if m:
        return "B 手工反例：" + MANUAL[m]
    if txt_broken(want):
        return "C .txt 自损（自重复）：%s" % want
    if has_cjk(sc) and not has_cjk(want):
        return "D .txt 侧未译（新值无汉字）：%s" % want
    ms = PAREN.findall(sc)
    if ms and not PAREN.search(want):
        outside = outside_paren(sc)
        if not LAT.search(outside):
            non_cls = [m for m in ms if is_alias(m)]
            if non_cls and len(non_cls) == len(ms):
                return "A 括号别名（.txt 无别名，保留）：%s" % ("/".join(non_cls))
    return None


def main():
    rows = [l.split("\t") for l in io.open(os.path.join(HERE, "out", "bridge-mismatch.tsv"),
                                            encoding="utf-8").read().splitlines() if l.strip()]
    plan = []
    stats = {}
    for n, i, se, sc, want in rows:
        i = int(i)
        r = keep_reason(sc, want, se)
        if r:
            plan.append((n, i, "KEEP", sc, want, r))
            k = r.split(" ")[0]
            stats[k] = stats.get(k, 0) + 1
        else:
            plan.append((n, i, "CHANGE", sc, want, ""))
    ch = [p for p in plan if p[2] == "CHANGE"]
    kp = [p for p in plan if p[2] == "KEEP"]
    print("计划: CHANGE %d 处 / %d 文件 | KEEP %d 处 / %d 文件"
          % (len(ch), len(set(p[0] for p in ch)), len(kp), len(set(p[0] for p in kp))))
    print("KEEP 规则分布:", stats)
    print()
    print("=" * 100)
    print("KEEP 明细（保留 .xscn 现值）")
    print("=" * 100)
    print("%-17s %-4s %-26s %-22s %s" % ("file", "i", "xscn(保留)", "txt(不采)", "reason"))
    for n, i, a, sc, want, r in kp:
        print("%-17s %-4s %-26s %-22s %s" % (n, i, sc[:26], want[:22], r[:52]))
    print()
    # KEEP 里若「英文原名有拉丁」但被规则 A 放过的，列出来复核
    print("=" * 100)
    print("待复核：KEEP 但 .xscn 括号外含拉丁字母（应为 0）")
    print("=" * 100)
    bad = [p for p in kp if LAT.search(outside_paren(p[3]))]
    for p in bad:
        print("  %-17s %-4s %s" % (p[0], p[1], p[3]))
    if not bad:
        print("  （无）")

    with io.open(os.path.join(HERE, "out", "unify-plan.tsv"), "w",
                 encoding="utf-8", newline="\n") as f:
        for n, i, a, sc, want, r in plan:
            f.write("%s\t%d\t%s\t%s\t%s\t%s\n" % (n, i, a, sc, want, r))
    print()
    print("已写 out/unify-plan.tsv")


if __name__ == "__main__":
    main()
