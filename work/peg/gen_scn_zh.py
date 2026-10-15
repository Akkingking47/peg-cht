# -*- coding: utf-8 -*-
"""
PeG 场景文本（Scenario / Userscen）中文化生成器
================================================================
依据：peg/research/场景文本方案.md + scenario-map.tsv

四类处理（用户 2026-10-10 确认，第 15 轮定稿）：
  ① **M 地图地名**（`*_m.txt`）→ **纯译，不加原文括号**（地图六角格空间极小）
  ② **U 单位名**（`*_u.txt`）→ **纯译，不加原文括号**（栏位窄；军阶/舰名已含原文要素）
  ③ **S 短标签**（其余 `*.txt`，行≤30 字符）→ **译 + (原文)**
  ④ **I/V/L 叙事**（长段落）→ 段落内**地名/专名替换为「译(原文)」，每次出现都加**

  ①② 由 `NO_PAREN_RE` 控制（`(_m|_u)$`）。

用法：
    python work/peg/gen_scn_zh.py build    # 生成到 peg/testbed/scn-zh/
    python work/peg/gen_scn_zh.py deploy   # 备份 + 部署到游戏
    python work/peg/gen_scn_zh.py verify   # 逐文件校验（行数/编码/残留）
    python work/peg/gen_scn_zh.py restore  # 从备份还原
"""
import os
import re
import sys
import shutil
import collections

ROOT = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG"
SRC_DIRS = [os.path.join(GAME, "Scenario"), os.path.join(GAME, "Userscen")]
BACKUP = os.path.join(ROOT, r"peg\testbed\backup")
OUTDIR = os.path.join(ROOT, r"peg\testbed\scn-zh")
MAPFILE = os.path.join(ROOT, r"peg\research\scenario-map.tsv")
LONGFILE = os.path.join(ROOT, r"peg\research\scenario-long-zh.tsv")   # 长段落整行译文（第 22 轮）
NUMFILE = os.path.join(ROOT, r"peg\research\scn-number.tsv")          # 场景列表数字序号（第 23 轮）
# ⭐ 按场景定点覆盖（第 37 轮）：`en | 项目 | 场景词干 | 译名 | 依据`
#    为什么必须有它：`scenario-map.tsv` 是**按英文键全局一张值**，而地名该怎么译要看
#    「该场景预设扮演哪方势力」（如 Amur River 中→黑龙江 / 俄→阿穆尔河）。
OVRFILE = os.path.join(ROOT, r"glossary\layers\scn-place-override.tsv")

NO_PAREN_RE = re.compile(r"(_m|_u)$", re.I)   # M 地图地名 / U 单位名：不加括号
# ⚠️ 整文件排除（原样拷贝，绝不改动）：
#   *REPORT*.TXT 含游戏脚本（Prestige:/Goto to/.....: if Victory），一译即坏；
#   *READ*ME*.txt 等为作者说明文档，非游戏文本。
SKIP_FILE_RE = re.compile(r"REPORT|READ[ _]?ME", re.I)
SHORT_MAX = 30                              # ≤30 字符视为短标签（整行加括号）

TOK = re.compile(r"%[sd]")


def load_map():
    m = {}
    with open(MAPFILE, encoding="utf-8-sig") as f:
        for ln, raw in enumerate(f, 1):
            s = raw.rstrip("\n")
            if not s.strip() or s.lstrip().startswith("#"):
                continue
            parts = s.split("\t")
            if len(parts) < 2:
                print(f"❌ 映射表第 {ln} 行格式错误：{s!r}"); sys.exit(1)
            m[parts[0]] = parts[1]
    return m


def load_numbers():
    """场景列表数字序号表：stem(小写) → (NN, entry)
    原理见 work/peg/build_scn_number.py。列表按显示名字节序排序，
    加 `NN ` 前缀即可把全部场景钉在最前、按序号排列（顺序可控）。
    ⚠️ 键统一转小写：SCN 与同名 _m.txt 的大小写常不一致。"""
    n = {}
    if not os.path.exists(NUMFILE):
        return n
    with open(NUMFILE, encoding="utf-8-sig") as f:
        for ln, raw in enumerate(f, 1):
            s = raw.rstrip("\n")
            if not s.strip() or s.lstrip().startswith("#"):
                continue
            p = s.split("\t")
            if len(p) < 3:
                continue
            try:
                n[p[0].lower()] = (p[1], int(p[2]))
            except ValueError:
                print(f"❌ 序号表第 {ln} 行格式错误：{s!r}"); sys.exit(1)
    return n


