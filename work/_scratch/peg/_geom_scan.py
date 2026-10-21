# -*- coding: utf-8 -*-
"""_geom_scan.py — 只读：.text 里「几何/屏幕尺寸相关立即数」普查。

输出每条命中：地址 / 字节 / 指令 / 邻近上下文 / 所在疑似函数范围，
并对常见几何值给出自动分类初判。

用法：
    python _geom_scan.py                 # 默认几何值集合
    python _geom_scan.py 762 787 --ctx 3
"""
import struct
import sys
import io
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM

SRC = r"D:\Program Files\PeG\PeG030.exe"
TEXT_VA, TEXT_FO, TEXT_RAW = 0x401000, 0x400, 0x8A200
TEXT_END = TEXT_VA + TEXT_RAW

# 想普查的值（十进制）
DEFAULTS = [800, 600, 572, 796, 550, 700, 762, 787, 500, 1920, 1080, 620, 844,
            640, 480, 400, 300, 240, 180, 480, 24, 36, 88, 60, 20, 0x780]

# 语义角色提示（仅用于标签，不是结论）
ROLE = {
    800: "宽800", 600: "高600", 572: "宽800-228?", 796: "宽800-4",
    550: "高600-50", 700: "右缘?", 762: "按钮x", 787: "按钮right",
    500: "行高?", 1920: "宽1920", 1080: "高1080", 620: "面板左缘",
    844: "面板右缘?", 640: "半宽/640", 480: "半高/480", 400: "地图格数?",
    300: "?", 240: "?", 180: "面板宽", 24: "步长24", 36: "宽36", 88: "高88",
    60: "?", 20: "?", 0x780: "1920",
}


def load():
    return open(SRC, "rb").read()


def sec_of_va(va):
    SECS = [(".text", 0x401000, 0x400, 0x8A136),
            (".rdata", 0x48C000, 0x8A600, 0x1017),
            (".data", 0x48E000, 0x8B800, 0x21BF3C),
            (".idata", 0x6AA000, 0xACC00, 0x1434),
            (".rsrc", 0x6AC000, 0xAE200, 0x52DC)]
    for n, sva, raw, size in SECS:
        if sva <= va < sva + size:
            return n


def fo_to_va(fo):
    SECS = [(".text", 0x401000, 0x400, 0x8A136),
            (".rdata", 0x48C000, 0x8A600, 0x1017),
            (".data", 0x48E000, 0x8B800, 0x21BF3C),
            (".idata", 0x6AA000, 0xACC00, 0x1434),
            (".rsrc", 0x6AC000, 0xAE200, 0x52DC)]
    for n, sva, raw, size in SECS:
        if raw <= fo < raw + size:
            return sva + (fo - raw)


def disasm_text(data):
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    blob = data[TEXT_FO:TEXT_FO + TEXT_RAW]
    out = []
    off = 0
    bad = 0
    while off < len(blob):
        got = False
        for ins in md.disasm(blob[off:off + 16], TEXT_VA + off):
            out.append((ins.address, ins.size, ins.mnemonic, ins.op_str,
                        [(op.type, op.imm) for op in ins.operands if op.type == CS_OP_IMM]))
            off += ins.size
            got = True
        if not got:
            off += 1
            bad += 1
    return out, bad


def func_ranges(insns):
    """按 push ebp; mov ebp,esp 开头 + ret/int3 收尾，粗略推函数起止。"""
    starts = [0]
    for i in range(1, len(insns)):
        a, sz, mn, ops, _im = insns[i]
        pa, psz, pmn, pops, _pim = insns[i - 1]
        if mn == "mov" and ops.replace(" ", "") == "ebp,esp" and pmn == "push" and pops == "ebp":
            starts.append(i)
    res = []
    for k, s in enumerate(starts):
        e = starts[k + 1] if k + 1 < len(starts) else len(insns)
        res.append((s, e))
    return res


def enclosing(insns, fr, addr):
    for s, e in fr:
        if insns[s][0] <= addr < (insns[e][0] if e < len(insns) else TEXT_END):
            return insns[s][0], (insns[e][0] if e < len(insns) else TEXT_END)
    return None, None


def cls_of(mn, ops, ret_before, ret_after):
    """初判分类。"""
    o = ops.replace(" ", "")
    if mn == "imul" and o.count(",") == 2:
        return "像素步长(stride/imul k)"
    if mn in ("push", "mov", "cmp") and o.endswith(("0x320", "0x258", "0x23c", "0x31c")):
        pass
    if mn in ("and", "or", "xor", "test", "not"):
        return "掩码/位运算(疑误报)"
    if mn in ("cmp", "sub", "add", "sbb") and ("0x4af" in o or "0x4c" in o):
        return "尺寸比较"
    if "es:" in o or "[0x4af" in o or "[0x4c" in o:
        return "布局表数据/结构性"
    return "位置基点/尺寸常量"


def main():
    args = [a for a in sys.argv[1:]]
    ctx = 2
    show_ctx = True
    vals = []
    i = 0
    while i < len(args):
        if args[i] == "--ctx":
            ctx = int(args[i + 1]); i += 2; continue
        if args[i] == "--noctx":
            show_ctx = False; i += 1; continue
        vals.append(int(args[i], 0)); i += 1
    if not vals:
        vals = list(DEFAULTS)

    data = load()
    insns, bad = disasm_text(data)
    fr = func_ranges(insns)
    idx = {a: k for k, (a, _s, _m, _o, _i) in enumerate(insns)}
    print("反汇编 %d 条（坏字节 %d）；疑似函数 %d 个" % (len(insns), bad, len(fr)))
    print("=" * 96)

    for want in vals:
        hits = [(a, sz, mn, ops) for (a, sz, mn, ops, ims) in insns
                if any(v == want for _t, v in ims)]
        print("")
        print("### 值 %d (0x%X)  %s  命中 %d 条" % (want, want, ROLE.get(want, ""), len(hits)))
        for a, sz, mn, ops in hits:
            k = idx[a]
            fs, fe = enclosing(insns, fr, a)
            # 取命中前 20 条内是否有 ret（判是否在函数尾部/参数压栈）
            tail = any(insns[j][2] in ("ret", "retn") for j in range(max(0, k - 3), k))
            tag = cls_of(mn, ops, tail, False)
            b = data[TEXT_FO + (a - TEXT_VA):TEXT_FO + (a - TEXT_VA) + sz]
            print("  0x%06X  f=0x%06X-0x%06X  %-28s %-8s %-30s [%s]" %
                  (a, fs or 0, fe or 0, b.hex(" "), mn, ops, tag))
            if show_ctx and ctx:
                for j in range(max(0, k - ctx), min(len(insns), k + ctx + 1)):
                    jj = insns[j]
                    print("        %s 0x%06X  %-8s %s" %
                          (">>" if j == k else "  ", jj[0], jj[2], jj[3]))
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
