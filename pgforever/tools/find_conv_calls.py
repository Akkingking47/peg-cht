# -*- coding: utf-8 -*-
r"""
定位 exe 中对 WideCharToMultiByte / MultiByteToWideChar 的调用点，
并尝试回溯其 CodePage 参数，判断是否存在 CP_ACP(0) 且应改为 CP_UTF8(65001)。
"""
import struct

EXE = r'D:\PGForever1.021\PGForever.exe'
b = open(EXE, 'rb').read()
e = struct.unpack_from('<I', b, 0x3c)[0]
nsec = struct.unpack_from('<H', b, e+6)[0]
sizeopt = struct.unpack_from('<H', b, e+20)[0]
optoff = e + 24
magic = struct.unpack_from('<H', b, optoff)[0]
ddoff = optoff + (112 if magic == 0x20b else 96)
imagebase = struct.unpack_from('<I', b, optoff + 28)[0]

secs = []
so = optoff + sizeopt
for i in range(nsec):
    o = so + i*40
    name = b[o:o+8].rstrip(b'\x00').decode()
    vs, va, srd, prd = struct.unpack_from('<IIII', b, o+8)
    secs.append((name, va, vs, prd, srd))
    if name == '.text':
        text_va, text_off, text_size = va, prd, srd


def rva2off(rva):
    for name, va, vs, prd, srd in secs:
        if va <= rva < va + max(vs, srd):
            return prd + (rva - va)
    return None


# 扫描导入表，找出目标函数的 IAT 项 VA
imp_rva, _ = struct.unpack_from('<II', b, ddoff + 8)
off = rva2off(imp_rva)
iat = {}
while off:
    d = b[off:off+20]
    if len(d) < 20 or d == b'\x00'*20:
        break
    name_rva = struct.unpack_from('<I', d, 12)[0]
    if name_rva == 0:
        break
    no = rva2off(name_rva)
    lib = b[no:b.index(b'\x00', no)].decode()
    ft = struct.unpack_from('<I', d, 0)[0]      # OriginalFirstThunk 或 FirstThunk
    to = rva2off(ft)
    while to:
        v = struct.unpack_from('<I', b, to)[0]
        if v == 0:
            break
        nm = None
        if not (v & 0x80000000):
            ho = rva2off(v + 2)
            nm = b[ho:b.index(b'\x00', ho)].decode()
        # ft 在导入表里是 RVA 数组，最终 IAT 与之一一对应（此 PE 未绑定）
        iat_key = (lib, nm)
        iat[to + 4 - 4] = iat_key                # 占位，稍后用另一遍
        to += 4
    off += 20

# 重新精确收集：用 FirstThunk(16) 得到 IAT 项 RVA
off = rva2off(imp_rva)
targets = {}
idx = 0
while off:
    d = b[off:off+20]
    if len(d) < 20 or d == b'\x00'*20:
        break
    name_rva = struct.unpack_from('<I', d, 12)[0]
    if name_rva == 0:
        break
    no = rva2off(name_rva)
    lib = b[no:b.index(b'\x00', no)].decode()
    ft = struct.unpack_from('<I', d, 0)[0]
    to = rva2off(ft)
    while to:
        v = struct.unpack_from('<I', b, to)[0]
        if v == 0:
            break
        nm = None
        if not (v & 0x80000000):
            ho = rva2off(v + 2)
            nm = b[ho:b.index(b'\x00', ho)].decode()
        if nm in ('WideCharToMultiByte', 'MultiByteToWideChar', 'GetACP'):
            # IAT 布局与 hint/name 表平行，按 idx 推算
            targets.setdefault((lib, nm), []).append(idx)
        idx += 1
        to += 4
    off += 20

print('目标函数条目: %s' % targets)

# 直接按名称在 .text 中搜索调用：FF15 xx xx xx xx (call [IAT])
# 先建立 IAT 项 RVA -> 名称映射（用 idx 顺序重建）
off = rva2off(imp_rva)
entries = []          # [(lib, name)] 按导入描述符*函数顺序
while off:
    d = b[off:off+20]
    if len(d) < 20 or d == b'\x00'*20:
        break
    name_rva = struct.unpack_from('<I', d, 12)[0]
    if name_rva == 0:
        break
    no = rva2off(name_rva)
    lib = b[no:b.index(b'\x00', no)].decode()
    ft = struct.unpack_from('<I', d, 0)[0]
    to = rva2off(ft)
    while to:
        v = struct.unpack_from('<I', b, to)[0]
        if v == 0:
            break
        nm = None
        if not (v & 0x80000000):
            ho = rva2off(v + 2)
            nm = b[ho:b.index(b'\x00', ho)].decode()
        entries.append((lib, nm))
        to += 4
    off += 20

# 再走一遍描述符，得到每个描述符的 IAT RVA（FirstThunk=16）
off = rva2off(imp_rva)
iat_map = {}
k = 0
while off:
    d = b[off:off+20]
    if len(d) < 20 or d == b'\x00'*20:
        break
    name_rva = struct.unpack_from('<I', d, 12)[0]
    if name_rva == 0:
        break
    ft = struct.unpack_from('<I', d, 16)[0]
    to = rva2off(ft)
    while to:
        v = struct.unpack_from('<I', b, to)[0]
        if v == 0:
            break
        if k < len(entries):
            iat_map[ft + (to - rva2off(ft))] = entries[k]
        k += 1
        to += 4
    off += 20

print('IAT 映射条目数: %d' % len(iat_map))

# 计算目标函数的 VA
tgt_va = {}
for (lib, nm) in [('KERNEL32.dll', 'WideCharToMultiByte'),
                  ('KERNEL32.dll', 'MultiByteToWideChar'),
                  ('KERNEL32.dll', 'GetACP')]:
    for va, key in iat_map.items():
        if key == (lib, nm):
            tgt_va.setdefault(nm, []).append(va)

print()
print('目标函数 IAT VA:')
for nm, vas in tgt_va.items():
    print('  %-22s %s' % (nm, ['%08X' % v for v in vas]))

# 在 .text 中搜索 FF15 <va> 形式的间接调用
print()
print('=== 调用点（call dword ptr [IAT]） ===')
for nm, vas in tgt_va.items():
    for va in vas:
        pat = b'\xff\x15' + struct.pack('<I', imagebase + va)
        start = text_off
        end = text_off + text_size
        i = b.find(pat, start, end)
        cnt = 0
        while i != -1 and cnt < 20:
            foff = i
            rva = text_va + (foff - text_off)
            # 向前回溯最多 24 字节，找 push 指令
            pre = b[max(start, foff-24):foff]
            pushes = []
            j = len(pre)
            while j > 0:
                j -= 1
                op = pre[j]
                if op in (0x6A,):          # push imm8
                    pushes.append(('imm8', pre[j+1] if j+1 < len(pre) else None))
                elif op == 0x68:           # push imm32
                    if j+5 <= len(pre):
                        pushes.append(('imm32', struct.unpack_from('<I', pre, j+1)[0]))
            print('  %s @VA %08X (file 0x%X)  前置 push: %s' % (nm, rva, foff, pushes[:6]))
            cnt += 1
            i = b.find(pat, i+1, end)
        if cnt == 0:
            print('  %s  未找到 FF15 调用（可能是 E8 或直接 jmp）' % nm)
