# -*- coding: utf-8 -*-
"""把定名（naming.tsv）铺到 PeG-WW2 侧：pegww2 研究表 + OLGWW2 efile 中文侧。

落点（只动「中文侧」；英文原文与死镜像一律不动）：
  ① pegww2\\research\\ww2-scn-map.tsv              列 ≥1（en 列不动）
  ② pegww2\\research\\_scn-fill-prose-r13-01.tsv   列 ≥1
  ③ EFILE_OLGWW2\\SCENARIO\\*.txt ＋ TEXT-ZH\\SCENARIO\\*.txt      逐行
  ④ EFILE_OLGWW2\\SCENARIO\\*.xscn                 字节级（引擎只读本目录）
  ⑤ EFILE_OLGWW2\\{equip,names,nations,strings_efile}.txt ＋ TEXT-ZH 同名   逐行

判定「中文侧」＝文本里存在**至少一个属于词库汉字的汉字**（ZH_SET，取自 glossary\\standard-glossary.tsv 的 zh 列）。
  （理由：① 真中文才用词库那套常用字；② cp1252 重音字母被 GBK 误解出的汉字是孤立怪字，
   如 Caballería→Caballer韆、Bailén→Bail閚，这些字不在词库字集里 ⇒ 不会误判为中文侧；
   ③ 若只要求「连续 ≥2 汉字」，像 `第52营/第1 African D`、`第290团/Saharian Grouping`
   这种汉字被数字隔开的单元格会被漏判（实测漏 9 行），故改为单字判定。
   命中而**无连续汉字**的行在明细里标 `LOOSE-`，供人工复核。）
保护：「译名(原文)」双语注（(old) / （old））跳过；多趟应用（≤5 趟）以覆盖两轮连锁规则
  （如 Mehal-la→梅哈利拉 后还需 塔博尔 梅哈利拉→梅哈利拉塔博尔）。
⚠️ TEXT-ZH\\SCENARIO\\*.xscn 是英文原文死镜像（引擎不读；work\\efile-nashornpbem\\scan_xscn_latin.py:42）⇒ 不动。
备份 backup\\before-naming-peg\\；默认 dry-run，--apply 写盘；明细写 work\\_sync-audit\\naming-peg-plan.txt。
"""
import io
import os
import re
import sys

sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\efile-nashornpbem")
from apply_residual import parse  # noqa: E402

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\OpenPG2"
EFILE = os.path.join(GAME, "EFILE_OLGWW2")
NAMING = os.path.join(WS, "work", "_sync-audit", "naming.tsv")
PLAN = os.path.join(WS, "work", "_sync-audit", "naming-peg-plan.txt")
BACKUP = os.path.join(WS, "backup", "before-naming-peg")
GLOSSARY_T = os.path.join(WS, "glossary", "standard-glossary.tsv")

TSV_TARGETS = [
    os.path.join(WS, "pegww2", "research", "ww2-scn-map.tsv"),
    os.path.join(WS, "pegww2", "research", "_scn-fill-prose-r13-01.tsv"),
]
ROOT_NAMES = ("equip.txt", "names.txt", "nations.txt", "strings_efile.txt", "fronts.txt")

CJK_RUN = re.compile(u"[\u4e00-\u9fff]{2,}")


def load_zh_set():
    """词库 zh 列用到的全部汉字 —— 作为「这段文本是中文侧」的判据。"""
    s = set()
    L = io.open(GLOSSARY_T, encoding="utf-8-sig").read().replace(
        "\r\n", "\n").split("\n")
    for i, ln in enumerate(L):
        if i == 0 or not ln.strip():
            continue
        c = ln.split("\t")
        if len(c) > 1:
            s.update(ch for ch in c[1] if u"\u4e00" <= ch <= u"\u9fff")
    return s


ZH_SET = load_zh_set()
LOOSE = []        # 汉字被数字/字母隔开（无连续汉字）的命中，需人工复核
DET = []          # 明细行
RULE_HITS = {}    # (old,new,key) -> 次数
GLOSS = []        # 被双语注保护跳过


