#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 DOCS 汉化 · RTF 处理器（抽取 / 回写 / 校验）· **默认 dry-run**。

原理（**结构与控制字逐字节不动**）：
  1. 定位 `{\fonttbl…}` 与 `{\colortbl…}` 两个头部组，跳过不译；
  2. 其余部分**只切正文 run**：以「`\\` + 字母控制字」为界，
     每两个控制字之间的裸文本即一段；逐段决定是否可译；
  3. 可译段 → 抽取为 `_src/<rel>.tsv`；译文回写时**只替换该段文本**，
     并在段首插入 `\\fCJK` 字体切换（追加一个 `\\fcharset134` 字体条目，保证中文能显示）；
  4. 不可译段（纯符号/数字/表格分隔/`\\'xx` 转义块）原样不动。

安全：只替换段文本；**控制字、花括号、字体表、颜色表、字段域一律不触碰**（G2/G3 靠回读校验）。
用法：
  python doc_rtf.py extract "<rel>"     # 抽取
  python doc_rtf.py build   "<rel>" [--apply]
  python doc_rtf.py verify  "<rel>"
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
DOCS = r"D:\Program Files\PeG-WW2\DOCS"
OUTROOT = os.path.join(WS, "pegww2", "docs-zh")
SRCROOT = os.path.join(OUTROOT, "_src")
FILLROOT = os.path.join(OUTROOT, "_fill")
# ⭐ 英文原件**固定备份**：源只能从这里（或 `_staging`）取
ORIGROOT = os.path.join(WS, "backup", "ORIGINAL-PeGWW2-DOCS")


def resolve_source(rel):
    """⭐ 源取法：`_staging`（格式变更件）→ 否则**固定的英文原件备份**。

    ⚠️⚠️ **绝不读游戏目录**。踩过（真事故）：原实现是「`_staging` 优先，否则读 `DOCS`」，
    而投放之后游戏目录里已经是**中文** ⇒ 重建变成"拿中文再翻一次"：
    译表的改动全不生效，成品被中文原文回流污染。**投放过的项目必须钉住英文原件。**
    """
    stage = os.path.join(OUTROOT, "_staging", rel)
    if os.path.isfile(stage):
        return stage
    p = os.path.join(ORIGROOT, rel)
    if not os.path.isfile(p):
        raise SystemExit("✗ 找不到英文原件：%s（本工具不读游戏目录）" % p)
    raw = open(p, "rb").read()
    if b"{\\fCJK" in raw:
        raise SystemExit("✗ 源含 CJK 字体注入（%s）⇒ 是中文成品，拒绝构建" % p)
    return p

CJK_FONT = "SimSun"
# 删除哨兵：某段译文写成这个值 ⇒ 回写时该段**变为空**（用于「序数后缀 th/rd/st/nd 单独成段」这类
# 中文里没有对应成分的片段）。用哨兵而不是留空，是为了让「已译/未译」判定仍然明确。
DEL_SENTINEL = "[[DEL]]"
_CTRL = re.compile(r"\\([a-zA-Z]+)(-?\d+)?[ ]?")
_TRANSLATABLE = re.compile(r"[A-Za-z]{2,}")
# 不译的头部/元数据组（B 组 RTF 里还有样式表、文档信息、字段指令表等）
HEAD_GROUPS = {
    "fonttbl", "colortbl", "stylesheet", "info", "listtable", "listoverridetable",
    "rsidtbl", "generator", "latentstyles", "datastore", "mmathPr", "themedata",
    "colorschememapping", "xmlnstbl", "wgrffmtfilter", "pgptbl", "filetbl",
}
# 字段指令（超链接/引用）里的关键字，其所在文本段一律不译
FIELD_KW = ("HYPERLINK", "PAGEREF", "MERGEFORMAT", "REF ", "INCLUDEPICTURE", "TOC ")

# 保护串（与 doc_translate 同口径）：URL / 路径 / 带扩展名的文件名 / 版本号
PROTECT = [
    re.compile(r"https?://\S+"),
    re.compile(r"[A-Za-z]:\\[^\s\"'<>|]*"),
    re.compile(r"\b[A-Za-z0-9_.\-]+\.(?:exe|zip|rtf|pdf|txt|doc|xls|scn|map|cam|s16|eqp|dat|wav|avi|smk|mov|jpg|gif|ini|ply|tqp|bin)\b", re.I),
    re.compile(r"\b(?:SCENARIO|USERSCEN|DOCS|WAVS|CINE|MAP|SAVE|ALTEFILE)\\\S*", re.I),
    re.compile(r"\b\d+\.\d+[a-z]?\b"),
]


