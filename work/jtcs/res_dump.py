# -*- coding: utf-8 -*-
"""只读资源提取：STRING 表 / MENU / DIALOG 标题与控件文本。"""
import struct, sys
from pe_probe import PE

TYPES = {1: 'CURSOR', 2: 'BITMAP', 3: 'ICON', 4: 'MENU', 5: 'DIALOG',
         6: 'STRING', 7: 'FONTDIR', 8: 'FONT', 9: 'ACCELERATOR',
         10: 'RCDATA', 11: 'MESSAGETABLE', 12: 'GROUP_CURSOR',
         14: 'GROUP_ICON', 16: 'VERSION', 24: 'MANIFEST'}


def build_tree(p):
    rva, size = p.dd[2]
    base = p.va2off(rva)
    d = p.d
    out = []

    def walk(off, path):
        nname, nid = struct.unpack_from('<HH', d, off + 12)
        for i in range(nname + nid):
            e = off + 16 + i * 8
            nameid, off2 = struct.unpack_from('<II', d, e)
            if nameid & 0x80000000:
                so = base + (nameid & 0x7FFFFFFF)
                ln = struct.unpack_from('<H', d, so)[0]
                nm = d[so + 2:so + 2 + ln * 2].decode('utf-16le', 'replace')
            else:
                nm = nameid
            if off2 & 0x80000000:
                walk(base + (off2 & 0x7FFFFFFF), path + [nm])
            else:
                de = base + off2
                drva, dsize, cp, _ = struct.unpack_from('<IIII', d, de)
                dataoff = p.va2off(drva)
                out.append((path + [nm], dataoff, dsize))
    walk(base, [])
    return out


def rd_str(d, off, end):
    s = []
    while off < end:
        ln = struct.unpack_from('<H', d, off)[0]
        off += 2
        s.append(d[off:off + ln * 2].decode('utf-16le', 'replace'))
        off += ln * 2
    return s


def dump_dialog(d, off, size):
    """极简 DLGTEMPLATE 解析（仅取 caption + 控件文本）"""
    end = off + size
    style, exstyle, ncd, x, y, cx, cy = struct.unpack_from('<IIHhhhh', d, off)
    o = off + 18
    # menu, class, title
    for label in ('menu', 'class', 'title'):
        if o + 2 > end:
            return
        v = struct.unpack_from('<H', d, o)[0]
        if v == 0:
            o += 2
        elif v == 0xFFFF:
            o += 4
        else:
            st = o
            while struct.unpack_from('<H', d, o)[0] != 0:
                o += 2
            o += 2
            if label == 'title':
                t = d[st:o].decode('utf-16le', 'replace').strip('\0')
                if t:
                    print('      [caption] %r' % t)
    if style & 0x40:  # DS_SETFONT
        pts = struct.unpack_from('<H', d, o)[0]
        o += 2
        st = o
        while struct.unpack_from('<H', d, o)[0] != 0:
            o += 2
        fam = d[st:o].decode('utf-16le', 'replace')
        o += 2
        print('      [font] %s %dpt' % (fam, pts))
        # weight, italic, charset
        if o + 4 <= end:
            wt, it, cs = struct.unpack_from('<HBB', d, o)
            o += 4
            print('      [fontattr] weight=%d italic=%d charset=%d' % (wt, it, cs))
    o = (o + 3) & ~3
    # controls
    while o + 8 <= end:
        cstyle, cex, cx0, cy0, ccx, ccy, cid = struct.unpack_from('<IIhhhhH', d, o)
        o += 18
        if cstyle == 0 and cid == 0:
            break
        clsname = ''
        o0 = o
        v = struct.unpack_from('<H', d, o)[0]
        if v == 0xFFFF:
            clsname = '#%d' % struct.unpack_from('<H', d, o + 2)[0]
            o += 4
        else:
            st = o
            while o + 2 <= end and struct.unpack_from('<H', d, o)[0] != 0:
                o += 2
            o += 2
            clsname = d[st:o].decode('utf-16le', 'replace').strip('\0')
        # title
        st = o
        v = struct.unpack_from('<H', d, o)[0]
        if v == 0xFFFF:
            o += 4
            txt = ''
        else:
            while o + 2 <= end and struct.unpack_from('<H', d, o)[0] != 0:
                o += 2
            o += 2
            txt = d[st:o].decode('utf-16le', 'replace').strip('\0')
        # extra count
        if o + 2 <= end:
            extra = struct.unpack_from('<H', d, o)[0]
            o += 2 + extra
        o = (o + 3) & ~3
        if txt:
            print('      [%-10s id=%-5d] %r' % (clsname or '?', cid, txt))


def main(path, want):
    p = PE(path)
    d = p.d
    tree = build_tree(p)
    print('资源条目总数:', tree.__len__())
    for path_, off, size in tree:
        t = TYPES.get(path_[0], str(path_[0]))
        if want and t not in want:
            continue
        if t == 'STRING':
            ss = rd_str(d, off, off + size)
            print('--- STRING block id=%s (%d 条) ---' % (path_[1], len(ss)))
            for i, s in enumerate(ss):
                if s:
                    print('   %4d: %r' % ((path_[1] - 1) * 16 + i, s))
        elif t == 'MENU':
            print('--- MENU id=%s size=%d ---' % (path_[1], size))
            o = off + 4
            end = off + size
            lvl = 0
            while o + 2 <= end:
                flags = struct.unpack_from('<H', d, o)[0]
                if flags & 0x10:
                    # wFlags + wID + 标题
                    o += 4
                    st = o
                    while o + 2 <= end and struct.unpack_from('<H', d, o)[0] != 0:
                        o += 2
                    o += 2
                    txt = d[st:o].decode('utf-16le', 'replace').strip('\0')
                    print('   ' + '  ' * lvl + '[' + txt + ']')
                    lvl += 1
                    continue
                if flags == 0:
                    o += 2
                    if lvl > 0:
                        lvl -= 1
                    continue
                o += 4  # skip wFlags + wID
                st = o
                while o + 2 <= end and struct.unpack_from('<H', d, o)[0] != 0:
                    o += 2
                txt = d[st:o].decode('utf-16le', 'replace').strip('\0')
                o += 2
                print('   ' + '  ' * lvl + repr(txt))
        elif t == 'DIALOG':
            print('--- DIALOG id=%s size=%d ---' % (path_[1], size))
            dump_dialog(d, off, size)


if __name__ == '__main__':
    p = sys.argv[1]
    want = set(sys.argv[2:]) or None
    main(p, want)