def is_zh(s):
    for ch in s:
        if ch in ZH_SET:
            return True
    return False


def load_rules():
    rows = []
    L = io.open(NAMING, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")
    for i, ln in enumerate(L):
        if i == 0 or not ln.strip() or ln.startswith("#"):
            continue
        c = ln.split("\t")
        if len(c) < 3:
            continue
        rows.append((c[0], c[1], c[2], c[3] if len(c) > 3 else ""))
    rows.sort(key=lambda r: -len(r[1]))
    return rows


RULES = load_rules()


def fix_text(s, where):
    """多趟应用规则；返回 (新文本, 命中列表)"""
    hits = []
    for _pass in range(5):
        changed = False
        for key, old, new, why in RULES:
            if old == new or old not in s:
                continue
            if ("(" + old + ")") in s or (u"（" + old + u"）") in s:
                GLOSS.append((where, key, old, new, s[:110]))
                continue
            s = s.replace(old, new)
            hits.append((key, old, new))
            changed = True
        if not changed:
            break
    return s, hits


def note(where, kind, before, after, hits):
    RULE_HITS.update({h: RULE_HITS.get(h, 0) + 1 for h in hits})
    if not CJK_RUN.search(before):
        kind = "LOOSE-" + kind
        LOOSE.append((where, before, after))
    DET.append("%s\t%s\t%s\t%s\t%s" % (where, kind, "/".join(h[0] for h in hits),
                                       before[:110], after[:110]))


def read_text(path):
    raw = open(path, "rb").read()
    if path.startswith(GAME):
        enc = "gbk"
    elif raw[:3] == b"\xef\xbb\xbf":
        enc = "utf-8-sig"
    elif raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        enc = "utf-16"
    else:
        enc = "utf-8"
    try:
        return raw, raw.decode(enc), enc, "\r\n" if "\r\n" in raw.decode(enc, "replace") else "\n"
    except Exception as e:
        DET.append("%s\tREADFAIL\t%s\t\t" % (path, str(e)[:60]))
        return raw, None, None, None


def write_text(path, raw, s, enc, nl):
    body = s if nl == "\n" else s.replace("\n", nl)
    data = body.encode(enc)
    if data == raw:
        return False
    backup(path)
    tmp = path + ".new"
    open(tmp, "wb").write(data)
    chk = open(tmp, "rb").read().decode(enc)
    assert chk == body, "回读不一致: %s" % path
    os.replace(tmp, path)
    return True


def backup(path):
    rel = os.path.relpath(path, "D:\\")
    rel = rel.replace("\\", "__").replace(":", "").replace("/", "__")
    dst = os.path.join(BACKUP, rel)
    if not os.path.exists(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "wb").write(open(path, "rb").read())


def do_tsv(path, apply):
    raw, s, enc, nl = read_text(path)
    if s is None:
        return 0
    lines = s.replace("\r\n", "\n").split("\n")
    n = 0
    for i, ln in enumerate(lines):
        if not ln.strip() or ln.startswith("#"):
            continue
        cols = ln.split("\t")
        hit_any = False
        for ci in range(1, len(cols)):
            if not is_zh(cols[ci]):
                continue
            ns, hits = fix_text(cols[ci], "%s:L%d:c%d" % (os.path.basename(path), i + 1, ci))
            if ns != cols[ci]:
                note("%s:L%d:c%d" % (os.path.basename(path), i + 1, ci), "tsv-zh", cols[ci], ns, hits)
                cols[ci] = ns
                hit_any = True
        if hit_any:
            lines[i] = "\t".join(cols)
            n += 1
    if n and apply:
        write_text(path, raw, "\n".join(lines), enc, nl)
    return n


def do_textfile(path, apply):
    raw, s, enc, nl = read_text(path)
    if s is None:
        return 0
    lines = s.replace("\r\n", "\n").split("\n")
    n = 0
    for i, ln in enumerate(lines):
        if not ln.strip() or not is_zh(ln):
            continue
        ns, hits = fix_text(ln, "%s:L%d" % (os.path.basename(path), i + 1))
        if ns != ln:
            note("%s:L%d" % (os.path.basename(path), i + 1), "txt", ln, ns, hits)
            lines[i] = ns
            n += 1
    if n and apply:
        write_text(path, raw, "\n".join(lines), enc, nl)
    return n


def do_xscn(path, apply):
    data, items, meta = parse(path)
    if items is None:
        return 0
    spans = []
    if meta and meta[0] is not None:
        spans.append(("title", meta[0], meta[1]))
    for gi, idx, off, L in items:
        spans.append(("g%d#%d" % (gi, idx), off, L))
    edits = []
    for loc, off, L in spans:
        try:
            v = data[off + 2:off + 2 + L].decode("gbk")
        except Exception:
            continue
        if not is_zh(v):
            continue
        nv, hits = fix_text(v, "%s:%s" % (os.path.basename(path), loc))
        if nv == v:
            continue
        note("%s:%s" % (os.path.basename(path), loc), "xscn", v, nv, hits)
        edits.append((off, L, nv.encode("gbk")))
    if not edits:
        return 0
    if apply:
        backup(path)
        out = bytearray(open(path, "rb").read())
        for off, L, new in sorted(edits, key=lambda x: -x[0]):
            out[off:off + 2 + L] = len(new).to_bytes(2, "little") + new
        tmp = path + ".new"
        open(tmp, "wb").write(bytes(out))
        d2, it2, me2 = parse(tmp)
        d1, it1, me1 = parse(path)
        if d2 == bytes(out) and me2[2] == me1[2] and len(it2) == len(it1):
            os.replace(tmp, path)
        else:
            os.remove(tmp)
            raise SystemExit("!! .xscn 校验失败已回滚: " + path)
    return len(edits)


def walk_efile(apply, counter):
    for dp, dns, fns in os.walk(EFILE):
        for fn in sorted(fns):
            low = fn.lower()
            p = os.path.join(dp, fn)
            intz = ("TEXT-ZH" in dp.split(os.sep))
            if low.endswith(".xscn"):
                if intz:
                    continue                      # 死镜像，不动
                counter["xscn"] += do_xscn(p, apply)
            elif low.endswith(".txt"):
                counter["txt"] += do_textfile(p, apply)


def main():
    apply = "--apply" in sys.argv
    counter = {"tsv": 0, "txt": 0, "xscn": 0}
    for p in TSV_TARGETS:
        counter["tsv"] += do_tsv(p, apply)
    walk_efile(apply, counter)
    print("=== 定名铺设到 PeG-WW2（%s） ===" % ("APPLY" if apply else "dry-run"))
    print("命中规则行 %d 条 · 规则串 %d 个" % (len(RULES), len({r[1] for r in RULES})))
    print("改动单元: tsv 行 %d · txt 行 %d · xscn 槽 %d" % (counter["tsv"], counter["txt"], counter["xscn"]))
    print("\n-- 规则命中次数 --")
    for (key, old, new), n in sorted(RULE_HITS.items(), key=lambda x: -x[1]):
        if n:
            print("  %-28s %-30s -> %-22s %d" % (key, old, new, n))
    if LOOSE:
        print("\n-- LOOSE：汉字被数字/字母隔开，靠单字判定才命中（需人工复核） %d 处 --" % len(LOOSE))
        for w, b, a in LOOSE:
            print("  %-46s %s => %s" % (w.split("\\")[-1], b[:60], a[:60]))
    if GLOSS:
        print("\n-- 双语注保护跳过（未改） %d 处 --" % len(GLOSS))
        seen = set()
        for w, k, o, nw, frag in GLOSS:
            if (o, nw) in seen:
                continue
            seen.add((o, nw))
            print("  %-46s %-22s %s" % (w.split("\\")[-1], o, frag[:90]))
    with io.open(PLAN, "w", encoding="utf-8", newline="\n") as f:
        f.write("位置\t类别\t命中规则\t原值\t新值\n")
        for d in DET:
            f.write(d + "\n")
    print("\n明细: %s (%d 行)" % (PLAN, len(DET)))
    if not apply:
        print("\n(dry-run，未写入；加 --apply 落盘)")


if __name__ == "__main__":
    main()
