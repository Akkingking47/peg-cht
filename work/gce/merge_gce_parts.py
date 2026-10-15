# -*- coding: utf-8 -*-
r"""合并 GCE `.xscn` 人工批次译文（`_gce_dst_partNN.txt`）→ 校验 → `xscn-new-NN.tsv`。

用法:
    python merge_gce_parts.py --check
    python merge_gce_parts.py --apply

校验（任一不过 ⇒ 不写盘）:
  1. 行数 == 对应 `_gce_todo_partNN.txt` 行数；
  2. 译文非空、无 TAB/CR/LF；
  3. `gce-xscn-map.tsv` 覆盖判定：本批键必须**不在**已覆盖集合内（防重复劳动）；
  4. `ok_dst` 守卫：译文含汉字，或 `src == dst`（口径保留）；
  5. GBK 可编码；
  6. **纯罗马数字方括号必须原样保留**（POLICY 三）——2026-10-08 收窄，原「全 ASCII 保留」与 POLICY 六 互斥；
  7. **不得引入全角标点**（`.xscn` 口径为半角）。
"""
import argparse
import glob
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
HAN = re.compile(r"[\u4e00-\u9fff]")


def rd2(path):
    out = []
    if not os.path.exists(path):
        return out
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2 and c[0]:
                out.append((c[0], c[1]))
    return out


def load_covered():
    m = {}
    for p in [os.path.join(HERE, "gce-xscn-map.tsv"), os.path.join(HERE, "_xscn_covered.tsv")]:
        for s, d in rd2(p):
            if s not in m and d.strip():
                m[s] = d
    return m


ROMAN = re.compile(r"^[IVXLCDM]+$")


def bracket_codes(s):
    """取出行内所有**方括号内容**。"""
    return re.findall(r"\[([^\]]*)\]", s)


def roman_brackets(s):
    """方括号内容为**纯罗马数字**者 ⇒ POLICY 三：军团/地域编号，必须原样保留。

    ⚠️ 2026-10-08 修（规则互斥）：原守卫是「方括号内容为纯 ASCII ⇒ 必须原样保留」，
    与 POLICY 六「方括号地名/人名**要译**」（`[Madrid]`→`[马德里]`、`[Navarra]`→`[纳瓦拉]`、
    `[Varela]`→`[巴雷拉]`）**直接互斥**，把 6 份合格译文**全数误杀**（part02/04/05/06/07
    的 `[Navarra]`→`[纳瓦拉]` 全被记为「代号被改写」）。
    精确规则只有一条：**纯罗马数字**才是代号（`[V]` `[XV]` `[XVIII]` `[XIV]`）；
    其余（地名/人名/通名/番号）一律可译。
    """
    return [t for t in bracket_codes(s) if ROMAN.match(t)]


