# -*- coding: utf-8 -*-
r"""_immediate_census.py — 只读：PeG030.exe `.text` 坐标类立即数普查（P0 第二路证据）。

目标（docs\80 §P0）：把 800/600/799/599/400/300/320/240/1920/1080/640/480
这些「设计空间坐标 / 尺寸」常量在代码里的落点全部列出来，供 L3/L5 归类。

产出：
  work\peg\relayout\text_immediates.tsv    主表（8 列，题面指定表头）
  work\peg\relayout\text_immediates_ctx.tsv  辅助证据表（cand / note / ctx），非必交
  work\peg\out\immediate-census-report.txt   中文报告（utf-8，防控制台乱码）
  work\peg\out\immediate-census-summary.txt  机器可读统计摘要

只读约束：只读母本 exe；只写上面 4 个文件。不启动游戏、不改 D:\Program Files\PeG\*。

判读口径（写进报告，避免"猜"变成结论）：
  * **excl 标记的命中不进汇总统计**，但**仍出现在主表里**（题面要求"全部写进文件"），
    由 ctx 列携带排除依据，读者可自行复核。
  * 排除依据只有三类可机械判定的：越界立即数 / 浮点常量位型 / 段内地址常量。
    「循环计数」「结构大小」无法从单条指令可靠判定，因此**不做静默丢弃**：
    只在 ctx 里标 `loop?` / `imul-len` 供人工复核，保留在统计中。

用法：
    C:\Python314\python.exe work\_scratch\peg\_immediate_census.py
    ... --full    # 额外把全部命中逐条打印到 gecos 报告（报告会变很大）
"""
import os
import re
import sys
import struct
import bisect
import collections

from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_MEM
import capstone.x86 as X86

# --------------------------------------------------------------------- 常量
SRC = r"D:\Program Files\PeG\PeG030.exe"
IMAGE_BASE = 0x400000
TEXT_VA = 0x401000
TEXT_FO = 0x400
TEXT_VSIZE = 0x8A136          # VirtualSize
TEXT_RAWSIZE = 0x8A200        # SizeOfRawData（尾 0xCA 字节在文件里是 int3 填充）
TEXT_END = TEXT_VA + TEXT_VSIZE

# 普查目标值（十进制）
TARGETS = [800, 600, 799, 599, 400, 300, 320, 240, 1920, 1080, 640, 480]
TARGET_SET = set(TARGETS)   # 供 _layout_stride_census.py 复用时做 in 判定

# 已知表基址（用于 L3 消费点交叉印证）
TBL_LAYOUT = 0x4A96E8     # 布局记录表，stride 15（docs\80 §L3）
TBL_MAIN = 0x490470       # 主布局表，x@+0x02 y@+0x04 right@+0x06（docs\72）
KNOWN_L3_CONSUMERS = {0x413932: "docs80 明列 L3 消费函数",
                      0x41407A: "docs80 明列 L3 消费函数",
                      0x430960: "docs80 明列 L3 消费函数",
                      0x445FFF: "docs80 明列 L3 消费函数"}

# "半屏"族：内联居中算术 (D - v)/2 的分母候选
HALVES = {400: 800, 300: 600, 320: 640, 240: 480}

RELPATH_TSV = r"work\peg\relayout\text_immediates.tsv"
RELPATH_CTX = r"work\peg\relayout\text_immediates_ctx.tsv"
RELPATH_REPORT = r"work\peg\out\immediate-census-report.txt"
RELPATH_SUMMARY = r"work\peg\out\immediate-census-summary.txt"

ROOT = r"D:\DSH\军事游戏汉化"

# --------------------------------------------------------------------- 反汇编
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True


def disasm_text(data):
    """线性反汇编 .text 全 VirtualSize；坏字节前进 1 字节重新同步。"""
    blob = data[TEXT_FO:TEXT_FO + TEXT_VSIZE]
    insns = []
    off = 0
    nbad = 0
    while off < len(blob):
        one = list(md.disasm(blob[off:off + 16], TEXT_VA + off, count=1))
        if not one:
            off += 1
            nbad += 1
            continue
        ins = one[0]
        insns.append(ins)
        off += ins.size
    return insns, nbad


def build_func_index(data, insns):
    """函数起点集合。

    两边都收：
      (a) 指令流里的 `push ebp` + `mov ebp,esp`（题面指定的 55 8B EC 回扫目标）；
      (b) 所有 `call rel32` 的目标地址（函数边界的最强证据，覆盖无帧指针的函数）。
    """
    starts = set()
    fo_text = TEXT_FO
    for i, ins in enumerate(insns):
        if ins.mnemonic == "push" and ins.op_str == "ebp" and i + 1 < len(insns):
            nxt = insns[i + 1]
            if nxt.mnemonic == "mov" and nxt.op_str.replace(" ", "") in ("ebp,esp", "ebp, esp"):
                starts.add(ins.address)
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == CS_OP_IMM:
            t = ins.operands[0].imm & 0xFFFFFFFF
            if TEXT_VA <= t < TEXT_END:
                starts.add(t)
    # 55 8B EC 原始字节回扫（不依赖解码对齐，与题面一致）
    pat = b"\x55\x8b\xec"
    pos = data.find(pat, fo_text, fo_text + TEXT_VSIZE)
    while pos >= 0:
        starts.add(TEXT_VA + (pos - fo_text))
        pos = data.find(pat, pos + 1, fo_text + TEXT_VSIZE)
    text_starts = sorted(starts)
    return text_starts


