# -*- coding: utf-8 -*-
"""OpenGeneral 根级汉化生成器：<efile>\\TEXT-ZH\\ 五件套

  equip.txt / names.txt / NamesEx.txt / nations.txt / strings_efile.txt

纪律（沿用 docs\\25 B1-EFILE_AG 的根级约定）：
  · 只写 <efile>\\TEXT-ZH\\，原文零改动
  · 出稿 GBK(936) / 无 BOM / CRLF / 行数与原文逐行对齐
  · **未命中项必须报出**，不允许静默漏译
  · 默认 dry-run，--apply 才写盘
  · 中文侧装不下的变音符 ⇒ ASCII 折写（docs\\24）

译文来源（优先级从低到高）：
  1) work\\efile_gus\\root-prematch-map.tsv   —— 程序/词库已定（1559 条）
  2) work\\efile_gus\\batch\\*.out.tsv        —— LLM 批次产出（覆盖 miss）
  3) SE 硬表（strings_efile.txt）与 nations 词表（PG2 12 efile 对拍 + 手工补）

覆盖关系：
  · strings_efile.txt 5 个 efile 全同（md5 FD0C9D57）⇒ 生成一份写 5 处
  · nations.txt GUS 系 4 个同（741AFAF9）、ALBERICH 独立（D0AE8593）
  · equip.txt GUS 系 4 个同（1636C24B）、ALBERICH 独立（1FA68216）
  · names.txt / NamesEx.txt 亦各按原文逐行映射（GUS 与 ALBERICH 92% 同）

用法：
    python make_og_root.py --report    # 只看表装载情况与未覆盖统计
    python make_og_root.py             # 打印计划（逐文件 diff 摘要）
    python make_og_root.py --apply     # 写盘
"""
import glob
import hashlib
import os
import sys
import unicodedata

OG = os.environ.get("OG_ROOT") or r"D:\OpenGeneral"
PG2 = os.environ.get("PG2_ROOT") or r"D:\OpenPG2"
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, ".."))

EFILES = ["EFILE_GUS", "EFILE_GUS_Zx", "EFILE_GUS_PeG", "EFILE_GUS_Wx", "EFILE_ALBERICH"]
# 五件套的生成顺序（nations / strings_efile 走专用表）
PLAIN_FILES = ["equip.txt", "names.txt", "NamesEx.txt"]
SPECIAL_FILES = ["nations.txt", "strings_efile.txt"]

# ---------------------------------------------------------------- 1) strings_efile.txt
# 键 = 原文整行（含行内注释），值 = 译文整行。对齐 strings-zh.txt + PG2 已收官 efile。
SE = {
    # [terrain] 20
    "CLEAR": "开阔地", "TOWN": "城镇", "AIRFIELD": "机场", "FOREST": "森林",
    "BOCCAGE": "树篱地", "HILL": "丘陵", "MOUNTAIN": "山地", "SAND": "沙漠",
    "SWAMP": "沼泽", "OCEAN": "海洋", "RIVER": "河流", "FORTIFICATION": "要塞",
    "PORT": "港口", "STREAM": "溪流", "ESCARPMENT": "断崖", "IMPASSABLE": "不可通行",
    "ROUGH": "崎岖地", "SNOW  * renamed CUSTOM terrain": "雪地  * renamed CUSTOM terrain",
    "ROADS": "公路", "RAILS": "铁路",
    # [movement] 14 —— 与 strings-zh.txt 的 [movement] 逐项对齐
    "Tracked": "履带", "Half Tracked": "半履带", "Wheeled": "轮式", "Leg": "徒步",
    "Towed": "牵引", "Air": "空中", "Naval": "海上", "Riverine": "内河",
    "All Terrain": "全地形", "Amphibious(Wheeled)": "两栖(轮式)", "Coastal": "近海",
    "Mountain (Leg)": "山地(徒步)", "Train": "铁路", "Helicopter": "直升机",
    # [movement2] 1
    "Amphibious(Tracked)": "两栖(履带)",
    # [classes] 24
    "None": "无", "Infantry": "步兵", "Tank": "坦克", "Recon": "侦察",
    "Anti-tank": "AT", "Dual-purpose": "两用",
    "Fortification": "要塞",          # [classes] 首字母大写，与 [terrain] 的 FORTIFICATION 是两个键
    "Ground Transport": "地面运输", "Rail Transport": "铁路运输", "Artillery": "炮兵",
    "Air Defense": "防空", "Fighter": "战斗机", "Tactical Bomber": "战术轰炸机",
    "Level Bomber": "重型轰炸机", "Air Transport": "运输机", "Helo Transport": "直升机运输",
    "Submarine": "潜艇", "Destroyer": "驱逐舰", "Battleship": "BB",
    "Carrier": "航空母舰", "Naval Transport": "海上运输", "Cruiser": "巡洋舰",
    "Auxiliary Ship": "辅助舰", "Riverine Ship": "内河舰",
    # [requisition] 22
    "Switch Ground+Air / Naval units menu": "切换 陆空/海军 单位菜单",
    "Select Air defense": "选择防空", "Select Dual-purpose": "选择两用",
    "Select Fortification": "选择要塞", "Select Anti Tank": "选择 AT",
    "Select Artillery": "选择炮兵", "Select Infantry": "选择步兵",
    "Select Recon": "选择侦察", "Select Tanks": "选择坦克",
    "Select Fighters": "选择战斗机", "Select Tactical Bombers": "选择战术轰炸机",
    "Select Level Bombers": "选择重型轰炸机", "Select Submarine": "选择潜艇",
    "Select Destroyer": "选择驱逐舰", "Select Battleship": "选择 BB",
    "Select Carrier": "选择航空母舰", "Select Cruiser": "选择巡洋舰",
    "Select Auxiliary Ship": "选择辅助舰", "Select Riverine Ship": "选择内河舰",
    "Name unit": "命名单位", "Reassign Unit": "重新分配单位", "Exit": "退出",
}

