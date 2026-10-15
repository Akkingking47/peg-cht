# -*- coding: utf-8 -*-
"""BASEKORP `label` 层（地图标签 .txt）汉化生成器。

层定位：`EFILE_BASEKORP\\SCENARIO\\*.txt` 中被 txt_workbench.py 判为 `label` 的 78 个文件
（场景名 / 河名 / 地名 / 部队番号链 / 少量战役说明与简报头），共 3,153 唯一行 / 6,589 实例。
它们此前被散文流程（只处理 kind=prose）按设计跳过 ⇒ BASEKORP `.txt` 覆盖率卡在 94.4%。

填译优先级（保证与既有各层一致）：
  1. `label-zh.tsv`      —— 本层专用缺口表（198 条，人工逐条精译）
  2. `bk-xscn-map.tsv`   —— `.xscn` 已交付译文表（同源镜像：`.xscn` 组 0 即本 .txt 名单）
  3. 否则 **报错**（绝不静默留英文）

输出：`<efile>\\TEXT-ZH\\SCENARIO\\<同名>.txt`，GBK(936) / 无 BOM / CRLF。
原文侧（`SCENARIO\\*.txt`）只读，绝不改写。
"""
import io
import os
import sys
import collections

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
EFILE = r"D:\OpenPG2\EFILE_BASEKORP"
SRC = os.path.join(EFILE, "SCENARIO")
ZH = os.path.join(EFILE, "TEXT-ZH", "SCENARIO")
MANUAL = os.path.join(HERE, "label-zh.tsv")
XSCN_MAP = os.path.join(HERE, "bk-xscn-map.tsv")
REPLIST = os.path.join(HERE, "rep-list.tsv")

# U+00AF(¯) 在 GBK 无编码（正是「cp1252 假汉字」的陷阱），按视觉等价替换。
FALLBACK = {"\u00af": "\u2500"}


def read_tsv(path):
    """读 src/dst 两列（允许第三列 note，如 bk-xscn-map.tsv 的 det/llm/cross）。

    ⚠️ 必须用完整 split("\\t") 取 c[0]/c[1]：用 split("\\t",1) 会把 note 并进译文，
       往标签行里塞进制表符（静默结构污染）。与 xscn.py::load_map 保持一致。
    """
    d = {}
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2 and c[0]:
                d[c[0]] = c[1]
    return d


def label_files():
    """rep-list.tsv 里 kind==label 且当前未部署（或已部署但需重建）的文件。"""
    out = []
    with io.open(REPLIST, encoding="utf-8") as f:
        f.readline()
        for ln in f:
            p = ln.rstrip("\r\n").split("\t")
            if len(p) >= 7 and p[3] == "label":
                out.append(p[1])
    return sorted(out)


def gbk_safe(s):
    try:
        return s.encode("gbk")
    except UnicodeEncodeError:
        for a, b in FALLBACK.items():
            s = s.replace(a, b)
        try:
            s.encode("gbk")
            return s.encode("gbk")
        except UnicodeEncodeError as e:
            raise SystemExit("GBK 无法编码: %r (%s)" % (s, e))


def main():
    dry = "--dry" in sys.argv
    manual = read_tsv(MANUAL)
    xmap = read_tsv(XSCN_MAP)
    print("label-zh 缺口表 %d 条 | xscn 映射表 %d 条" % (len(manual), len(xmap)))

    files = label_files()
    print("label 文件 %d 个%s" % (len(files), "  [DRY RUN]" if dry else ""))

    miss = []
    used_manual = used_xmap = used_keep = 0
    plan = []          # (fn, lines, out, blob)
    tot_lines = tot_zh = 0
    src_bytes = tgt_bytes = 0

    for fn in files:
        sp = os.path.join(SRC, fn)
        raw = open(sp, "rb").read()
        # 结构守卫：原文必须是纯 CRLF、无 BOM
        if raw.count(b"\n") != raw.count(b"\r\n"):
            raise SystemExit("原文含裸 LF: %s" % fn)
        if raw[:3] == b"\xef\xbb\xbf":
            raise SystemExit("原文含 BOM: %s" % fn)

        text = raw.decode("cp1252")
        lines = text.split("\r\n")
        out = []
        for l in lines:
            if not l.strip():
                out.append(l)
                continue
            if l in manual:
                d = manual[l]
                used_manual += 1
            elif l in xmap:
                d = xmap[l]
                used_xmap += 1
            else:
                miss.append((fn, l))
                d = None
            if d == "" and l.strip():
                raise SystemExit("空译文: %s :: %r" % (fn, l))
            out.append(d if d is not None else l)

        for l in out:
            if l.strip():
                if "\t" in l or "\n" in l or "\r" in l:
                    raise SystemExit("译文含控制符 @ %s: %r" % (fn, l))
                gbk_safe(l)          # GBK 前置校验（含 ¯→─ 兜底）
        blob = "\r\n".join(out).encode("gbk")
        if blob.count(b"\n") != blob.count(b"\r\n"):
            raise SystemExit("输出换行异常: %s" % fn)
        if blob.decode("gbk").split("\r\n") != out:
            raise SystemExit("编解码往返不一致: %s" % fn)

        plan.append((fn, lines, out, blob))
        tot_lines += sum(1 for x in lines if x.strip())
        tot_zh += sum(1 for c in "".join(out) if "\u4e00" <= c <= "\u9fff")
        src_bytes += len(raw)
        tgt_bytes += len(blob)

    print("填译来源：缺口表 %d | xscn 映射 %d" % (used_manual, used_xmap))
    if miss:
        cnt = collections.Counter(miss)
        print("!! 未覆盖 %d 处（唯一 %d）——**未落盘**:" % (len(miss), len(cnt)))
        for (fn, l), n in cnt.most_common(60):
            print("   %-22s x%-3d %r" % (fn, n, l))
        raise SystemExit(1)

    if dry:
        print("DRY RUN 结束：%d 文件 / 非空行 %d / 输出汉字 %d / 字节 %d -> %d"
              % (len(plan), tot_lines, tot_zh, src_bytes, tgt_bytes))
        return

    if not os.path.isdir(ZH):
        os.makedirs(ZH)
    for fn, lines, out, blob in plan:
        tgt = os.path.join(ZH, fn)
        with open(tgt, "wb") as f:
            f.write(blob)
        back = open(tgt, "rb").read()      # 回读校验
        if back != blob:
            raise SystemExit("回读不一致: %s" % fn)
        if back[:3] == b"\xef\xbb\xbf":
            raise SystemExit("输出含 BOM: %s" % fn)
        if back.count(b"\n") != back.count(b"\r\n"):
            raise SystemExit("输出含裸 LF: %s" % fn)
        if back.decode("gbk").split("\r\n") != out:
            raise SystemExit("回读行不一致: %s" % fn)

    print("---")
    print("写出 %d 个文件 | 非空行 %d | 输出汉字 %d" % (len(plan), tot_lines, tot_zh))
    print("字节 %d -> %d" % (src_bytes, tgt_bytes))
    print("OK 全部行已覆盖，原文件未改动")


def _enc_ok(lines):
    try:
        for l in lines:
            l.encode("gbk")
        return True
    except UnicodeEncodeError:
        return False


if __name__ == "__main__":
    main()
