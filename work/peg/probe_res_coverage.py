# -*- coding: utf-8 -*-
"""S2：静态定位 1024x768 下右侧/右下花屏的根因候选（**只读**，不修改任何游戏文件）。

背景：v4 补丁（259 站点，见 out/res_diff_report.txt）把 800x600 的画布抬到 1024x768，
窗口尺寸、显示模式、主表面 desc、视口/clip、右列与底栏矩形都改了；实机截图
（旧分支 out/shot-v3.png，已随分支删除）显示：顶栏/底栏跨全宽正常，但**右下出现
品红/绿横条 + 1~2px 黑白竖条 + 未绘制黑区**——典型的「画布变宽了，但某处仍在用
旧的尺寸/行距」的症状。

本脚本把以下四类证据一次性枚举出来，与 v4 已补的 259 站点对账：
  (A) 未覆盖的尺寸家族立即数：800/799/796/600/599/572/571/570 ... 里**没被 v4 改过**的
  (B) 行距(pitch)候选：1600(=800*2)/1200/2048/1536/3200/2400 等 16bpp 行字节数
  (C) DirectDraw vtable 调用普查：Blt(0x14)/BltFast(0x1C)/Flip(0x2C)/Lock(0x64)/
      Unlock(0x80)/GetDC(0x44)/ReleaseDC(0x68)/CreateSurface(0x18)/SetDisplayMode(0x54)
      各自的位置与上下文（用于判断 present 机制是 Blt 还是 Lock+软件拷贝）
  (D) 关键全局的引用点：运行期宽高、（疑似）表面对象/画布/尺寸缓存

口径提醒：VA→FO 必须走节表，不能套 .text 的 VA-0x401000+0x400（.data 会错）。

输出：
  out/res_coverage_probe.txt   全量明细
  标准输出                     紧凑摘要（本脚本读回来做判断用这个）
"""
import collections
import os
import struct
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_MEM

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"D:\Program Files\PeG\PeG030.exe"
TSV = os.path.join(HERE, "out", "res_diff_v4.tsv")
OUT = os.path.join(HERE, "out", "res_coverage_probe.txt")
SRC_MD5 = "c462e897b3aa1c384870c857ce9e01df"
PW, PH = 1024, 768                    # v4 产物对应的目标分辨率
PDX, PDY = PW - 800, PH - 600

# (A) 尺寸家族：值 -> 标签
SIZE_VALS = {
    800: "W800", 799: "w-1", 796: "w-4", 600: "H600", 599: "h-1",
    572: "h-28", 571: "h-28?", 570: "h-30", 1024: "W1024", 1023: "w-1",
    1020: "w-4", 768: "H768", 767: "h-1", 740: "h-28", 738: "h-30",
}
# (B) 16bpp 行字节数候选
PITCH_VALS = {
    1600: "800*2", 1200: "600*2", 2048: "1024*2", 1536: "768*2",
    3200: "2*800*2", 2400: "2*600*2", 3136: "?", 1280: "640*2",
    960: "480*2", 896: "448*2", 672: "336*2", 640: "320*2", 480: "240*2",
}
# (D) 关键全局（旧分支 probe_res32 留下的地址，标注待验证）
WATCH = {
    0x61E928: "运行期屏宽（cmp/mov 800）", 0x61E92C: "运行期屏高（600）",
    0x663388: "运行期屏宽 B", 0x66338C: "运行期屏高 B",
    0x6769A8: "运行期屏宽 C", 0x6769AC: "运行期屏高 C",
    0x676904: "DDraw 表面对象（GDI 文字用）", 0x6761E0: "IDirectDraw 接口?",
    0x69D020: "1600B 缓冲?（待验证）", 0x655538: "画布/缓冲（待验证）",
    0x655560: "尺寸缓存 +0（待验证）", 0x655564: "尺寸缓存 +4（待验证）",
    0x655568: "尺寸缓存 +8（待验证）", 0x65556C: "尺寸缓存 +C（待验证）",
    0x655574: "地图表面（待验证）", 0x6877B4: "疑似屏宽（待验证）",
    0x4AF2F8: "视点 x（待验证）", 0x4AF2FC: "视点 y（待验证）",
    0x4AF300: "视口（待验证）",
}
# (C) vtable 偏移 -> 名称（DirectDraw / DirectDrawSurface 两套，重叠的标两个）
VT = {
    0x10: "CreateClipper | AddOverlayDirtyRect",
    0x14: "Blt | CreatePalette", 0x18: "CreateSurface | BltBatch",
    0x1C: "BltFast | DuplicateSurface", 0x20: "BltBatch? | EnumDisplayModes",
    0x24: "EnumAttachedSurfaces", 0x28: "EnumOverlayZOrders",
    0x2C: "Flip | GetCaps", 0x30: "GetAttachedSurface | GetDisplayMode",
    0x38: "GetCaps | GetGDISurface", 0x3C: "GetClipper | GetMonitorFrequency",
    0x44: "GetDC | GetVerticalBlankStatus", 0x48: "GetFlipStatus | Initialize",
    0x4C: "GetOverlayPosition | RestoreDisplayMode", 0x50: "SetCooperativeLevel",
    0x54: "SetDisplayMode | GetPixelFormat", 0x58: "WaitForVerticalBlank | GetSurfaceDesc",
    0x64: "Lock", 0x68: "ReleaseDC", 0x6C: "Restore", 0x70: "SetClipper",
    0x74: "SetColorKey", 0x80: "Unlock",
}


