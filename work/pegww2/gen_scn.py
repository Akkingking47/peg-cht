#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 场景层生成器：原文备份 + 译法真源（值模式·整行匹配） ⇒ 出稿。

与 `gen_value.py`（根级单文件）的区别：
  · 本作场景层是 **3,778 个文件**，需**逐文件**构建、逐文件校验、镜像目录结构
  · 只做**整行精确匹配**，**绝不做行内子串替换**（防前作「内嵌替换误伤」重演）
  · 原文列带 **TSV 转义**（`\\t`/`\\xNN`），因此匹配前先 unesc

五道硬校验（任一不过 ⇒ 该文件**拒绝落盘**并计入失败）：
  ① 行数严格一致（逐文件）
  ② 无 CR/LF/TAB 混入译文
  ③ **TAB/控制字符个数与原文一致**（原文含 `\\t`/`\\xNN` 时）
  ④ 禁用译法（整串精确匹配）
  ⑤ GBK 可编码
用法: python gen_scn.py [build|dry]
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsv_esc import esc, unesc  # noqa: E402

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2"
BKROOT = os.path.join(WS, "pegww2", "testbed", "backup")   # ⭐ 原文备份（构建**必须**从这里读）
RES = os.path.join(WS, "pegww2", "research")
MAP = os.path.join(RES, "ww2-scn-map.tsv")
BAN = os.path.join(RES, "banned.tsv")
# ⭐ 按场景定点覆盖（第 37 轮 · 用户裁定④）：`en | 项目 | 场景词干 | 译名 | 依据`
#    地名该用哪个写法取决于**该场景预设扮演哪方势力**，而 `ww2-scn-map.tsv` 只有全局一张值。
OVRFILE = os.path.join(WS, r"glossary\layers\scn-place-override.tsv")
OUTROOT = os.path.join(WS, "pegww2", "testbed", "out")
_sink = io.StringIO()

EXCLUDE = re.compile(r"(?i)(^info\.txt$|read ?me|report)")
CTL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


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


def load_map():
    m = {}
    with open(MAP, encoding="utf-8-sig") as f:
        for line in f:
            s = line.rstrip("\r\n")
            if not s or s.startswith("#") or s.split("\t")[0].strip() == "原文":
                continue
            f2 = s.split("\t")
            if len(f2) >= 3 and f2[0].strip():
                # ⚠️ 键**必须也 unesc**（踩坑 W15）：原文散文里夹 `\x00`/`\x01` 等控制字符，
                #    写盘时用 `\xNN` 转义；若读回时键保持转义原样，而查表用的
                #    `orig.strip()` 里是**真控制字符** ⇒ **永远匹配不上**，
                #    表现为「该行仍是英文」且**不报错**，属**静默缺口**。
                #    实测：带 NUL 补位的长简报行成批漏译（`tsv_esc.py` 文档已预言此坑）。
                m[unesc(f2[0])] = (unesc(f2[1]), f2[2].strip())
                m.setdefault(esc(f2[0]), m[unesc(f2[0])])   # 兼容旧查表写法
    return m


SUFFIX = r"(?:i|m|u|l|bv|tv|v)"
STEM_TAIL = re.compile(r"(?i)(?:_%s$|(?<=[0-9])%s$)" % (SUFFIX, SUFFIX))


def stem_of(fn):
    """场景词干（小写）：`7Pzra7147_i.TXT` → `7pzra7147`；`BoB14V.txt` → `bob14`。
    ⚠️ 后缀**常常没有下划线**（`110bv.TXT`）⇒ 只认 `_xx$` 会漏剥。"""
    base = os.path.splitext(fn)[0]
    return STEM_TAIL.sub("", STEM_TAIL.sub("", base)).lower()


def load_scn_override():
    """按场景定点覆盖：`{(场景词干小写, 英文键): 译名}`（只取 `PEGWW2` 侧）。"""
    ov = {}
    if not os.path.isfile(OVRFILE):
        return ov
    with open(OVRFILE, encoding="utf-8-sig") as f:
        for ln, raw in enumerate(f, 1):
            s = raw.rstrip("\r\n")
            if not s.strip() or s.startswith("#") or s.split("\t")[0] == "en":
                continue
            c = s.split("\t")
            if len(c) < 4:
                print(f"⚠️ scn-place-override.tsv 第 {ln} 行字段不足，跳过：{s!r}")
                continue
            if c[1].strip().upper() != "PEGWW2":
                continue
            ov[(c[2].strip().lower(), unesc(c[0]))] = unesc(c[3])
    return ov


