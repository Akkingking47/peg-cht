# -*- coding: utf-8 -*-
"""只读 PE 探测：机器类型/子系统/节表/导入表(GDI 相关)/资源目录概况。
不修改任何被探测文件。"""
import struct, sys, os

GDI_API = ('TextOut', 'ExtTextOut', 'DrawText', 'CreateFont', 'CreateFontIndirect',
           'GetCharWidth', 'GetTextExtent', 'AddFontResource', 'SetTextColor',
           'SetBkMode', 'DrawTextEx', 'GetTextMetrics', 'SelectObject',
           'SetTextCharacterExtra', 'GetGlyphOutline', 'EnumFontFamilies')
KERNEL_API = ('MultiByteToWideChar', 'WideCharToMultiByte', 'GetACP', 'GetOEMCP',
              'GetCPInfo', 'SetThreadLocale', 'CompareString', 'LCMapString',
              'GetUserDefaultLCID', 'GetSystemDefaultLCID', 'CharUpper', 'CharLower',
              'IsDBCSLeadByte', 'GetStringTypeA', 'GetStringTypeW')


class PE:
    def __init__(self, path):
        self.path = path
        self.d = open(path, 'rb').read()
        d = self.d
        if d[:2] != b'MZ':
            raise ValueError('not MZ')
        e_lfanew = struct.unpack_from('<I', d, 0x3C)[0]
        assert d[e_lfanew:e_lfanew + 4] == b'PE\0\0', 'not PE'
        self.nt = e_lfanew
        coff = e_lfanew + 4
        (self.machine, self.nsec, self.tstamp, self.symptr, self.nsym,
         self.optsize, self.characteristics) = struct.unpack_from('<HHIIIHH', d, coff)
        opt = coff + 20
        self.magic = struct.unpack_from('<H', d, opt)[0]
        self.pe32plus = (self.magic == 0x20b)
        self.subsystem = struct.unpack_from('<H', d, opt + 68)[0]
        self.imagebase = struct.unpack_from('<I', d, opt + 28)[0]
        self.sections = []
        secoff = opt + self.optsize
        for i in range(self.nsec):
            o = secoff + i * 40
            name = d[o:o + 8].rstrip(b'\0').decode('latin1')
            vsize, va, rsize, roff = struct.unpack_from('<IIII', d, o + 8)
            chars = struct.unpack_from('<I', d, o + 36)[0]
            self.sections.append(dict(name=name, va=va, vsize=vsize, roff=roff,
                                      rsize=rsize, chars=chars))
        # data dirs
        dd = opt + (108 if self.pe32plus else 96)
        self.dd = [struct.unpack_from('<II', d, dd + i * 8) for i in range(16)]

    def off2va(self, off):
        for s in self.sections:
            if s['roff'] <= off < s['roff'] + s['rsize']:
                return s['va'] + (off - s['roff'])
        return None

    def va2off(self, va):
        for s in self.sections:
            if s['va'] <= va < s['va'] + max(s['vsize'], s['rsize']):
                return s['roff'] + (va - s['va'])
        return None

    def sec_of(self, va):
        for s in self.sections:
            if s['va'] <= va < s['va'] + max(s['vsize'], s['rsize']):
                return s['name'], s['chars']
        return '?', 0

    def imports(self):
        """返回 [(dllname, [funcnames])]"""
        rva, size = self.dd[1]
        if not rva:
            return []
        base = self.va2off(rva)
        out = []
        i = 0
        while True:
            desc = base + i * 20
            if desc + 20 > len(self.d):
                break
            oft, ts, fwd, nameRva, ft = struct.unpack_from('<IIIII', self.d, desc)
            if nameRva == 0:
                break
            noff = self.va2off(nameRva)
            dll = self.d[noff:self.d.index(b'\0', noff)].decode('latin1')
            thunk = self.va2off(oft or ft)
            funcs = []
            j = 0
            while True:
                if self.pe32plus:
                    v = struct.unpack_from('<Q', self.d, thunk + j * 8)[0]
                    j += 1
                    if v == 0:
                        break
                    if v & (1 << 63):
                        funcs.append('#ord%d' % (v & 0xFFFF))
                        continue
                    fo = self.va2off(v & 0x7FFFFFFF)
                else:
                    v = struct.unpack_from('<I', self.d, thunk + j * 4)[0]
                    j += 1
                    if v == 0:
                        break
                    if v & 0x80000000:
                        funcs.append('#ord%d' % (v & 0xFFFF))
                        continue
                    fo = self.va2off(v + 2)
                funcs.append(self.d[fo:self.d.index(b'\0', fo)].decode('latin1'))
            out.append((dll, funcs))
            i += 1
        return out

    def resources(self):
        """返回 {type_name: count}"""
        rva, size = self.dd[2]
        if not rva:
            return {}
        base = self.va2off(rva)
        d = self.d
        TYPES = {1: 'CURSOR', 2: 'BITMAP', 3: 'ICON', 4: 'MENU', 5: 'DIALOG',
                 6: 'STRING', 7: 'FONTDIR', 8: 'FONT', 9: 'ACCELERATOR',
                 10: 'RCDATA', 11: 'MESSAGETABLE', 12: 'GROUP_CURSOR',
                 14: 'GROUP_ICON', 16: 'VERSION', 24: 'MANIFEST'}

        def walk(off, level, prefix):
            res = {}
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
                if level == 0:
                    label = TYPES.get(nm, str(nm))
                    sub = walk(base + (off2 & 0x7FFFFFFF), 1, label)
                    res[label] = sub
                elif level == 1:
                    sub = walk(base + (off2 & 0x7FFFFFFF), 2, prefix)
                    res[nm] = sub
                else:
                    res[nm] = off2
            return res
        try:
            return walk(base, 0, '')
        except Exception as e:
            return {'_err': str(e)}


