#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xsch.py —— `.xsch`（分支选择屏）结构解析 / 导出 / 回写。

★ 结构模型（2026-09-28 逆向；AO 双样本起手，**全库 52 文件 / 115 记录实测 0 异常**）：

    文件头 (24 B):
        u16  ver     = 1
        u16  count   = 选项（记录）数
        char[20] name            # 例 "choice1" / "pg_choice" / "1215"

    记录 × count（顺序紧排，无对齐填充）:
        12 B 头:  [0]u8 [1]u8 00 00 [4]u16 [6]u16 [8]u32
                  —— 全部是**版面/音轨/字体参数**，格式无关，回写时**原样保留**。
                  ⚠️ [0] 实测有 0x00 与 0x01 两种（OPENPG choice*.xsch 的 rec0 是 0x00）；
                     [8..12] 是 u32，实测 6 / 7 / 4000 / 0xFE… ⇒ **不是魔数，不可硬编码**。
        [槽 A]   固定 **104 B**，左对齐 + \0 填充；**槽内可含多个 \0 分隔的短串**
                 （例 OPENPG choice1：`North Africa\0Choice1_i\0PG1.mp3`）
        u16      tail = 槽 A 之后、从 tail 字段之后起算、到「本记录结束」的字节数
        [槽 B]   变长正文（\r\n 分行），长度 = tail

    记录结束 = (tail 字段结束处) + tail。最后一条记录的结束 == 文件长度（**唯一自洽判据**）。

⚠️ 四条铁律：
  1. **槽 A 是定长 104 B**（全库 52 文件实测一致）：译文（GBK）字节数**必须 ≤ 104**（填 \0），否则撑破。
     —— 多串槽要**逐段**替换，并保留段间 \0。
  2. **槽 B 变长**：改 B 后重算 `tail`，后续记录**整体平移** —— 结构无绝对偏移，只此一个相对长度 ⇒ 平移安全。
  3. 槽 A 是**选项标题**（可能含场景名/音轨名等机器串），槽 B 是**选项详情**（多行电报体）；
     只译**人类可读**的部分，机器串（`PG1.mp3` `Choice1_i`）**原样保留**。
  4. 文件头 [0]/[1]/[4]/[6]/[8..12] 一律原样回写；**不得**按"tag==0x01"之类假设做结构判据。

用法：
    python xsch.py --efile AO verify
    python xsch.py --efile AO verifyall
    python xsch.py --efile AO export [--out FILE]
    python xsch.py --efile AO apply --map FILE [--apply]     # src(槽A整段/槽B原文) -> dst
