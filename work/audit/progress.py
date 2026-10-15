# -*- coding: utf-8 -*-
"""全库汉化进度实测（唯源：直读文件，不看映射表、不采信文档自述）。

用法：
    python progress.py                 # 打印 markdown 表格（docs\\00 的进度区由它生成）
    python progress.py --dump-fake     # 打印实证假汉字黑名单

判据（重要，三处都踩过坑）：
 1. **汉字一律按 GB2312 字节范围认定**（`gb2312_han()`）。cp1252 高字节
    （ä=0xE4 / Ü=0xDC / ñ=0xF1 …）与后继字节会被 GBK 拼成**假汉字**
    （`Pr鋞or` / `S蹹SCHAR` / `Compa耥a`=Compañía / `H鲻r`），把未译串算成已译。
 2. 光靠 GB2312 不够 —— `耥`(U+8025) / `鲻`(U+9CBB) / `篥` / `屮` / `篾` 这些
    **确在 GB2312 内**，仍会被误判。故再叠一层**实证黑名单** `FAKE_HAN`：
    扫「纯 cp1252 原文侧」（`backup\\ORIGINAL-*` + 未开始 efile 的 `SCENARIO\\*.xscn`）
    里解出的全部汉字，它们必然是假汉字。
 3. `.ply`「有正文」必须**先剔 NUL** —— 501 B 全 NUL 的空壳 `strip()` 去不掉 NUL，
    否则 AO(3)/Clu(22)/PzLIGA(14) 这些空文件全被算成有正文（曾把 63 误报成 100）。
"""
import glob
import hashlib
import os
import re
import struct
import sys

GAME = r"D:\OpenPG2"
WORK = r"D:\DSH\军事游戏汉化"
CJK = re.compile(r"[\u4e00-\u9fff]")
LAT = re.compile(r"[A-Za-z]")
# 「口径保留」样式：纯符号/数字/大写缩写，或方括号包裹，或 IJN 舰名
KEEP_PAT = re.compile(r"^[\[\]\(\)\{\}\-/\\.:,\s]*[A-Z0-9\[\]\(\)\{\}\-/\\.:,\s]*$")


# ------------------------------------------------------------------ 判据基础
def gb2312_han(ch):
    """该字符是否为 GB2312 汉字（0xB0A1–0xF7FE）。"""
    try:
        bs = ch.encode("gb2312")
    except UnicodeEncodeError:
        return False
    return len(bs) == 2 and 0xB0 <= bs[0] <= 0xF7 and 0xA1 <= bs[1] <= 0xFE


def build_fake_han(efile):
    """**按 efile** 实证假汉字集合。

    来源优先级：
      1. `backup\\ORIGINAL-<efile>\\SCENARIO\\*.xscn`（已汉化 efile 的原文备份）
      2. `<efile>\\SCENARIO\\*.xscn`（未汉化 efile 的当前文件 = 原文）
    ⚠️ 必须**分 efile**：全局合并会把 KAISER 的假汉字（`師` 等）拿去排除
    AG 的真译文，导致 AG 少算。局限：若某 efile 无备份却已部分汉化，会被污染。
    """
    if efile in _FAKE_CACHE:
        return _FAKE_CACHE[efile]
    fake = set()
    pats = glob.glob(os.path.join(WORK, "backup", "ORIGINAL-" + efile, "SCENARIO", "*.xscn"))
    if not pats:
        pats = glob.glob(os.path.join(GAME, efile, "SCENARIO", "*.xscn"))
    for f in pats:
        try:
            b = open(f, "rb").read()
        except OSError:
            continue
        if not any(x >= 0x80 for x in b):
            continue
        for ch in b.decode("gbk", "replace"):
            if "\u4e00" <= ch <= "\u9fff":
                fake.add(ch)
    _FAKE_CACHE[efile] = fake
    return fake


