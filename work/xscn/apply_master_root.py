# -*- coding: utf-8 -*-
r"""根级四件套程序优先匹配器 —— 新 efile 开工，先用词库自动定译，只剩 miss 才交 LLM。

用法: python apply_master_root.py --efile GUS --root D:\OpenGeneral [--files a,b]

对应 `apply_master.py`（那个只管 `.xscn`）；本器管 efile **根目录**这五件：
    equip.txt  names.txt  NamesEx.txt  nations.txt  strings_efile.txt

流程（「程序做翻译、LLM 只校验」）：
  1. 读 <root>/<efile>/ 下五个文件（按 cp1252 读，避开假汉字陷阱）
  2. 逐行分类 —— 下列行**保留原文**，不进 miss：
       空行 / `*` `**` 注释行 / `[段头]` / `VERSION` `Error! VERSION` 版本标识行
  3. 其余行走词库，优先级由低到高：master-glossary.tsv > _root_dict.tsv（根级实证） > master-resolve.tsv（冲突裁定）
  4. 输出 work\<efile-lower>\
       root-prematch-map.tsv   程序已定 src→dst
       root-prematch-miss.tsv  需 LLM 的 src（按出现次数降序）

⚠️ 本器**只产出映射表，不写任何游戏文件**。落 `TEXT-ZH\` 由后续部署脚本负责。
"""
import collections
import importlib.util
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.environ.get("XSCN_ROOT") or r"D:\OpenPG2"
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(os.path.dirname(HERE))          # D:\DSH\军事游戏汉化
FILES = ["equip.txt", "names.txt", "NamesEx.txt", "nations.txt", "strings_efile.txt"]

VERSION_RE = re.compile(r"^(Error!\s*)?VERSION\b", re.I)
SECTION_RE = re.compile(r"^\[[^\]]*\]\s*$")


def rd(path):
    """读 TSV 建 src->dst（dst = 第 2 列）；setdefault ⇒ 首次出现优先。"""
    d = {}
    if not os.path.exists(path):
        return d
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2 and c[0] and c[1]:
                d.setdefault(c[0], c[1])
    return d


def keep_as_is(s):
    """这些行保留原文（不翻译、不计 miss）。返回原因字符串或 None。"""
    t = s.strip()
    if not t:
        return "空行"
    if t.startswith("*"):
        return "注释"
    if SECTION_RE.match(t):
        return "段头"
    if VERSION_RE.match(t):
        return "版本标识"
    return None


SUSPECT = "\u00b9\u00b2\u00b3\u00bc\u00bd\u00be\u00b0\u00b1"


def _pick_enc(raw):
    """原文是西欧单字节，但各家 efile 用的表不同：
      · GUS 系列 = cp1250（波兰）—— `Jastrz¹b`(cp1252) 其实是 `Jastrząb`(cp1250)
      · WW2 多数 = cp1252（德/英）
      · 少数 = UTF-8（如 OLGWW2\\names.txt 的 `Barrón`）
    先判严格 UTF-8（含高位字节且能无损解码即认），再用「解出可疑字符 ¹²³¼½¾°± 更少」在 cp1250/cp1252 间择一。"""
    if any(b >= 0x80 for b in raw):
        try:
            raw.decode("utf-8")
            return "utf-8"
        except UnicodeDecodeError:
            pass
    a = raw.decode("cp1252", "replace")
    b = raw.decode("cp1250", "replace")
    return "cp1250" if sum(b.count(c) for c in SUSPECT) < sum(a.count(c) for c in SUSPECT) else "cp1252"


def read_lines(path, enc="auto"):
    """按西欧单字节读原文，去 BOM，统一换行后按 \\n 切。enc=auto 时见 _pick_enc。"""
    raw = open(path, "rb").read()
    if raw[:3] == b"\xef\xbb\xbf":
        raw = raw[3:]
    if enc == "auto":
        enc = _pick_enc(raw)
    return raw.decode(enc, "replace").replace("\r\n", "\n").split("\n")


