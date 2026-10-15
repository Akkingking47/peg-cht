# -*- coding: utf-8 -*-
"""译文一致性 linter —— 规则表驱动，输入任意 .tsv 映射表或成品 .txt，逐行跑规则，输出违规清单。

用法：
    python lint_zh.py <文件> [<文件> ...]            # 规则表默认取同目录 lint_rules.tsv
    python lint_zh.py --rules work\\lint_rules.tsv peg\\research\\gui030-zh.tsv
    python lint_zh.py --json peg\\testbed\\Gui030.zh.txt > lint.json
    python lint_zh.py --quiet *.tsv                      # 只打摘要，不打逐条
    python lint_zh.py --stats                            # 只打规则表结构（列名 + 每类条数），不跑文件
    python lint_zh.py --min-severity mid <文件>          # 只把 mid/high 算作违规（默认 low，即全算）
    python lint_zh.py --help

输出：每行一条 `文件:行:规则:内容`（规则形如 `类型:匹配`，超长匹配截断为 40 字符）。
退出码：有违规 = 1，无违规 = 0，用法/规则表/IO 错误 = 2。
（`--min-severity high` 时同理：有 high 违规 = 1。）

设计要点（都是踩过的坑，改之前先读）：
 1. **规则全在 `lint_rules.tsv`，代码里不内嵌任何词条** —— 加规则只动表，不动这个文件。
    表里 `-` 是空值哨兵（期望/严重度不适用时写它），保证每行恒定 7 字段。
 2. **黑名单整串精确，禁用词才用子串** —— 照抄 `work\\peg\\gen_gui030_zh.py:337` 的
    `zh.strip() == bad or zh.strip().rstrip("- ").strip() == bad`：整串匹配才不会
    把合规译文「补充兵员」误判成黑名单「补充兵」。
 3. **编码：先 UTF-8 严格，失败才回退 GBK** —— 顺序不能反。GBK 几乎能吃下任意字节，
    放前面会把 UTF-8 文件解成乱码（仓库纪律见 `docs\\41-分支工作区经验吸收清单.md:120`：
    GBK 文件不能用 grep/rg 搜中文，会假报无匹配 ⇒ 中文一律 Python 按编码读）。
 4. **`.tsv` 只查 译文 列，`备注/说明/note` 列绝不查** —— 备注里写着「禁用"声望"」这类
    元话语，查它必然自己命中自己。表头识别不到 译文 列就整体降级成「按行文本」模式。
 5. **`latin` 规则先剥括注、再擦白名单** —— 顺序是：剥 `译名(原文)` 括注 → 按 `allow` 行
    擦掉「口径保留」样式（纯符号/数字整串、军舰舰名、≤5 位全大写缩写）→ 还剩拉丁字母才报。
    不这么做，`Phra Nahka Si Ayutthaya(大城府)` 这类合规行会被全量误报。
    另外 `latin` 只在**该行确实含汉字**时才报（规则本义是「中文里残留拉丁字母」），
    所以整行未译（如 `Air Mission`）不归它管 —— 这是已知的规则空洞，别拿它当漏检。
 6. **`原文` 适用列的规则（后缀锁定）只在带原文列的 .tsv 上生效**，成品 .txt 记 skipped
    并计入摘要 `skipped`，不计入违规（否则纯文本文件会被全量误报）。
 7. **刻意不实现**（写了必误报，别补）：
    · 半角逗号/冒号不判违规 —— 铁律 §三-8「标点随原文」（`peg\\research\\各国军语风格口径.md:64`）。
    · 简体「占领」不判违规 —— 民国感清单里的 `佔領` 只在原文是 `Overrun` 时才算错
      （`各国军语风格口径.md:117`），做子串规则会淹掉真违规。
    完整清单见 `lint_rules.tsv` 末尾注释块。
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RULES = os.path.join(HERE, "lint_rules.tsv")

# 规则类型（与 lint_rules.tsv 的「类型」列一一对应，改表前先改这里）
RULE_TYPES = (
    "banned",     # 整串黑名单：译文去空白后精确等于「匹配」
    "forbidden",  # 禁用词：译文含「匹配」子串
    "regex",      # 正则禁用：译文 re.search(匹配)
    "punct",      # 标点规范：引擎同 regex，只换标签
    "paren",      # 括注格式：引擎同 regex，只换标签
    "prefix",     # 前缀锁定：译文命中「匹配」时必须以「期望」开头
    "suffix",     # 后缀锁定：**原文**命中「匹配」时译文必须以「期望」结尾
    "empty",      # 空译文
    "latin",      # 中文里残留拉丁字母（先剥括注 + 擦 allow）
    "allow",      # 白名单：只服务 latin，按行序擦除
)
SEV_RANK = {"high": 3, "mid": 2, "low": 1}
RANK_SEV = {v: k for k, v in SEV_RANK.items()}
COLUMNS = ("类型", "适用", "匹配", "期望", "严重度", "依据", "说明")
NONE = "-"  # 空值哨兵

CJK = re.compile(r"[\u4e00-\u9fff]")
LAT = re.compile(r"[A-Za-z]")
# `译名(原文)` / `译名（原文）` 括注里的纯拉丁原文（进 latin 检查前先剥掉）
GLOSS = re.compile(r"[（(]\s*[A-Za-z0-9][A-Za-z0-9 .,'’\-]*\s*[)）]")

ZH_NAMES = ("译文", "中文", "译名", "中译", "zh", "chinese", "target", "trans")
EN_NAMES = ("原文", "英文", "en", "english", "source", "src", "key")
NOTE_NAMES = ("备注", "说明", "note", "comment", "context", "依据")


# ------------------------------------------------------------------ 读文件
def read_text(path):
    """按 UTF-8 → GBK 顺序试读，返回 (文本, 编码名)。顺序不可颠倒，理由见模块 docstring-3。"""
    with open(path, "rb") as fh:
        raw = fh.read()
    for enc in ("utf-8-sig", "gbk"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8/replace"


# ------------------------------------------------------------------ 规则表
class Rule(object):
    __slots__ = ("type", "apply", "match", "expect", "sev", "src", "note", "line", "rx")

    def __init__(self, f, line):
        self.type, self.apply, self.match, self.expect, self.sev, self.src, self.note = f
        self.line = line
        self.rx = None
        if self.match != NONE and self.type in ("regex", "punct", "paren", "prefix", "suffix", "latin", "allow"):
            self.rx = re.compile(self.match)

    @property
    def rank(self):
        return SEV_RANK.get(self.sev, 0)

    def rid(self):
        """`文件:行:规则:内容` 里的「规则」字段：类型:匹配（超长截 40 字符）。"""
        pat = self.match if len(self.match) <= 40 else self.match[:39] + "…"
        return "%s:%s" % (self.type, pat)

    def why(self):
        return "应为「%s」｜依据 %s｜%s" % (self.expect, self.src, self.note)


def load_rules(path):
    """读规则表；返回 (规则列表, 统计 dict, 未实现注释行列表)。行数/字段数不符即报错，不静默跳过。"""
    text, enc = read_text(path)
    rules, skipped_notes, collecting = [], [], False
    for ln, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            if "未实现清单" in line:
                collecting = True
                continue
            if collecting:
                body = line.lstrip("# ").strip()
                if body and set(body) <= set("="):   # 分隔线
                    continue
                if body:
                    skipped_notes.append(body)
            continue
        f = line.split("\t")
        if f[0] == COLUMNS[0] and len(f) == len(COLUMNS):  # 表头行
            continue
        if len(f) != len(COLUMNS):
            raise SystemExit("规则表 %s:%d 字段数 %d ≠ %d：%r" % (path, ln, len(f), len(COLUMNS), line))
        if f[0] not in RULE_TYPES:
            raise SystemExit("规则表 %s:%d 未知类型 %r（合法：%s）" % (path, ln, f[0], "/".join(RULE_TYPES)))
        rules.append(Rule(f, ln))
    stats = {}
    for r in rules:
        stats[r.type] = stats.get(r.type, 0) + 1
    return rules, stats, skipped_notes, enc


# ------------------------------------------------------------------ 记录：把任意输入切成「一条译文」
def sniff_header(lines):
    """找表头行，返回 {zh: idx, en: idx, note: idx}（找不到 译文 列返回 None）。"""
    for raw in lines[:20]:
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = [x.strip().lower() for x in line.split("\t")]
        cols = {}
        for key, names in (("zh", ZH_NAMES), ("en", EN_NAMES), ("note", NOTE_NAMES)):
            hits = [i for i, x in enumerate(fields) if x in names]
            if not hits:
                hits = [i for i, x in enumerate(fields) if names is not ZH_NAMES and any(n in x for n in names)]
            if hits:
                cols[key] = hits[0]
        return cols if "zh" in cols else None
    return None


def iter_records(path):
    """产出 (行号, 译文, 原文)，以及模式说明。.tsv 走列模式（失败降级文本模式），.txt 走文本模式。

    文本模式下**若该行含 TAB 表格**，则按字段切分、只查含汉字的字段 —— 无表头的中间表里
    原文列整列是英文，整行照查会让 `latin` 与标点规则全量误报（实测 `work\\kaiser\\xscn-place.tsv`
    的 `"Omakaitse"\\t"自卫队"` 被整行误报）。不含任何汉字的行直接跳过。
    """
    lines = read_text(path)[0].splitlines()
    mode, cols = "text", None
    if path.lower().endswith((".tsv", ".tab", ".csv")):
        cols = sniff_header(lines)
        mode = "table" if cols else "text"
    for ln, raw in enumerate(lines, 1):
        line = raw.rstrip("\r\n")
        if mode == "table":
            if line.lstrip().startswith("#"):
                continue
            f = line.split("\t")
            zh = f[cols["zh"]] if len(f) > cols["zh"] else ""
            en = f[cols["en"]] if ("en" in cols and len(f) > cols["en"]) else ""
            if not zh.strip() and not en.strip():
                continue  # 结构性空行，不是「空译文」
            yield ln, zh, en
            continue
        if "\t" in line:
            for f in (x for x in line.split("\t") if CJK.search(x)):
                yield ln, f, ""
            continue
        if not line.strip():
            continue  # 结构性空行（成品 .txt 的段落分隔），不是「空译文」
        yield ln, line, ""
    return


# ------------------------------------------------------------------ 逐条跑规则
def check(zh, en, rules, allows, ctx):
    """对一条译文跑全部规则，返回违规列表 [dict]。"""
    hits = []
    has_cjk = bool(CJK.search(zh))

    def add(rule, msg):
        hits.append({
            "file": ctx["file"], "line": ctx["line"], "rule": rule.rid(), "type": rule.type,
            "severity": rule.sev, "rank": rule.rank, "text": zh, "source": en,
            "expect": rule.expect, "evidence": rule.src, "note": rule.note, "message": msg,
        })

    for r in rules:
        if r.type == "allow":
            continue
        if r.apply == "原文" and not en:
            ctx["skipped"] += 1          # 成品 .txt 没有原文列：记 skipped，不报假违规
            continue
        detail = None
        if r.type == "banned":
            s = zh.strip()
            if s == r.match or s.rstrip("- ").strip() == r.match:
                detail = "整串命中黑名单"
        elif r.type == "forbidden":
            if r.match in zh:
                detail = "含禁用词"
        elif r.type in ("regex", "punct", "paren"):
            if r.rx.search(zh):
                detail = "命中禁用式"
        elif r.type == "prefix":
            if r.rx.search(zh) and not zh.strip().startswith(r.expect):
                detail = "前缀锁定不满足"
        elif r.type == "suffix":
            if r.rx.search(en) and not zh.strip().endswith(r.expect):
                detail = "后缀锁定不满足"
        elif r.type == "empty":
            if not zh.strip():
                detail = "空译文"
        elif r.type == "latin":
            if not has_cjk:
                continue                 # 本义是「中文里残留」，整行未译不归它管（见 docstring-5）
            bare = GLOSS.sub("", zh)
            for a in allows:
                bare = a.rx.sub("", bare)
            m = (r.rx or LAT).search(bare)
            if m:
                detail = "残留拉丁「%s」" % m.group(0)
        if detail is None:
            continue
        if r.expect != NONE:
            detail += "；应为「%s」" % r.expect
        add(r, "%s  [%s] %s" % (zh if zh.strip() else "（空）", detail, r.src))
    return hits


# ------------------------------------------------------------------ 入口
def print_stats(rules, stats, skipped_notes, rules_path):
    print("规则表: %s" % rules_path)
    print("列名: %s" % " ".join(COLUMNS))
    print("数据行: %d" % len(rules))
    for t in RULE_TYPES:
        if stats.get(t):
            print("  %-9s %3d" % (t, stats[t]))
    if skipped_notes:
        print("\n素材不足 / 刻意未实现（表内注释块）：")
        for s in skipped_notes:
            print("  · %s" % s)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="lint_zh.py",
        description="译文一致性 linter：对 .tsv 映射表或成品 .txt 逐行跑规则，输出「文件:行:规则:内容」。",
        epilog="退出码：有违规=1，无违规=0，用法/规则表/IO 错误=2。规则表默认 %s" % DEFAULT_RULES,
    )
    ap.add_argument("files", nargs="*", help="待检查的文件（可多个）；.tsv 走列模式，其余按行文本")
    ap.add_argument("--rules", default=DEFAULT_RULES, help="规则表路径（默认 %s）" % DEFAULT_RULES)
    ap.add_argument("--json", action="store_true", help="输出 JSON（{violations, summary}）而非逐条文本")
    ap.add_argument("--quiet", action="store_true", help="只打摘要，不打逐条违规")
    ap.add_argument("--stats", action="store_true", help="打印规则表结构（列名 + 每类条数 + 未实现清单）后退出")
    ap.add_argument("--min-severity", choices=("low", "mid", "high"), default="low",
                    help="只把不低于该严重度的命中的算作违规（默认 low，即全算）")
    args = ap.parse_args(argv)

    try:
        rules, stats, skipped_notes, enc = load_rules(args.rules)
    except (OSError, SystemExit) as e:
        print(str(e) if isinstance(e, SystemExit) else "规则表读不到：%s" % e, file=sys.stderr)
        return 2

    if args.stats:
        print_stats(rules, stats, skipped_notes, args.rules)
        return 0
    if not args.files:
        ap.print_usage(sys.stderr)
        print("错误：没给文件（要只看规则表结构请加 --stats）", file=sys.stderr)
        return 2

    allows = [r for r in rules if r.type == "allow"]
    floor = SEV_RANK[args.min_severity]
    all_hits, per_file, n_skipped, errors = [], [], 0, []
    for path in args.files:
        if not os.path.isfile(path):
            errors.append("找不到文件：%s" % path)
            continue
        ctx = {"file": path, "line": 0, "skipped": 0}
        n_rec = 0
        try:
            for ln, zh, en in iter_records(path):
                ctx["line"] = ln
                n_rec += 1
                all_hits.extend(h for h in check(zh, en, rules, allows, ctx) if h["rank"] >= floor)
        except OSError as e:
            errors.append("读不了文件：%s（%s）" % (path, e))
            continue
        n_skipped += ctx["skipped"]
        hits_f = [h for h in all_hits if h["file"] == path]
        per_file.append({"file": path, "encoding": read_text(path)[1], "records": n_rec,
                         "violations": len(hits_f),
                         "by_severity": {s: sum(1 for h in hits_f if h["severity"] == s) for s in ("high", "mid", "low")}})

    all_hits.sort(key=lambda h: (h["file"], h["line"], -h["rank"]))
    summary = {
        "rules": args.rules, "rules_rows": len(rules), "rules_by_type": stats,
        "min_severity": args.min_severity, "files": per_file, "violations": len(all_hits),
        "by_severity": {s: sum(1 for h in all_hits if h["severity"] == s) for s in ("high", "mid", "low")},
        "rules_rows_skipped_no_source_column": n_skipped, "errors": errors,
    }
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
    if args.json:
        print(json.dumps({"violations": all_hits, "summary": summary}, ensure_ascii=False, indent=2))
    else:
        if not args.quiet:
            for h in all_hits:
                print("%s:%d:%s:%s" % (h["file"], h["line"], h["rule"], h["message"]))
        for f in per_file:
            print("# %s  [%s]  记录 %d  违规 %d  (high %d / mid %d / low %d)" % (
                f["file"], f["encoding"], f["records"], f["violations"],
                f["by_severity"]["high"], f["by_severity"]["mid"], f["by_severity"]["low"]), file=sys.stderr)
        print("# 合计 %d 条违规 (high %d / mid %d / low %d)；规则 %d 行；无原文列跳过 %d 次" % (
            summary["violations"], summary["by_severity"]["high"], summary["by_severity"]["mid"],
            summary["by_severity"]["low"], len(rules), n_skipped), file=sys.stderr)
    return 1 if all_hits else (2 if errors and not all_hits else 0)


if __name__ == "__main__":
    try:  # 控制台可能是 GBK 码页，中文违规内容统一按 UTF-8 输出
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
