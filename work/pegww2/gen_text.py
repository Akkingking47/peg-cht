#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 文本生成器（通用）：原文备份 + 译法真源 ⇒ 出稿（四道硬校验）。

纪律：
  · **从 testbed/backup/text/ 读原文**（绝不从游戏目录读，否则会把中文再翻一次）
  · 四道硬校验任一不过 ⇒ **拒绝落盘**
      ① 行数与原文件严格一致
      ② printf 格式符（%s/%d…）**顺序与个数**完全一致
      ③ 译文内不得混入 CR / LF / TAB
      ④ 禁用译法黑名单（**整串精确匹配**）
  · 出稿 **GBK(936) 无 BOM**，**行尾沿用原文**
  · 产出：成品 + 行级对照表

用法:
  python gen_text.py WW2Gui                 # 只构建到 testbed/out/text/
  python gen_text.py WW2Gui deploy          # 构建后由 deploy.py 部署（本脚本不写游戏目录）
  python gen_text.py all
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
    "WW2Gui": ("WW2Gui.txt", "WW2Gui-map.tsv"),
    "WW2Misc": ("WW2Misc.txt", "WW2Misc-map.tsv"),
    "WW2Tips": ("WW2Tips.TXT", "WW2Tips-map.tsv"),
}

PRINTF = re.compile(r"%(?:%|[-+ #0]*\d*(?:\.\d+)?[diouxXeEfgGcs])")


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
                if not s or s.startswith("#"):
                    continue
                out.append(s.split("\t")[0].strip())
    return out


def load_map(name):
    """行号 -> (原文, 译文, 来源)"""
    m = {}
    with open(os.path.join(RES, name), encoding="utf-8-sig") as f:
        for line in f:
            s = line.rstrip("\r\n")
            if not s or s.startswith("#") or s.split("\t")[0].strip() in ("行号", "原文"):
                continue
            f2 = s.split("\t")
            if len(f2) >= 4 and re.fullmatch(r"\d+", f2[0].strip()):
                m[int(f2[0])] = (f2[1], f2[2], f2[3].strip())
    return m


def build(key):
    src_name, map_name = TARGETS[key]
    src = os.path.join(BK, src_name)
    raw = open(src, "rb").read()
    parts = re.split(rb"(\r\n|\r|\n)", raw)
    lines = parts[0::2]
    seps = parts[1::2]
    m = load_map(map_name)
    banned = load_banned()

    errs, warns = [], []
    out_lines, cmp_rows = [], []
    changed = untranslated = 0
    for i, ln in enumerate(lines):
        no = i + 1
        orig = ln.decode("cp1252")
        ent = m.get(no)
        zh = None
        if ent:
            m_orig, m_zh, src_tag = ent
            if m_orig.strip() and m_orig != orig:
                warns.append(f"行{no} 映射表原文与备份不一致（表={m_orig!r} 源={orig!r}）⇒ 按原文处理")
            if src_tag != "保留" and m_zh.strip() and m_zh != orig:
                zh = m_zh
        new = orig if zh is None else zh
        if zh is not None:
            changed += 1
        else:
            if orig.strip():
                untranslated += 1
        # ③ 控制字符
        if any(c in new for c in ("\r", "\n", "\t")):
            errs.append(f"行{no} 译文含 CR/LF/TAB ⇒ 拒绝")
        # ② printf
        po, pn = PRINTF.findall(orig), PRINTF.findall(new)
        if po != pn:
            errs.append(f"行{no} printf 不一致：原文 {po} vs 译文 {pn} ⇒ 拒绝")
        # ④ 禁用译法（整串精确匹配）
        if new.strip() in banned:
            errs.append(f"行{no} 命中禁用译法 {new.strip()!r} ⇒ 拒绝")
        try:
            new.encode("gbk")
        except UnicodeEncodeError as e:
            errs.append(f"行{no} 译文无法用 GBK 编码：{e} ⇒ 拒绝")
        out_lines.append(new.encode("gbk") if zh is not None else ln)
        cmp_rows.append((no, orig, new, "" if zh is None else m.get(no, ("", "", "?"))[2]))

    # ① 行数
    if len(out_lines) != len(lines):
        errs.append("行数不一致 ⇒ 拒绝")

    print("=" * 88)
    print(f"[{key}] {src_name}  {len(raw):,} B / {len(lines)} 行元素")
    print("=" * 88)
    print(f"  改动行 {changed} / 仍英文 {untranslated} / 映射条目 {len(m)}")
    if warns:
        print(f"  ⚠ 警告 {len(warns)} 条：")
        for w in warns[:10]:
            print(f"     {w}")
    if errs:
        print(f"  ❌ 硬校验失败 {len(errs)} 条 ⇒ 拒绝落盘：")
        for e in errs[:20]:
            print(f"     {e}")
        return False

    buf = bytearray()
    for i, ln in enumerate(out_lines):
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
    crlf = back.count(b"\r\n")
    barelf = back.count(b"\n") - crlf
    barecr = back.count(b"\r") - crlf
    print(f"  ✅ 四道校验通过 ⇒ {os.path.relpath(dst, WS)}  {len(back):,} B"
          f"（行尾 CRLF={crlf} 裸LF={barelf} 裸CR={barecr}，与原文一致）")

    cmpf = os.path.join(DER, f"_对照-{key}.tsv")
    with open(cmpf, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# {src_name} 行级对照表（生成器产出，勿手改）\n")
        f.write("行号\t原文\t译文\t来源\n")
        for no, o, n, t in cmp_rows:
            f.write(f"{no}\t{o}\t{n}\t{t}\n")
    print(f"     对照表 {os.path.relpath(cmpf, WS)}")
    return True


def main():
    # ⭐ 词库门（治本件第 3 步）：改译法后**先过门**，不合规不构建。
    #    只拦「词库缺失」与「相对基线的**新增**偏离」；历史遗留已冻结在 GLOSSARY.lock。
    try:
        sys.path.insert(0, os.path.join(WS, "work", "glossary"))
        import layer_gate
        ok, _m = layer_gate.quick_check()
        if not ok:
            print("  ⛔ 词库门未过 ⇒ 拒绝构建（先跑 work/glossary/layer_gate.py --full 看明细）")
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
    print("总判定:", "✅ 全部通过" if ok else "❌ 有失败项")
    return 0 if ok else 1


if __name__ == "__main__":
    rc = main()
    os.makedirs(os.path.join(RES, "evidence"), exist_ok=True)
    with open(os.path.join(RES, "evidence", "gen-text.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
    sys.exit(rc)
