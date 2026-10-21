# -*- coding: utf-8 -*-
"""S1：从「母本 PeG030.exe」与「v4 实验产物 PeG030res.exe」的逐字节 diff 反推
分辨率补丁的全部改动点，做语义标注，并**生成**可复现的 patch_resolution.py。

背景：上一个工作区（D:\\DSH\\军事游戏汉化-1，已删除）里这批脚本与日志全部丢失，
唯一幸存产物是 D:\\Program Files\\PeG-1\\PeG030res.exe（2026-10-13 01:12:02）。
两个安装目录的 PeG030.exe 逐字节相同（md5 C462E897B3AA1C384870C857CE9E01DF），
因此 母本↔res 的 diff 就是那条实验线的全部改动点。

提取口径：对每个连续差异段，在 ±4 字节内枚举所有能覆盖它的 2/4 字节小端窗口，
取「窗口起点=差异段起点、宽度最小、能打上标签」的那个。标签规则：
  w / w-1 / w-4 / h / h-1 / h-28 / h-30  绝对值：旧值 → 新分辨率下的定值
  dx / dy                                平移量：旧值 + (w-800) / 旧值 + (h-600)
注：799/796/599/570/572 这几条与 dx/dy **代数上恒等**（799+dx = w-1 恒成立），
保留绝对标签只为可读；唯一不等价的是 571 → h-28。

自证：按站点重放一遍应当与 v4 产物逐字节相同（否则脚本报错不生成）。

只读：本脚本不修改、不写入任何游戏文件。
输出：
  work/peg/out/res_diff_v4.tsv        逐站点明细
  work/peg/out/res_diff_report.txt    语义报告（含 .text 指令上下文）
  work/peg/patch_resolution.py        自动生成的可复现补丁脚本（内嵌站点表）
"""
import collections
import datetime
import hashlib
import os
import struct
import sys

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(GAME, "PeG030.exe")        # 母本（中文主线，绝不修改）
DST = os.path.join(GAME_ALT, "PeG030res.exe")   # v4 实验产物（1024x768）
SRC_MD5 = "c462e897b3aa1c384870c857ce9e01df"
DST_MD5 = "2107b73bbfd4213719b622a1a9d4c6ad"
OUT_DIR = os.path.join(HERE, "out")

PW, PH = 1024, 768            # v4 产物对应的分辨率
PDX, PDY = PW - 800, PH - 600

# 中文补丁标记（必须原样保留在产物里）。前两条给 VA，第三条给文件偏移。
# 注意：VA→FO 不能套 .text 的换算公式（VA-0x401000+0x400），必须走节表，
# 例如 0x4ABC8C 在 .data 里，对应 FO 0xA948C。
CHECKS_VA = [
    ("charset 0x4718E3", 0x4718E3, b"\x6a\x86"),
    ("__mbcodepage 0x4ABC8C", 0x4ABC8C, b"\xa8\x03"),
]
CHECKS_FO = [
    ("LCID fo 0x7BE86", 0x7BE86, b"\xb8\x04\x08\x00\x00"),
]


