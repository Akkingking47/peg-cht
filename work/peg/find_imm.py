# -*- coding: utf-8 -*-
"""在 .text 全量反汇编里查找「立即数等于某个值」的指令，并打印上下文。

为什么需要它：像工具列按钮的 x 762 / right 787 / 面板宽 180 / 面板左缘偏移 620
这类几何常量，如果出现在代码里就是立即数（imm）。定位「谁在按 762 画按钮」用
按地址查引用（xref_data.py）找不到，因为它们不是内存地址而是纯数值 → 用本工具。

用法：
    python find_imm.py 762 787 620
    python find_imm.py 0x2fa --ctx 6      # 单个值 + 打印 6 条上下文
    python find_imm.py 762 --all          # 不限制打印条数

注意：立即数出现次数很多（掩码、位运算里也会出现），所以默认只打印前 40 条，
并把 `and/or/xor/test/cmp` 单独标成 [MASK?]（通常不是几何常量）。
"""
import sys
import os

try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
except ImportError:
    sys.exit("需要 capstone：python -m pip install capstone")

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"D:\Program Files\PeG\PeG030.exe"

# 节表（由 analyze_pe.py 校准）
SECTIONS = [
    (".text",  0x401000, 0x8A136, 0x400,   0x8A200),
    (".rdata", 0x48C000, 0x1017,  0x8A600, 0x1200),
    (".data",  0x48E000, 0x21BF3C, 0x8B800, 0x21400),
    (".idata", 0x6AA000, 0x5172,  0xACC00, 0x5632),
    (".rsrc",  0x6AC000, 0x52DC,  0xAE200, 0x5400),
]
IMAGE_BASE = 0x400000


def load(path):
    with open(path, "rb") as f:
        return f.read()


def sec_of_va(va):
    for name, va0, vsize, raw, rawsize in SECTIONS:
        if va0 <= va < va0 + max(vsize, rawsize):
            return name, va0, vsize, raw, rawsize
    return None


def va2fo(va):
    s = sec_of_va(va)
    if not s:
        return None
    name, va0, vsize, raw, rawsize = s
    off = raw + (va - va0)
    if off >= raw + rawsize:
        return None
    return off


def fo2va(fo):
    for name, va0, vsize, raw, rawsize in SECTIONS:
        if raw <= fo < raw + rawsize:
            return va0 + (fo - raw)
    return None


def disasm_all(blob, va0):
    """线性反汇编，遇到坏字节就跳过一个字节继续（capstone 单次 disasm 会停）。"""
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    out = []
    off = 0
    n = len(blob)
    nbad = 0
    while off < n:
        got = False
        for ins in md.disasm(blob[off:], va0 + off):
            out.append(ins)
            off += ins.size
            got = True
        if not got:
            off += 1
            nbad += 1
    return out, nbad


MASK_MNEMONIC = {"and", "or", "xor", "test", "shl", "shr", "sar", "not", "bt", "bts", "btc", "btr"}


def imm_of(ins):
    """返回指令里出现的所有立即数（int 列表）。"""
    vals = []
    for op in ins.operands:
        if op.type == 2:  # X86_OP_IMM
            vals.append(op.imm & 0xFFFFFFFF)
    return vals


def main():
    args = [a for a in sys.argv[1:]]
    ctx = 4
    show_all = False
    vals = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--ctx":
            ctx = int(args[i + 1]); i += 2; continue
        if a == "--all":
            show_all = True; i += 1; continue
        if a == "--src":
            global SRC
            SRC = args[i + 1]; i += 2; continue
        vals.append(int(a, 0)); i += 1
    if not vals:
        sys.exit(__doc__)

    data = load(SRC)
    va0, vsize, raw, rawsize = 0x401000, 0x8A136, 0x400, 0x8A200
    blob = data[raw:raw + rawsize]
    insns, nbad = disasm_all(blob, va0)
    idx = {ins.address: k for k, ins in enumerate(insns)}
    where = " ".join(hex(v) for v in vals)
    print("EXE : %s" % SRC)
    print("反汇编 %d 条指令（坏字节跳过 %d 处）" % (len(insns), nbad))
    print("查找立即数：%s" % where)
    print("=" * 78)

    for want in vals:
        hits = [ins for ins in insns if want in imm_of(ins)]
        print("")
        print("### 立即数 %d (0x%X) 命中 %d 条" % (want, want, len(hits)))
        limit = len(hits) if show_all else 40
        for k, ins in enumerate(hits[:limit]):
            tag = " [MASK?]" if ins.mnemonic in MASK_MNEMONIC else ""
            print("  %s  %-8s %s%s" % (hex(ins.address), ins.mnemonic, ins.op_str, tag))
            if ctx:
                p = idx.get(ins.address)
                if p is not None:
                    lo = max(0, p - ctx // 2)
                    for j in range(lo, min(len(insns), lo + ctx)):
                        mark = ">>" if j == p else "  "
                        print("      %s %s  %-8s %s" % (mark, hex(insns[j].address), insns[j].mnemonic, insns[j].op_str))
        if len(hits) > limit:
            print("  …还有 %d 条（--all 全部打印）" % (len(hits) - limit))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