def flat(tree, prefix=''):
    n = 0
    if isinstance(tree, dict):
        for k, v in tree.items():
            n += flat(v, prefix)
    else:
        n = 1
    return n


def main(path):
    p = PE(path)
    print('=' * 78)
    print('FILE :', path, ' size=%d' % len(p.d))
    print('MACHINE: %04X  magic=%04X(%s)  subsystem=%d  imagebase=%08X' % (
        p.machine, p.magic, 'PE32+' if p.pe32plus else 'PE32', p.subsystem, p.imagebase))
    print('timestamp=%08X (%s)' % (p.tstamp, __import__('time').strftime(
        '%Y-%m-%d', __import__('time').gmtime(p.tstamp))))
    print('sections:')
    for s in p.sections:
        print('   %-9s va=%08X vsz=%08X raw=%08X roff=%08X ch=%08X %s' % (
            s['name'], s['va'], s['vsize'], s['rsize'], s['roff'], s['chars'],
            'X' if s['chars'] & 0x20000000 else '-'))
    imps = p.imports()
    print('imports (%d dll):' % len(imps))
    hit = []
    kern = []
    for dll, fs in imps:
        print('   %-16s %d funcs' % (dll, len(fs)))
        for f in fs:
            if any(f.startswith(a) for a in GDI_API):
                hit.append((dll, f))
            if any(f.startswith(a) for a in KERNEL_API):
                kern.append((dll, f))
    print('  --- 文本渲染相关 ---')
    for dll, f in hit:
        print('     %s!%s' % (dll, f))
    print('  --- 代码页/字符集相关 ---')
    for dll, f in kern:
        print('     %s!%s' % (dll, f))
    r = p.resources()
    print('resources (%d 顶层类型):' % len(r))
    for k, v in r.items():
        print('   %-14s 条目=%d' % (k, flat(v)))
    return p, imps


if __name__ == '__main__':
    for a in sys.argv[1:]:
        main(a)
