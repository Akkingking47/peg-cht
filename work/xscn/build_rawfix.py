# -*- coding: utf-8 -*-
r"""汇总残槽译文 → 严校验 → 按 efile 切出 `rawfix --map` 用的映射表。

输入:
  work\xscn\residual-union.tsv        联合残槽（src freq efiles cand source）
  work\xscn\residual-manual-zh.tsv    本会话亲译的部队/杂项（src dst note）
  work\xscn\residual-titles-zh.tsv    标题（src dst efile）
  work\xscn\residual-chunks\chunk-NN.tsv   子代理输入（单列）
  work\xscn\residual-zh\part-NN.tsv        子代理输出（src<TAB>dst）

输出:
  work\comww2\comww2-xscn-rawfix.tsv
  work\atomic\atomic-xscn-rawfix.tsv
退出码非 0 = 校验未过，禁止落盘。
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LAT = re.compile(r"[A-Za-z]")
LATRUN = re.compile(r"[A-Za-z]+")
STRUCT = re.compile(r"[/\[\]()（）]")

# 结构符号数允许不一致的权威条目（label-keep 09-30 已定译法，跨层一致优先）
STRUCT_EXC = {
    "244 (Res) Flk Bn [GK Norw.]": "label-keep 把 (Res) 吸收为「预备」，属既定译法",
    "40 Pz Bn Zbv [GK Norw.]": "label-keep 增补「（特种用途）」注解 Zbv，属既定译法",
}


def rd_lines(p):
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        return f.read().replace("\r\n", "\n").split("\n")


def rd_simple(p):
    """两列 src->dst，跳过表头与空行。"""
    d = {}
    for i, ln in enumerate(rd_lines(p)):
        if i == 0 or not ln.strip():
            continue
        c = ln.split("\t")
        if len(c) >= 2:
            d[c[0]] = c[1]
    return d


def main():
    errs = []
    # 1) 联合表
    union = {}
    for i, ln in enumerate(rd_lines(os.path.join(HERE, "residual-union.tsv"))):
        if i == 0 or not ln.strip():
            continue
        c = ln.split("\t")
        union[c[0]] = {"freq": int(c[1]), "efiles": c[2].split("+"), "cand": c[3]}
    # 2) 已有译法 = 候选 + 亲译 + 标题（标题键属于 union 之外，单独收集）
    dst = {}
    for k, v in union.items():
        if v["cand"]:
            dst[k] = v["cand"]
    for p, nm in ((os.path.join(HERE, "residual-manual-zh.tsv"), "manual"),
                  (os.path.join(HERE, "residual-titles-zh.tsv"), "titles")):
        for k, v in rd_simple(p).items():
            if not v:
                errs.append("%s: %r 译文为空" % (nm, k))
            elif k in dst and dst[k] != v:
                errs.append("译法冲突 %r: %r vs %r（%s）" % (k, dst[k], v, nm))
            else:
                dst[k] = v
    # 3) 子代理产物：逐行对拍
    cdir = os.path.join(HERE, "residual-chunks")
    zdir = os.path.join(HERE, "residual-zh")
    parts = sorted(f for f in os.listdir(zdir) if f.startswith("part-") and f.endswith(".tsv"))
    if not parts:
        errs.append("没有任何 part-NN.tsv（子代理尚未交付）")
    for pf in parts:
        cf = os.path.join(cdir, pf.replace("part-", "chunk-"))
        if not os.path.exists(cf):
            errs.append("%s 无对应 %s" % (pf, os.path.basename(cf)))
            continue
        src_lines = [l for l in rd_lines(cf)]
        if src_lines and src_lines[-1] == "":
            src_lines.pop()
        out_lines = rd_lines(os.path.join(zdir, pf))
        if out_lines and out_lines[-1] == "":
            out_lines.pop()
        if len(out_lines) != len(src_lines):
            errs.append("%s 行数 %d != 输入 %d" % (pf, len(out_lines), len(src_lines)))
            continue
        for n, (a, b) in enumerate(zip(src_lines, out_lines), 1):
            c = b.split("\t")
            if len(c) != 2:
                errs.append("%s:%d 不是恰好 1 个 TAB: %r" % (pf, n, b[:60]))
                continue
            if c[0] != a:
                errs.append("%s:%d 原文列不符: %r != %r" % (pf, n, c[0][:50], a[:50]))
                continue
            if not c[1].strip():
                errs.append("%s:%d 译文为空: %r" % (pf, n, a[:50]))
                continue
            if a in dst and dst[a] != c[1]:
                errs.append("%s:%d 与既有译法冲突 %r: %r vs %r" % (pf, n, a[:40], dst[a], c[1]))
                continue
            if len(c) > 2:
                errs.append("%s:%d 多列" % (pf, n))
                continue
            dst[a] = c[1]
    # 3b) 本会话复核订正（覆盖子代理产物，可审计）
    ovp = os.path.join(HERE, "residual-overrides.tsv")
    if os.path.exists(ovp):
        for i, ln in enumerate(rd_lines(ovp)):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2 and c[0] in dst and dst[c[0]] != c[1]:
                print("   · 复核订正：%r: %r -> %r（%s）"
                      % (c[0], dst[c[0]], c[1], c[2] if len(c) > 2 else ""))
                dst[c[0]] = c[1]
    # 4) 覆盖性 + 内容校验
    need = [k for k, v in union.items() if not v["cand"]]
    missing = [k for k in need if k not in dst]
    if missing:
        errs.append("以下 %d 条仍无译文（前 20）：%s"
                    % (len(missing), " | ".join(missing[:20])))
    kept = []
    drop = set()
    for k, v in list(dst.items()):
        if "\t" in v or "\n" in v:
            errs.append("译文含制表/换行: %r" % k)
            continue
        if v != v.strip():
            errs.append("译文有首尾空格: %r" % k)
            continue
        if v == k:                      # 口径保留 ⇒ src==dst ⇒ rawfix 本就是 no-op
            kept.append(k)
            drop.add(k)
            continue
        # 允许的拉丁：dst 里的每一段拉丁都出自 src（被保留的代号，如 [RAF] / MAAF.ASC）
        bad = [t for t in LATRUN.findall(v) if t not in k]
        if bad:
            errs.append("译文含 src 之外的新拉丁字母 %s: %r -> %r" % (bad, k, v))
            continue
        try:
            v.encode("gbk")
        except UnicodeEncodeError:
            errs.append("译文 GBK 装不下: %r -> %r" % (k, v))
            continue
        if k not in STRUCT_EXC and len(STRUCT.findall(k)) != len(STRUCT.findall(v)):
            errs.append("结构符号数不符: %r(%d) -> %r(%d)"
                        % (k, len(STRUCT.findall(k)), v, len(STRUCT.findall(v))))
    for k in STRUCT_EXC:
        if k in dst:
            print("   · 结构例外（既定译法）：%s —— %s" % (k, STRUCT_EXC[k]))
    if kept:
        print("   · 口径保留（src==dst，不进映射表）：%d 条 %s" % (len(kept), kept))
    for k in drop:
        dst.pop(k, None)
    if errs:
        print("!! 校验未过，共 %d 条问题：" % len(errs))
        for e in errs[:60]:
            print("   " + e)
        return 1

    # 5) 按 efile 切表
    tag_of = {"ATOMIC": "atomic", "COMWW2": "comww2"}
    stat = {}
    for tag, sub in tag_of.items():
        rows = []
        for k, v in union.items():
            if tag in v["efiles"] and k in dst:
                rows.append((k, dst[k], v["freq"]))
        # 标题（键不在 union 里）
        for i, ln in enumerate(rd_lines(os.path.join(HERE, "residual-titles-zh.tsv"))):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 3 and c[2] == tag:
                rows.append((c[0], c[1], -1))
        outp = os.path.join(ROOT, "work", sub, "%s-xscn-rawfix.tsv" % sub)
        with io.open(outp, "w", encoding="utf-8", newline="\n") as f:
            f.write("src\tdst\tfreq\tkind\n")
            for k, v, n in sorted(rows, key=lambda x: (x[2] < 0, -x[2])):
                f.write("%s\t%s\t%d\t%s\n" % (k, v, max(n, 0), "TITLE" if n < 0 else "slot"))
        stat[tag] = (len(rows), sum(max(n, 0) for _k, _v, n in rows), sum(1 for x in rows if x[2] < 0))
        print("已写 %s（%d 条，覆盖 %d 槽，含标题 %d）" % (outp, stat[tag][0], stat[tag][1], stat[tag][2]))
    print("总计译文 %d 条；联合残槽 %d 条全部覆盖 ✓" % (len(dst), len(union)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