def protect(s):
    saved = []

    def sub(m):
        saved.append(m.group(0))
        return "\x01%d\x02" % (len(saved) - 1)
    out = s
    for pat in PROTECT:
        out = pat.sub(sub, out)
    return out, saved


def restore(s, saved):
    return re.sub(r"\x01(\d+)\x02", lambda m: saved[int(m.group(1))], s)


class _Tee:
    def __init__(self, *s):
        self.s = s

    def write(self, x):
        for t in self.s:
            t.write(x)
        return len(x)

    def flush(self):
        for t in self.s:
            t.flush()


_sink = io.StringIO()
sys.stdout = _Tee(sys.stdout, _sink)


def parse_off(raw):
    """解析 RTF，返回 (chunks, offs)：offs[i] = 该 chunk 在**原始字节流中的起始偏移**。

    ⚠️ 不能用「chunk 长度累加」求偏移：`\\'xx` 转义是 4 个原始字符 → 1 个字符，
       累加会漂移，导致按区间屏蔽 `{\\*…}` 时误判（曾因此漏掉一半 SmartTag 元数据）。
    """
    s = raw.decode("latin-1")
    chunks = []
    offs = []
    i = 0
    n = len(s)
    while i < n:
        start = i
        if s[i] == "\\":
            m = _CTRL.match(s, i)
            if m:
                chunks.append(("ctrl", m.group(0)))
                offs.append(start)
                i = m.end()
                continue
            if i + 1 < n and s[i + 1] in "\\{}":
                chunks.append(("ctrl", s[i:i + 2]))
                offs.append(start)
                i += 2
                continue
            if i + 2 < n and s[i + 1] == "'":           # \'xx 转义 → 还原成字符（cp1252），
                try:                                    # 否则重音字母会丢、URL 会被切碎
                    chunks.append(("text", bytes([int(s[i + 2:i + 4], 16)]).decode("cp1252")))
                except Exception:
                    chunks.append(("ctrl", s[i:i + 4]))
                offs.append(start)
                i += 4
                continue
            chunks.append(("ctrl", s[i]))
            offs.append(start)
            i += 1
            continue
        if s[i] in "{}":
            chunks.append(("ctrl", s[i]))
            offs.append(start)
            i += 1
            continue
        j = i
        while j < n and s[j] not in "\\{}":
            j += 1
        chunks.append(("text", s[i:j]))
        offs.append(start)
        i = j
    return chunks, offs


def parse(raw):
    return parse_off(raw)[0]


