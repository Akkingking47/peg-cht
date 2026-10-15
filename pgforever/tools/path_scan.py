# -*- coding: utf-8 -*-
"""
文本加载路径扫描器
==================
把「磁盘文本 -> 屏幕」链路上所有可疑调用点枚举出来：
  - HTMLayout*  API
  - WideCharToMultiByte / MultiByteToWideChar
  - CreateFile*/ReadFile  （用于找文件读取链）

对每个调用点标注：所属函数入口、前若干条指令、操作数。
"""
import struct
from capstone import *

EXE = r'D:\PGForever1.021\PGForever.exe'
IMAGEBASE = 0x400000
raw = open(EXE, 'rb').read()

e_lfanew = struct.unpack_from('<I', raw, 0x3C)[0]
pe = e_lfanew
num_sec = struct.unpack_from('<H', raw, pe + 6)[0]
opt_size = struct.unpack_from('<H', raw, pe + 0x14)[0]
sec_tbl = pe + 0x18 + opt_size
opt = pe + 0x18
imp_rva, imp_size = struct.unpack_from('<II', raw, opt + 0x60 + 8)

SECTIONS = []
for i in range(num_sec):
    off = sec_tbl + i * 0x28
    name = raw[off:off + 8].rstrip(b'\x00').decode('latin1')
    vsize, vaddr, rsize, raddr = struct.unpack_from('<IIII', raw, off + 8)
    SECTIONS.append((name, vaddr, vsize, raddr, rsize))
    print('sec %-8s VA=%08X vsize=%X raw=%08X rsize=%X' % (name, IMAGEBASE + vaddr, vsize, raddr, rsize))


def rva2off(rva):
    for name, vaddr, vsize, raddr, rsize in SECTIONS:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            return raddr + (rva - vaddr)
    return None


# ---- IAT 映射 ----
slot2name = {}
descr = rva2off(imp_rva)
while True:
    oft, _, _, name_rva, ft = struct.unpack_from('<IIIII', raw, descr)
    if ft == 0:
        break
    dll = raw[rva2off(name_rva):].split(b'\x00')[0].decode('latin1', 'replace')
    int_off = rva2off(oft) if oft else None
    iat_off = rva2off(ft)
    j = 0
    while True:
        (val,) = struct.unpack_from('<I', raw, (int_off if int_off is not None else iat_off) + j * 4)
        if val == 0:
            break
        iat_va = IMAGEBASE + ft + j * 4
        if val & 0x80000000:
            nm = 'ord%d' % (val & 0x7fffffff)
        else:
            no = rva2off(val)
            nm = raw[no + 2:].split(b'\x00')[0].decode('latin1', 'replace') if no else '?'
        slot2name[iat_va] = dll + '!' + nm
        j += 1
    descr += 0x14

# ---- 反汇编整段可执行区 ----
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
allins = []
for name, vaddr, vsize, raddr, rsize in SECTIONS:
    if not (name.startswith('.text') or name.startswith('.rdata')):
        continue
    if name != '.text':
        continue
    code = raw[raddr:raddr + rsize]
    allins.extend(md.disasm(code, IMAGEBASE + vaddr))
allins.sort(key=lambda i: i.address)
print('指令数:', len(allins))
addr_set = {i.address: k for k, i in enumerate(allins)}


def func_start(va):
    k = addr_set.get(va)
    if k is None:
        return None
    for j in range(k, max(0, k - 4000), -1):
        a = allins[j]
        if a.mnemonic == 'push' and a.op_str == 'ebp' and j + 1 < len(allins):
            b = allins[j + 1]
            if b.mnemonic == 'mov' and b.op_str.replace(' ', '') == 'ebp,esp':
                return a.address
    return None


# ---- 找所有 call [0x47xxxx] ----
CATS = {
    'HTMLayout': lambda n: n.startswith('htmlayout!') or 'HTMLayout' in n,
    'Conv': lambda n: ('WideChar' in n or 'MultiByte' in n),
    'File': lambda n: (n.endswith('!CreateFileW') or n.endswith('!CreateFileA')
                       or n.endswith('!ReadFile') or n.endswith('!fopen')
                       or n.endswith('!fread') or n.endswith('!_wfopen')),
    'Mem': lambda n: n.endswith('!malloc') or n.endswith('!calloc') or n.endswith('!realloc'),
}

for cat, pred in CATS.items():
    print('\n' + '=' * 70)
    print('### %s' % cat)
    print('=' * 70)
    for k, ins in enumerate(allins):
        if ins.mnemonic != 'call':
            continue
        op = ins.operands[0] if ins.operands else None
        if op is None or op.type != CS_OP_MEM:
            continue
        tgt_va = None
        if op.mem.base == 0 and op.mem.index == 0:
            tgt_va = op.mem.disp
        if tgt_va is None:
            continue
        nm = slot2name.get(tgt_va)
        if not nm or not pred(nm):
            continue
        fs = func_start(ins.address)
        # 抓前 12 条指令
        ctx = allins[max(0, k - 12):k + 1]
        ctxs = ' ; '.join('%s %s' % (x.mnemonic, x.op_str) for x in ctx)
        print('\n-- @%08X  func=%s  %s' % (ins.address, ('%08X' % fs) if fs else '?', nm))
        print('   %s' % ctxs)
