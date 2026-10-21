# -*- coding: utf-8 -*-
"""向上追溯调用链，找出传给字体创建函数的字面量参数。
用法: trace_font.py <exe> <起始地址(十六进制)> <层数>"""
import struct, sys
from capstone import *
from pe_probe import PE


def load(path):
    p = PE(path)
    s = [x for x in p.sections if x['name'] == '.text'][0]
    base = p.imagebase + s['va']
    code = p.d[s['roff']:s['roff'] + s['rsize']]
    return p, base, code


def find_func_start(p, base, code, addr, limit=0x400):
    """向前找 prologue：55 8B EC"""
    off = addr - base
    for k in range(off, max(0, off - limit), -1):
        if code[k] == 0x55 and code[k + 1] == 0x8B and code[k + 2] == 0xEC:
            return base + k
    return None


def callers(base, code, tgt):
    out = []
    for i in range(len(code) - 5):
        if code[i] == 0xE8:
            rel = struct.unpack_from('<i', code, i + 1)[0]
            a = base + i
            if a + 5 + rel == tgt:
                out.append(a)
    return out


def dump(p, base, addr, before=0x70, after=0x8):
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    st = addr - before
    off = p.va2off(st - p.imagebase)
    for i in md.disasm(p.d[off:off + before + after], st):
        mark = ' <<<' if i.address == addr else ''
        print('  %08X %-10s %s %s%s' % (i.address, ''.join('%02X' % b for b in i.bytes),
                                        i.mnemonic, i.op_str, mark))


if __name__ == '__main__':
    path, start, depth = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3])
    p, base, code = load(path)
    level = [start]
    for d in range(depth):
        nxt = []
        print('##### 第 %d 层，共 %d 个函数' % (d + 1, len(level)))
        for fn in level[:6]:
            fstart = find_func_start(p, base, code, fn)
            cs = callers(base, code, fstart) if fstart else []
            print('  函数 %s (起始 %s) 被 %d 处调用' % (hex(fn), hex(fstart) if fstart else '?', len(cs)))
            for c in cs[:4]:
                print('   --- 调用点 %s 上下文 ---' % hex(c))
                dump(p, base, c)
                nxt.append(c)
        level = list(dict.fromkeys(nxt))
        if not level:
            break