def star_spans(s):
    """返回所有 RTF「可忽略目标组」`{\\*…}` 的**字节区间** [(start,end)]（花括号配平）。

    ⚠️ 为什么要按区间而不是改词法：改词法会**改变段号空间**，而段号是「抽取↔回写」两侧的键约定，
       一变就毁掉既有译稿（同 W21 教训）。按区间屏蔽既不动键，又能把 SmartTag/factoid 元数据排除在翻译之外。
    """
    spans = []
    i = 0
    n = len(s)
    while i < n:
        if s.startswith("{\\*", i):
            depth = 0
            j = i
            while j < n:
                if s[j] == "\\":
                    j += 2
                    continue
                if s[j] == "{":
                    depth += 1
                elif s[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            spans.append((i, min(j + 1, n)))
            i = j + 1
            continue
        i += 1
    return spans


def mask_heads(chunks, raw=None):
    """标记不可译的 text 段：① 头部/元数据组内 ② `\\fldinst` 字段指令组内。

    ⚠️ B 组 RTF 含 `{\\stylesheet…}`（Normal;/heading 1; 等样式名）与 `{\\info…}`（作者/标题），
       以及超链接域 `{\\field{\\*\\fldinst HYPERLINK "http://…"}}` —— 前两类必须整体跳过，
       字段指令里的 URL 更不许译。
    """
    keep = [True] * len(chunks)
    depth = 0
    head_depth = None
    fld_depth = None
    star_depth = None
    for idx, (k, t) in enumerate(chunks):
        if k == "ctrl" and t == "{":
            depth += 1
        elif k == "ctrl" and t == "}":
            if head_depth is not None and depth == head_depth:
                head_depth = None
            if fld_depth is not None and depth == fld_depth:
                fld_depth = None
            if star_depth is not None and depth == star_depth:
                star_depth = None
            depth -= 1
            continue
        if k == "ctrl" and t == "\\*":
            star_depth = depth       # RTF「可忽略目标组」：`{\*\…}` 内的文本一律不译
        if k == "ctrl" and t.startswith("\\"):
            name = re.match(r"\\([a-zA-Z]+)", t)
            nm = name.group(1) if name else ""
            if nm in HEAD_GROUPS and head_depth is None:
                head_depth = depth             # `{` 已先计数 ⇒ 组内容就在当前深度
            if nm == "fldinst":
                fld_depth = depth
        if head_depth is not None and depth >= head_depth:
            if k == "text":
                keep[idx] = False
        if fld_depth is not None and depth >= fld_depth:
            if k == "text":
                keep[idx] = False
        if star_depth is not None and depth >= star_depth:
            if k == "text":
                keep[idx] = False
    # ② 按字节区间屏蔽 `{\*…}`（不改词法：段号空间保持不变）
    if raw is not None:
        spans = star_spans(raw.decode("latin-1"))
        if spans:
            _, offs = parse_off(raw)
            for idx, (k, t) in enumerate(chunks):
                if k == "text" and idx < len(offs) and any(a <= offs[idx] < b for a, b in spans):
                    keep[idx] = False
    return keep


def insert_cjk_font(buf):
    """在 `{\\fonttbl…}` 组内末尾（**该组自身深度**的最后一个 `;` 之后）追加 CJK 字体条目；幂等。

    ⚠️ 坑：RTF 里组以控制字开头（`{\\fonttbl{...}}`）时，子组也以 `{` 开始，
       故「一个 `\\ctrl{` 序列应只算 1 层」——否则深度会多算一层。
    """
    if CJK_FONT in buf:
        return buf, True
    i = buf.find("\\fonttbl")
    if i < 0:
        return buf, False
    # 若控制字后紧跟 '{'，说明该 '{' 属于同一个组（不单独计层）
    merged_open = (i + len("\\fonttbl") < len(buf) and buf[i + len("\\fonttbl")] == "{")
    depth = 0
    j = i
    last_semi = -1
    while j < len(buf):
        c = buf[j]
        if c == "\\":
            j += 2
            continue
        if c == "{":
            if not (j == i + len("\\fonttbl") and merged_open):
                depth += 1
        elif c == "}":
            depth -= 1
            if depth < 0:
                break
        elif c == ";" and depth == 0:
            last_semi = j
        j += 1
    if last_semi < 0:
        return buf, False
    entry = "{\\fCJK\\fnil\\fcharset134 " + CJK_FONT + ";}"
    return buf[:last_semi + 1] + entry + buf[last_semi + 1:], True


def escape_rtf_text(s):
    """把**文本内容**里的 RTF 结构字符转义（控制字不要经过这里）。

    `\\`→`\\\\`　`{`→`\\{`　`}`→`\\}`
    ⚠️ 只对文本内容调用；曾误施于整个缓冲区 ⇒ 连控制字都被转义、成品全部坏掉。
    """
    return s.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def to_rtf_bytes(s):
    """把 (可能含中文的) 字符串编码成 RTF 字节流（**只做字符编码，不做结构转义**）。

    ⚠️ 绝不能用 `latin-1, "replace"` —— 那会把**所有中文变成 `?`**（曾差点铸成大错）。
    结构字符（`\\` `{` `}`）的转义见 `escape_rtf_text()`，必须**只对文本内容**做。
    规则（**尽量保持与原文件同形**，未改动处字节不变）：
      · ASCII            → 原样
      · 能映回 cp1252 单字节 → 该字节原本来自 `\\'xx` 转义的就写回 `\\'xx`；来自裸高字节的就写裸字节
      · 其它（如中文）    → `\\uN?`（N 为 16 位有符号）
    """
    out = bytearray()
    for ch in s:
        o = ord(ch)
        if o < 0x80:
            out.append(o)
            continue
        if o <= 0xFF:
            out.append(o)            # 原文件里的裸字节（含 0x80–0x9F）按原样写回
            continue
        raw = None
        try:
            b = ch.encode("cp1252")
            if len(b) == 1:
                raw = b[0]
        except Exception:
            raw = None
        if raw is None:
            n = o if o <= 0xFFFF else 0x3F
            if n > 0x7FFF:
                n -= 0x10000
            out += ("\\u%d?" % n).encode("ascii")
        elif 0x80 <= raw <= 0x9F:
            out += ("\\'%02x" % raw).encode("ascii")   # cp1252 特殊区（如 U+201C）写回 `\'xx` 原形
        else:
            out.append(raw)
    return bytes(out)


def eligible(chunks, keep, i):
    """段 i 是否「可译」——**单一真源**：抽取、回写、校验、切片脚本都调它，避免两侧口径漂移。"""
    k, t = chunks[i]
    if k != "text" or not keep[i]:
        return False
    t2 = re.sub(r" {2,}", " ", re.sub(r"[\r\n\t]+", " ", t).strip())
    if not t2 or not _TRANSLATABLE.search(t2):
        return False
    if re.fullmatch(r"[\s;:,.\-]*", t2):
        return False
    if any(kw in t2.upper() for kw in FIELD_KW):
        return False
    return True


def eligible_ids(rel):
    """给定相对路径，返回可译段号集合。"""
    raw = open(resolve_source(rel), "rb").read()
    chunks = parse(raw)
    keep = mask_heads(chunks, raw)
    return {i for i in range(len(chunks)) if eligible(chunks, keep, i)}


def do(rel, mode):
    # ⭐ 源文件解析：`_staging`（如 .doc→.rtf 转换产物）优先，否则**英文原件备份**
    #    —— 暂存用于「原件不许改、但需要换格式才能处理」的场景（D4 的 .doc）
    #    ⚠️ 绝不读游戏目录（投放后那里已是中文）
    raw = open(resolve_source(rel), "rb").read()
    chunks = parse(raw)
    keep = mask_heads(chunks, raw)
    src_tsv = os.path.join(SRCROOT, rel + ".tsv")
    fill_tsv = os.path.join(FILLROOT, rel + ".tsv")

    if mode == "extract":
        rows = []
        for i, (k, t) in enumerate(chunks):
            if k != "text" or not keep[i]:
                continue
            # RTF 里控制字后的换行不显示；段内换行/制表一律折叠成单空格（避免破坏 TSV，且 RTF 空白不参与排版）
            t2 = re.sub(r"[\r\n\t]+", " ", t).strip()
            t2 = re.sub(r" {2,}", " ", t2)
            if not t2 or not _TRANSLATABLE.search(t2):
                continue
            if any(kw in t2.upper() for kw in FIELD_KW):
                continue                       # 字段指令残留一律不译
            if re.fullmatch(r"[\s;:,.\-]*", t2):
                continue
            pr, saved = protect(t2)            # ⭐ 保护串 → 占位符
            rows.append((i, t2, pr, saved))
        os.makedirs(os.path.dirname(src_tsv), exist_ok=True)
        os.makedirs(os.path.dirname(fill_tsv), exist_ok=True)
        with open(src_tsv, "w", encoding="utf-8", newline="\n") as f:
            f.write("# %s · RTF 抽取（段号 \t 原文；段号=chunk 序号，回写按它定位）\n" % rel)
            f.write("# 保护串（URL/文件名/版本号）已替换为 \\x01N\\x02，译文里原样保留即可\n")
            f.write("段号\t原文\tprotected\n")
            for i, t, pr, saved in rows:
                f.write("%d\t%s\t%s\n" % (i, t.replace("\t", "\\t"), pr.replace("\t", "\\t")))
        if not os.path.isfile(fill_tsv):
            with open(fill_tsv, "w", encoding="utf-8", newline="\n") as f:
                f.write("# %s · 译文填写表：只改第三列（译文）\n" % rel)
                f.write("段号\t原文\t译文\n")
                for i, t, pr, saved in rows:
                    f.write("%d\t%s\t\n" % (i, t.replace("\t", "\\t")))
        print("  [extract] %-56s 可译段 %3d → %s" % (rel[:56], len(rows), os.path.relpath(src_tsv, WS)))
        return len(rows)

    # build / verify
    tr = {}
    for l in open(fill_tsv, encoding="utf-8"):
        if not l.strip() or l.startswith("#") or l.startswith("段号"):
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) >= 3 and c[0].strip().isdigit() and c[2].strip():
            tr[int(c[0])] = c[2]

    # 逐段重算「原文 → 保护串清单」，回写时还原占位符
    def norm(t):
        return re.sub(r" {2,}", " ", re.sub(r"[\r\n\t]+", " ", t).strip())

    def eligible(i, t):
        if not keep[i] or not _TRANSLATABLE.search(t):
            return False
        t2 = norm(t)
        if not t2 or re.fullmatch(r"[\s;:,.\-]*", t2):
            return False
        if any(kw in t2.upper() for kw in FIELD_KW):
            return False
        return True

    saved_map = {}
    for i, (k, t) in enumerate(chunks):
        if k == "text" and eligible(i, t):
            _, saved = protect(norm(t))
            saved_map[i] = saved
    missing = sum(1 for i in saved_map if i not in tr)
    ignored = [i for i in tr if i not in saved_map]      # 曾误译、现已不可译的段（如 SmartTag 元数据）
    out = []
    for i, (k, t) in enumerate(chunks):
        if k == "text" and i in tr and i in saved_map:
            txt = tr[i]
            if txt.strip() == DEL_SENTINEL:
                out.append(("text", ""))          # 哨兵 ⇒ 该段在成品里为空
                continue
            if saved_map[i]:
                txt = restore(txt, saved_map[i])
            out.append(("ctrl", "\\fCJK "))       # ⭐ 字体切换是**控制字**，不能当文本转义
            out.append(("text", txt))
        else:
            out.append((k, t))
    # ⚠️⚠️ **按类型编码**：控制字原样，只有**文本内容**才做结构字符转义（`\`→`\\` `{`→`\{` `}`→`\}`）。
    #      曾把转义施加到整个缓冲区 ⇒ 连 `\rtf1`/`\fonttbl` 都被写成 `\\rtf1`/`\\fonttbl`，
    #      **31 份成品全部不是合法 RTF**（Word 打不开）——而按"写出的 chunk 序列"做的校验**看不出来**。
    buf_b = bytearray()
    for k, t in out:
        if k == "ctrl":
            buf_b += t.encode("latin-1", "replace")
        else:
            buf_b += to_rtf_bytes(escape_rtf_text(t))
    buf = buf_b.decode("latin-1")
    # 真·插入字体条目（平衡花括号定位，幂等）
    if tr:
        buf, ok = insert_cjk_font(buf)
        if not ok:
            print("  ⚠️ 未找到 fonttbl，未插入 CJK 字体（中文可能显示为方框）")
    if mode == "verify":
        # ⭐ 判据三层：① **文本段逐位对齐**（译段比译文、未译段必须与原文一致）
        #              ② **控制字序列**（去掉自插的 `\fCJK `）必须与原文一致
        #              ③ **编码后真实字节的头部与花括号数**（这才抓得住"连控制字都被转义"这类结构性灾难）
        diffs = []
        old_text = [t for k, t in chunks if k == "text"]
        new_text = [t for k, t in out if k == "text"]
        if len(old_text) != len(new_text):
            diffs.append((-1, "文本段数 %d→%d" % (len(old_text), len(new_text))))
        else:
            j = 0
            for i, (k, t) in enumerate(chunks):
                if k != "text":
                    continue
                nt = new_text[j]
                j += 1
                if i in tr and i in saved_map:
                    if tr[i].strip() == DEL_SENTINEL:
                        if nt != "":
                            diffs.append((i, "哨兵段非空"))
                        continue
                    exp = restore(tr[i], saved_map[i]) if saved_map[i] else tr[i]
                    if nt != exp:
                        diffs.append((i, "译文不符"))
                    continue
                if nt != t:
                    diffs.append((i, "%r→%r" % (t[:24], nt[:24])))
        old_ctrl = [t for k, t in chunks if k == "ctrl"]
        new_ctrl = [t for k, t in out if k == "ctrl" and t != "\\fCJK "]
        ctrl_ok = old_ctrl == new_ctrl
        enc = b"".join((t.encode("latin-1", "replace") if k == "ctrl" else to_rtf_bytes(escape_rtf_text(t)))
                       for k, t in out)
        if tr:
            enc2, _ = insert_cjk_font(enc.decode("latin-1"))
            enc = enc2.encode("latin-1", "replace")
        src_bytes = raw
        head_ok = enc.startswith(b"{\\rtf1") and src_bytes.startswith(b"{\\rtf1")
        brace_ok = enc.count(b"{") - src_bytes.count(b"{") == (1 if tr else 0)
        eng = [(i, t) for i, (k, t) in enumerate(chunks) if k == "text" and i in tr
               and tr[i].strip() != DEL_SENTINEL
               and not re.search(r"[\u4e00-\u9fff]", tr[i])]
        ok = (not diffs) and ctrl_ok and head_ok and brace_ok
        print("  [verify ] %-56s 结构 %s · 段级差异 %d · 控制字 %s · 头部 %s · 花括号 %s · 待译 %d · 疑未译 %d" % (
            rel[:56], "✅" if ok else "❌", len(diffs),
            "✅" if ctrl_ok else "❌", "✅" if head_ok else "❌",
            "✅" if brace_ok else "❌", missing, len(eng)))
        for i, d in diffs[:6]:
            print("        ⚠️ 段%d 差异: %s" % (i, d))
        for i, t in eng[:6]:
            print("        ⚠️ 疑未译: 段%d %r" % (i, t[:56]))
        return len(diffs) + (0 if ctrl_ok else 50) + (0 if head_ok and brace_ok else 99)
    if "--apply" not in sys.argv:
        print("  [build  ] %-56s 待写 %d 段（dry-run；加 --apply）" % (rel[:56], len(tr)))
        return 0
    dst = os.path.join(OUTROOT, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "wb") as f:
        f.write(to_rtf_bytes(buf))
    back = open(dst, "rb").read()
    print("  [build  ] %-56s 已写 %s（%d B）" % (rel[:56], os.path.relpath(dst, WS), len(back)))
    return 0