# ------------------------------------------- 2) nations.txt 手工补（PG2 对拍未命中项）
NATIONS_EXTRA = {
    "Armia Krajowa": "波兰家乡军", "Republic of Poland": "波兰共和国",
    "LWP": "波兰人民军", "US Marines": "美国海军陆战队", "Terrorists": "恐怖分子",
    "Austro Hungary": "奥匈帝国", "Bosnia": "波斯尼亚", "Bielarus": "白俄罗斯",
    "Iran": "伊朗", "Afghanistan": "阿富汗", "Kosovo": "科索沃", "Kuwait": "科威特",
    "Libya": "利比亚", "DDR": "东德", "FRG": "西德", "Syria": "叙利亚",
    "Vietnam": "越南", "South Vietnam": "南越", "Chechnya": "车臣",
    "Malaysia": "马来西亚", "Singapore": "新加坡", "Sri Lanka": "斯里兰卡",
    "United Nations": "联合国", "Warsaw Pact": "华约", "NATO": "北约",
    "European Union": "欧盟", "Euskadi": "巴斯克", "Slovenia": "斯洛文尼亚",
    "Kazakhstan": "哈萨克斯坦", "Novorossiya": "新俄罗斯", "Czechia": "捷克",
}

# ---------------------------------------------------------------- 3) 变音符折写
_MANUAL = {"ł": "l", "Ł": "L", "ø": "o", "Ø": "O", "đ": "d", "Đ": "D",
           "ı": "i", "İ": "I", "æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE",
           "ß": "ss", "þ": "th", "ð": "d", "Ð": "D"}


# ------------------------------------------------- 4) 强制保留原文的「测试者署名块」
# names.txt / NamesEx.txt 头部 31 行是 efile 作者的测试者网名（Gustlik 即 GusOpen 作者），
# 属署名性质而非人名。PG2 已交付的 efile 一律原样保留这 31 行。
# 下列 5 个会被通用人名词库误命中（Radar→雷达、Pepe→佩佩…），故强制保留，
# 否则文件里会出现「26 个英文 + 5 个中文」的自相矛盾混排。
KEEP_NAMES = {
    "Gustlik", "Zsamot", "Greg", "Czata", "Kowdar", "Criss", "Hansen", "Rozprza",
    "Majerek", "Depet", "Kris", "Marder", "Dolas", "Pelebudka", "Grisha", "Saygon",
    "Scheisskopf", "Radar", "Roberto", "Triste", "Mirkus", "Pablo", "Mapet", "Exiter",
    "Janus", "Szarik", "Pepe", "Giees", "Daban", "Rommel", "Darko",
}
KEEP_FILES = ("names.txt", "NamesEx.txt")

# 反向个例：同一串在 equip.txt 里是型号（保留原文），在 names 两份里却是姓氏（该音译）。
# 这是共用一份 src→dst 表的固有冲突；实测两 efile 全部冲突**仅此 2 个**（交集 6,259∩2,801）。
NAME_OVERRIDE = {"Archer": "阿彻", "Kara": "卡拉"}