def load_long():
    """长段落整行译文表：原文 → 译文（译文内已含地名/人名的 (原文) 括注）"""
    m = {}
    if not os.path.exists(LONGFILE):
        return m
    with open(LONGFILE, encoding="utf-8-sig") as f:
        for ln, raw in enumerate(f, 1):
            s = raw.rstrip("\n")
            if not s.strip() or s.lstrip().startswith("#"):
                continue
            parts = s.split("\t")
            if len(parts) < 2 or not parts[0]:
                print(f"❌ 长表第 {ln} 行格式错误：{s!r}"); sys.exit(1)
            m[parts[0]] = parts[1]
    return m


SUFFIX = r"(?:i|m|u|l|bv|tv|v)"
STEM_TAIL = re.compile(r"(?i)(?:_%s$|(?<=[0-9])%s$)" % (SUFFIX, SUFFIX))


def stem_of(fn):
    """取场景词干：`ALMATY1_m.txt` → `almaty1`；`Vladivostok2i.TXT` → `vladivostok2`。
    ⚠️ 后缀**常常没有下划线**（`110bv.TXT`/`110l.TXT`），只认 `_xx$` 会漏剥 ⇒
       同场景继承与 `.scn` 查找双双失效（`faction_place_audit.py` 踩过同一个坑）。"""
    base = os.path.splitext(fn)[0]
    return STEM_TAIL.sub("", STEM_TAIL.sub("", base)).lower()


def load_scn_override():
    """按场景定点覆盖：`{(场景词干小写, 英文键): 译名}`。
    键既可以是映射表的短名，也可以是长段表的整行原文（长行优先命中长表）。"""
    ov = {}
    if not os.path.isfile(OVRFILE):
        return ov
    with open(OVRFILE, encoding="utf-8-sig") as f:
        for ln, raw in enumerate(f, 1):
            s = raw.rstrip("\n")
            if not s.strip() or s.lstrip().startswith("#") or s.split("\t")[0] == "en":
                continue
            c = s.split("\t")
            if len(c) < 4:
                print(f"⚠️ scn-place-override.tsv 第 {ln} 行字段不足，跳过：{s!r}")
                continue
            if c[1].strip().upper() != "PEG":       # 本文件只取 PEG 侧
                continue
            ov[(c[2].strip().lower(), c[0])] = c[3]
    return ov


def build_matcher(mp):
    """按原文长度降序的关键词表，用于长段落内嵌替换（最长优先、大小写敏感、词边界）"""
    keys = sorted(mp, key=len, reverse=True)
    return keys


def inline_replace(text, mp, keys, paren=True):
    """把行内的地名/专名替换为「译(原文)」（paren=False 则只出纯译）。
    最长优先、大小写敏感、词边界、不重复替换。"""
    out = []
    i, n = 0, len(text)
    while i < n:
        hit = None
        for k in keys:
            if len(k) < 3:            # 太短的键不做内嵌替换，避免误伤
                continue
            if text.startswith(k, i):
                # 词边界：前一个字符不能是字母（避免 xAlmaty 命中 Almaty）
                if i > 0 and (text[i-1].isalpha() or text[i-1] == "'"):
                    continue
                # 后一个字符不能是字母（避免 Almatyx 命中 Almaty）
                j = i + len(k)
                if j < n and text[j].isalpha():
                    continue
                hit = k
                break
        if hit:
            out.append(mp[hit] + ("(" + hit + ")" if paren else ""))
            i += len(hit)
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def translate_line(line, no_paren, mp, keys, lmp=None):
    """统一逻辑：整行命中优先；未命中则回退到行内替换。
    no_paren=True（M 地图地名 / U 单位名）⇒ 不加原文括号。

    ⚠️ 第 22 轮新增：**长段落整行命中 ⇒ 直接输出译文，不追加整段原文**
    （译文内已对「地名/人名」逐个加了 `(原文)`，见 各国军语风格口径.md §3.1）。"""
    if not line.strip():
        return line, False
    # ① 长段落/整句：整行命中（专用长表优先）
    if lmp is not None:
        t = lmp.get(line)
        if t is not None:
            return t, True                       # 直出，不加整段 (原文)
    t = mp.get(line)
    if t is not None:                            # ② 短标签整行命中 ⇒ 译(原文)
        if no_paren:
            return t, True
        return f"{t}({line})", True
    # ③ 未整行命中 → 行内替换（解决坐标行 `(00,33) #地名`、`BMP-2 Taliban` 等）
    new = inline_replace(line, mp, keys, paren=not no_paren)
    return new, new != line