def main():
    mode = sys.argv[1]
    arg = sys.argv[2]
    BATCHES = {
        "D2": [
            r"1st SS Leibstandarte Division\PeGWW2 LSSAH Campaign Install.rtf",
            r"Band of Brothers\PeG-WW2 BoB Campaign Install.rtf",
            r"Blitzkrieg Objective France\PeG-WW2 FI Campaign Install.rtf",
            r"Boot of Death\PeG-WW2 IT Campaign Install.rtf",
            r"British Campaign in Europe\PeG-WW2 WD Campaign Install.rtf",
            r"Das Reich\PeGWW2 DR Campaign Install.rtf",
            r"Deutsches Afrika Korps\PeG-WW2 DAK Campaign Install.rtf",
            r"For Stalin and Motherland\PeG WWII ZS campaign install.rtf",
            r"Germany at War\PeGWW2 GAW Campaign Install.rtf",
            r"Mediterranean 46\PeGWW2 LH_Ger46Med Campaign Install.rtf",
            r"Operation Sealion\PeG-WW2 SL Campaign Install.rtf",
            r"Red Alert\PeGWW2 RA Campaign Install.rtf",
            r"Red Menace (German side)\PeGWW2 RG Campaign Install.rtf",
            r"Red Menace\PeGWW2 RM Campaign Install.rtf",
            r"Red World Order\PeG-WW2 S00 Campaign Install.rtf",
            r"Reich Defence\PeGWW2 B7 Campaign Install.rtf",
            r"Road to Berlin\PeG WWII RTB campaign install.rtf",
            r"Romanian Struggle\PeG-WW2 R7 Campaign Install.rtf",
            r"The 7 PzrArmee defends the Reich\PeGWW2 7Pzr Campaign Install.rtf",
            r"The Gallantry of the 7 PzrArmee\PeGWW2 G7Pzr Campaign Install.rtf",
        ],
        "D3": [
            r"British Campaign in Europe\BCampaign Information.rtf",
            r"Reich Defence\PG2_RDCampaign Information.rtf",
            r"Reich Defence\PG2_Reich Defense Campaign Evaluation.rtf",
            r"Road to Berlin\PG2 RTB Campaign Information J Gabitto.rtf",
            r"Romanian Struggle\PG2_RomCampaign Information.rtf",
            r"Romanian Struggle\PG2_RomCampaignEvaluation.rtf",
        ],
        # D4：6 份 .doc 先由 Word COM 转成 .rtf 放进 _staging（**原件零改动**），再走同一 RTF 管线
        "D4": [
            r"Blitzkrieg Objective France\readme.rtf",
            r"Boot of Death\Readme.rtf",
            r"For Stalin and Motherland\PG2_Readme.rtf",
            r"Red World Order\readme_PG2.rtf",
            r"The 7 PzrArmee defends the Reich\PG2_DA7Camp.rtf",
            r"The Gallantry of the 7 PzrArmee\PG2_DA7Camp.rtf",
        ],
    }
    files = BATCHES.get(arg, [arg])
    rc = 0
    for rel in files:
        rc = max(rc, do(rel, mode))
    return rc


if __name__ == "__main__":
    rc = main()
    os.makedirs(OUTROOT, exist_ok=True)
    with open(os.path.join(OUTROOT, "_rtf-log.txt"), "a", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
    sys.exit(rc)
