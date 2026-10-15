#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 DOCS 汉化 · 通用工具（抽取 / 回写 / 校验），**默认 dry-run**。

设计要点（与游戏文本层的关键区别）：
  · 文档不是"整行查表"，而是**段落抽取 → 人工/子代理翻译 → 原结构回写**
  · **保护串**（文件名/路径/URL/版本号/按钮名）在抽取阶段替换为占位符 `\x01N\x02`，
    回写时还原 ⇒ 保证它们**逐字节不变**（G3 检验）
  · 支持格式：.txt（行=段）· .rtf（正文 run=段，保留全部控制字与字体表）
  · 编码：TXT 出稿 **UTF-8 with BOM**（Windows 记事本/写字板可读；原件零改动，译文另存）

用法：
  python doc_translate.py extract <D1|file...>    # 抽取 → docs-zh/_src/<rel>.tsv
  python doc_translate.py build   <D1|file...>    # 回写 → docs-zh/<rel>（--apply 才落盘）
  python doc_translate.py verify  <D1|file...>    # 五道校验
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
DOCS = r"D:\Program Files\PeG-WW2\DOCS"
OUTROOT = os.path.join(WS, "pegww2", "docs-zh")
# ⭐ 英文原件**固定备份**：源只能从这里（或 `_staging`）取
ORIGROOT = os.path.join(WS, "backup", "ORIGINAL-PeGWW2-DOCS")


def resolve_source(rel):
    """⭐ 源取法：`_staging`（格式变更件）→ 否则**固定的英文原件备份**。

    ⚠️⚠️ **绝不读游戏目录**。踩过（真事故）：原实现是「`_staging` 优先，否则读 `DOCS`」，
    而投放之后游戏目录里已经是**中文** ⇒ 重建变成"拿中文再翻一次"：译表改动全不生效，
    成品被中文原文回流污染。**投放过的项目必须钉住英文原件。**
    """
    stage = os.path.join(OUTROOT, "_staging", rel)
    if os.path.isfile(stage):
        return stage
    p = os.path.join(ORIGROOT, rel)
    if not os.path.isfile(p):
        raise SystemExit("✗ 找不到英文原件：%s（本工具不读游戏目录）" % p)
    raw = open(p, "rb").read()
    if raw.startswith(b"\xef\xbb\xbf"):        # 带 BOM 的 UTF-8 ⇒ 多为我方产物
        raise SystemExit("✗ 源是带 BOM 的 UTF-8（%s）⇒ 疑似成品，拒绝构建" % p)
    return p
SRCROOT = os.path.join(OUTROOT, "_src")
FILLROOT = os.path.join(OUTROOT, "_fill")

# ⭐ D1..D5 批次清单（相对 DOCS 的路径）
BATCHES = {
    "D1": [
        "PeG-WW2 2.7 Read Me.txt",
        "PeG-WW2 2.7 Update.txt",
        "New Videos for PeGWWII.txt",
        "LG_shp2s16_ReadMe.txt",
        "Manual.rtf",
    ],
}

_sink = io.StringIO()


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


sys.stdout = _Tee(sys.stdout, _sink)

# ---------- 保护串 ----------
# ⚠️ 只保护**无歧义**的串（带扩展名的文件名 / 路径 / URL / 版本号 / 明确的程序名）。
#    曾用裸词 `NAMES` ⇒ 把散文里的 "names" 也保护了（假阳性），译者正常译成「名称」反而被判"保护串丢失"。
PROTECT = [
    re.compile(r"https?://\S+"),
    re.compile(r"[A-Za-z]:\\[^\s\"'<>|,.;:)\]}]*"),   # 盘符路径（不含尾部标点，否则会把「。」「）」也吃进保护串）
    re.compile(r"\b[A-Za-z0-9_.\-]+\.(?:exe|zip|rtf|pdf|txt|doc|xls|scn|map|cam|s16|eqp|dat|wav|avi|smk|mov|jpg|gif|ini|ply|tqp|bin)\b", re.I),
    re.compile(r"\b(?:SCENARIO|USERSCEN|DOCS|WAVS|CINE|MAP|SAVE|ALTEFILE)\\\S*", re.I),
    re.compile(r"\b\d+\.\d+[a-z]?\b"),                          # 版本号 2.7c / 1.02d
    re.compile(r"\b(?:EQUIP97|MODGEN|PEOPLES|WW2GEN|WW2GUI|WW2MISC|WW2TIPS|WW2-EQP|GUI97|MISC97|TIPS97|BUTTONS|INFOICON|START)\b"),
]