"""
import sys, os, struct, argparse

GAME = r"D:\OpenPG2"
ROOT = r"D:\DSH\军事游戏汉化"

HDR_SIZE = 24
REC_HDR = 12
SLOT_A = 104          # ★ 全库定长，实测 52/52


def parse(d):
    """解析 .xsch → (hdr, records)。records[i] 含 hdr/A/B 原始字节与偏移。"""
    if len(d) < HDR_SIZE + REC_HDR + SLOT_A + 2:
        raise ValueError("文件过短")
    ver, cnt = struct.unpack_from("<HH", d, 0)
    name = d[4:HDR_SIZE].split(b"\x00")[0].decode("cp1252")
    off = HDR_SIZE
    recs = []
    for i in range(cnt):
        if off + REC_HDR + SLOT_A + 2 > len(d):
            raise ValueError(f"记录 {i} 越界 (@0x{off:X})")
        hdr = d[off:off + REC_HDR]
        a0 = off + REC_HDR
        p = a0 + SLOT_A
        tail = struct.unpack_from("<H", d, p)[0]
        end = p + 2 + tail
        if end > len(d):
            raise ValueError(f"记录 {i} tail={tail} 溢出 (@0x{off:X})")
        recs.append({
            "idx": i,
            "hdr_off": off,
            "hdr": hdr,
            "A_off": a0,
            "A": d[a0:p],
            "tail_off": p,
            "tail": tail,
            "B_off": p + 2,
            "B": d[p + 2:end],
            "end": end,
        })
        off = end
    if off != len(d):
        raise ValueError(f"解析结束 0x{off:X} != 文件长度 0x{len(d):X}")
    return {"ver": ver, "cnt": cnt, "name": name}, recs


def build(hdr, recs, encoding="gbk"):
    """按记录重建文件。rec['A_zh']/rec['B_zh'] 为可选译文（str；A_zh 可携带 \0 分段）。"""
    out = bytearray()
    out += struct.pack("<HH", hdr["ver"], hdr["cnt"])
    out += hdr["name"].encode("cp1252").ljust(20, b"\x00")[:20]
    for r in recs:
        slot = bytearray(r["hdr"])
        A = r.get("A_zh")
        if A is None:
            slot += r["A"]
        else:
            # 译文按 \0 分段编码，段间补 \0，末尾 \0 填充至 SLOT_A
            parts = A.split("\x00")
            enc = b"\x00".join(p.encode(encoding) for p in parts)
            if len(enc) > SLOT_A:
                raise ValueError(f"记录 {r['idx']} 槽A 译文 {len(enc)}B > {SLOT_A}B")
            slot += enc.ljust(SLOT_A, b"\x00")
        B = r.get("B_zh")
        Bb = r["B"] if B is None else B.encode(encoding)
        if len(Bb) > 0xFFFF:
            raise ValueError(f"记录 {r['idx']} 槽B 译文过长")
        slot += struct.pack("<H", len(Bb))
        slot += Bb
        out += slot
    return bytes(out)


def _decode_slot_a(a):
    """槽 A 解码：拆 \0 分段，去尾部填充。返回 [(str|None), ...]。"""
    segs = a.rstrip(b"\x00").split(b"\x00")
    if segs == [b""]:
        return []
    return [s.decode("cp1252") for s in segs]


def _load(path):
    with open(path, "rb") as fh:
        return fh.read()


def _iter_lib():
    for ef in sorted(os.listdir(GAME)):
        sd = os.path.join(GAME, ef, "SCENARIO")
        if not os.path.isdir(sd):
            continue
        for f in sorted(x for x in os.listdir(sd) if x.lower().endswith(".xsch")):
            yield ef, f, os.path.join(sd, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--efile", help="verify/export/apply 用；verifyall 无需")
    ap.add_argument("op", choices=["verify", "verifyall", "export", "apply"])
    ap.add_argument("--map", help="apply：TSV（file\\tidx\\tfield(A|B)\\tsrc\\tdst）")
    ap.add_argument("--out")
    ap.add_argument("--apply", action="store_true", help="真正落盘（默认干跑）")
    a = ap.parse_args()

    if a.op == "verifyall":
        nf = nr = bad = 0
        for ef, f, p in _iter_lib():
            nf += 1
            try:
                hdr, recs = parse(_load(p))
                nr += len(recs)
            except Exception as e:
                bad += 1
                print(f"  ❌ {ef}/{f}  {e}")
        print(f"全库 .xsch：{nf} 文件 / {nr} 记录；结构异常 {bad}")
        return 0 if bad == 0 else 1

    if not a.efile:
        print("verify/export/apply 需要 --efile")
        return 2
    base = os.path.join(GAME, "EFILE_" + a.efile, "SCENARIO")
    files = sorted(f for f in os.listdir(base) if f.lower().endswith(".xsch"))

    if a.op == "verify":
        bad = 0
        for f in files:
            p = os.path.join(base, f)
            try:
                hdr, recs = parse(_load(p))
                nb = sum(1 for r in recs if r["B"])
                segs = [len(_decode_slot_a(r["A"])) for r in recs]
                print(f"  {f:22s} cnt={hdr['cnt']} OK  B非空={nb} A段数={segs}")
            except Exception as e:
                print(f"  {f:22s} ❌ {e}")
                bad += 1
        print(f"{a.efile}: {len(files)} 文件，结构异常 {bad}")
        return 0 if bad == 0 else 1

    if a.op == "export":
        rows = []
        for f in files:
            hdr, recs = parse(_load(os.path.join(base, f)))
            for r in recs:
                Asegs = _decode_slot_a(r["A"])
                rows.append((f, r["idx"], Asegs, r["B"].decode("cp1252")))
        out = a.out or os.path.join(ROOT, "work", "ao", f"{a.efile.lower()}-xsch-export.tsv")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("file\trec\tA_segs\tB\n")
            for f, i, Asegs, B in rows:
                fh.write(f"{f}\t{i}\t{' | '.join(Asegs)}\t{B.replace(chr(13)+chr(10),'<CRLF>')}\n")
        print(f"导出 {len(rows)} 条 -> {out}")
        return 0

    if a.op == "apply":
        if not a.map:
            print("apply 需要 --map")
            return 2
        def unesc(s):
            return (s.replace("<CRLF>", "\r\n")
                     .replace("\\r\\n", "\r\n")
                     .replace("\\n", "\r\n"))
        mapping = {}
        with open(a.map, encoding="utf-8") as fh:
            next(fh, None)
            for line in fh:
                line = line.rstrip("\n")
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) < 5:
                    continue
                fn, idx, field, src, dst = parts[0], int(parts[1]), parts[2], parts[3], parts[4]
                mapping[(fn, idx, field)] = (unesc(src), unesc(dst))
        changed = total = 0
        for f in files:
            p = os.path.join(base, f)
            hdr, recs = parse(_load(p))
            hit = 0
            for r in recs:
                k = (f, r["idx"], "B")
                if k in mapping:
                    src, dst = mapping[k]
                    if r["B"].decode("cp1252") != src:
                        print(f"  ⚠️ {f} rec{r['idx']} B 原文不符，跳过")
                        continue
                    r["B_zh"] = dst
                    hit += 1
                k = (f, r["idx"], "A")
                if k in mapping:
                    src, dst = mapping[k]
                    cur = "\x00".join(_decode_slot_a(r["A"]))
                    if cur != src:
                        print(f"  ⚠️ {f} rec{r['idx']} A 原文不符，跳过")
                        continue
                    r["A_zh"] = dst
                    hit += 1
            total += hit
            if hit == 0:
                continue
            new = build(hdr, recs)
            if a.apply:
                with open(p, "wb") as fh:
                    fh.write(new)
            changed += 1
            print(f"  {'✅' if a.apply else '🔍'} {f}: {hit} 处{'已写' if a.apply else '(干跑)'}")
        print(f"{'已写' if a.apply else '干跑'}：{changed} 文件 / {total} 处")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