def load_banned():
    out = []
    with open(BAN, encoding="utf-8-sig") as f:
        for line in f:
            s = line.rstrip("\r\n")
            if s and not s.startswith("#"):
                out.append(s.split("\t")[0].strip())
    return out


def main():
    dry = "dry" in sys.argv
    m = load_map()
    ovr = load_scn_override()
    # ⭐ per-file 覆盖表：子目录 \t 文件名 \t 行号(0-based) \t 期望原文 \t 译文
    file_ov = {}
    OVF = os.path.join(RES, "_scn-file-overrides.tsv")
    if os.path.isfile(OVF):
        for j, l in enumerate(open(OVF, encoding="utf-8")):
            if j < 2 or not l.strip() or l.startswith("#"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 5 and c[2].strip().isdigit():
                file_ov[(c[0].strip(), c[1].strip(), int(c[2]))] = c[4]
    banned = load_banned()
    from collections import Counter
    print(f"译法真源: {len(m)} 条（其中有效译文 {sum(1 for v, t in m.values() if v.strip() and t != '保留')} 条）"
          f" · 禁用词 {len(banned)} 条 · 按场景定点覆盖 {len(ovr)} 条（{len({s for s, _ in ovr})} 个场景）")
    tag = Counter()
    files_ok = files_bad = 0
    changed_total = 0
    unmatched = Counter()
    outcomes = []
    src_from_bak = src_from_game = 0
    for sub in ("SCENARIO", "USERSCEN"):
        d = os.path.join(GAME, sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            p = os.path.join(d, f)
            if not os.path.isfile(p) or not re.search(r"(?i)\.(txt|tx|t|log|ply)$", f):
                continue
            if f.lower().endswith(".ply") or EXCLUDE.search(f):
                continue
            # ⭐ 按场景定点覆盖（第 37 轮）：本文件**生效的**映射表；空覆盖表时与覆盖前逐字节相同
            #    ⚠️ `m` 的值是 `(译文, 来源)` 二元组 ⇒ 覆盖值必须也包成二元组，
            #       否则 `zh, src = ent` 会把中文字符串拆包（曾报 `too many values to unpack`）。
            _st = stem_of(f)
            eff_m = m
            if _st:
                _mo = {}
                for (s, en), zh in ovr.items():
                    if s == _st:
                        _mo[en] = (zh, m[en][1] if en in m else "scn-override")
                if _mo:
                    eff_m = dict(m)
                    eff_m.update(_mo)
            # ⭐⭐ **构建必须从 backup 读原文**（踩坑 W14：曾从游戏目录读 ⇒ 部署后二次生成静默变 no-op）
            bak = os.path.join(BKROOT, sub, f)
            if os.path.isfile(bak):
                raw = open(bak, "rb").read()
                src_from_bak += 1
            else:
                raw = open(p, "rb").read()
                src_from_game += 1
                if any(b > 127 for b in raw[:4096]):
                    print(f"  ⚠️ 备份缺失且源含高位字节（可能已是成品，需警觉）: {sub}/{f}")
            parts = re.split(rb"(\r\n|\r|\n)", raw)
            lines, seps = parts[0::2], parts[1::2]
            errs, out, changed = [], [], 0
            for i, ln in enumerate(lines):
                orig = ln.decode("latin-1")
                key = orig.strip()
                ent = eff_m.get(key) if key else None
                # ⭐ per-file 覆盖：按「子目录+文件名+行号」定点改写，**不走整串键控**
                #   为什么必须有它：同一个串在别的文件里可能是正文（如简报段落也当场景名），
                #   整串键控会把那些正文一起改错（实测误伤 36 个键 ⇒ 已回滚）。
                ov = file_ov.get((sub, f, i))
                if ov is not None:
                    ent = (ov, "per-file")
                if not ent or not ent[0].strip() or ent[1] == "保留":
                    if key and re.search(r"[A-Za-z]", key):
                        unmatched[key] += 1
                    out.append(ln)
                    continue
                zh, src = ent
                if any(c in zh for c in ("\r", "\n", "\t")):
                    errs.append(f"行{i + 1} 含 CR/LF/TAB")
                # ⭐ 控制字符**随原文保留**（踩坑 W16）：原文常有 **NUL 补位**（如
                #    `The success ... in your hands!\x00`），译文表里没有 ⇒ 直接报
                #    「控制字符个数不一致」把整文件拒掉。正解是把**尾部控制字符**
                #    原样搬到译文末尾（游戏数据依赖定长补位，丢不得）。
                if len(CTL.findall(zh)) < len(CTL.findall(orig)):
                    #    ⚠️ 扫描**必须容忍行尾分隔符**（踩坑 W16-bis）：`usvsussr10.txt` 行0 是
                    #       `Allied Forces seize Vladavostok` + NUL×470 + `\r` —— 旧扫描从行尾
                    #       倒着遇到 `\r`（**不在 CTL 里**）立刻 break ⇒ 一个 NUL 都搬不过来 ⇒
                    #       控制字符个数不一致把整文件拒掉。正解：把「行尾的空白+控制字符连续段」
                    #       整体当补位（`\r`/`\n`/`\t`/空格 与 CTL 同级），遇到真字符才停。
                    tail = []
                    for ch in reversed(orig):
                        if CTL.match(ch) or ch in "\r\n\t ":
                            tail.append(ch)
                        else:
                            break
                    if tail:
                        zh = zh + "".join(reversed(tail))
                if zh.strip() in banned:
                    errs.append(f"行{i + 1} 命中禁用译法 {zh.strip()!r}")
                if len(CTL.findall(zh)) != len(CTL.findall(orig)):
                    errs.append(f"行{i + 1} 控制字符个数不一致（原文 {len(CTL.findall(orig))} / 译文 {len(CTL.findall(zh))}）")
                try:
                    zh.encode("gbk")
                except UnicodeEncodeError as e:
                    errs.append(f"行{i + 1} GBK 无法编码: {e}")
                lead = orig[:len(orig) - len(orig.lstrip())]
                trail = orig[len(orig.rstrip()):]
                nb = (lead + zh.strip() + trail).encode("gbk")
                if nb != ln:
                    changed += 1
                out.append(nb)
            if len(out) != len(lines):
                errs.append("行数不一致")
            if errs:
                files_bad += 1
                outcomes.append((sub, f, f"❌ {len(errs)} 项：{errs[0][:70]}", changed))
                continue
            buf = bytearray()
            for i, ln in enumerate(out):
                buf += ln
                if i < len(seps):
                    buf += seps[i]
            if not dry:
                dst = os.path.join(OUTROOT, sub, f)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, "wb") as fh:
                    fh.write(bytes(buf))
                back = open(dst, "rb").read()
                assert back == bytes(buf), f"回读校验失败 {f}"
                assert len(re.split(rb"\r\n|\r|\n", back)) == len(lines), f"复验行数失败 {f}"
            files_ok += 1
            changed_total += changed
            outcomes.append((sub, f, "✅", changed))
    print()
    print("=" * 96)
    print(f"逐文件结果：通过 {files_ok} · 失败 {files_bad} · 累计改动行 {changed_total}")
    print(f"  源取自备份 {src_from_bak} 个 · 源取自游戏目录(无备份) {src_from_game} 个")
    print("=" * 96)
    for sub, f, msg, ch in outcomes:
        if msg != "✅":
            print(f"  {sub}/{f}: {msg}")
    print(f"  未命中（原样保留）唯一串 {len(unmatched)} · 占出现次数 {sum(unmatched.values())}")
    print()
    print("  —— 未命中 top 20（多为纯型号/元数据/已被过滤的垃圾）——")
    for k, c in unmatched.most_common(20):
        print(f"    {c:>4d}  {k[:88]!r}")
    print()
    print("总判定:", "✅ 全部通过" if files_bad == 0 else f"❌ {files_bad} 个文件失败")


if __name__ == "__main__":
    main()
    os.makedirs(os.path.join(RES, "evidence"), exist_ok=True)
    with open(os.path.join(RES, "evidence", "gen-scn.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