def to_gbk(s):
    """把 cp1252 特殊标点转成 GBK 可编码的等价字符（否则整行编码失败）"""
    for k, v in (("\u2019", "'"), ("\u2018", "'"), ("\u201c", '"'), ("\u201d", '"'),
                 ("\u2013", "-"), ("\u2014", "--"), ("\u2026", "..."), ("\u00a0", " ")):
        s = s.replace(k, v)
    return s.encode("gbk")


def cmd_build(mp, keys, lmp, nmp=None, ovr=None):
    nmp = nmp or {}
    ovr = ovr or {}
    os.makedirs(OUTDIR, exist_ok=True)
    stats = collections.Counter()
    untranslated = []
    # ⚠️ 必须从【备份】读原文：游戏目录可能已被部署成中文（否则会「中文再翻一次」）
    for d in [os.path.join(BACKUP, s) for s in ("Scenario", "Userscen")]:
        if not os.path.isdir(d):
            continue
        sub = os.path.basename(d)
        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith(".txt"):
                continue
            p = os.path.join(d, fn)
            raw = open(p, "rb").read()
            if SKIP_FILE_RE.search(fn):        # 脚本/说明文档：原样拷贝
                od = os.path.join(OUTDIR, sub); os.makedirs(od, exist_ok=True)
                open(os.path.join(od, fn), "wb").write(raw)
                stats["跳过硬拷"] += 1; stats["文件"] += 1
                continue
            # ⚠️ 行尾可能是 CRLF / LF / **裸 CR**（引擎把 CR、LF 都当行尾）。
            #    必须三者都拆，否则裸 CR 文件会被当成「一行」⇒ 长表匹配失败 ⇒ 半中半英。
            EOL = re.compile(rb"(\r\n|\r|\n)")
            parts, seps = [], []
            pos = 0
            for m in EOL.finditer(raw):
                parts.append(raw[pos:m.start()]); seps.append(m.group(1)); pos = m.end()
            parts.append(raw[pos:])
            no_paren = bool(NO_PAREN_RE.search(os.path.splitext(fn)[0]))
            # ⭐ 按场景定点覆盖：把该词干的覆盖值并进**本文件生效的**映射/长段表
            #    （不动全局表 ⇒ 其它场景不受影响；空覆盖表时与覆盖前逐字节相同）
            st = stem_of(fn)
            eff_mp, eff_lmp, eff_keys = mp, lmp, keys
            if st:
                mo = {en: zh for (s, en), zh in ovr.items() if s == st}
                if mo:
                    eff_mp = dict(mp)
                    eff_lmp = dict(lmp)
                    for en, zh in mo.items():
                        if en in eff_lmp:
                            eff_lmp[en] = zh        # 长段整行原文 ⇒ 覆盖长表
                        else:
                            eff_mp[en] = zh         # 否则当映射表键
                    eff_keys = build_matcher(eff_mp)
                    stats["场景定点覆盖"] += 1
            outl = []
            for i, lb in enumerate(parts):
                try:
                    s = lb.decode("cp1252")
                except Exception:
                    outl.append(lb); continue
                if not s.strip():
                    outl.append(lb); continue
                new, changed = translate_line(s, no_paren, eff_mp, eff_keys, eff_lmp)
                if changed:
                    try:
                        outl.append(to_gbk(new))
                        stats["译"] += 1
                    except UnicodeEncodeError:
                        outl.append(lb); stats["编码失败"] += 1
                        untranslated.append((fn, s))
                else:
                    outl.append(lb)
                    stats["未译"] += 1
                    untranslated.append((fn, s))
            # ⭐ 场景名数字序号：`<stem>_m.txt` 的第 entry 行加 `NN ` 前缀
            #    ⇒ 列表按显示名字节序排 ⇒ 全部带序号项排最前、按序号排列（顺序可控）。
            #    ⚠️ SCN 与 _m.txt 的文件名**大小写常不一致**（如 ALMATY3.SCN ↔ Almaty3_m.txt），
            #       Windows 能对上，脚本必须**大小写不敏感**匹配。
            m = re.match(r"^(.*)_m$", os.path.splitext(fn)[0], re.I)
            if m and m.group(1).lower() in nmp:
                nn, ent = nmp[m.group(1).lower()]
                if 0 <= ent < len(outl):
                    outl[ent] = nn.encode("ascii") + b" " + outl[ent]
                    stats["加序号"] += 1
            # 逐段回插原行尾（保持 CRLF / LF / CR 原样）
            data = b""
            for i, piece in enumerate(outl):
                data += piece
                if i < len(seps):
                    data += seps[i]
            od = os.path.join(OUTDIR, sub)
            os.makedirs(od, exist_ok=True)
            open(os.path.join(od, fn), "wb").write(data)
            stats["文件"] += 1
    print(f"生成 {stats['文件']} 个文件 → {OUTDIR}")
    print(f"  译 {stats['译']} 行 / 未译 {stats['未译']} 行 / 编码失败 {stats['编码失败']} 行")
    up = os.path.join(ROOT, r"peg\testbed\_scn-untranslated.tsv")
    cnt = collections.Counter(s for _, s in untranslated)
    with open(up, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 场景文本未命中清单（原文串 → 出现文件数）\n次数\t原文\n")
        for s, n in cnt.most_common():
            f.write(f"{n}\t{s}\n")
    print(f"  未命中清单 → {up}（唯一串 {len(cnt)} 条）")
    return cnt


def cmd_deploy(mp, keys):
    bdir = os.path.join(BACKUP, "Scenario")
    udir = os.path.join(BACKUP, "Userscen")
    for d, bd in ((os.path.join(GAME, "Scenario"), bdir), (os.path.join(GAME, "Userscen"), udir)):
        if not os.path.isdir(d):
            continue
        if not os.path.isdir(bd):
            shutil.copytree(d, bd)
            print(f"已备份 {d} → {bd}")
    n = 0
    for d in SRC_DIRS:
        sub = os.path.basename(d)
        od = os.path.join(OUTDIR, sub)
        if not os.path.isdir(od):
            continue
        for fn in os.listdir(od):
            src = os.path.join(od, fn)
            dst = os.path.join(d, fn)
            if os.path.exists(dst):
                shutil.copy2(src, dst); n += 1
    print(f"已部署 {n} 个文件")


def cmd_verify(mp, keys):
    bad = 0
    for d in SRC_DIRS:
        sub = os.path.basename(d)
        bd = os.path.join(BACKUP, sub)
        if not os.path.isdir(bd):
            print(f"  （无备份 {bd}，跳过）"); continue
        for fn in sorted(os.listdir(bd)):
            if not fn.lower().endswith(".txt"):
                continue
            b = open(os.path.join(bd, fn), "rb").read()
            l = os.path.join(d, fn)
            if not os.path.exists(l):
                print(f"  ❌ 缺失 {fn}"); bad += 1; continue
            a = open(l, "rb").read()
            # 行数必须一致
            nb = len(b.split(b"\r\n")); na = len(a.split(b"\r\n"))
            if b.count(b"\r\n") == 0 and b.count(b"\n") > 0:
                nb = len(b.split(b"\n")); na = len(a.split(b"\n"))
            if nb != na:
                print(f"  ❌ 行数不一致 {fn}: 原 {nb} → 现 {na}"); bad += 1
    print(f"校验完成，异常 {bad} 个")


def cmd_restore():
    n = 0
    for sub in ("Scenario", "Userscen"):
        bd = os.path.join(BACKUP, sub)
        d = os.path.join(GAME, sub)
        if not os.path.isdir(bd):
            continue
        for fn in os.listdir(bd):
            shutil.copy2(os.path.join(bd, fn), os.path.join(d, fn)); n += 1
    print(f"已还原 {n} 个文件")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "restore":
        cmd_restore(); return
    mp = load_map()
    lmp = load_long()
    nmp = load_numbers()
    ovr = load_scn_override()
    keys = build_matcher(mp)
    print(f"映射表：{len(mp)} 条；其中 ≥3 字符（可内嵌替换）{sum(1 for k in keys if len(k)>=3)} 条")
    print(f"长段表：{len(lmp)} 条")
    print(f"序号表：{len(nmp)} 条")
    print(f"按场景定点覆盖：{len(ovr)} 条（{len({s for s, _ in ovr})} 个场景）")
    if cmd == "build":
        cmd_build(mp, keys, lmp, nmp, ovr)
    elif cmd == "deploy":
        cmd_deploy(mp, keys)
    elif cmd == "verify":
        cmd_verify(mp, keys)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