# 需要逐条打印上下文的重点区间（S2 的疑点簇；来自 res_constants 记忆与旧分支 probe_res31）
FOCUS_RANGES = [
    (0x401000, 0x401020),
    (0x40E720, 0x40E770),
    (0x410D60, 0x410DF0),
    (0x4144E0, 0x414780),
    (0x41C4C0, 0x41C4F0),
    (0x4426C0, 0x442730),
    (0x4672C0, 0x4672E0),
    (0x467990, 0x4679B0),
    (0x44C700, 0x44C7A0),
    (0x44C840, 0x44C8E0),
    (0x44CC40, 0x44CCE0),
]


def disasm_all(md, blob, va0):
    """线性反汇编整节：capstone 遇到坏字节会停，这里跳过坏字节继续（统计跳过字节数）"""
    res = []
    off = 0
    n = len(blob)
    bad = 0
    while off < n:
        progressed = False
        for ins in md.disasm(blob[off:], va0 + off):
            res.append(ins)
            off += ins.size
            progressed = True
        if not progressed:
            off += 1
            bad += 1
    return res, bad


def imm_sites(ins):
    """产出该指令里每个立即数操作数的 (立即数在内存中的 VA, 值)。
    用 capstone 5 的 ins.encoding.imm_offset/imm_size 精确定位——
    这才能和 v4 站点表（记录的是立即数地址）严格对齐。"""
    try:
        e = ins.encoding
        off, size = e.imm_offset, e.imm_size
    except Exception:
        return
    if not size:
        return
    imms = [op.imm & 0xFFFFFFFF for op in ins.operands if op.type == CS_OP_IMM]
    if not imms:
        return
    step = size // len(imms) if len(imms) > 1 else size
    for i, v in enumerate(imms):
        yield ins.address + off + step * i, v


def parse_pe(data):
    e = struct.unpack_from("<I", data, 0x3C)[0]
    assert data[e:e + 4] == b"PE\0\0", "不是 PE"
    coff = e + 4
    nsec = struct.unpack_from("<H", data, coff + 2)[0]
    opt_size = struct.unpack_from("<H", data, coff + 16)[0]
    opt = coff + 20
    magic = struct.unpack_from("<H", data, opt)[0]
    base = (struct.unpack_from("<I", data, opt + 28)[0] if magic == 0x10B
            else struct.unpack_from("<Q", data, opt + 24)[0])
    secs = []
    for i in range(nsec):
        off = opt + opt_size + i * 40
        raw = data[off:off + 40]
        name = raw[:8].rstrip(b"\0").decode("latin1")
        vsize, va, raw_size, raw_off = struct.unpack_from("<IIII", raw, 8)
        secs.append((name, va, vsize, raw_off, raw_size))
    return base, secs


def va_to_fo(va, base, secs):
    rva = va - base
    for name, sva, vsize, raw_off, raw_size in secs:
        if sva <= rva < sva + raw_size:
            return raw_off + (rva - sva), name
    return None, "?"


def fo_to_va(fo, base, secs):
    for name, sva, vsize, raw_off, raw_size in secs:
        if raw_off <= fo < raw_off + raw_size:
            return base + sva + (fo - raw_off), name
    return None, "?"