_FAKE_CACHE = {}
FAKE_HAN = set()          # 仅 --dump-fake 用（全库并集）


def han(ch, fake):
    return gb2312_han(ch) and ch not in fake


def _printable(b):
    """槽字节合法性：可打印 ASCII / 高位字节（GBK 前导+尾字节） / 制表换行。

    逐字沿用 `work\\xscn\\xscn.py::_printable`（2026-09-29 同步，见 MECHANICS §18/§20）。
    ⚠️ 这是**启发式守卫**，只用于「明显异常时保守跳过」，绝不是「组是否结束」的信号。
    """
    return b >= 0x20 or b in (0x09, 0x0A, 0x0D)


def zh_score(b, fake=frozenset()):
    """最长连续「真汉字」段长度；0 = 无汉字（原文/残留/纯符号）。"""
    try:
        s = b.decode("gbk")
    except UnicodeDecodeError:
        s = b.decode("gbk", "replace")
    best = cur = 0
    for ch in s:
        if han(ch, fake):
            cur += 1
            if cur > best:
                best = cur
        else:
            cur = 0
    return best


def is_zh(b, fake=frozenset()):
    return zh_score(b, fake) >= 1


def txt_is_zh(b, fake=frozenset()):
    """`.txt` 中文侧是否已汉化。

    ⚠️ 只用 `zh_score >= 3`（最长**连续**汉字段 ≥3）会**漏计短标签文件** ——
       `bberlin.txt`＝「柏林」、`bchannel.txt`＝「海峡」、`cm4don.txt`＝「顿河」这类
       全文件只有 2 个汉字 ⇒ 被判「未中文化」（BASEKORP 报表 2,338 / 实际 2,344）。
    判据（2026-09-29 修）：连续段 ≥3 **或**（连续段 ≥2 且**无残留拉丁字母**）。
       后半段是保守的：只要还留着英文词就不算已汉化。
    """
    if zh_score(b, fake) >= 3:
        return True
    return zh_score(b, fake) >= 2 and not LAT.search(b.decode("gbk", "replace"))


def kept_style(b):
    """残留串是否为「按口径保留」：舰名、方括号标记、纯编号/缩写、游戏自带数据。

    ⚠️ 这是**启发式**，不能穷举。OLGWW2 修完后仍剩 ~50 条未命中此判据者，
    已人工核验全为军舰舰名 / 火炮口径（`Achilles` / `Admiral Hipper` / `3 inch/45`
    / `Victoria/[Col. A.Vega]`）⇒ 同属 §五 口径保留。故「完成」用**比例阈值**
    （疑似漏译 ≤ 0.5%）而非绝对 0。
    """
    s = b.decode("gbk", "replace").strip().strip("\"'`´«»“”‘’")
    if not s:
        return True
    if s == "Name Error":                     # 游戏自带（原始备份里同样存在）
        return True
    if s.startswith("[") or "/[" in s:        # 方括号包裹的编队/番号标记
        return True
    if s.startswith(("USS ", "HMS ", "HMAS ", "HMIS ", "KMS ", "IJN ", "RM ", "MN ",
                     "ORP ", "HNLMS ", "ARA ", "SM ", "Almirante ", "Reggia",
                     "HMNZ ", "HMNoS ", "HSM ", "KM ", "RNI ", "SMG ", "NS ", "Uad ")):
        return True                           # 军舰舰名（口径：保留原文）
    if s.endswith(" Maru"):                   # 日本商船
        return True
    if re.search(r"\d\s*(inch|mm|cm|pdr)", s, re.I):   # 火炮口径
        return True
    core = re.sub(r"[\[\]\(\)\{\}\-/\\.:,\s]", "", s)
    if not core:                              # 纯符号
        return True
    if re.fullmatch(r"[A-Z0-9a-z\.]+", core) and not re.search(r"[a-z]{3,}", core):
        return True                           # 无 3+ 连续小写 ⇒ 更像编号/缩写
    return False