def protect(s):
    """返回 (带占位符的串, [(占位符, 原文), ...])"""
    saved = []

    def sub(m):
        saved.append(m.group(0))
        return "\x01%d\x02" % (len(saved) - 1)
    out = s
    for pat in PROTECT:
        out = pat.sub(sub, out)
    return out, saved


def restore(s, saved):
    def sub(m):
        i = int(m.group(1))
        return saved[i] if 0 <= i < len(saved) else m.group(0)   # 越界则原样保留，不炸
    return re.sub(r"\x01(\d+)\x02", sub, s)


# 哨兵：译文写成它 ⇒ 该行**保留原文**（用于文件名/URL/拉丁专名这类"无需翻译"的行）。
# 用哨兵而不是留空，是为了让「已译/未译」判定明确区分"有意保留"与"还没做"。
KEEP_SENTINEL = "[[KEEP]]"


# ---------- TXT ----------
def txt_split(raw):
    """按 CRLF/CR/LF 三态切，保留分隔符 —— 回写时逐字节还原。"""
    parts = re.split(rb"(\r\n|\r|\n)", raw)
    return parts[0::2], parts[1::2]


def do_txt(path, rel, mode):
    # ⭐ 暂存目录优先（原件无法直接处理、需换格式的场景，如 Word 打不开的 .doc → .txt），
    #    否则**英文原件备份**；⚠️ 绝不读游戏目录（投放后那里已是中文）
    raw = open(resolve_source(rel), "rb").read()
    lines, seps = txt_split(raw)
    src_tsv = os.path.join(SRCROOT, rel + ".tsv")
    fill_tsv = os.path.join(FILLROOT, rel + ".tsv")
    if mode == "extract":
        rows, n = [], 0
        for i, ln in enumerate(lines):
            t = ln.decode("cp1252")
            if not t.strip() or not re.search(r"[A-Za-z]", t):
                continue
            pr, saved = protect(t)
            n += 1
            rows.append((i, t, pr, saved))
        os.makedirs(os.path.dirname(src_tsv), exist_ok=True)
        os.makedirs(os.path.dirname(fill_tsv), exist_ok=True)
        import json
        with open(src_tsv, "w", encoding="utf-8", newline="\n") as f:
            f.write("# %s · TXT 抽取（行号 \t 原文 \t 含占位符 \t 保护串清单）\n" % rel)
            f.write("# 保护串已替换为 \\x01N\\x02；译文写回 _fill 的同名文件（占位符原样保留，或直接写回原串也可）\n")
            f.write("行号\t原文\tprotected\t保护串\n")
            for i, t, pr, saved in rows:
                f.write("%d\t%s\t%s\t%s\n" % (i, t.replace("\t", "\\t"), pr.replace("\t", "\\t"),
                                              json.dumps(saved, ensure_ascii=False).replace("\t", "\\t")))
        if not os.path.isfile(fill_tsv):
            with open(fill_tsv, "w", encoding="utf-8", newline="\n") as f:
                f.write("# %s · 译文填写表：只改第三列（译文），其余别动\n" % rel)
                f.write("行号\t原文\t译文\n")
                for i, t, pr, saved in rows:
                    f.write("%d\t%s\t\n" % (i, t.replace("\t", "\\t")))
        print("  [extract] %-58s 可译行 %3d → %s" % (rel[:58], n, os.path.relpath(src_tsv, WS)))
        return n
    # build / verify
    import json
    # ⭐ 保护串清单**以 _src 表为准**（不重算）——否则改一次 PROTECT 就会让旧译文的占位符错位
    saved_map = {}
    if os.path.isfile(src_tsv):
        for l in open(src_tsv, encoding="utf-8"):
            if l.startswith("#") or l.startswith("行号"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 4 and c[0].strip().isdigit():
                try:
                    saved_map[int(c[0])] = json.loads(c[3].replace("\\t", "\t"))
                except Exception:
                    saved_map[int(c[0])] = []
    fills = {}
    with open(fill_tsv, encoding="utf-8") as f:
        for l in f:
            if not l.strip() or l.startswith("#") or l.startswith("行号"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 3 and c[0].strip().isdigit():
                fills[int(c[0])] = c[2]
    missing = [i for i in range(len(lines)) if lines[i].strip() and re.search(r"[A-Za-z]", lines[i].decode("cp1252")) and not fills.get(i, "").strip()]
    out = []
    for i, ln in enumerate(lines):
        if i in fills and fills[i].strip():
            if fills[i].strip() == KEEP_SENTINEL:      # 哨兵 ⇒ 保留原文
                out.append(ln)
                continue
            t = ln.decode("cp1252")
            saved = saved_map.get(i) or protect(t)[1]
            lead = t[:len(t) - len(t.lstrip())]
            trail = t[len(t.rstrip()):]
            new = lead + restore(fills[i], saved) + trail
            out.append(new.encode("utf-8-sig" if i == 0 else "utf-8"))
        else:
            out.append(ln)
    buf = bytearray()
    for i, seg in enumerate(out):
        buf += seg
        if i < len(seps):
            buf += seps[i]
    if mode == "verify":
        # G1 行数一致 / G3 保护串零漂移 / G5 残留整段英文
        # ⭐ G3 判据：把译文（含占位符或直接写的原串）还原成最终文本后，
        #    每个保护串都必须**出现在其中**——这样译者「保留占位符」或「直接写回原串」都算通过。
        bad = []
        for i in fills:
            if not fills[i].strip():
                continue
            if fills[i].strip() == KEEP_SENTINEL:
                continue          # 哨兵 ⇒ 该行原样保留原文，保护串必然在
            t = lines[i].decode("cp1252")
            saved = saved_map.get(i) or protect(t)[1]
            final = restore(fills[i], saved)
            for s in saved:
                if s not in final:
                    bad.append((i + 1, s))
        english = [(k + 1, fills[k]) for k in sorted(fills)
                   if fills[k].strip() and fills[k].strip() != KEEP_SENTINEL
                   and not re.search(r"[\u4e00-\u9fff]", fills[k])
                   and not re.fullmatch(r"[\x01\x02\d\s\-=*_/\\|.:()\[\]<>+&%#@!?'\",;]*", fills[k])]
        print("  [verify ] %-58s 行数 %s · 保护串漂移 %d · 待译 %d · 疑未译 %d" % (
            rel[:58], "✅" if len(out) == len(lines) else "❌", len(bad), len(missing), len(english)))
        for i, s in bad[:5]:
            print("        ⚠️ 行%d 保护串丢失: %r" % (i, s))
        for ln, tx in english[:8]:
            print("        ⚠️ 疑未译: 行%d %r" % (ln, tx[:60]))
        return len(bad) + len(missing)
    if "--apply" not in sys.argv:
        print("  [build  ] %-58s 待写 %d 段（dry-run，未落盘；加 --apply）" % (rel[:58], len(fills)))
        return 0
    dst = os.path.join(OUTROOT, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "wb") as f:
        f.write(bytes(buf))
    back = open(dst, "rb").read()
    print("  [build  ] %-58s 已写 %s（%d B）回读 %s" % (
        rel[:58], os.path.relpath(dst, WS), len(back), "✅" if back == bytes(buf) else "❌"))
    return 0


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "extract"
    args = [a for a in sys.argv[2:] if not a.startswith("-")]
    if not args:
        args = ["D1"]
    files = []
    for a in args:
        files += BATCHES.get(a, [a])
    print("=" * 104)
    print("DOCS 汉化工具  mode=%s  共 %d 个文件" % (mode, len(files)))
    print("=" * 104)
    for rel in files:
        ext = os.path.splitext(rel)[1].lower()
        if ext == ".txt":
            do_txt(None, rel, mode)
        else:
            print("  [skip   ] %-58s （%s 待专用处理器）" % (rel[:58], ext))
    return 0


if __name__ == "__main__":
    rc = main()
    os.makedirs(OUTROOT, exist_ok=True)
    with open(os.path.join(OUTROOT, "_tool-log.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
    sys.exit(rc)
