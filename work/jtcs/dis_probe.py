# -*- coding: utf-8 -*-
"""只读反汇编探测：定位 IAT 调用点，回溯 push 立即数，用于还原
CreateFontA 的 charset / 字体名等参数。"""
import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from pe_probe import PE

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False


def iat_map(p):
    """{va_of_iat_slot: (dll, func)}"""
    rva, size = p.dd[1]
    base = p.va2off(rva)
    m = {}
    i = 0
    while True:
        desc = base + i * 20
        oft, ts, fwd, nameRva, ft = struct.unpack_from('<IIIII', p.d, desc)
        if nameRva == 0:
            break
        noff = p.va2off(nameRva)
        dll = p.d[noff:p.d.index(b'\0', noff)].decode('latin1')
        thunk = p.va2off(oft or ft)
        j = 0
        while True:
            v = struct.unpack_from('<I', p.d, thunk + j * 4)[0]
            if v == 0:
                break
            if v & 0x80000000:
                nm = '#%d' % (v & 0xFFFF)
            else:
                fo = p.va2off(v + 2)
                nm = p.d[fo:p.d.index(b'\0', fo)].decode('latin1')
            m[p.imagebase + (ft + j * 4)] = (dll, nm)
            j += 1
        i += 1
    return m


def text_sec(p):
    for s in p.sections:
        if s['name'] == '.text':
            return s['roff'], s['rsize'], p.imagebase + s['va']
    return None


def cstr(p, va):
    o = p.va2off(va - p.imagebase) if va >= p.imagebase else p.va2off(va)
    if o is None:
        return None
    e = p.d.index(b'\0', o)
    return p.d[o:e]


def main(path, targets):
    p = PE(path)
    iat = iat_map(p)
    byname = {}
    for va, (dll, nm) in iat.items():
        byname.setdefault(nm, []).append(va)
    roff, rsize, base_va = text_sec(p)
    code = p.d[roff:roff + rsize]

    for t in targets:
        slots = byname.get(t, [])
        if not slots:
            print('!! %s 不在导入表中' % t)
            continue
        pats = [(s, b'\xff\x15' + struct.pack('<I', s)) for s in slots]
        sites = []
        for s, pat in pats:
            start = 0
            while True:
                k = code.find(pat, start)
                if k < 0:
                    break
                sites.append((k, s))
                start = k + 1
        print('=== %s : %d 处调用 ===' % (t, len(sites)))
        for k, s in sites[:24]:
            # 回溯 72 字节，取最后 13 条 push 立即数
            st = max(0, k - 72)
            ins = list(md.disasm(code[st:k], base_va + st))
            pushes = []
            for i in ins:
                if i.mnemonic == 'push':
                    pushes.append(i.op_str)
            print('   @%08X  push链=%s' % (base_va + k, pushes[-13:]))
            # 尝试解析字符串参数
            for pr in pushes[-13:]:
                if pr.startswith('0x'):
                    v = int(pr, 16)
                    cs = cstr(p, v)
                    if cs and 2 < len(cs) < 40 and all(32 <= c < 127 for c in cs):
                        print('        字符串参数 -> %r' % cs.decode('latin1'))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
