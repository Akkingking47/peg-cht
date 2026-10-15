# -*- coding: utf-8 -*-
"""标准译名库查询工具

用法:
  python glossary.py <原文>                # 查标准译名（模糊匹配）
  python glossary.py -r <中文>             # 反查：这个中文对应哪些原文
  python glossary.py -c PLACE              # 按类别列出
  python glossary.py -e EFILE_OLGWW2       # 按 efile 列出
  python glossary.py -c PLACE -e EFILE_OLGWW2 -n 50
  python glossary.py --stats               # 统计概览
  python glossary.py --check <原文>        # 只判合规：给出标准译名与可信度
  python glossary.py --export out.tsv      # 导出（UTF-8 无 BOM，给程序用）

库文件: glossary/standard-glossary.tsv（本目录的 ../.. 下的 glossary/）
列: en zh cat scope status src conf
    status: LOCKED=有标准中文译名 / POLICY=按口径保留原文
    conf  : HIGH=唯一无争议 / MID=仅表述差异 / LOW=有实质冲突或缩写歧义
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GL = os.path.normpath(os.path.join(HERE, "..", "..", "glossary", "standard-glossary.tsv"))
HEAD = ["en", "zh", "cat", "scope", "status", "src", "conf", "zh_in"]


def load(path=GL):
    if not os.path.exists(path):
        sys.exit("库文件不存在: %s\n先跑 build_glossary.py" % path)
    rows = []
    for ln in io.open(path, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")[1:]:
        if not ln.strip():
            continue
        c = ln.split("\t")
        while len(c) < len(HEAD):
            c.append("")
        rows.append(c[:len(HEAD)])
    return rows


def w(s, n):
    """按显示宽度截断（CJK 算 2 列）"""
    out, cur = "", 0
    for ch in s:
        cw = 2 if ord(ch) > 0x2000 else 1
        if cur + cw > n:
            return out + "…"
        out += ch
        cur += cw
    return out


def show(rows):
    if not rows:
        print("（无匹配）")
        return
    print("%-30s %-26s %-8s %-18s %-7s %s" % ("原文", "标准译名", "类别", "efile", "状态", "可信"))
    print("-" * 104)
    for r in rows:
        print("%-30s %-26s %-8s %-18s %-7s %s"
              % (w(r[0], 30), w(r[1], 26), r[2], r[3], r[4], r[6]))
    print("（%d 条）" % len(rows))


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return
    rows = load()

    if a[0] == "--stats":
        cat = {}
        st = {}
        cf = {}
        ef = {}
        for r in rows:
            cat[r[2]] = cat.get(r[2], 0) + 1
            st[r[4]] = st.get(r[4], 0) + 1
            cf[r[6]] = cf.get(r[6], 0) + 1
            ef[r[3]] = ef.get(r[3], 0) + 1
        print("标准译名库: %s" % GL)
        print("总计 %d 条\n" % len(rows))
        for t, d in (("按类别", cat), ("按状态", st), ("按可信度", cf), ("按 efile", ef)):
            print("-- %s --" % t)
            for k, v in sorted(d.items(), key=lambda kv: -kv[1]):
                print("   %-10s %6d" % (k, v))
            print()
        return

    if a[0] == "--export":
        out = a[1] if len(a) > 1 else "glossary-export.tsv"
        with io.open(out, "w", encoding="utf-8", newline="\r\n") as f:
            f.write("\t".join(HEAD) + "\n")
            for r in rows:
                f.write("\t".join(r) + "\n")
        print("已导出 %d 条 -> %s（UTF-8 无 BOM）" % (len(rows), out))
        return

    if a[0] == "--check":
        if len(a) < 2:
            sys.exit("用法: --check <原文>")
        q = a[1]
        hit = [r for r in rows if r[0] == q]
        if not hit:
            print("库中无此条目 —— 需新增译名")
            return
        show(hit)
        return

    # -r 反查
    if a[0] in ("-r", "--reverse"):
        q = a[1] if len(a) > 1 else ""
        show([r for r in rows if q in r[1]])
        return

    # 过滤
    cat = ef = None
    q = None
    n = 40
    i = 0
    while i < len(a):
        if a[i] == "-c" and i + 1 < len(a):
            cat = a[i + 1]; i += 2
        elif a[i] == "-e" and i + 1 < len(a):
            ef = a[i + 1]; i += 2
        elif a[i] == "-n" and i + 1 < len(a):
            n = int(a[i + 1]); i += 2
        else:
            q = a[i]; i += 1

    sel = rows
    if q:
        sel = [r for r in sel if q.lower() in r[0].lower()]
    if cat:
        sel = [r for r in sel if r[2] == cat.upper()]
    if ef:
        sel = [r for r in sel if r[3] == ef.upper()]

    if len(sel) > n:
        print("匹配 %d 条，显示前 %d 条（-n 调整）\n" % (len(sel), n))
        show(sel[:n])
    else:
        show(sel)


if __name__ == "__main__":
    main()