def load_patched():
    """va -> (section, file_off, width, old, new, tag, note)"""
    out = {}
    with open(TSV, encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 8 or not p[2].startswith("0x"):
                continue
            out[int(p[2], 16)] = (p[1], p[3], int(p[4]), int(p[5]), int(p[6]), p[7],
                                  p[8] if len(p) > 8 else "")
    return out


def main():
    with open(SRC, "rb") as f:
        data = f.read()
    base, secs = parse_pe(data)
    text = [s for s in secs if s[0] == ".text"][0]
    name, tva, tvsize, traw, trawsize = text
    patched = load_patched()

    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    blob = data[traw:traw + trawsize]
    insns, nbad = disasm_all(md, blob, base + tva)

    lines = []
    def w(s=""):
        lines.append(s)

    w("PeG030.exe 静态覆盖扫描（只读）")
    w("节：%s VA=0x%X raw=0x%X size=0x%X" % (name, base + tva, traw, trawsize))
    w("v4 已补站点：%d 个（其中 .text %d）" %
      (len(patched), sum(1 for v in patched.values() if v[0] == ".text")))
    w("反汇编指令数：%d（跳过无法解码的字节 %d 个）" % (len(insns), nbad))

    # ---------- (A) 尺寸家族立即数：改了 vs 没改 ----------
    hit_size = []
    for ins in insns:
        for iva, v in imm_sites(ins):
            if v in SIZE_VALS:
                hit_size.append((iva, ins.address, ins.mnemonic, ins.op_str, v))

    w("\n" + "=" * 72)
    w("(A) 尺寸家族立即数：v4 改过的 / **没改过的**（用 capstone imm_offset 精确定位立即数地址）")
    w("=" * 72)
    miss = []
    seen = set()
    for iva, ia, m, o, v in hit_size:
        p = patched.get(iva)
        if p is not None:
            seen.add(iva)
        else:
            miss.append((iva, ia, m, o, v))
        w("  %s imm@0x%06X ins@0x%06X  %-8s %-40s %-6d %s" %
          ("[已补]" if p else "[漏!] ", iva, ia, m, o, v, SIZE_VALS[v]))
    w("")
    w(">>> 尺寸家族立即数命中 %d 个；其中**未补 %d 个**" % (len(hit_size), len(miss)))
    for iva, ia, m, o, v in miss:
        w("     漏 imm@0x%06X ins@0x%06X  %-8s %-42s %d (%s)" % (iva, ia, m, o, v, SIZE_VALS[v]))

    # 分类：位掩码类（and/or/xor/test）多半与屏幕尺寸无关，降级；其余算「尺寸型」候选
    MASKY = {"and", "or", "xor", "test", "bt", "bts", "btr"}
    sugg = []
    for iva, ia, m, o, v in miss:
        if v == 1024:
            nv = PW
        elif v == 768:
            nv = PH
        elif v in (800, 799, 796):
            nv = PW - (800 - v)
        elif v in (600, 599, 596):
            nv = PH - (600 - v)
        elif v in (572, 571):
            nv = PH - 28
        elif v == 570:
            nv = PH - 30
        else:
            nv = v
        fo, sec = va_to_fo(ia, base, secs)
        sugg.append((sec, iva, ia, fo or 0, m, o, v, nv, "MASK?" if m in MASKY else "size"))
    tsv = os.path.join(HERE, "out", "res_missing_candidates.tsv")
    with open(tsv, "w", encoding="utf-8", newline="\n") as f:
        f.write("section\timm_va\tins_va\tfile_off\tmnemonic\tinstruction\told\tsuggested\tkind\n")
        for sec, iva, ia, fo, m, o, v, nv, kind in sugg:
            f.write("%s\t0x%06X\t0x%06X\t0x%06X\t%s\t%s\t%d\t%d\t%s\n"
                    % (sec, iva, ia, fo, m, o, v, nv, kind))
    nmask = sum(1 for x in sugg if x[8] == "MASK?")
    nsize = len(sugg) - nmask
    w("")
    w(">>> 未补点分类：尺寸型候选 %d 个 / 位掩码类（多半无关）%d 个" % (nsize, nmask))
    w(">>> 候选清单 -> %s" % tsv)
    for sec, iva, ia, fo, m, o, v, nv, kind in sugg:
        if kind == "size":
            w("     尺寸型 0x%06X(fo 0x%06X)  %-8s %-40s  %d -> %d" % (ia, fo, m, o, v, nv))
    notseen = [x for x in sorted(patched) if x not in seen and patched[x][0] == ".text"]
    w("")
    w(">>> 站点表里 .text 的 %d 个已补点中，本扫描没撞上的：%d 个（多为 4 字节窗口取值的差异）"
      % (sum(1 for v in patched.values() if v[0] == ".text"), len(notseen)))

    # ---------- (B) 行距/pitch 候选 ----------
    w("\n" + "=" * 72)
    w("(B) 16bpp 行字节数(pitch)候选 + 乘2/左移一类的行距运算")
    w("=" * 72)
    n_pitch = 0
    for ins in insns:
        imms = [op.imm & 0xFFFFFFFF for op in ins.operands if op.type == CS_OP_IMM]
        pv = [v for v in imms if v in PITCH_VALS]
        is_scale = (ins.mnemonic in ("imul", "mul", "shl", "sal")
                    and any(v in (2, 800, 600, 1024, 768) for v in imms))
        if pv or is_scale:
            n_pitch += 1
            tag = ",".join(PITCH_VALS[v] for v in pv) or ("scale %s" % imms)
            w("  0x%06X  %-9s %-46s %s" % (ins.address, ins.mnemonic, ins.op_str, tag))
    w("")
    w(">>> pitch/scale 命中 %d 条" % n_pitch)

    # ---------- (C) DirectDraw vtable 调用普查 ----------
    w("\n" + "=" * 72)
    w("(C) DirectDraw / Surface vtable 调用点普查")
    w("=" * 72)
    census = collections.Counter()
    calls = collections.defaultdict(list)
    idx_of = {ins.address: i for i, ins in enumerate(insns)}
    for ins in insns:
        if ins.mnemonic != "call" or len(ins.operands) != 1:
            continue
        op = ins.operands[0]
        if op.type != CS_OP_MEM or op.mem.index != 0 or op.mem.base == 0:
            continue
        d = op.mem.disp & 0xFFFFFFFF
        if d not in VT:
            continue
        census[d] += 1
        i = idx_of[ins.address]
        ctx = ["%s %s" % (x.mnemonic, x.op_str) for x in insns[max(0, i - 5):i]]
        calls[d].append((ins.address, ins.op_str, ctx))
    for d in sorted(census):
        w("  [+0x%02X] %-34s %d 处" % (d, VT[d], census[d]))
    for d in (0x54, 0x18, 0x14, 0x1C, 0x2C, 0x64, 0x80, 0x44, 0x68):
        for va, ops, ctx in calls.get(d, []):
            w("\n  --- [+0x%02X] %s @ 0x%06X  %s" % (d, VT[d], va, ops))
            for c in ctx:
                w("        %s" % c)
            p = patched.get(va)
            w("        %s" % ("已在本站点表" if p else "不在 v4 站点表"))
            if p:
                w("        v4: %d -> %d [%s] %s" % (p[3], p[4], p[5], p[6]))

    # ---------- (D) 关键全局引用 ----------
    w("\n" + "=" * 72)
    w("(D) 关键全局的引用点")
    w("=" * 72)
    refs = collections.defaultdict(list)
    for ins in insns:
        for op in ins.operands:
            if op.type != CS_OP_MEM or op.mem.base != 0 or op.mem.index != 0:
                continue
            d = op.mem.disp & 0xFFFFFFFF
            if d in WATCH:
                refs[d].append((ins.address, ins.mnemonic, ins.op_str))
    for va in sorted(WATCH):
        rs = refs.get(va, [])
        w("  0x%06X %-30s %d 处引用" % (va, WATCH[va], len(rs)))
        for a, m, o in rs[:12]:
            p = patched.get(a)
            w("      0x%06X  %-8s %-40s %s" % (a, m, o, "[已补]" if p else ""))
        if len(rs) > 12:
            w("      ... 另有 %d 处（见全量文件）" % (len(rs) - 12))

    # ---------- (E) 重点区间逐条上下文 ----------
    w("\n" + "=" * 72)
    w("(E) 重点区间逐条上下文（疑点簇）")
    w("=" * 72)
    for lo, hi in FOCUS_RANGES:
        w("\n--- 0x%06X ~ 0x%06X ---" % (lo, hi))
        for ins in insns:
            if lo <= ins.address <= hi:
                p = None
                for k in range(ins.size):
                    if (ins.address + k) in patched:
                        p = patched[ins.address + k]
                        break
                mark = ""
                if p:
                    mark = "   <<< v4: %d -> %d [%s] %s" % (p[3], p[4], p[5], p[6])
                w("  0x%06X  %-9s %s%s" % (ins.address, ins.mnemonic, ins.op_str, mark))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    # ---------- 紧凑摘要 ----------
    print("== S2 静态覆盖扫描 ==")
    print("指令 %d 条；v4 已补 .text %d 站点；尺寸家族命中 %d，其中**漏点 %d**" %
          (len(insns), sum(1 for v in patched.values() if v[0] == ".text"),
           len(hit_size), len(miss)))
    for iva, ia, m, o, v in miss:
        print("  漏 imm@0x%06X ins@0x%06X  %-8s %-40s %d %s" % (iva, ia, m, o, v, SIZE_VALS[v]))
    print("  未补点分类：尺寸型候选 %d / 位掩码类 %d（清单 out/res_missing_candidates.tsv）"
          % (nsize, nmask))
    print("pitch/scale 命中 %d 条（明细见文件）" % n_pitch)
    print("vtable 调用普查：")
    for d in sorted(census):
        print("  +0x%02X %-34s %d" % (d, VT[d], census[d]))
    print("关键全局有引用的：%s" %
          ", ".join("0x%X(%d)" % (v, len(refs[v])) for v in sorted(refs)))
    print("全量明细 -> %s" % OUT)


if __name__ == "__main__":
    main()