# ------------------------------------------------------------------ PE / exe
def pe_sections(d):
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    nsec = struct.unpack_from("<H", d, pe + 6)[0]
    opt = struct.unpack_from("<H", d, pe + 20)[0]
    base = pe + 24 + opt
    out = []
    for i in range(nsec):
        o = base + i * 40
        name = d[o:o + 8].rstrip(b"\0").decode("latin1")
        vs, va, rs, fo = struct.unpack_from("<IIII", d, o + 8)
        out.append((name, va, fo, rs, vs))
    return pe, out


def rva2fo(secs, rva):
    for n, va, fo, rs, vs in secs:
        if va <= rva < va + rs:
            return fo + (rva - va)
    return None


def walk_res(d, secs):
    pe, _ = pe_sections(d)
    rva, _sz = struct.unpack_from("<II", d, pe + 24 + 96 + 2 * 8)
    rbase = rva2fo(secs, rva)
    res = []

    def walk(off, level, path):
        n_named, n_id = struct.unpack_from("<HH", d, off + 12)
        for i in range(n_named + n_id):
            eo = off + 16 + i * 8
            name, offv = struct.unpack_from("<II", d, eo)
            if name & 0x80000000:
                nmoff = rbase + (name & 0x7FFFFFFF)
                ln = struct.unpack_from("<H", d, nmoff)[0]
                nm = d[nmoff + 2:nmoff + 2 + ln * 2].decode("utf-16le")
            else:
                nm = name
            child = rbase + (offv & 0x7FFFFFFF)
            if level < 2:
                walk(child, level + 1, path + [nm])
            else:
                do, ds = struct.unpack_from("<II", d, child)
                res.append((path + [nm], rva2fo(secs, do), ds))

    walk(rbase, 0, [])
    return res


# ------------------------------------------------------------------ .xscn
def parse_xscn(data):
    """返回 (title, entries)；cnt==0 视为合法空组（不是结束信号）。"""
    st = data.find(b"<N:")
    if st < 0:
        return None, []
    try:
        e = data.index(b">", st)
    except ValueError:
        return None, []
    off = e + 1
    if off + 2 > len(data):
        return None, []
    tl = int.from_bytes(data[off:off + 2], "little")
    off += 2
    title = data[off:off + tl]
    off += tl
    out = []
    while off + 2 <= len(data):
        cnt = int.from_bytes(data[off:off + 2], "little")
        off += 2
        if cnt == 0:
            if off >= len(data):
                break
            continue
        ok = True
        for _ in range(cnt):
            if off + 2 > len(data):
                ok = False
                break
            L = int.from_bytes(data[off:off + 2], "little")
            off += 2
            if L > len(data) - off:
                ok = False
                break
            chunk = data[off:off + L]
            # 组内条目**不全是字符串**：存在二进制槽（占 u16 len + L 字节，但非文本）。
            # ⇒ 跳过登记，但**仍推进 off**（MECHANICS §18）。旧版无条件登记 ⇒
            #   全库 16 个非文本槽被当可译条目，且虚增 leak（MECHANICS §20）。
            if all(_printable(c) for c in chunk):
                out.append(chunk)
            off += L
        if not ok or off >= len(data):
            break
    return title, out


# ------------------------------------------------------------------ 各层
def sec_l1():
    p = os.path.join(GAME, "OPENGUI", "strings-zh.txt")
    if not os.path.exists(p):
        return [("L1 UI 主串", "缺失 " + p, "-")]
    raw = open(p, "rb").read()
    txt = None
    for enc in ("gbk", "utf-8"):
        try:
            txt = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    ne = [L for L in txt.replace("\r\n", "\n").split("\n") if L.strip()]
    # `*` 开头 = 官方模板注释（引擎不读，见 MEMORY §七.10）；段标记 [xxx] 也不译
    body = [L for L in ne if not L.lstrip().startswith("*")
            and not (L.strip().startswith("[") and L.strip().endswith("]"))]
    zh = [L for L in body if CJK.search(L)]
    keep = [L for L in body if not CJK.search(L)]
    return [("L1 UI 主串",
             f"{len(ne)} 非空行；去 `*` 注释后 **{len(body)} 待译行 / {len(zh)} 含汉字**，"
             f"其余 {len(keep)} 行全为应保留项",
             "100%" if len(keep) <= 20 else "?")]