def md5f(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def parse_pe(data):
    e = struct.unpack_from("<I", data, 0x3C)[0]
    assert data[e:e + 4] == b"PE\0\0", "不是 PE"
    coff = e + 4
    nsec = struct.unpack_from("<H", data, coff + 2)[0]
    opt_size = struct.unpack_from("<H", data, coff + 16)[0]
    opt = coff + 20
    magic = struct.unpack_from("<H", data, opt)[0]
    base = struct.unpack_from("<I", data, opt + 28)[0] if magic == 0x10B else struct.unpack_from("<Q", data, opt + 24)[0]
    secs = []
    for i in range(nsec):
        off = opt + opt_size + i * 40
        raw = data[off:off + 40]
        name = raw[:8].rstrip(b"\0").decode("latin1")
        vsize, va, raw_size, raw_off = struct.unpack_from("<IIII", raw, 8)
        secs.append((name, va, vsize, raw_off, raw_size))
    return base, secs


def fo_to_va(fo, base, secs):
    for name, sva, vsize, raw_off, raw_size in secs:
        if raw_off <= fo < raw_off + raw_size:
            return base + sva + (fo - raw_off), name
    return None, "?"


def va_to_fo(va, base, secs):
    rva = va - base
    for name, sva, vsize, raw_off, raw_size in secs:
        if sva <= rva < sva + raw_size:
            return raw_off + (rva - sva), name
    return None, "?"


def resolve_checks(base, secs):
    """把中文补丁标记统一解析成 (标签, 文件偏移, 期望字节)"""
    out = []
    for lbl, va, exp in CHECKS_VA:
        fo, sec = va_to_fo(va, base, secs)
        if fo is None:
            raise SystemExit("中文补丁标记 VA 0x%X 不在任何节里" % va)
        out.append(("%s (%s)" % (lbl, sec), fo, exp))
    for lbl, fo, exp in CHECKS_FO:
        out.append((lbl, fo, exp))
    return out


def tag_slot(ov, nv):
    """整数值对 (old,new) 的语义标签；认不出返回 None"""
    if ov == 800 and nv == PW:
        return "w"
    if ov == 799 and nv == PW - 1:
        return "w-1"
    if ov == 796 and nv == PW - 4:
        return "w-4"
    if ov == 600 and nv == PH:
        return "h"
    if ov == 599 and nv == PH - 1:
        return "h-1"
    if ov in (571, 572) and nv == PH - 28:
        return "h-28"
    if ov == 570 and nv == PH - 30:
        return "h-30"
    if nv == ov + PDX:
        return "dx"
    if nv == ov + PDY:
        return "dy"
    return None


def extract():
    src = open(SRC, "rb").read()
    dst = open(DST, "rb").read()
    base, secs = parse_pe(src)
    n = min(len(src), len(dst))
    runs = []
    i = 0
    while i < n:
        if src[i] != dst[i]:
            j = i
            while j < n and src[j] != dst[j]:
                j += 1
            runs.append((i, j))
            i = j
        else:
            i += 1
    ndiff = sum(b - a for a, b in runs)

    sites, unknown = [], []
    for fo, end in runs:
        best = None
        for width in (2, 4):
            for start in range(fo - width + 1, end):
                if start < 0 or start + width > n:
                    continue
                if not (start <= fo and start + width >= end):
                    continue
                ov = int.from_bytes(src[start:start + width], "little")
                nv = int.from_bytes(dst[start:start + width], "little")
                if ov == nv:
                    continue
                t = tag_slot(ov, nv)
                if t is None:
                    continue
                key = (0 if start == fo else 1, 0 if width == 2 else 1, abs(start - fo))
                if best is None or key < best[0]:
                    best = (key, start, width, ov, nv, t)
        if best is None:
            unknown.append((fo, end, src[fo:end].hex(" "), dst[fo:end].hex(" ")))
            continue
        _, start, width, ov, nv, t = best
        va, sec = fo_to_va(start, base, secs)
        sites.append((start, va, sec, ov, nv, t, width))

    # 全覆盖性 + 自证重放
    changed = bytearray(n)
    for a, b in runs:
        for k in range(a, b):
            changed[k] = 1
    covered = bytearray(n)
    for fo, va, sec, ov, nv, t, width in sites:
        for k in range(fo, fo + width):
            covered[k] = 1
    miss = [x for x in range(n) if changed[x] and not covered[x]]

    replay = bytearray(src)
    for fo, va, sec, ov, nv, t, width in sites:
        replay[fo:fo + width] = nv.to_bytes(width, "little")
    replay_ok = bytes(replay) == dst

    text_sec = [s for s in secs if s[0] == ".text"][0]
    info = dict(ndiff=ndiff, nruns=len(runs), miss=miss, replay_ok=replay_ok)
    return src, dst, base, secs, sites, unknown, info, text_sec


def main():
    src, dst, base, secs, sites, unknown, info, text_sec = extract()
    checks = resolve_checks(base, secs)
    rep = []

    def out(s=""):
        rep.append(s)

    out("母本 %s  %d B  md5 %s" % (SRC, len(src), md5f(SRC)))
    out("产物 %s  %d B  md5 %s" % (DST, len(dst), md5f(DST)))
    out("ImageBase 0x%X  母本md5相符=%s  等长=%s  产物md5相符=%s" %
        (base, md5f(SRC) == SRC_MD5, len(src) == len(dst), md5f(DST) == DST_MD5))
    for name, sva, vsize, raw_off, raw_size in secs:
        out("  %-8s VA 0x%06X vsize %-8d raw 0x%06X size %-8d" % (name, base + sva, vsize, raw_off, raw_size))
    out("\n差异字节 %d，连续段 %d，站点 %d，认不出 %d，未被覆盖的差异字节 %d %s" %
        (info["ndiff"], info["nruns"], len(sites), len(unknown), len(info["miss"]),
         ("（首个 0x%X）" % info["miss"][0]) if info["miss"] else ""))
    out("自证重放（按站点重放后与 v4 产物逐字节相同）：%s" % ("✅" if info["replay_ok"] else "❌"))

    out("\n== 标签直方图（节 × 语义 × 宽度） ==")
    for (sec, t, wd), c in sorted(collections.Counter((s[2], s[5], s[6]) for s in sites).items(),
                                  key=lambda x: (-x[1], x[0])):
        out("  %-8s %-6s u%d  %d" % (sec, t, wd, c))
    if unknown:
        out("\n⚠ 认不出的差异段 %d 个：" % len(unknown))
        for fo, end, ob, nb in unknown:
            out("  fo 0x%06X..0x%06X  %s -> %s" % (fo, end, ob, nb))

    out("\n== .data 同标签站点间距（推断记录步长） ==")
    byt = collections.defaultdict(list)
    for fo, va, sec, ov, nv, t, wd in sites:
        if sec == ".data":
            byt[t].append(fo)
    for t, offs in sorted(byt.items(), key=lambda x: -len(x[1])):
        offs = sorted(offs)
        gaps = collections.Counter(b - a for a, b in zip(offs, offs[1:]))
        out("  %-6s n=%-4d 间距 %s" % (t, len(offs), ", ".join("%d×%d" % (g, c) for g, c in gaps.most_common(8))))

    # capstone：给 .text 站点配指令文本
    notes = {}
    have_cs = False
    try:
        from capstone import Cs, CS_ARCH_X86, CS_MODE_32
        md = Cs(CS_ARCH_X86, CS_MODE_32)
        have_cs = True
    except Exception as exc:
        out("\n（无 capstone：%s）" % exc)
    if have_cs:
        for fo, va, sec, ov, nv, t, wd in sites:
            if sec != ".text":
                continue
            lo = max(text_sec[3], fo - 20)
            cva, _ = fo_to_va(lo, base, secs)
            for ins in md.disasm(src[lo:fo + 20], cva):
                if ins.address <= va < ins.address + ins.size:
                    notes[fo] = "%s %s" % (ins.mnemonic, ins.op_str)
        out("\n== .text 站点（指令上下文） ==")
        seen = set()
        for fo, va, sec, ov, nv, t, wd in sites:
            if sec != ".text":
                continue
            lo = max(text_sec[3], fo - 20)
            cva, _ = fo_to_va(lo, base, secs)
            hit = None
            for ins in md.disasm(src[lo:fo + 20], cva):
                if ins.address <= va < ins.address + ins.size:
                    hit = ins.address
            if hit in seen:
                continue
            seen.add(hit)
            out("-- fo 0x%06X VA 0x%06X  %d -> %d  [%s u%d]  %s" %
                (fo, va, ov, nv, t, wd, notes.get(fo, "")))
            for ins in md.disasm(src[lo:fo + 20], cva):
                mark = "   <<<< 本槽" if ins.address <= va < ins.address + ins.size else ""
                out("    0x%06X  %-22s %-34s%s" % (ins.address, ins.bytes.hex(" "), ins.mnemonic + " " + ins.op_str, mark))

    out("\n== .data 站点 ==")
    for fo, va, sec, ov, nv, t, wd in sites:
        if sec == ".data":
            out("  fo 0x%06X VA 0x%06X  %-6d -> %-6d [%s u%d]" % (fo, va, ov, nv, t, wd))

    out("\n== 中文补丁复核（产物必须保留） ==")
    for lbl, fo, exp in checks:
        got_s, got_d = src[fo:fo + len(exp)], dst[fo:fo + len(exp)]
        out("  %-28s fo 0x%06X 母本 %-14s 产物 %-14s %s" %
            (lbl, fo, got_s.hex(" "), got_d.hex(" "), "OK" if got_d == exp else "⚠不符"))

    os.makedirs(OUT_DIR, exist_ok=True)
    tsv = os.path.join(OUT_DIR, "res_diff_v4.tsv")
    with open(tsv, "w", encoding="utf-8", newline="") as f:
        f.write("index\tsection\tva\tfile_off\twidth\told\tnew\ttag\tnote\n")
        for idx, (fo, va, sec, ov, nv, t, wd) in enumerate(sites):
            f.write("%d\t%s\t0x%06X\t0x%06X\t%d\t%d\t%d\t%s\t%s\n" %
                    (idx, sec, va, fo, wd, ov, nv, t, notes.get(fo, "")))
    rpt = os.path.join(OUT_DIR, "res_diff_report.txt")
    with open(rpt, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(rep) + "\n")
    gen = os.path.join(HERE, "patch_resolution.py")
    if info["replay_ok"] and not unknown and not info["miss"]:
        with open(gen, "w", encoding="utf-8", newline="\n") as f:
            f.write(render_patch_script(sites, unknown, notes, info["ndiff"], info["nruns"], checks))
        out("\n已生成 %s" % gen)
    else:
        out("\n⚠ 自证未通过，未生成补丁脚本")
    print("\n".join(rep))
    print("\n已写 %s\n已写 %s" % (tsv, rpt))
    return 0 if (info["replay_ok"] and not unknown) else 2


PATCH_HEAD = '''# -*- coding: utf-8 -*-
"""PeG 分辨率补丁 v5（由 diff 反推重建）——生成于 {stamp}

本文件由 work/peg/diff_res_canvas.py 自动生成，请勿手改；改口径请改生成器。

来源：母本 PeG030.exe（md5 {src_md5}）
      与 v4 实验产物 PeG030res.exe（md5 {dst_md5}）逐字节 diff
      = 差异 {ndiff} 字节 / {nruns} 个连续段 / {nsites} 个站点
      v4 站点对应分辨率 {pw}x{ph}，按站点重放与 v4 产物**逐字节相同**

纪律（继承原 v4）：
  * 绝不修改母本 PeG030.exe；只读当母本，产物另写副本；
  * 每个站点写入前做内容断言（当前整数必须等于记录里的旧值），任一不符即整体拒改；
  * 先写内存 -> 回读校验 -> 才落盘；
  * 落盘后复核中文补丁三处仍在（charset / codepage / LCID）；
  * 站点里若还有认不出的改动，脚本整体拒绝（绝不产出半成品 exe）。

站点语义（tag）：
  w / w-1 / w-4    绝对值：800 / 799 / 796  -> w / w-1 / w-4
  h / h-1          绝对值：600 / 599        -> h / h-1
  h-28 / h-30      绝对值：571|572 / 570    -> h-28 / h-30
  dx / dy          平移：旧值 + (w-800) / 旧值 + (h-600)
  （799/796/599/570/572 的绝对标签与 dx/dy 代数恒等；唯一不等价的是 571 -> h-28）

用法：
  python patch_resolution.py                              干跑：校验母本、逐点断言、打印计划
  python patch_resolution.py --repro                      复现 v4 产物并比对 md5（完整性自证）
  python patch_resolution.py --w 1280 --h 960 --out out/x.exe           干跑新分辨率
  python patch_resolution.py --w 1280 --h 960 --out out/x.exe --apply   落盘
  默认只写 work/peg/out/ 下的副本；要部署到安装目录请自己显式 --out。

母本若换版本（再次汉化改动等），md5 校验会失败并拒绝运行，需重跑 diff_res_canvas.py。
"""
import argparse
import hashlib
import os
import struct
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SRC = r"D:\\Program Files\\PeG\\PeG030.exe"
DST_V4 = r"D:\\Program Files\\PeG-1\\PeG030res.exe"
SRC_MD5 = "{src_md5}"
DST_V4_MD5 = "{dst_md5}"
HERE = os.path.dirname(os.path.abspath(__file__))

# 中文补丁必须在产物里保留的三处（文件偏移, 期望字节）
CN_CHECKS = [
{cn_checks}
]

# 认不出的改动点（必须为空；非空则拒绝运行）
UNKNOWN = [
{unknown_lines}
]

# (文件偏移, VA, 旧值, 标签, 宽度)，备注 = 原指令
SITES = [
{site_lines}
]


def md5f(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def new_value(tag, old, w, h):
    if tag == "w":
        return w
    if tag == "w-1":
        return w - 1
    if tag == "w-4":
        return w - 4
    if tag == "h":
        return h
    if tag == "h-1":
        return h - 1
    if tag == "h-28":
        return h - 28
    if tag == "h-30":
        return h - 30
    if tag == "dx":
        return old + (w - 800)
    if tag == "dy":
        return old + (h - 600)
    raise SystemExit("未知标签 %r" % tag)


def build(w, h, quiet=False):
    """在内存里造出产物字节；返回 (bytes, 计划列表)"""
    if w < 800 or h < 600:
        raise SystemExit("拒绝：只有 w>=800 且 h>=600 才成立（右移/下拉假设），收到 %dx%d" % (w, h))
    if UNKNOWN:
        raise SystemExit("拒绝：还有 %d 个认不出的改动点，需先补齐语义" % len(UNKNOWN))
    raw = open(SRC, "rb").read()
    got = md5f(SRC)
    if got != SRC_MD5:
        raise SystemExit("拒绝：母本 md5 %s != 记录 %s" % (got, SRC_MD5))
    buf = bytearray(raw)
    plan = []
    for fo, va, old, tag, width in SITES:
        cur = int.from_bytes(buf[fo:fo + width], "little")
        nv = new_value(tag, old, w, h)
        if cur != old:
            raise SystemExit("内容断言失败 @fo 0x%06X VA 0x%06X [%s]：当前 %d，记录旧值 %d" % (fo, va, tag, cur, old))
        if not (0 <= nv < (1 << (8 * width))):
            raise SystemExit("新值越界 @fo 0x%06X [%s u%d] -> %d" % (fo, tag, width, nv))
        buf[fo:fo + width] = nv.to_bytes(width, "little")
        plan.append((fo, va, old, nv, tag, width))
    for lbl, fo, exp in CN_CHECKS:
        gotb = bytes(buf[fo:fo + len(exp)])
        if gotb != exp:
            raise SystemExit("中文补丁被破坏：%s 期望 %s 实得 %s" % (lbl, exp.hex(), gotb.hex()))
    if not quiet:
        for fo, va, old, nv, tag, width in plan:
            print("  0x%06X VA 0x%06X  %-5d -> %-5d [%s u%d]" % (fo, va, old, nv, tag, width))
    return bytes(buf), plan


def write_out(buf, path):
    tmp = path + ".tmp"
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(tmp, "wb") as f:
        f.write(buf)
    if open(tmp, "rb").read() != buf:
        raise SystemExit("回读校验失败，未落盘：%s" % tmp)
    os.replace(tmp, path)
    print("已落盘 %s  (%d B, md5 %s)" % (path, len(buf), md5f(path)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--w", type=int, default={pw})
    ap.add_argument("--h", type=int, default={ph})
    ap.add_argument("--out", default=None)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--repro", action="store_true", help="复现 v4 产物并比对 md5")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    print("母本 %s  md5 %s" % (SRC, md5f(SRC)))
    print("目标 %dx%d，站点 %d 个" % (a.w, a.h, len(SITES)))
    buf, plan = build(a.w, a.h, quiet=a.quiet)
    print("内存构建完成：%d 个站点已改，中文补丁三处仍在" % len(plan))

    if a.repro:
        out = a.out or os.path.join(HERE, "out", "PeG030res.repro.exe")
        write_out(buf, out)
        got = md5f(out)
        rec = md5f(DST_V4) if os.path.exists(DST_V4) else DST_V4_MD5
        ok = got == DST_V4_MD5
        print("复现结果 md5 %s；v4 产物 md5 %s；%s" % (got, rec, "逐字节一致 ✅" if ok else "⚠不一致"))
        return 0 if ok else 2

    out = a.out or os.path.join(HERE, "out", "PeG030res.%dx%d.exe" % (a.w, a.h))
    if a.apply:
        write_out(buf, out)
    else:
        print("干跑：未写盘。要落盘加 --apply，产物将写到 %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def render_patch_script(sites, unknown, notes, ndiff, nruns, checks):
    site_lines = []
    for fo, va, sec, ov, nv, t, wd in sites:
        note = notes.get(fo, "")
        site_lines.append('    (0x%06X, 0x%06X, %5d, %-7s, %d),  # %-6s %s' %
                          (fo, va, ov, '"%s"' % t, wd, sec, note))
    unk_lines = ['    (0x%06X, 0x%06X, %d, %d),' % (fo, va or 0, ov, nv) for fo, va, ov, nv in unknown]
    cn_lines = ['    ("%s", 0x%06X, bytes.fromhex("%s")),' % (lbl, fo, exp.hex()) for lbl, fo, exp in checks]
    return PATCH_HEAD.format(stamp=datetime.date.today().isoformat(),
                             src_md5=SRC_MD5, dst_md5=DST_MD5, ndiff=ndiff, nruns=nruns,
                             nsites=len(sites) + len(unknown), pw=PW, ph=PH,
                             unknown_lines="\n".join(unk_lines),
                             cn_checks="\n".join(cn_lines),
                             site_lines="\n".join(site_lines))


if __name__ == "__main__":
    sys.exit(main())
