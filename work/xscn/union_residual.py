# -*- coding: utf-8 -*-
r"""合并 ATOMIC + COMWW2 的残槽清单为一张「联合待译表」，保证跨 efile 同名地名的译法一致。

用法: python union_residual.py ATOMIC COMWW2

输出:
  work\xscn\residual-union.tsv      src  freq  efiles  cand  source
  work\xscn\residual-chunks\chunk-NN.tsv   单列（仅「无既有译法」的行，按 N 均分）
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
NCHUNK = int(os.environ.get("NCHUNK", "6"))
PREFIX = os.environ.get("PREFIX", "")            # 输出文件名前缀（多批次互不覆盖）
SPLIT_UNIT = os.environ.get("SPLIT_UNIT", "1") != "0"   # 是否把部队/番号类剔出交本会话

# 部队番号/编制类（含歧义缩写、杂项）—— 不交子代理，由本会话按 POLICY.md 亲自处理
UNIT_RE = re.compile(
    r"(Division|Div\.|\bDiv\b|Brig|Batt|\bBn\b|Reg\.|\bReg\b|Abt|Korps|Army|Corps|Wing|HQ|"
    r"Pi |MG |Pz|Art|Sap|J[äa]ger|Fallschirm|Kurl[äa]ndisch|IR |ArtReg|\bJG\b|Aufkl|"
    r"MAAF|\.AF|\.FW|\.FG|ASC|GAVCA|\bKBF\b|\bBAP\b|\bAAD\b|\bVAK\b|JgdFl|SchlFl|Para|"
    r"K[üu]stenschutz|Sturmbr[üu]cke|Technische|R[ée]sistance|Hospital|F[äa]lt|Flyvestation|"
    r"Goleti|Verst[äa]rktes|PzGren|TigerAbt|Fjg|Broich|Superga|Mineral|Ba[kt]i K)")


def rd_cand(tag):
    p = os.path.join(ROOT, "work", tag.lower(), "residual-cand.tsv")
    d = {}
    if not os.path.exists(p):
        return d
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 4:
                d[c[0]] = (int(c[1]), c[2], c[3])
    return d


def main():
    tags = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not tags:
        print(__doc__)
        return 2
    union = {}
    for t in tags:
        for k, (freq, dst, who) in rd_cand(t).items():
            e = union.setdefault(k, {"freq": 0, "efiles": [], "dst": "", "src": ""})
            e["freq"] += freq
            e["efiles"].append(t)
            if dst and not e["dst"]:
                e["dst"], e["src"] = dst, who
    out = os.path.join(HERE, "residual-%sunion.tsv" % PREFIX)
    miss = []
    manual = []
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tfreq\tefiles\tcand\tsource\n")
        for k in sorted(union):
            e = union[k]
            f.write("%s\t%d\t%s\t%s\t%s\n" % (k, e["freq"], "+".join(e["efiles"]), e["dst"], e["src"]))
            if not e["dst"]:
                if SPLIT_UNIT and UNIT_RE.search(k):
                    manual.append((k, e["freq"], "+".join(e["efiles"])))
                else:
                    miss.append((k, e["freq"], "+".join(e["efiles"])))
    mp = os.path.join(HERE, "residual-%smanual.tsv" % PREFIX)
    with io.open(mp, "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tfreq\tefiles\tdst\n")
        for k, n, ef in manual:
            f.write("%s\t%d\t%s\t\n" % (k, n, ef))
    print("联合残槽唯一 %d；既有译法 %d；**待译 %d**；部队/杂项 %d（自处理，见 residual-%smanual.tsv）"
          % (len(union), len(union) - len(miss) - len(manual), len(miss), len(manual), PREFIX))
    miss = [m[0] for m in miss]
    # 分块（顺序均分，保持跨 efile 同名同块不重复即可 —— miss 已去重）
    cdir = os.path.join(HERE, "residual-chunks-%s" % (PREFIX or "all"))
    os.makedirs(cdir, exist_ok=True)
    for old in os.listdir(cdir):
        os.remove(os.path.join(cdir, old))
    per = (len(miss) + NCHUNK - 1) // NCHUNK
    for i in range(NCHUNK):
        part = miss[i * per:(i + 1) * per]
        if not part:
            continue
        p = os.path.join(cdir, "chunk-%02d.tsv" % (i + 1))
        with io.open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(part) + "\n")
        print("  chunk-%02d: %d 行" % (i + 1, len(part)))
    print("已写 %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