def sec_l7():
    p = os.path.join(GAME, "OpenGen.exe")
    d = open(p, "rb").read()
    md5 = hashlib.md5(d).hexdigest()
    secs = pe_sections(d)[1]
    led = os.path.join(WORK, "work", "exe", "ledger.md")
    cur = None
    if os.path.exists(led):
        t = open(led, encoding="utf-8", errors="replace").read()
        m = re.search(r"\|\s*\*\*当前\*\*\s*\|\s*\*\*`([0-9A-Fa-f]{32})`\*\*", t)
        if m:
            cur = m.group(1)
    ok = "台账一致" if (cur and cur.lower() == md5) else ("台账记 " + (cur or "?")[:8])
    res = walk_res(d, secs)
    dlg = [x for x in res if x[0][0] == 5]
    dz = sum(1 for _p, fo, sz in dlg if CJK.search(d[fo:fo + sz].decode("utf-16le", "ignore")))
    return [("L7 exe", f"md5 `{md5[:8]}`；`RT_DIALOG` **{dz}/{len(dlg)}** 含中文", ok)]


def sec_l8():
    rows = []
    for pat, tag in ((os.path.join(GAME, "OPENGUI", "hex_text.png"), "hex_text(根)"),
                     (os.path.join(GAME, "EFILE_*", "OPENGUI", "hex_text.png"), "hex_text(efile)"),
                     (os.path.join(GAME, "OPENGUI", "mouse_build.png"), "mouse_build"),
                     (os.path.join(GAME, "OPENGUI", "mouse_missions.png"), "mouse_missions")):
        fs = glob.glob(pat)
        h = {}
        for f in fs:
            h.setdefault(hashlib.md5(open(f, "rb").read()).hexdigest()[:8], []).append(f)
        rows.append((tag, f"{len(fs)} 份 / {len(h)} 种内容", ", ".join(sorted(h)[:4])))
    return rows


def efile_scan():
    rows = []
    for d in sorted(os.listdir(GAME)):
        if not d.upper().startswith("EFILE_"):
            continue
        base = os.path.join(GAME, d)
        fake = build_fake_han(d)
        # .xscn
        n = nz = leak = 0
        for f in glob.glob(os.path.join(base, "SCENARIO", "*.xscn")):
            try:
                _t, ent = parse_xscn(open(f, "rb").read())
            except Exception:
                continue
            for e in ent:
                n += 1                     # 空串也计数（AG 有 4 个空串，口径与旧记录 7152 对齐）
                if not e.strip():
                    continue
                if is_zh(e, fake):
                    nz += 1
                elif not kept_style(e):
                    leak += 1
        # .txt（中文侧优先）—— 判据见 txt_is_zh()
        # ⚠️ 分母先剔「空壳」（strip 后为空，无正文可译）—— 与下方 .ply 同口径
        #    （§三 注 3）。否则 BASEKORP 会被 50 个空壳永久压在 97.9%，
        #    「完成」所需的 >99% 根本不可达（全库仅 BASEKORP 有空壳）。
        tx = []
        for f in glob.glob(os.path.join(base, "SCENARIO", "*.txt")):
            b = open(f, "rb").read()
            if b.replace(b"\r", b"").replace(b"\n", b"").strip(b" \t"):
                tx.append(f)
        tz = sum(1 for f in tx
                 if txt_is_zh(open(_zh_side(base, f), "rb").read(), fake))
        # .ply（先剔 NUL）
        pls = glob.glob(os.path.join(base, "SCENARIO", "*.ply"))
        pb = pz = 0
        for f in pls:
            b = open(f, "rb").read().replace(b"\x00", b"")
            s = b.decode("cp1252", "replace")
            if len(s.strip()) > 30 and "Intro text" not in s:
                pb += 1
                if zh_score(open(_zh_side(base, f), "rb").read().replace(b"\x00", b""), fake) > 0:
                    pz += 1
        rows.append((d.replace("EFILE_", ""), n, nz, leak, len(tx), tz, pb, pz))
    return rows


