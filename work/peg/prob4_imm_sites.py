# -*- coding: utf-8 -*-
"""prob4_imm_sites.py — 全 .text 扫描 800/799/798/601/600/599 立即数站点，
标注：指令 VA / 所在指令 / 立即数 VA / 是否在已知 141 补丁清单里 / 是否已被 v10b 改。

已知清单（来自 patch_res_wh.CODE_EDITS + build_v10.CANVAS_SITES + 任务描述）统一在这里。
"""
import json
import re
import struct
import sys
sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\peg")
import hint_pe as H

# ---- 已知 141 条补丁里的「代码侧」站点（指令 VA 或立即数 VA）----
# patch_res_wh.py CODE_EDITS：imm32 地址
CODE_EDITS = [0x41C4D7, 0x41C4DE, 0x44C5CD, 0x44C5D2, 0x44C731, 0x44C778,
              0x44C86A, 0x44C8B1, 0x44CC68, 0x44CCAF]
# build_v10.py CANVAS_SITES：指令 VA
CANVAS_SITES = [0x4421D4, 0x4421DE, 0x442219, 0x442223,
                0x43B22C, 0x43B242, 0x43BD8F, 0x43BDA5]
# build_v10 PANEL_SITE：指令 VA
PANEL_SITES = [0x45696D]
# 任务描述说的 4 条画布描述符（指令 VA）
DESC_VAS = [0x4421D4, 0x4421DE, 0x442219, 0x442223]
REPAINT = [0x4489D8]

base = H.load(H.SRC)
port = H.load(H.PORT)

TARGETS = {0x31F: "799", 0x320: "800", 0x321: "801", 0x31E: "798",
           0x257: "599", 0x258: "600", 0x259: "601", 0x256: "598",
           0x1DF: "479", 0x1E0: "480", 0x18F: "399", 0x190: "400",
           0x12B: "299", 0x12C: "300", 0x63: "99", 0x64: "100",
           0x5F: "95", 0x60: "96", 0x2D: "45", 0x1E: "30",
           0x78: "120", 0x7C: "124"}

rows = []
for ins in H.dis_all(H.TEXT_VA, H.TEXT_VA + H.TEXT_SIZE, base):
    nums = re.findall(r"0x([0-9a-f]+)", ins.op_str)
    # 立即数编码的实际文件偏移：直接用 capstone 操作数
    for m in re.finditer(r"0x([0-9a-f]{2,8})", ins.op_str):
        v = int(m.group(1), 16)
        if v in TARGETS:
            # 找到该 imm 在指令字节里的偏移（最后一个匹配，从尾部找）
            ib = struct.pack("<I", v) if v > 0xFF else struct.pack("<I", v)
            rows.append((ins.address, ins.mnemonic + " " + ins.op_str, v, ins.size))

print("=== .text 里值 ∈{799,800,801,798,599,600,601,598,...} 的立即数站点 ===")
print("指令 VA / 反汇编 / 十进制 / 立即数 VA(推算) / v10b 是否改了该指令字节")
print()
known_instr = set(CODE_EDITS) | set(CANVAS_SITES) | set(PANEL_SITES) | set(REPAINT)
imm_va_set = set(CODE_EDITS)

n = 0
for va, txt, v, size in rows:
    if v not in (0x31F, 0x320, 0x321, 0x31E, 0x257, 0x258, 0x259, 0x256):
        continue
    b1 = H.blob(base, va, max(size, 1))
    b2 = H.blob(port, va, max(size, 1))
    changed = b1 != b2
    mark = ""
    if va in known_instr or va in imm_va_set:
        mark = " <== 已在 141 清单"
    if not changed and mark:
        mark += " (!v10b 未变)"
    print("0x%06X  %-44s = %-4d   len=%d  %s  changed=%s%s"
          % (va, txt, v, size, b1.hex(" "), changed, mark))
    n += 1
print("\n合计 %d 个站点" % n)
