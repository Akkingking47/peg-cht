# -*- coding: utf-8 -*-
r"""
审计所有 HTMLayoutSetElementHtml / SetElementInnerText16 调用点：
检查其 htmlLength / length 参数是否来自 W2U8（UTF-8 转换）后的串，
还是错误地用了别的长度字段。

对每个 call [0x47f0e0] / [0x47f0e4] 点，回看前 40 条指令，
找出 push 的 4 个参数来源。
"""
import struct
from capstone import *

EXE = r'D:\PGForever1.021\PGForever.exe'
raw = open(EXE, 'rb').read()
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

TEXT_OFF, TEXT_VA, TEXT_SZ = 0x400, 0x401000, 0x7DE00
text = raw[TEXT_OFF:TEXT_OFF + TEXT_SZ]
insns = list(md.disasm(text, TEXT_VA))
idx = {i.address: n for n, i in enumerate(insns)}

TARGETS = {0x47F0E0: 'SetElementHtml', 0x47F0E4: 'SetElementInnerText16'}
W2U8 = 0x402B50
# W2U8 的「正确长度」缓存在调用后 —— 但我们要看调用点用的 push 源

print('=' * 78)
for n, ins in enumerate(insns):
    if ins.mnemonic != 'call':
        continue
    if not ins.op_str.startswith('dword ptr [0x47f0e'):
        continue
    try:
        slot = int(ins.op_str.split('[')[1].split(']')[0], 16)
    except Exception:
        continue
    if slot not in TARGETS:
        continue
    name = TARGETS[slot]
    print('\n### %s  @ %08X' % (name, ins.address))
    # 回看 30 条
    lo = max(0, n - 30)
    w2u8_at = None
    for k in range(lo, n):
        i = insns[k]
        if i.mnemonic == 'call' and i.op_str.startswith('0x402b50'):
            w2u8_at = i.address
    if w2u8_at:
        print('   ★ 紧邻上游有 W2U8 @ %08X  → 内容为 UTF-8 字节流' % w2u8_at)
    else:
        print('   （无 W2U8，内容可能本来就是窄串）')
    # 打印 push 序列（末尾几条）
    pushes = []
    for k in range(max(lo, n - 12), n):
        i = insns[k]
        if i.mnemonic in ('push', 'mov', 'lea'):
            pushes.append('    %08X  %-6s %s' % (i.address, i.mnemonic, i.op_str))
    print('    --- 调用前 12 条 ---')
    for l in pushes:
        print(l)
