# -*- coding: utf-8 -*-
r"""EFILE_Clu `names.txt` 中文侧生成器（992 个非空行）。

填译链（单一优先级）：
  1. `work\clu\names-miss-zh.tsv`   本批新译（子代理按人名/贵族/玩名家谱口径产出）
  2. `work\xscn\_root_dict.tsv`     跨 efile「原文↔TEXT-ZH」实证词典（816 条白捡）
  3. `work\xscn\master-glossary.tsv` / `master-resolve.tsv`
  4. `glossary\standard-glossary.tsv`
  ⚠️ **保留原文的尾空格**（names.txt 有 114 行带尾部空格填充，MECHANICS §16.4）。

出稿 `TEXT-ZH\names.txt`：GBK(936) / 无 BOM / 换行沿用原文（CRLF）/ 行数逐行对齐。
用法: python make_clu_names.py [--apply]
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
WX = r"D:\DSH\军事游戏汉化\work\xscn"
EFILE = r"D:\OpenPG2\EFILE_Clu"


def rd(path, k=0, v=1, header=True):
    """读两列 TSV。⚠️ `header=False` 用于**无表头**的子代理产出（本轮 names-miss-zh.tsv
    直接从第 1 行起是数据，旧版按默认跳表头 ⇒ 第 1 条 `Cayysar` 被静默丢掉）。"""
    d = {}
    if not os.path.exists(path):
        return d
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if (header and i == 0) or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) > max(k, v) and c[k].strip() and c[v].strip():
                d.setdefault(c[k].strip(), c[v].strip())
    return d


def main():
    apply = "--apply" in sys.argv
    miss_zh = rd(os.path.join(HERE, "names-miss-zh.tsv"), header=False)
    srcs = [("本批新译", miss_zh),
            ("root-dict", rd(os.path.join(WX, "_root_dict.tsv"))),
            ("master", rd(os.path.join(WX, "master-glossary.tsv"))),
            ("resolve", rd(os.path.join(WX, "master-resolve.tsv"))),
            ("glossary", rd(r"D:\DSH\军事游戏汉化\glossary\standard-glossary.tsv"))]
    raw = open(os.path.join(EFILE, "names.txt"), "rb").read()
    nl = "\r\n" if raw.count(b"\r\n") else "\n"
    lines = raw.decode("cp1252").split(nl)
    out, used, miss = [], {}, []
    for l in lines:
        core = l.strip()
        if not core or core.startswith("*"):
            out.append(l)
            continue
        dst, who = "", ""
        for nm, d in srcs:
            if core in d:
                dst, who = d[core], nm
                break
        if not dst:
            miss.append(core)
            out.append(l)
            continue
        lead = l[:len(l) - len(l.lstrip())]
        trail = l[len(l.rstrip()):]
        out.append(lead + dst + trail)
        used[who] = used.get(who, 0) + 1
    print("names.txt 行 %d  命中 %s  未覆盖 %d" % (len(lines), used, len(miss)))
    if miss:
        print("   未覆盖样例:", miss[:10])
    blob = nl.join(out).encode("gbk")
    print("字节 %d -> %d" % (len(raw), len(blob)))
    if blob.decode("gbk").split(nl) != out:
        raise SystemExit("!! 编解码往返不一致")
    if not apply:
        print("(dry-run，加 --apply 落盘)")
        return 0
    d = os.path.join(EFILE, "TEXT-ZH")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "names.txt")
    with open(p, "wb") as f:
        f.write(blob)
    back = open(p, "rb").read()
    assert back == blob and back[:3] != b"\xef\xbb\xbf", "回读不一致"
    assert back.count(b"\n") == back.count(b"\r\n"), "出现裸 LF"
    print("已写 %s（GBK / 无 BOM / CRLF；原文未动）" % p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
