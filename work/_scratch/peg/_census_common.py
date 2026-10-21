# -*- coding: utf-8 -*-
"""_census_common.py — 坐标立即数普查公共层。

被 _immediate_census.py 与 _layout_stride_census.py 共用：
  load_text()      读 PE、定位 .text、计算 file_off 映射
  disasm_text()    线性反汇编全段（坏字节前进 1 字节重新同步）
  func_starts()    函数起点集合（55 8B EC 字节回扫 + call rel32 目标）
  func_start_of()  二分取所属函数起点
  targets()        目标立即数值表

file_off 约定（题面给定，全段恒定）：
    file_off = va - 0x400000 - 0x1000 + 0x1000 = va - 0x400000
"""
import bisect
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r"D:\DSH\军事游戏汉化"
SRC = r"D:\Program Files\PeG\PeG030.exe"

IMAGE_BASE = 0x400000
TEXT_RVA = 0x1000
TEXT_VSIZE = 0x8A136
TEXT_RAW = 565760
TEXT_FO = 0x1000            # .text 文件偏移（= PointerToRawData）
TEXT_VA = IMAGE_BASE + TEXT_RVA          # 0x401000
TEXT_END = TEXT_VA + TEXT_VSIZE          # 0x48B136

TARGETS = [800, 600, 799, 599, 400, 300, 320, 240, 1920, 1080, 640, 480]
TARGET_HEX = {v: "0x%X" % v for v in TARGETS}

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True


def va2fo(va):
    return va - IMAGE_BASE


def load_text():
    with open(SRC, "rb") as f:
        data = f.read()
    return data


def disasm_text(data):
    """线性反汇编 .text 全 VirtualSize；坏字节前进 1 字节重新同步。

    返回 (insns, nbad)。nbad = 强制重新同步的次数，用于报告解码健康度。
    """
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


def func_starts(data, insns):
    """函数起点集合（升序）。

    两边都收：
      (a) 指令流里的 `push ebp` + `mov ebp,esp`（题面指定的 55 8B EC 回扫目标）；
      (b) 所有 `call rel32` 的目标地址（函数边界最强证据，覆盖无帧指针的函数）。
    再加 (c) 原始字节 55 8B EC 全段回扫（不依赖解码对齐，与题面一致）。
    """
    starts = set()
    for i, ins in enumerate(insns):
        if ins.mnemonic == "push" and ins.op_str == "ebp" and i + 1 < len(insns):
            nxt = insns[i + 1]
            if nxt.mnemonic == "mov" and nxt.op_str.replace(" ", "") in ("ebp,esp", "ebp, esp"):
                starts.add(ins.address)
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == 2:  # CS_OP_IMM
            t = ins.operands[0].imm & 0xFFFFFFFF
            if TEXT_VA <= t < TEXT_END:
                starts.add(t)
    pat = b"\x55\x8b\xec"
    pos = data.find(pat, TEXT_FO, TEXT_FO + TEXT_VSIZE)
    while pos >= 0:
        starts.add(TEXT_VA + (pos - TEXT_FO))
        pos = data.find(pat, pos + 1, TEXT_FO + TEXT_VSIZE)
    return sorted(starts)


def func_start_of(addr, starts):
    """二分找 <= addr 的最近函数起点。"""
    i = bisect.bisect_right(starts, addr) - 1
    if i < 0:
        return TEXT_VA
    return starts[i]


def ff32(raw):
    return struct.unpack("<f", struct.pack("<I", raw & 0xFFFFFFFF))[0]


def func_start_of(addr, starts):
    """二分找 <= addr 的最近函数起点。"""
    i = bisect.bisect_right(starts, addr) - 1
    if i < 0:
        return TEXT_VA
    return starts[i]


# --------------------------------------------------------------------- PE 解析
def pe_text_bounds(path=None):
    """从 PE 头读出 .text 的 (RVA, VirtualSize, PointerToRawData, SizeOfRawData)。

    题面已经把常量给了我们，这一步是为了**自证**它们（避免抄错），
    并让 file_off 映射有独立依据。
    """
    import struct as _s
    with open(path or SRC, "rb") as f:
        head = f.read(0x400)
    e_lfanew = _s.unpack_from("<I", head, 0x3C)[0]
    assert head[e_lfanew:e_lfanew + 4] == b"PE\0\0", "not a PE"
    coff = e_lfanew + 4
    nsec = _s.unpack_from("<H", head, coff + 2)[0]
    opt_size = _s.unpack_from("<H", head, coff + 16)[0]
    sec0 = coff + 20 + opt_size
    out = []
    for i in range(nsec):
        o = sec0 + i * 40
        name = head[o:o + 8].rstrip(b"\0").decode("latin1")
        vsize, rva, rsize, praw = _s.unpack_from("<IIII", head, o + 8)
        out.append((name, rva, vsize, praw, rsize))
    return out


def find_text_section():
    for name, rva, vsize, praw, rsize in pe_text_bounds():
        if name == ".text":
            return rva, vsize, praw, rsize
    raise RuntimeError(".text not found")


# --------------------------------------------------- 函数起点可信度判别（关键）
def build_start_evidence(data, insns, starts=None):
    """把候选函数起点分成"有证据"和"仅字节模式"两类。

    动机（踩坑记录）：`55 8B EC` 字节回扫**会命中数据区**。
    实测 `0x46CE7E` 在文件里是 `51 e8 d2 64`，根不是函数头；真正的函数头是
    `0x46C27E`。前一个普查脚本用的线性扫掠在这里跨过函数入口，
    把数据当成代码，在 `0x46CE7E` 造出了一个假函数，并顺带把它的"命中"写进了表。

    判别规则：
      evidence = {入口 RVA == OptionalHeader.AddressOfEntryPoint}
               ∪ {全部 call rel32 目标}
               ∪ {被线性扫掠解码出的指令地址}
      byte_only = func_starts() 的字节模式候选 − evidence
      → `byte_only` 的函数**一律不可信**（数据区巧合），其名下命中全部另表隔离。

    返回 (starts_all, evidence_set, byte_only_set)。
    """
    if starts is None:
        starts = func_starts(data, insns)
    decoded = set(ins.address for ins in insns)
    calls = set()
    for ins in insns:
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == 2:
            t = ins.operands[0].imm & 0xFFFFFFFF
            if TEXT_VA <= t < TEXT_END:
                calls.add(t)
    # 入口点
    import struct as _s
    with open(SRC, "rb") as f:
        head = f.read(0x400)
    e_lfanew = _s.unpack_from("<I", head, 0x3C)[0]
    entry_rva = _s.unpack_from("<I", head, e_lfanew + 4 + 20 + 16)[0]
    evidence = calls | decoded | {IMAGE_BASE + entry_rva}
    byte_only = set(s for s in starts if s not in evidence)
    return starts, evidence, byte_only