def ascii_only(t):
    return bool(t) and all(ord(c) < 128 for c in t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    cov = load_covered()
    parts = sorted(glob.glob(os.path.join(HERE, "_gce_todo_part*.txt")))
    errors = []
    warnings = []
    written = 0
    for p in parts:
        tag = re.search(r"part(\d+)", os.path.basename(p)).group(1)
        src_lines = [ln.rstrip("\n") for ln in io.open(p, encoding="utf-8", newline="").read().replace("\r\n", "\n").split("\n") if ln.strip()]
        keys = [ln.split("|", 1)[1] for ln in src_lines]
        dp = os.path.join(HERE, "_gce_dst_part%s.txt" % tag)
        if not os.path.exists(dp):
            errors.append("缺译文 %s（%d 条）" % (os.path.basename(dp), len(keys)))
            continue
        with io.open(dp, encoding="utf-8", newline="") as f:
            raw = f.read()
        if raw.startswith("\ufeff"):
            errors.append("%s 含 BOM" % os.path.basename(dp))
        dst = [x for x in raw.replace("\r\n", "\n").split("\n") if x.strip()]
        if len(dst) != len(keys):
            errors.append("%s 行数不符：待译 %d / 译文 %d" % (os.path.basename(dp), len(keys), len(dst)))
            continue
        rows = []
        for s, d in zip(keys, dst):
            d = d.strip()
            if not d:
                errors.append("%s 空译文: %r" % (os.path.basename(dp), s))
                continue
            if "\t" in d or "\r" in d:
                errors.append("%s 译文含 TAB/CR: %r" % (os.path.basename(dp), s))
                continue
            if not HAN.search(d) and d != s.strip():
                errors.append("%s 译文既无汉字又非恒等（疑似漏译）: %r -> %r"
                              % (os.path.basename(dp), s, d))
                continue
            # ⭐ 罗马数字方括号守卫（POLICY 三；09-30 实测 part01 把 [XIV] 译成 [第14]）
            #    ⚠️ 09-30 原守卫「方括号全 ASCII ⇒ 必须保留」与 POLICY 六 互斥，
            #    误杀 6 份合格译文；2026-10-08 收窄为「仅纯罗马数字」（见 roman_brackets）。
            for t in roman_brackets(s):
                if ("[%s]" % t) not in d:
                    errors.append("%s 罗马数字方括号被改写（POLICY 三）: %r 中的 [%s] -> %r"
                                  % (os.path.basename(dp), s[:40], t, d[:40]))
            # ⭐ 半角标点守卫（`.xscn` 口径用半角；原文无全角标点）
            for fw in "（）［］，、；：":
                if fw in d and fw not in s:
                    errors.append("%s 引入了全角标点（`.xscn` 口径为半角）: %r 中的 %r -> %r"
                                  % (os.path.basename(dp), s[:40], fw, d[:40]))
            # ⚠️ 提示（非错误）：罗马数字 + 后续文字（`[V Trincheras]`）需人工看
            for t in bracket_codes(s):
                if t and not ROMAN.match(t) and ROMAN.match(t.split(" ")[0]):
                    warnings.append("罗马数字+文字方括号待人工核（POLICY 三）: %r -> %r" % (s[:40], d[:40]))
            if s.count("[") != d.count("[") or s.count("]") != d.count("]"):
                errors.append("%s 方括号数量不符: %r -> %r" % (os.path.basename(dp), s[:40], d[:40]))
            if s.count("/") != d.count("/"):
                errors.append("%s 斜杠数量不符: %r -> %r" % (os.path.basename(dp), s[:40], d[:40]))
            if s in cov and cov[s] != d:
                warnings.append("与既有覆盖不一致（既有=%s / 本批=%s）%r" % (cov[s][:20], d[:20], s[:40]))
            try:
                d.encode("gbk")
            except UnicodeEncodeError as e:
                errors.append("%s GBK 不可编码: %r (%s)" % (os.path.basename(dp), s, e))
                continue
            rows.append((s, d))
        print("  part%s: %d 条（源 %d）" % (tag, len(rows), len(keys)))
        if a.apply and not errors:
            out = os.path.join(HERE, "xscn-new-%s.tsv" % tag)
            with io.open(out, "w", encoding="utf-8", newline="") as f:
                f.write("src\tdst\n")
                for s, d in rows:
                    f.write("%s\t%s\n" % (s, d))
            back = [l.split("\t") for l in io.open(out, encoding="utf-8").read().split("\n")[1:] if l.strip()]
            if len(back) != len(rows) or any(b[0] != r[0] or b[1] != r[1] for b, r in zip(back, rows)):
                raise SystemExit("回读不一致: %s" % out)
            written += 1

    if warnings:
        print("提示（非错误）%d 条：" % len(warnings))
        for w in warnings[:10]:
            print("   ~ %s" % w)
    print("错误 %d" % len(errors))
    if errors:
        print("!! 校验失败：")
        for e in errors[:50]:
            print("   - %s" % e)
        return 1
    if a.apply:
        print("已写 xscn-new-*.tsv 共 %d 个" % written)
    return 0


if __name__ == "__main__":
    sys.exit(main())