# `D:\OpenPG2` 已交付件实证：绰号**著名的意译、冷门或有歧义的保留原文**
# （`Black Hawk→黑鹰`、`F-14 Tomcat→雄猫`、`MIM-104 Patriot→爱国者`、`CH-47 Chinook→支奴干`、
#   `FIM-92 Stinger→毒刺`、`AH-64A Apache→阿帕奇`；而 `M7 Priest`/`F4F-3 Wildcat`/`M1 Abrams`/
#   `MGR-1 Honest John` 一律保留）。批次作者自行判断时会有出入，这里只对**已决定保留**的
# 装备名做最后一层归一，把 PG2 已实证意译的 6 个绰号补上（实测只影响 8 行）。
NICK = [("Black Hawk", "黑鹰"), ("Patriot", "爱国者"), ("Chinook", "支奴干"),
        ("Stinger", "毒刺"), ("Tomcat", "雄猫"), ("Apache", "阿帕奇")]


def _gbk_ok(ch):
    try:
        ch.encode("gbk")
        return True
    except UnicodeEncodeError:
        return False


# 标点：GBK 装不下且 NFKD 拆不掉的（实测 GUS equip.txt 里有 2 个 U+201E „ ）
_PUNCT = {"„": '"', "“": '"', "”": '"', "‟": '"', "‚": "'", "‘": "'", "’": "'",
          "′": "'", "″": '"', "–": "-", "—": "-", "―": "-", "‒": "-", "‐": "-",
          "‑": "-", "…": "...", "×": "x", "÷": "/", "№": "No.", "§": "S",
          "¶": "P", "†": "+", "‡": "++", "€": "EUR", "£": "GBP", "¥": "JPY",
          "‹": "<", "›": ">", "«": "<<", "»": ">>", "\u00a0": " ", "\u200b": "",
          "\ufeff": ""}


def _fold_ch(ch):
    """折成 ASCII：先查手册，再查标点表，再走 NFKD 去组合符，最后兜底 '?'。"""
    if ch in _MANUAL:
        return _MANUAL[ch]
    if ch in _PUNCT:
        return _PUNCT[ch]
    d = unicodedata.normalize("NFKD", ch)
    a = "".join(c for c in d if not unicodedata.combining(c))
    return a if a and a.isascii() else "?"


def fold_gbk(s):
    """把 GBK 装不下的字符折成 ASCII。返回 (新串, 折写次数)。"""
    if all(_gbk_ok(c) for c in s):
        return s, 0
    out, n = [], 0
    for c in s:
        if _gbk_ok(c):
            out.append(c)
        else:
            out.append(_fold_ch(c))
            n += 1
    return "".join(out), n


# ---------------------------------------------------------------- 读写
def read_lines(path, enc="cp1250"):
    raw = open(path, "rb").read()
    if raw[:3] == b"\xef\xbb\xbf":
        raw = raw[3:]
    if enc == "auto":
        for e in ("utf-8", "cp1250", "cp1252"):
            try:
                raw.decode(e)
                enc = e
                break
            except UnicodeDecodeError:
                enc = "cp1250"
    return raw.decode(enc, "replace").replace("\r\n", "\n").replace("\r", "\n").split("\n")


def write_gbk(path, lines):
    """GBK / 无 BOM / CRLF。先写 .tmp 回读校验，再落盘（硬纪律 §2）。"""
    body = "\r\n".join(lines).encode("gbk")
    assert not body.startswith(b"\xef\xbb\xbf"), "BOM 混入"
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(body)
    assert open(tmp, "rb").read().decode("gbk").replace("\r\n", "\n") == "\n".join(lines), "回读不一致"
    os.replace(tmp, path)


def load_pairs():
    """按优先级叠加：prematch-map 先，batch\\*.out.tsv 后（miss 专属，不重叠）。"""
    tr, src_of = {}, {}
    p = os.path.join(WORK, "efile_gus", "root-prematch-map.tsv")
    n1 = 0
    if os.path.isfile(p):
        for i, l in enumerate(open(p, encoding="utf-8")):
            if i == 0:
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 2:
                tr[c[0]] = c[1]
                src_of[c[0]] = "prematch"
                n1 += 1
    n2 = 0
    for p in sorted(glob.glob(os.path.join(WORK, "efile_gus", "batch", "*.out.tsv"))):
        for i, l in enumerate(open(p, encoding="utf-8")):
            if i == 0:
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 2 and c[0] not in src_of:
                tr[c[0]] = c[1]
                src_of[c[0]] = os.path.basename(p)
                n2 += 1
    return tr, src_of, n1, n2