def _zh_side(base, f):
    """中文侧优先：TEXT-ZH\\SCENARIO\\ 同名文件存在则用它。"""
    zh = os.path.join(base, "TEXT-ZH", "SCENARIO", os.path.basename(f))
    return zh if os.path.exists(zh) else f


def main():
    if "--dump-fake" in sys.argv:
        for d in sorted(os.listdir(GAME)):
            if d.upper().startswith("EFILE_"):
                FAKE_HAN |= build_fake_han(d)
        print("实证假汉字（全库并集 %d 个）：%s" % (len(FAKE_HAN), "".join(sorted(FAKE_HAN))))
        return
    print("<!-- 由 work/audit/progress.py 生成；勿手改 -->")
    print("实测时间：%s" % __import__("time").strftime("%Y-%m-%d %H:%M"))
    print()
    for tag, val, note in sec_l1() + sec_l7():
        print(f"- **{tag}**：{val}　（{note}）")
    print()
    print("### L8 位图（内容种类数 < 份数 ⇒ 有重绘）")
    for tag, val, note in sec_l8():
        print(f"- {tag}：{val}")
    print()
    rows = efile_scan()
    tx = sum(r[1] for r in rows)
    txz = sum(r[2] for r in rows)
    tleak = sum(r[3] for r in rows)
    tt = sum(r[4] for r in rows)
    ttz = sum(r[5] for r in rows)
    tpb = sum(r[6] for r in rows)
    tpz = sum(r[7] for r in rows)
    print("### 各 efile 实测矩阵")
    print("| efile | `.xscn` 条 | 含汉字 | 占比 | 疑似漏译 | `.txt` | 已中文化 | 占比 | `.ply` 有正文 | 已中文化 |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for ef, n, nz, leak, t_n, t_z, pb, pz in rows:
        px = f"{nz * 100 / n:.1f}%" if n else "—"
        pt = f"{t_z * 100 / t_n:.1f}%" if t_n else "—"
        print(f"| {ef} | {n} | {nz} | {px} | {leak} | {t_n} | {t_z} | {pt} | {pb} | {pz} |")
    print(f"| **合计** | **{tx}** | **{txz}** | **{txz * 100 / tx:.1f}%** | **{tleak}** | "
          f"**{tt}** | **{ttz}** | **{ttz * 100 / tt:.1f}%** | **{tpb}** | **{tpz}** |")
    done = [r[0] for r in rows
            if r[1] and r[3] * 100.0 / r[1] <= 0.5 and (not r[4] or r[5] * 100.0 / r[4] > 99)
            and (not r[6] or r[7] == r[6])]
    print()
    print(f"**完成（`.xscn` 疑似漏译 ≤ 0.5% 且 `.txt` > 99% 且 `.ply` 全译）：{len(done)} 个 efile** —— "
          f"{'、'.join(done)}")
    print("\n> 「疑似漏译」= 既不含汉字、也不匹配「口径保留」样式（舰名/方括号/编号/缩写）的残留串。")
    print("> 该判据是启发式的最坏上界，实际多为舰名；各 efile 的**覆盖率**才是主指标。")
    print(f"> 假汉字黑名单按 efile 分建（`--dump-fake` 查全库并集）。")


if __name__ == "__main__":
    main()