def func_start_of(addr, text_starts):
    """二分找 <= addr 的最近函数起点。"""
    i = bisect.bisect_right(text_starts, addr) - 1
    if i < 0:
        return TEXT_VA
    return text_starts[i]


def collect_start_evidence(insns):
    """函数起点的**独立**证据集合（用于剔除字节模式假的函数头）。

    动机（踩坑记录）：`55 8B EC` 全段字节回扫**会命中数据区**。
    实测 `0x46CE7E` 文件里是 `51 e8 d2 64`，根本不是函数头；
    真正的函数头在 `0x46C27E`。前一版脚本的线性扫掠在这里跨过了真实入口，
    把数据当代码解码，造出假的 `0x46CE7E` 函数并把"命中"写进了表。

    证据**只能**来自：`call rel32` 目标，以及 PE 入口点。
    **故意不包含"线性扫掠解码出的地址"** —— 线性扫掠对数据区无所不decode，
    把它当证据等于没有证据（这是上一版的逻辑漏洞）。
    """
    ev = set()
    for ins in insns:
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == CS_OP_IMM:
            t = ins.operands[0].imm & 0xFFFFFFFF
            if TEXT_VA <= t < TEXT_END:
                ev.add(t)
    # PE 入口点（OptionalHeader.AddressOfEntryPoint 在 e_lfanew+0x28）
    try:
        import struct as _s
        head = open(SRC, "rb").read(0x400)
        e = _s.unpack_from("<I", head, 0x3C)[0]
        ev.add(IMAGE_BASE + _s.unpack_from("<I", head, e + 0x28)[0])
    except Exception:
        pass
    return ev


# --------------------------------------------------------------------- 取值
def imm_values(ins):
    """返回 [(值, 是否符号扩展负数)]，只取真正的 IMM 操作数。"""
    out = []
    for op in ins.operands:
        if op.type == CS_OP_IMM:
            raw = op.imm & 0xFFFFFFFF
            out.append(raw)
    return out


# --------------------------------------------------------------------- 排除
def ff32(raw):
    return struct.unpack("<f", struct.pack("<I", raw))[0]


def check_exclude(ins, raw):
    """针对**命中的那个立即数**做可机械判定的排除。返回 (notes, excluded_reason)。

    注意只判命中的那个值：一条指令里可以同时有目标立即数和别的常量，
    按整条指令扫会把无关常量当成排除依据（早期版本的这个 bug 已修）。
    """
    notes = []
    # 浮点常量位型：800.0f == 0x44480000 之类
    m = raw & 0x7FFFFFFF
    if 0x43800000 <= m <= 0x45800000:
        f = ff32(raw)
        if 32.0 <= f <= 4096.0:
            notes.append("float32(%.3f)" % f)
            return notes, "float32(%.3f)" % f
    # 段内地址常量：0x400200..0x73FFFF
    if IMAGE_BASE + 0x200 <= raw < 0x740000:
        notes.append("addr-in-image")
        return notes, "addr_const"
    return notes, None


# --------------------------------------------------------------------- 分类
COMPARE_MNEMONICS = {"cmp", "test", "sub", "sbb"}
BRANCH_MNEMONICS = {"jz", "jnz", "je", "jne", "jb", "jbe", "ja", "jae", "jl", "jle",
                    "jg", "jge", "js", "jns", "jo", "jno", "jp", "jnp", "jecxz",
                    "loop", "jmp"}


def mnem_is_cc_branch(mn):
    return mn.startswith("j") or mn == "loop"