def build_nations_map():
    m = {}
    for d in sorted(os.listdir(PG2)):
        if not d.upper().startswith("EFILE_"):
            continue
        a, b = os.path.join(PG2, d, "nations.txt"), os.path.join(PG2, d, "TEXT-ZH", "nations.txt")
        if not (os.path.isfile(a) and os.path.isfile(b)):
            continue
        A, B = read_lines(a, "auto"), read_lines(b, "gbk")
        if len(A) != len(B):
            print("  ! 行数不等，跳过 %s (%d vs %d)" % (d, len(A), len(B)))
            continue
        for x, y in zip(A, B):
            xs, ys = x.strip(), y.strip()
            if xs and not xs.startswith("*") and xs != ys:
                m.setdefault(xs, ys)
    m.update(NATIONS_EXTRA)
    return m


def main():
    apply_ = "--apply" in sys.argv
    report_ = "--report" in sys.argv
    tr, src_of, n1, n2 = load_pairs()
    nmap = build_nations_map()
    print("[%s]" % OG)
    print("  译文表：prematch %d 条 + batch %d 条 = %d 条" % (n1, n2, len(tr)))
    print("  nations 词表 %d 条（含手工补 %d）" % (len(nmap), len(NATIONS_EXTRA)))
    print("  strings_efile 硬表 %d 条" % len(SE))
    print()

    plans = []       # (efile, fn, new_lines, [(i,src,dst)], stats)
    seen_plain = {}
    unmatched = {}

    for fn in PLAIN_FILES + SPECIAL_FILES:
        for ef in EFILES:
            src = os.path.join(OG, ef, fn)
            if not os.path.isfile(src):
                continue
            # 内容相同的源文件只生成一次，复制到各 efile
            h = hashlib.md5(open(src, "rb").read()).hexdigest()[:8].upper()
            if fn == "strings_efile.txt" and h in seen_plain:
                plans.append((ef, fn, seen_plain[h][0], seen_plain[h][1], seen_plain[h][2]))
                continue
            L = read_lines(src, "auto")
            out, diff, miss, nfold = [], [], [], 0
            for i, ln in enumerate(L):
                s = ln.strip()
                keep = ((not s) or s.startswith("*") or s.startswith("[")
                        or (fn in KEEP_FILES and s in KEEP_NAMES))
                t = None
                if not keep:
                    if fn in KEEP_FILES and s in NAME_OVERRIDE:
                        t = NAME_OVERRIDE[s]
                    else:
                        t = SE.get(s) if fn == "strings_efile.txt" else (
                            nmap.get(s) if fn == "nations.txt" else tr.get(s))
                if t is not None and t != ln:
                    v = t
                    diff.append((i, ln, v))
                else:
                    v = ln
                    if not keep and fn in PLAIN_FILES:
                        miss.append(s)
                if fn == "equip.txt" and v == ln:
                    nv = ln
                    for _a, _b in NICK:
                        nv = nv.replace(_a, _b)
                    if nv != ln:
                        v = nv
                        diff.append((i, ln, v))
                        if miss and miss[-1] == s:
                            miss.pop()
                v2, nf = fold_gbk(v)
                nfold += nf
                out.append(v2)
            st = (len(L) - nfold, len(diff), len(miss), nfold)
            if fn == "strings_efile.txt":
                seen_plain[h] = (out, diff, st)
            plans.append((ef, fn, out, diff, st))
            unmatched.setdefault(fn, set()).update(miss)

    if report_:
        for fn, s in unmatched.items():
            print("  %-18s 未覆盖(保留原文) 唯一 %d" % (fn, len(s)))
        return

    print("=" * 86)
    bad = 0
    for ef, fn, out, diff, st in plans:
        src = os.path.join(OG, ef, fn)
        n_src = len(read_lines(src, "auto"))
        n_out = len(out)
        ok = n_src == n_out and all(_gbk_ok(c) for ln in out for c in ln)
        if not ok:
            bad += 1
        print("%s %-13s %-16s 行 %d->%d  译文 %5d  保留 %5d  折写 %4d  %s"
              % ("OK " if ok else "!! ", ef, fn, n_src, n_out, st[1], st[2], st[3],
                 "" if st[3] == 0 else "← 折写"))
    print()
    print("行数/编码异常 %d" % bad)
    for fn in PLAIN_FILES:
        if unmatched.get(fn):
            print("  %-18s 保留原文的唯一串 %d 条" % (fn, len(unmatched[fn])))

    if not apply_:
        print()
        print("dry-run：未写盘。加 --apply 落盘。")
        return
    n = 0
    for ef, fn, out, diff, st in plans:
        d = os.path.join(OG, ef, "TEXT-ZH")
        os.makedirs(d, exist_ok=True)
        write_gbk(os.path.join(d, fn), out)
        n += 1
    print()
    print("已写入 %d 个文件。" % n)


if __name__ == "__main__":
    main()
