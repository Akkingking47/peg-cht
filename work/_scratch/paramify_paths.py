"""一次性工具：把 work/peg 与 peg 脚本里硬编码的两个绝对根路径参数化。

替换规则（默认值 = 作者本机布局，故行为零变化）：
    WS       <- 环境变量 PEG_WORKSPACE，默认 D:\\DSH\\军事游戏汉化
    GAME     <- 环境变量 PEG_GAME，      默认 D:\\Program Files\\PeG
    GAME_ALT <- 环境变量 PEG_GAME_ALT，  默认 D:\\Program Files\\PeG-1

用法：
    python paramify_paths.py            # dry-run，只打印计划
    python paramify_paths.py --apply    # 实际写入
"""
import ast
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))            # 工作区根

SYMS = [
    ("WS", "PEG_WORKSPACE", r"D:\DSH\军事游戏汉化"),
    ("GAME", "PEG_GAME", r"D:\Program Files\PeG"),
    ("GAME_ALT", "PEG_GAME_ALT", r"D:\Program Files\PeG-1"),
]

TARGET_DIRS = [
    os.path.join(ROOT, "work", "peg"),
    os.path.join(ROOT, "peg"),
]

LINE_ASSIGN = re.compile(
    r"^\s*(WS|GAME|GAME_ALT)\s*=\s*(?:r)?(['\"])[^'\"]*\2\s*(#.*)?$"
)


def header_text(need_os):
    out = [
        "",
        "# ── 路径真源 ────────────────────────────────────────────────────────",
        "# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。",
    ]
    if need_os:
        out.append("import os")
    out += [
        'WS       = os.environ.get("PEG_WORKSPACE", r"D:\\DSH\\军事游戏汉化")',
        'GAME     = os.environ.get("PEG_GAME",      r"D:\\Program Files\\PeG")',
        'GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\\Program Files\\PeG-1")',
        "# ───────────────────────────────────────────────────────────────────",
        "",
    ]
    return "\n".join(out) + "\n"


def build_literal_re():
    alts = "|".join(re.escape(rt) for _, _, rt in SYMS)
    return re.compile(
        r"(?:(?P<raw>r))?(?P<q>['\"])(" + alts + r")(?P<suf>[^'\"]*)(?P=q)"
    )


LIT = build_literal_re()


def root_to_sym(value):
    # 长者优先，否则 "D:\Program Files\PeG-1" 会被 "D:\Program Files\PeG" 前缀抢先匹配
    for sym, _, rt in sorted(SYMS, key=lambda s: -len(s[2])):
        if value == rt:
            return sym, ""
        if value.startswith(rt):
            return sym, value[len(rt):]
    return None, None


def expr_for(sym, suffix):
    parts = [p for p in re.split(r"[\\/]+", suffix) if p]
    if not parts:
        return sym
    return 'os.path.join(%s, %s)' % (sym, ", ".join('"%s"' % p for p in parts))


def replace_literals(text):
    def sub(m):
        sym, suffix = root_to_sym(m.group(3) + m.group(4))
        if sym is None:
            return m.group(0)
        return expr_for(sym, suffix)
    return LIT.sub(sub, text)


def has_os_import(text):
    return bool(
        re.search(r"^\s*import\s+os\s*$", text, re.M)
        or re.search(r"^\s*import\s+[^\n]*\bos\s*[,)]", text, re.M)
        or re.search(r"^\s*import\s+[^\n]*,\s*os\s*$", text, re.M)
        or re.search(r"^\s*from\s+os\s+import\b", text, re.M)
    )


def insert_line_no(text):
    """返回「插入点行号」（1-based）：文档字符串 + 首段连续 import 块之后。"""
    tree = ast.parse(text)
    body = tree.body
    idx = 0
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
            and isinstance(body[0].value.value, str):
        idx = 1
    last = 0
    start = idx
    while idx < len(body) and isinstance(body[idx], (ast.Import, ast.ImportFrom)):
        last = body[idx].end_lineno
        idx += 1
    if last == 0:
        last = body[start - 1].end_lineno if start > 0 else 0
    return last


def process(path, apply):
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    if not any(rt in src for _, _, rt in SYMS):
        return None
    n_lit = len(LIT.findall(src))

    # 先删掉与头块重复的自赋值行（此时还是字面量形态），再做字面量替换
    kept, dropped = [], 0
    for line in src.splitlines(keepends=True):
        if LINE_ASSIGN.match(line.rstrip("\r\n")):
            dropped += 1
            continue
        kept.append(line)
    new = replace_literals("".join(kept))

    new_lit = len(LIT.findall(new))
    if new_lit != 0:
        raise RuntimeError("仍有未替换的字面量：%s (%d)" % (path, new_lit))

    ln = insert_line_no(new)
    lines = new.splitlines(keepends=True)
    hdr = header_text(not has_os_import(new))
    new = "".join(lines[:ln]) + hdr + "".join(lines[ln:])

    ast.parse(new)                      # 语法自检
    if apply:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new)
    return n_lit, dropped


def repair(apply):
    """修正在首轮替换中被前缀误匹配的 PeG-1 路径。"""
    pat_a = re.compile(r'os\.path\.join\(GAME, "-1", ')
    pat_b = re.compile(r'os\.path\.join\(GAME, "-1"\)')
    n = 0
    for d in TARGET_DIRS:
        for dirpath, _dirs, names in os.walk(d):
            if os.path.basename(dirpath) == "out":
                continue
            for nm in sorted(names):
                if not nm.endswith(".py"):
                    continue
                p = os.path.join(dirpath, nm)
                with open(p, "r", encoding="utf-8") as f:
                    src = f.read()
                if "-1" not in src:
                    continue
                new = pat_a.sub("os.path.join(GAME_ALT, ", src)
                new = pat_b.sub("GAME_ALT", new)
                if new != src:
                    n += 1
                    print("repair: %s" % os.path.relpath(p, ROOT))
                    ast.parse(new)
                    if apply:
                        with open(p, "w", encoding="utf-8", newline="") as f:
                            f.write(new)
    print("repair 命中 %d 个文件 (%s)" % (n, "已写入" if apply else "dry-run"))


def main():
    if "--repair" in sys.argv:
        repair("--apply" in sys.argv)
        return
    apply = "--apply" in sys.argv
    files = []
    for d in TARGET_DIRS:
        for dirpath, _dirs, names in os.walk(d):
            if os.path.basename(dirpath) == "out":
                continue
            for n in sorted(names):
                if n.endswith(".py"):
                    files.append(os.path.join(dirpath, n))
    total_lit = total_files = 0
    for p in files:
        r = process(p, apply)
        if r:
            total_files += 1
            total_lit += r[0]
            print("%-64s 字面量=%-3d 删自赋值=%d" % (
                os.path.relpath(p, ROOT), r[0], r[1]))
    print("\n合计：%d 个文件，%d 处字面量  (%s)" % (
        total_files, total_lit, "已写入" if apply else "dry-run"))


if __name__ == "__main__":
    main()