def classify(ins, val, i, insns):
    """返回 (guess, note_list)。guess ∈ clamp_max/boundary/center_math/rect_size/other。"""
    mn = ins.mnemonic
    ops = ins.op_str.replace(" ", "")
    notes = []

    # ---- 位移收集：本指令 + 后 3 条内的 [reg+disp] ----
    disps = []
    window = insns[i:i + 4]
    for w in window:
        for op in w.operands:
            if op.type == CS_OP_MEM and op.mem.disp and abs(op.mem.disp) < 0x20000:
                disps.append(op.mem.disp)
    # +0x02/+0x04/+0x06 是主布局表字段偏移、+0x0A 是控件数组 id
    if any(d in (2, 4, 6) for d in disps):
        notes.append("field+%s" % "/".join("%X" % d for d in disps if d in (2, 4, 6)))
    if 0x0A in disps:
        notes.append("field+0A")

    # ---- 分支/继续条件（判边界与循环）----
    nxt = insns[i + 1] if i + 1 < len(insns) else None
    nxt2 = insns[i + 2] if i + 2 < len(insns) else None
    cc_after = bool(nxt and mnem_is_cc_branch(nxt.mnemonic))
    cc_after2 = bool(nxt2 and mnem_is_cc_branch(nxt2.mnemonic))
    # 比较型：cmp/sub/test 且其后紧跟条件跳转 = 边界/钳位读法
    if cc_after and mn in COMPARE_MNEMONICS:
        notes.append("cmp+jcc")

    # ---- 循环嫌疑：cmp 后跳，寄存器在邻域内被 inc/dec 修改 ----
    dst_reg = None
    if ins.operands and ins.operands[0].type == X86.X86_OP_REG:
        dst_reg = ins.reg_name(ins.operands[0].reg)
    loop_suspect = False
    if cc_after and dst_reg:
        for w in insns[max(0, i - 3):i + 5]:
            if w.mnemonic in ("inc", "dec", "add", "sub") and w.operands and \
               w.operands[0].type == X86.X86_OP_REG and w.reg_name(w.operands[0].reg) == dst_reg:
                if w.mnemonic in ("inc", "dec") or (w.operands[-1].type == CS_OP_IMM
                                                    and 0 < (w.operands[-1].imm & 0xFFFFFFFF) <= 4):
                    loop_suspect = True
                    break
    if loop_suspect:
        notes.append("loop?")

    # ---- 位图头嫌疑：c7 .. 42 4d = 直接写文件头 'BM'，此时 800/600 是图像宽高 ----
    fn_start = insns[max(0, i - 60):i]
    for w in fn_start:
        if w.mnemonic == "mov" and "0x4d42" in w.op_str.replace(" ", ""):
            notes.append("bitmap-header?")

    # ---- 位掩码：and/or/xor/shl/shr 配合 2^n-1 或 2^n 常量 ----
    # `and dl, 0xf0`（240）这类是**像素/索引对齐掩码**，不是坐标。必须排除，
    # 否则 240 的 center_math 分布会被掩码污染（实测约 25 条）。
    # 注意：本分支必须放在 center_math 之前 —— 240/320 同时是"半屏值"，
    # 放在后面会被 center_math 提前 return 掉（踩坑：第一版就踩了这个顺序）。
    if mn in ("and", "or", "xor", "shl", "shr", "sar", "rol", "ror", "bt", "bts", "btr"):
        if val in (240, 480, 1920, 400, 300, 320, 800, 600) and bin(val).count("1") <= 2:
            return ("other", notes + ["bitmask-align"])

    # ---- imul 三操作数 = 定长步长乘法（结构大小/memset 长度嫌疑）----
    if mn == "imul" and len(ins.operands) == 3:
        notes.append("imul-len")
        # 400/240/800/600 作为乘积因子且非半屏值 → 更像行跨距(uint8 宽)或结构尺寸，
        # 而不是屏幕坐标。标 rect_mul 而不是 center_math，避免污染 L5 排序。
        if val in (800, 600, 400, 240):
            return ("rect_mul", notes + ["mul-by-width"])
        return ("other", notes)

    # ---- 内存宽位（word ptr）立即数：16 位坐标字段，比 dword 更可能是坐标 ----
    if "wordptr" in ops:
        notes.append("word-imm")

    # ---- clamp 族：v == D-1，或 v == D - 1 的减法/比较 ----
    if val in (799, 599):
        return ("clamp_max", notes + ["D-1"])
    if mn in COMPARE_MNEMONICS:
        if val in (800, 600, 640, 480, 1920, 1080):
            return ("clamp_max", notes + ["bound-check"])
        return ("boundary", notes)

    # ---- 内联居中算术 ----
    if val in (400, 300, 320, 240):
        if mn in ("mov", "lea"):
            return ("center_math", notes + ["half-preload"])
        return ("center_math", notes)

    # ---- 矩形宽高 / 描述符尺寸 ----
    if val in (800, 600, 640, 480, 1920, 1080, 320, 240):
        if mn in ("push", "mov", "lea"):
            return ("rect_size", notes + ["size-preload"])
        if mn in ("add", "sub"):
            return ("rect_size", notes)
        return ("other", notes + ["size-like-context"])

    return ("other", notes)


def func_text_of(insns, start, addr):
    """取函数内 [start, addr) 的指令列表，用于给函数打分。"""
    out = []
    for w in insns:
        if w.address < start:
            continue
        if w.address >= addr:
            break
        out.append(w)
    return out


