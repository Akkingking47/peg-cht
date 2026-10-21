#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 值模式文本生成器（原文串查表）：原文备份 + 译法真源 ⇒ 出稿。

适用：`ww2-eqp.txt`（装备名）、`WW2NAME.TXT`（人名）—— 引擎按**行号**取字，
      因此生成器**只做整行替换、绝不增删行**；重复原文串自动得到同一译文。

四道硬校验：① 行数严格一致 ② 无 CR/LF/TAB 混入 ③ 禁用译法（整串精确匹配）④ GBK 可编码
另保留原行的**首尾空白**（只替换去空白后的核心串），避免格式漂移。
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "text")
RES = os.path.join(WS, "pegww2", "research")
DER = os.path.join(RES, "_derived")          # 生成器产出（可复算，勿手改；见 research/README.md）
OUT = os.path.join(WS, "pegww2", "testbed", "out", "text")
os.makedirs(DER, exist_ok=True)
_sink = io.StringIO()

TARGETS = {
    "ww2-eqp": ("ww2-eqp.txt", "ww2-eqp-map.tsv"),
    "WW2NAME": ("WW2NAME.TXT", "WW2NAME-map.tsv"),
}


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


def load_banned():
    p = os.path.join(RES, "banned.tsv")
    out = []
    if os.path.isfile(p):
        with open(p, encoding="utf-8-sig") as f:
            for line in f:
                s = line.rstrip("\r\n")
                if s and not s.startswith("#"):
                    out.append(s.split("\t")[0].strip())
    return out


def load_map(name):
    m = {}
    with open(os.path.join(RES, name), encoding="utf-8-sig") as f:
        for line in f:
            s = line.rstrip("\r\n")
            if not s or s.startswith("#") or s.split("\t")[0].strip() in ("原文", "行号"):
                continue
            f2 = s.split("\t")
            if len(f2) >= 2:
                m[f2[0]] = (f2[1], f2[2].strip() if len(f2) >= 3 else "")
    return m


def build(key):
    src_name, map_name = TARGETS[key]
    raw = open(os.path.join(BK, src_name), "rb").read()
    parts = re.split(rb"(\r\n|\r|\n)", raw)
    lines, seps = parts[0::2], parts[1::2]
    m = load_map(map_name)
    banned = load_banned()
    errs = []
    out, changed, miss = [], 0, []
    for i, ln in enumerate(lines):
        no = i + 1
        orig = ln.decode("cp1252")
        core = orig.strip()
        ent = m.get(core)
        if not ent or not ent[0].strip() or ent[1].strip() == "保留":
            if core:
                miss.append((no, core))
            out.append(ln)
            continue
        zh = ent[0]      # ⚠️ 必须是 ent[0]=译文；曾误写 ent[1] ⇒ 把「来源」标签当译文写进了成品
        # ⭐ 护栏：译文绝不能等于工作表的「来源」标签（W18 事故：曾把 新译/词库 当译文写进成品）
        if zh.strip() in ("新译", "词库", "PeG", "PeG同串", "保留", "人工确认", "人工确认(引擎日志行原样)"):
            errs.append(f"行{no} 译文等于来源标签 {zh.strip()!r} ⇒ 拒绝（疑似取错列）")
        if not re.search(r"[\u4e00-\u9fff]", zh) and re.search(r"[\u4e00-\u9fff]", orig):
            errs.append(f"行{no} 原文含中文但译文不含 ⇒ 拒绝")
        if any(c in zh for c in ("\r", "\n", "\t")):
            errs.append(f"行{no} 译文含 CR/LF/TAB ⇒ 拒绝")
        if zh.strip() in banned:
            errs.append(f"行{no} 命中禁用译法 {zh.strip()!r} ⇒ 拒绝")
        try:
            zh.encode("gbk")
        except UnicodeEncodeError as e:
            errs.append(f"行{no} 无法 GBK 编码：{e} ⇒ 拒绝")
        # 保留原行首尾空白
        lead = orig[:len(orig) - len(orig.lstrip())]
        trail = orig[len(orig.rstrip()):]
        newline = lead + zh + trail
        if newline != orig:
            changed += 1
        out.append(newline.encode("gbk"))
    if len(out) != len(lines):
        errs.append("行数不一致 ⇒ 拒绝")
    print("=" * 92)
    print(f"[{key}] {src_name}  {len(raw):,} B / {len(lines)} 行元素 · 映射 {len(m)} 条")
    print("=" * 92)
    print(f"  改动行 {changed} · 未命中(原样保留) {len(miss)}")
    for no, c in miss[:10]:
        print(f"      行{no:<5d} {c[:70]}")
    if errs:
        print(f"  ❌ 硬校验失败 {len(errs)} 条 ⇒ 拒绝落盘")
        for e in errs[:20]:
            print(f"     {e}")
        return False
    buf = bytearray()
    for i, ln in enumerate(out):
        buf += ln
        if i < len(seps):
            buf += seps[i]
    os.makedirs(OUT, exist_ok=True)
    dst = os.path.join(OUT, src_name)
    with open(dst, "wb") as f:
        f.write(bytes(buf))
    back = open(dst, "rb").read()
    assert back == bytes(buf), "回读校验失败"
    assert back[:3] != b"\xef\xbb\xbf", "含 BOM ⇒ 拒绝"
    assert len(re.split(rb"\r\n|\r|\n", back)) == len(lines), "行尾/行数复验失败"
    crlf = back.count(b"\r\n")
    print(f"  ✅ 校验通过 ⇒ {os.path.relpath(dst, WS)}  {len(back):,} B "
          f"(CRLF={crlf} 裸LF={back.count(b'\n') - crlf} 裸CR={back.count(b'\r') - crlf})")
    # 行级对照表
    cmpf = os.path.join(DER, f"_对照-{key}.tsv")
    with open(cmpf, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# {src_name} 行级对照表（生成器产出）\n行号\t原文\t译文\t来源\n")
        for i, ln in enumerate(lines):
            o = ln.decode("cp1252")
            ent = m.get(o.strip())
            # ⚠️ 曾是 `ent[1]`（=来源标签）⇒ 对照表整列写成「新译/词库」；译文是 ent[0]（与主流程一致）
            z = ent[0] if (ent and ent[0].strip() and ent[1].strip() != "保留") else o
            f.write(f"{i + 1}\t{o}\t{z}\t{ent[1] if ent else '—'}\n")
    print(f"     对照表 {os.path.relpath(cmpf, WS)}")
    return True


def main():
    # ⭐ 词库门（治本件第 3 步）：值模式（装备/人名）构建前先过门
    try:
        sys.path.insert(0, os.path.join(WS, "work", "glossary"))
        import layer_gate
        ok_g, _m = layer_gate.quick_check()
        if not ok_g:
            print("  ⛔ 词库门未过 ⇒ 拒绝构建（先跑 work/glossary/layer_gate.py --full）")
            return 1
    except Exception as e:
        print("  （词库门跳过：%s）" % e)
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    keys = list(TARGETS) if (not args or args[0] == "all") else [args[0]]
    ok = True
    for k in keys:
        if k not in TARGETS:
            print(f"未知目标 {k}；可选 {list(TARGETS)}")
            ok = False
            continue
        ok &= build(k)
        print()
    from collections import defaultdict
    print("总判定:", "✅ 全部通过" if ok else "❌ 有失败项")
    return 0 if ok else 1


if __name__ == "__main__":
    rc = main()
    os.makedirs(os.path.join(RES, "evidence"), exist_ok=True)
    with open(os.path.join(RES, "evidence", "gen-value.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
    sys.exit(rc)