def main():
    a = sys.argv[sys.argv.index("--efile") + 1] if "--efile" in sys.argv else None
    if not a:
        raise SystemExit("用法: python apply_master_root.py --efile GUS [--root D:\\OpenGeneral] [--files a,b]")
    root = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else ROOT
    spec = importlib.util.spec_from_file_location("xscn", os.path.join(HERE, "xscn.py"))
    xscn = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(xscn)
    except SystemExit:
        pass
    ef = xscn.norm_efile(a)
    ef = xscn.resolve_dir(root, ef) or ef          # 磁盘真实大小写
    files = sys.argv[sys.argv.index("--files") + 1].split(",") if "--files" in sys.argv else FILES
    enc = sys.argv[sys.argv.index("--enc") + 1] if "--enc" in sys.argv else "auto"
    outdir = os.path.join(WORK, "work", ef.lower())
    os.makedirs(outdir, exist_ok=True)

    # 词库：优先级由低到高依次覆盖
    master = rd(os.path.join(HERE, "master-glossary.tsv"))
    rootd = rd(os.path.join(HERE, "_root_dict.tsv"))
    only_root = [s for s in rootd if s not in master]
    master.update(rootd)
    master.update(rd(os.path.join(HERE, "master-resolve.tsv")))

    hit = collections.Counter()      # 命中 src -> 行数
    miss = collections.Counter()     # 未命中 src -> 行数
    where = collections.defaultdict(list)
    kept = collections.Counter()
    per = []
    for fn in files:
        p = os.path.join(root, ef, fn)
        if not os.path.exists(p):
            per.append((fn, 0, 0, 0, 0, "缺"))
            continue
        n = nhit = nkeep = 0
        for idx, ln in enumerate(read_lines(p, enc)):
            t = ln.rstrip("\r")
            n += 1
            why = keep_as_is(t)
            if why:
                kept[why] += 1
                nkeep += 1
                continue
            key = t.strip()
            if key in master:
                hit[key] += 1
                nhit += 1
                if len(where[key]) < 3:
                    where[key].append("%s:%d" % (fn, idx))
            else:
                miss[key] += 1
        per.append((fn, n, nkeep, nhit, n - nkeep - nhit, "OK"))

    print("[%s]  %s" % (root, ef))
    print("%-18s %6s %7s %7s %7s" % ("文件", "行", "保留", "命中", "待译"))
    tot = [0, 0, 0, 0]
    for fn, n, nkeep, nhit, nmiss, st in per:
        print("%-18s %6d %7d %7d %7d  %s" % (fn, n, nkeep, nhit, nmiss, st))
        for i, v in enumerate((n, nkeep, nhit, nmiss)):
            tot[i] += v
    print("%-18s %6d %7d %7d %7d" % ("合计", *tot))
    print("保留原文构成: %s" % dict(kept))
    print("待译唯一串 %d（占待译行 %d 的 %.1f%%）" % (len(miss), tot[3], 100.0 * len(miss) / max(1, tot[3])))
    print("=> 行级程序覆盖 %.1f%%" % (100.0 * tot[2] / max(1, tot[2] + tot[3])))
    print("_root_dict 独有（不在 master-glossary）条目 %d" % len(only_root))

    with io.open(os.path.join(outdir, "root-prematch-map.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tdst\n")
        for s in sorted(hit):
            f.write("%s\t%s\n" % (s, master[s]))
    with io.open(os.path.join(outdir, "root-prematch-miss.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tn\n")
        for s, k in sorted(miss.items(), key=lambda kv: (-kv[1], kv[0])):
            f.write("%s\t%d\n" % (s, k))
    print("已写 %s\\root-prematch-map.tsv / root-prematch-miss.tsv" % outdir)
    print("命中样例（前 12，按行数）：")
    for s, k in hit.most_common(12):
        print("   %-30s -> %-24s x%d   %s" % (s[:30], master[s][:24], k, where[s][:2]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