# --------------------------------------------------------------------- 主流程
def main():
    full = "--full" in sys.argv
    data = open(SRC, "rb").read()
    insns, nbad = disasm_text(data)
    text_starts = build_func_index(data, insns)
    starts_set = set(text_starts)
    # 起点可信度：55 8B EC 字节回扫会命中数据区（实测 0x46CE7E 真身是 51 e8 d2 64），
    # 仅字节模式命中、又没有任何 call/解码/入口证据的"函数"不可信，其命中另表隔离。
    evidence = collect_start_evidence(insns)
    byte_only = set(s for s in text_starts if s not in evidence)
    func_insns_all = collections.defaultdict(list)
    for ins in insns:
        func_insns_all[func_start_of(ins.address, text_starts)].append(ins)

    # 指令地址 -> 序号
    idx = {ins.address: k for k, ins in enumerate(insns)}
    insns_sorted = insns

    # 函数 -> 指令列表（用于打分）
    func_insns = collections.defaultdict(list)
    for ins in insns:
        fs = func_start_of(ins.address, text_starts)
        if ins.address in starts_set:
            fs = ins.address
        func_insns[fs].append(ins)

    hits = []          # (va, ins, val, notes, excluded)
    for i, ins in enumerate(insns):
        got = None
        for raw in imm_values(ins):
            if raw in TARGETS:
                got = raw
                break
        if got is None:
            continue
        fs = ins.address if ins.address in starts_set else func_start_of(ins.address, text_starts)
        notes, excluded = check_exclude(ins, got)
        guess, cnotes = classify(ins, got, i, insns)
        notes = cnotes + notes
        if fs in byte_only and ins.address not in evidence:
            notes = notes + ["unvalidated-func-start"]
            excluded = excluded or "unvalidated_func_start"
        hits.append({
            "va": ins.address,
            "fo": TEXT_FO + (ins.address - TEXT_VA),
            "func_start": fs,
            "instr_hex": ins.bytes.hex(" "),
            "instr_text": "%s %s" % (ins.mnemonic, ins.op_str),
            "value_dec": got,
            "guess": guess,
            "note": ",".join(notes),
            "excluded": excluded,
        })

    # ---------------- L3 消费点交叉印证：函数内出现 0x4A96E8 / 0x490470 ----------------
    def func_has_base_const(fs):
        got = []
        for w in func_insns.get(fs, []):
            for raw in imm_values(w):
                if raw == TBL_LAYOUT:
                    got.append("0x4A96E8")
                if raw == TBL_MAIN:
                    got.append("0x490470")
            # imul reg,reg,0xF = 布局记录 stride
            if w.mnemonic == "imul" and len(w.operands) == 3 and \
               w.operands[-1].type == CS_OP_IMM and (w.operands[-1].imm & 0xFFFFFFFF) == 0xF:
                got.append("imul*0xF")
            # mem disp 直指表基址（add reg,0x4A96E8 会编码成 mem disp 或 IMM，两者都收）
            for op in w.operands:
                if op.type == CS_OP_MEM and (op.mem.disp & 0xFFFFFFFF) in (TBL_LAYOUT, TBL_MAIN):
                    got.append("mem+0x%X" % (op.mem.disp & 0xFFFFFFFF))
        return sorted(set(got))

    # ---------------- 表 1：主 TSV ----------------
    os.makedirs(os.path.join(ROOT, "work", "peg", "relayout"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "work", "peg", "out"), exist_ok=True)

    hits.sort(key=lambda h: (h["va"]))
    p_tsv = os.path.join(ROOT, RELPATH_TSV)
    with open(p_tsv, "w", encoding="utf-8", newline="\n") as f:
        f.write("va\tfile_off\tfunc_start\tinstr_hex\tinstr_text\tvalue_hex\tvalue_dec\tguess\n")
        for h in hits:
            f.write("0x%06X\t0x%06X\t0x%06X\t%s\t%s\t0x%X\t%d\t%s\n" % (
                h["va"], h["fo"], h["func_start"], h["instr_hex"],
                h["instr_text"], h["value_dec"], h["value_dec"], h["guess"]))

    # 辅助表（证据）
    p_ctx = os.path.join(ROOT, RELPATH_CTX)
    with open(p_ctx, "w", encoding="utf-8", newline="\n") as f:
        f.write("va\tvalue_dec\tguess\tnote\texcluded\ttable_base_in_func\n")
        for h in hits:
            tb = func_has_base_const(h["func_start"])
            f.write("0x%06X\t%d\t%s\t%s\t%s\t%s\n" % (
                h["va"], h["value_dec"], h["guess"], h["note"],
                h["excluded"] or "", ";".join(tb)))

    # ---------------- 统计 ----------------
    live = [h for h in hits if not h["excluded"]]
    n_excl = len(hits) - len(live)
    n_excl_addr = sum(1 for h in hits if h["excluded"] == "addr_const")
    n_excl_float = sum(1 for h in hits
                       if h["excluded"] and h["excluded"].startswith("float32"))
    n_loop = sum(1 for h in live if "loop?" in h["note"])
    n_imullen = sum(1 for h in live if "imul-len" in h["note"])

    per_value = collections.Counter()
    per_value_live = collections.Counter()
    guess_by_value = collections.defaultdict(collections.Counter)
    for h in hits:
        per_value[h["value_dec"]] += 1
    for h in live:
        per_value_live[h["value_dec"]] += 1
        guess_by_value[h["value_dec"]][h["guess"]] += 1
    for h in hits:
        if h["excluded"]:
            guess_by_value[h["value_dec"]]["excluded"] += 1

    func_hits = collections.defaultdict(list)
    for h in live:
        func_hits[h["func_start"]].append(h)
    top_funcs = sorted(func_hits.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:20]

    both_800_600 = []
    only_800 = []
    only_600 = []
    for fs, hs in func_hits.items():
        vals = set(h["value_dec"] for h in hs)
        if 800 in vals and 600 in vals:
            both_800_600.append(fs)
        if 800 in vals and 600 not in vals:
            only_800.append(fs)
        if 600 in vals and 800 not in vals:
            only_600.append(fs)
    both_800_600.sort()
    only_800.sort()
    only_600.sort()

    # 已知 L3 消费函数是否落在命中里
    l3_known = {}
    for fs in (0x413932, 0x41407A, 0x430960, 0x445FFF):
        n = len(func_hits.get(fs, []))
        tb = func_has_base_const(fs)
        l3_known[fs] = (n, tb)

    # ---------------- 打分：L3 / L5 候选函数 ----------------
    def score_l3(fs):
        hs = func_hits[fs]
        s = 0
        reasons = []
        tb = func_has_base_const(fs)
        if "0x4A96E8" in tb:
            s += 100
            reasons.append("读布局表基址0x4A96E8")
        if "imul*0xF" in tb:
            s += 60
            reasons.append("imul*stride0xF")
        if "0x490470" in tb:
            s += 80
            reasons.append("读主布局表0x490470")
        if fs in KNOWN_L3_CONSUMERS:
            s += 50
            reasons.append("docs80 已列 L3 消费函数")
        vals = set(h["value_dec"] for h in hs)
        if 800 in vals and 600 in vals:
            s += 30
            reasons.append("同函数含800+600")
        if any(h["note"].find("field+") >= 0 for h in hs):
            s += 20
            reasons.append("命中点读写+0x02/+0x04/+0x06 字段偏移")
        s += min(len(hs), 12) * 2
        reasons.append("命中%d条" % len(hs))
        return s, reasons

    def score_l5(fs):
        hs = func_hits[fs]
        s = 0
        reasons = []
        halves = [h for h in hs if h["value_dec"] in HALVES and h["guess"] == "center_math"]
        if halves:
            s += 40
            reasons.append("半屏常量%s" % "/".join(str(h["value_dec"]) for h in halves[:4]))
        body = func_insns.get(fs, [])
        has_shift = any(w.mnemonic in ("sar", "shr") for w in body)
        has_div2 = any(w.mnemonic == "imul" and len(w.operands) == 3 and
                       w.operands[-1].type == CS_OP_IMM and (w.operands[-1].imm & 0xFFFFFFFF) in (2,)
                       for w in body)
        has_neg = any(w.mnemonic == "neg" for w in body)
        has_cdq = any(w.mnemonic == "cdq" for w in body)
        is_neg = False
        if halves:
            hs_va = min(h["va"] for h in halves)
            for w in body:
                if w.mnemonic in ("sub", "neg") and abs(w.address - hs_va) <= 0x40:
                    is_neg = True
        if has_shift:
            s += 20
            reasons.append("函数内有sar/shr")
        if has_div2:
            s += 15
            reasons.append("imul*2")
        if has_cdq:
            s += 15
            reasons.append("cdq")
        if is_neg:
            s += 35
            reasons.append("半屏常量邻近sub/neg")
        if 800 in set(h["value_dec"] for h in hs) and 600 in set(h["value_dec"] for h in hs):
            s += 10
            reasons.append("同函数含800+600")
        s += min(len(hs), 10)
        reasons.append("命中%d条" % len(hs))
        return s, reasons

    l3_rank = sorted(func_hits, key=lambda fs: (-score_l3(fs)[0], fs))[:15]
    l5_rank = sorted(func_hits, key=lambda fs: (-score_l5(fs)[0], fs))[:15]

    # ---------------- 摘要文件 ----------------
    lines = []
    A = lines.append
    A("IMMEDIATE-CENSUS SUMMARY")
    A("exe              = %s" % SRC)
    A("text             = VA 0x%X .. 0x%X (VirtualSize 0x%X)" % (TEXT_VA, TEXT_END, TEXT_VSIZE))
    A("instructions     = %d (resync %d)" % (len(insns), nbad))
    A("func_starts      = %d" % len(text_starts))
    A("targets          = %s" % ",".join(str(t) for t in TARGETS))
    A("hits_raw         = %d" % len(hits))
    A("hits_excluded    = %d" % n_excl)
    A("hits_live        = %d" % len(live))
    A("")
    A("[per value: raw / live / guess-distribution]")
    for v in TARGETS:
        dist = ", ".join("%s=%d" % kv for kv in sorted(guess_by_value[v].items()))
        A("%5d (0x%03X)  raw=%-5d live=%-5d  %s" % (v, v, per_value[v], per_value_live[v], dist))
    A("")
    A("[top20 funcs by live hit count]")
    for fs, hs in top_funcs:
        vals = collections.Counter(h["value_dec"] for h in hs)
        tb = func_has_base_const(fs)
        A("0x%06X  n=%-4d  %s%s" % (fs, len(hs),
                                    " ".join("%d:%d" % (k, vals[k]) for k in sorted(vals)),
                                    ("  TBL[%s]" % ";".join(tb)) if tb else ""))
    A("")
    A("[funcs with both 800 and 600] n=%d" % len(both_800_600))
    for fs in both_800_600:
        A("  0x%06X n=%d" % (fs, len(func_hits[fs])))
    A("[funcs with 800 only] n=%d" % len(only_800))
    for fs in only_800:
        A("  0x%06X n=%d" % (fs, len(func_hits[fs])))
    A("[funcs with 600 only] n=%d" % len(only_600))
    for fs in only_600:
        A("  0x%06X n=%d" % (fs, len(func_hits[fs])))
    A("")
    A("[known L3 consumers from docs80 - do they show immediates?]")
    for fs, (n, tb) in sorted(l3_known.items()):
        A("  0x%06X  immediate_hits=%d  tbl_markers=%s" % (fs, n, ";".join(tb) or "-"))
    A("")
    A("[L3 candidate ranking]")
    for fs in l3_rank:
        s, rs = score_l3(fs)
        A("  score=%-4d 0x%06X  %s" % (s, fs, " | ".join(rs)))
    A("")
    A("[L5 candidate ranking]")
    for fs in l5_rank:
        s, rs = score_l5(fs)
        A("  score=%-4d 0x%06X  %s" % (s, fs, " | ".join(rs)))
    p_sum = os.path.join(ROOT, RELPATH_SUMMARY)
    with open(p_sum, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    # ---------------- 中文报告 ----------------
    R = []
    a = R.append
    a("# PeG030.exe `.text` 坐标类立即数普查报告（P0 第二路证据）")
    a("")
    a("对象：`%s`（**只读**，未修改）" % SRC)
    a("脚本：`work\\_scratch\\peg\\_immediate_census.py`（capstone 线性反汇编）")
    a("")
    a("## 1. 覆盖与总量")
    a("")
    a("| 项 | 值 |")
    a("|---|---|")
    a("| `.text` | VA 0x%06X–0x%06X，VirtualSize 0x%X |" % (TEXT_VA, TEXT_END, TEXT_VSIZE))
    a("| 文件偏移换算 | `fo = VA - 0x400000`（本题 .text 的 RAW=0x400 与 RVA=0x1000 巧合相等） |")
    a("| 反汇编指令数 | %d（坏字节重同步 %d 处） |" % (len(insns), nbad))
    a("| 识别出的函数起点 | %d |" % len(text_starts))
    a("| 原始命中 | **%d** |" % len(hits))
    a("| 机械排除（浮点位型/段内地址） | %d |" % n_excl)
    a("| 计入统计的有效命中 | **%d** |" % len(live))
    a("")
    a("函数起点判定：`55 8B EC`（push ebp; mov ebp,esp）字节回扫 + 所有 `call rel32` 的")
    a("目标地址，两者取并集。仅用前者会漏掉所有无帧指针函数；仅用后者会漏掉只被跳转")
    a("到达的函数。题目要求\"向上回扫 55 8B EC\"，本表 `func_start` 即该回扫结果，")
    a("并在无该序言时退化为最近的已识别函数边界。")
    a("")
    a("## 2. 每值命中分布")
    a("")
    a("| 值 | hex | 原始 | 有效 | guess 分布 |")
    a("|---|---|---|---|---|")
    for v in TARGETS:
        dist = "，".join("%s=%d" % kv for kv in sorted(guess_by_value[v].items()))
        a("| %d | 0x%X | %d | %d | %s |" % (v, v, per_value[v], per_value_live[v], dist))
    a("")
    a("## 3. 排除依据（可机械判定的三类）")
    a("")
    a("每题面原文要求\"把显然的循环计数、结构大小、地址常量排除掉并说明排除依据\"。")
    a("实际执行如下，**只排除能给出确定证据的**，不确定的一律保留并在辅助表标注：")
    a("")
    a("1. **越界立即数**：目标值全部 ≤1920，任何 >0xFFFF 的立即数不可能命中，天然不入表。")
    a("2. **段内地址常量**：立即数落在 `0x400200–0x73FFFF`（映像内）→ 标 `addr_const`")
    a("   排除。依据：这些是 `push 0x48E202` / `mov eax,0x48C000` 这类取址指令，")
    a("   与设计坐标无因果关系。实测排除 **%d** 条。" % n_excl_addr)
    a("3. **浮点常量位型**：立即数位型可解释为 32.0–4096.0 的 IEEE-754 单精度")
    a("   （如 `800.0f = 0x44480000`）→ 标 `float32(x)` 排除。依据：x87/SSE 常量池的")
    a("   位型落进整数目标值是**位型巧合**，不是设计坐标。实测排除 **%d** 条。" % n_excl_float)
    a("")
    a("**未排除但需人工复核的两类**（无法从单条指令可靠判定，故不静默丢弃）：")
    a("")
    a("- `loop?`：`cmp reg,值` + 紧随条件跳转，且该寄存器在邻域 ±3 条内被 `inc/dec`")
    a("  修改（自增循环计数器的典型形态）。实测标记 **%d** 条。" % n_loop)
    a("- `imul-len`：三操作数 `imul reg,reg,值`。这类**几乎必然是定长步长/结构大小**")
    a("  （项目里布局表 stride `imul reg,reg,0xF`、单位表 memset `400×0x58` 都是此形态），")
    a("  但 stride 本身就是布局证据，所以标 `other` 保留而不删。实测标记 **%d** 条。"
      % n_imullen)
    a("")
    a("> 辅助证据表 `%s` 的 `note` 列携带上述标记，" % RELPATH_CTX)
    a("> `table_base_in_func` 列标注该函数内是否出现布局表基址。")
    a("")
    a("## 4. 函数命中簇：Top 20")
    a("")
    a("| func_start | 命中数 | 值分布 | 表基址标记 |")
    a("|---|---|---|---|")
    for fs, hs in top_funcs:
        vals = collections.Counter(h["value_dec"] for h in hs)
        tb = func_has_base_const(fs)
        a("| 0x%06X | %d | %s | %s |" % (fs, len(hs),
                                        " ".join("%d×%d" % (k, vals[k]) for k in sorted(vals)),
                                        "，".join(tb) if tb else "—"))
    a("")
    a("## 5. 800/600 共现 vs 仅 800")
    a("")
    a("题面判断：**同时出现 800 与 600 的函数极可能是布局/居中/视口代码**；")
    a("**只有 800 的可能是宽度钳位**。实测结果：")
    a("")
    a("- **800 与 600 同现**：%d 个函数" % len(both_800_600))
    a("- **仅 800**：%d 个函数" % len(only_800))
    a("- **仅 600**：%d 个函数" % len(only_600))
    a("")
    a("### 5.1 800+600 同现（前 30）")
    a("")
    a("| func_start | 命中数 | 值分布 | 表基址标记 |")
    a("|---|---|---|---|")
    for fs in both_800_600[:30]:
        hs = func_hits[fs]
        vals = collections.Counter(h["value_dec"] for h in hs)
        tb = func_has_base_const(fs)
        a("| 0x%06X | %d | %s | %s |" % (fs, len(hs),
                                        " ".join("%d×%d" % (k, vals[k]) for k in sorted(vals)),
                                        "，".join(tb) if tb else "—"))
    a("")
    if len(both_800_600) > 30:
        a("（其余 %d 个见摘要文件）" % (len(both_800_600) - 30))
        a("")
    a("### 5.2 仅 800（宽度钳位嫌疑，前 30）")
    a("")
    a("| func_start | 命中数 | 值分布 |")
    a("|---|---|---|")
    for fs in only_800[:30]:
        hs = func_hits[fs]
        vals = collections.Counter(h["value_dec"] for h in hs)
        a("| 0x%06X | %d | %s |" % (fs, len(hs),
                                   " ".join("%d×%d" % (k, vals[k]) for k in sorted(vals))))
    a("")
    a("### 5.3 仅 600（下/高度钳位嫌疑，前 20）")
    a("")
    a("| func_start | 命中数 | 值分布 |")
    a("|---|---|---|")
    for fs in only_600[:20]:
        hs = func_hits[fs]
        vals = collections.Counter(h["value_dec"] for h in hs)
        a("| 0x%06X | %d | %s |" % (fs, len(hs),
                                   " ".join("%d×%d" % (k, vals[k]) for k in sorted(vals))))
    a("")
    a("### 5.4 对题面判读的修正（重要）")
    a("")
    a("题面的两个猜测方向都对，但**不能只靠\"是否同现\"区分**：")
    a("")
    a("- 800 与 600 **同现**也可能只是\"先钳宽再看高\"的两条独立守卫，未必是布局消费点；")
    a("- **仅含 800** 的函数里，`cmp …,0x320` 是钳位上限，而 `push 0x320` 是矩形宽——")
    a("  两者语义完全不同，靠共现无法分辨，必须看助记符与邻近字段偏移。")
    a("")
    a("因此本报告给出**更强判据**：函数内是否出现布局表基址 `0x4A96E8` / 主布局表")
    a("`0x490470` / stride `imul reg,reg,0xF`。这才是 L3 消费点的直接证据。")
    a("")
    a("## 6. L3 布局表消费点候选（Top 10）")
    a("")
    a("判据（加权）：函数内出现 `0x4A96E8`（+100）/ `0x490470`（+80）/ `imul*0xF`（+60）")
    a("/ 命中点读写 `+0x02/+0x04/+0x06` 字段偏移（+20）/ 同函数 800+600（+30）/")
    a("docs\\80 已列的消费函数（+50）/ 命中条数（每条 +2，上限 12 条）。")
    a("")
    a("| 排名 | func_start | 分数 | 判据 |")
    a("|---|---|---|---|")
    for i, fs in enumerate(l3_rank[:10], 1):
        s, rs = score_l3(fs)
        a("| %d | 0x%06X | %d | %s |" % (i, fs, s, "，".join(rs)))
    a("")
    a("### 6.1 与 docs\\80 已知 L3 消费函数的对照")
    a("")
    a("docs\\80 §L3 明列 4 个消费函数：`0x413932`、`0x41407A`、`0x430960`、`0x445FFF`。")
    a("它们**不一定含 800/600 立即数**——因为它们读的是布局表记录里的坐标字段，")
    a("设计坐标在数据段而不在指令流里。实测：")
    a("")
    a("| func_start | 立即数命中 | 函数内表基址标记 |")
    a("|---|---|---|")
    for fs, (n, tb) in sorted(l3_known.items()):
        a("| 0x%06X | %d | %s |" % (fs, n, "，".join(tb) if tb else "—"))
    a("")
    a("**这条结论对 P0 很重要**：立即数普查（本表）与布局表普查（第一路证据）是")
    a("互补而非重叠的两条证据链。L3 消费点的主要识别手段是**表基址引用**，")
    a("立即数普查负责的是 L5（内联居中算术）与 L2（裁剪/边界）这两层。")
    a("")
    a("## 7. L5 内联居中算术候选（Top 10）")
    a("")
    a("judged by：半屏常量（400/300/320/240）且 guess=center_math（+40），")
    a("函数内有 `sar/shr`（+20）、`imul*2`（+15）、`cdq`（+15），")
    a("半屏常量邻近 `sub/neg`（+35，即 `(800-w)/2` 的 `sub` 形态）。")
    a("")
    a("| 排名 | func_start | 分数 | 判据 |")
    a("|---|---|---|---|")
    for i, fs in enumerate(l5_rank[:10], 1):
        s, rs = score_l5(fs)
        a("| %d | 0x%06X | %d | %s |" % (i, fs, s, "，".join(rs)))
    a("")
    a("### 7.1 半屏常量的形态说明")
    a("")
    a("所谓\"`(800-w)/2` 形态的立即数\"，编译器**不会**把 400 直接编成一条指令，")
    a("而是：")
    a("")
    a("```asm")
    a("; (800 - w) / 2  的典型编译结果")
    a("mov  ecx, 0x320      ; <-- 这里才是立即数命中点")
    a("sub  ecx, eax")
    a("sar  ecx, 1          ; 或 cdq + sub eax,edx + sar eax,1")
    a("```")
    a("")
    a("所以 L5 的定位特征是**\"400/300/320/240 立即数 + 邻近的 sub/sar\"**，")
    a("本报告的 L5 打分就是按这个形态设计的。相对地，`push 0x190` / `mov [..],0x190`")
    a("（无邻近 sub/sar）更可能是尺寸常量而非居中算术，会落到 `rect_size` 或 `other`。")
    a("")
    a("## 8. guess 取值口径")
    a("")
    a("| guess | 含义 | 判定规则 |")
    a("|---|---|---|")
    a("| `clamp_max` | 上界钳位/越界判定 | 值为 799/599（= D−1），或 `cmp/sub/test` 型且值为屏宽高族 |")
    a("| `boundary` | 一般边界比较 | `cmp/sub/test` 型命中其余值 |")
    a("| `center_math` | 居中算术 | 值为 400/300/320/240（半屏族） |")
    a("| `rect_size` | 矩形宽高/描述符尺寸 | 值为屏宽高族且为 `push/mov/lea/add/sub` |")
    a("| `other` | 其余（含 imul 步长、未判定） | 兜底 |")
    a("")
    a("## 9. 交付物")
    a("")
    a("| 文件 | 内容 |")
    a("|---|---|")
    a("| `%s` | 主表，%d 行（含题面要求的 8 列） |" % (RELPATH_TSV, len(hits)))
    a("| `%s` | 辅助证据表，带 note / excluded / 表基址标记 |" % RELPATH_CTX)
    a("| `%s` | 本报告 |" % RELPATH_REPORT)
    a("| `%s` | 机器可读统计摘要 |" % RELPATH_SUMMARY)
    a("")
    a("只读声明：母本 `D:\\Program Files\\PeG\\PeG030.exe` 及 `D:\\Program Files\\PeG\\` 下")
    a("任何文件均未修改（脚本只以 `\"rb\"` 打开）。未启动游戏。")
    a("")
    a("## 10. 附：全部命中（按 VA）")
    a("")
    if full:
        a("| va | func_start | instr | 值 | guess | note |")
        a("|---|---|---|---|---|---|")
        for h in hits:
            a("| 0x%06X | 0x%06X | `%s` | %d | %s | %s |" % (
                h["va"], h["func_start"], h["instr_text"], h["value_dec"], h["guess"],
                h["note"] + ((" EXCL:" + h["excluded"]) if h["excluded"] else "")))
    else:
        a("共 %d 条，全部在主表 `%s`（%d 列，制表符分隔）。" % (len(hits), RELPATH_TSV, 8))
        a("本报告只嵌入统计与候选清单，避免报告膨胀；加 `--full` 可把逐条清单也写进报告。")

    p_rep = os.path.join(ROOT, RELPATH_REPORT)
    with open(p_rep, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(R) + "\n")

    # 控制台简版（防乱码用 ascii-safe 关键数字）
    print("OK hits=%d excluded=%d live=%d funcs=%d insns=%d"
          % (len(hits), n_excl, len(live), len(text_starts), len(insns)))
    print("TSV     : %s" % p_tsv)
    print("CTX     : %s" % p_ctx)
    print("REPORT  : %s" % p_rep)
    print("SUMMARY : %s" % p_sum)
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
