# -*- coding: utf-8 -*-
"""稳健解析 PeG030.exe 两种对话框模板 + 枚举控件（判中文输入能力）"""
import pefile, struct, os, collections

pe = pefile.PE(r"D:\Program Files\PeG\PeG030.exe")

ORD_CLASS = {0x80: "Button", 0x81: "Edit", 0x82: "Static", 0x83: "ListBox",
             0x84: "ScrollBar", 0x85: "ComboBox"}

def read_sz_utf16(d, off):
    """null-terminated UTF-16 string"""
    out = []
    while True:
        c = struct.unpack_from("<H", d, off)[0]; off += 2
        if c == 0:
            return "".join(out), off
        out.append(chr(c))

def read_sz_ord_or_str(d, off):
    """ordinal (0xFFFF + u16) 或 null-terminated UTF-16 串"""
    v = struct.unpack_from("<H", d, off)[0]
    if v == 0xFFFF:
        return f"<ord {struct.unpack_from('<H', d, off+2)[0]}>", off + 4
    return read_sz_utf16(d, off)

def parse_dialog(d, is_ex):
    if is_ex:
        # dlgVer(2) sig(2) helpID(4) exStyle(4) style(4) cItems(2) x y cx cy(8) => 26
        dlgVer, sig = struct.unpack_from("<HH", d, 0)
        helpID, exStyle, style, cItems = struct.unpack_from("<IIII", d, 4)
        x, y, cx, cy = struct.unpack_from("<hhhh", d, 18)
        off = 26
    else:
        # style(4) exStyle(4) cdit(2) x y cx cy(8) => 18
        style, exStyle, cItems = struct.unpack_from("<IIH", d, 0)
        x, y, cx, cy = struct.unpack_from("<hhhh", d, 10)
        off = 18
    menu, off = read_sz_ord_or_str(d, off)
    cls, off = read_sz_ord_or_str(d, off)
    title, off = read_sz_utf16(d, off)
    font = None
    if style & 0x40:  # DS_SETFONT
        if is_ex:
            pt, = struct.unpack_from("<h", d, off); off += 2
            wt, = struct.unpack_from("<H", d, off); off += 2
            it, cs = struct.unpack_from("<BB", d, off); off += 2
            fname, off = read_sz_utf16(d, off)
            font = (pt, wt, it, cs, fname)
        else:
            # DLGTEMPLATE: WORD pointSize; WCHAR typeface[];  (no weight/italic/charset)
            pt, = struct.unpack_from("<h", d, off); off += 2
            fname, off = read_sz_utf16(d, off)
            font = (pt, None, None, None, fname)
        # creation data (WORD)
        if off % 2 == 0:
            off += 2
    ctrls = []
    for i in range(cItems):
        off = (off + 3) & ~3
        if is_ex:
            c_help, c_ex, c_style, c_x, c_y, c_cx, c_cy, c_id = struct.unpack_from("<IIIhhhhI", d, off)
            off += 4+4+4+2+2+2+2+4
        else:
            c_style, c_ex, c_x, c_y, c_cx, c_cy, c_id = struct.unpack_from("<IIhhhhH", d, off)
            off += 4+4+2+2+2+2+2
        ccls, off = read_sz_ord_or_str(d, off)
        if ccls.startswith("<ord"):
            ccls = ORD_CLASS.get(int(ccls.split()[1].rstrip(">")), ccls)
        ctxt, off = read_sz_ord_or_str(d, off)
        if off % 2:
            off += 1
        ec, = struct.unpack_from("<H", d, off); off += 2
        off += ec
        ctrls.append((ccls, c_id, ctxt, c_style, ec))
    return title, font, ctrls, style, (x, y, cx, cy)

print("### 对话框枚举")
allctrl = collections.Counter()
edit_dialogs = []
for etype in pe.DIRECTORY_ENTRY_RESOURCE.entries:
    if pefile.RESOURCE_TYPE.get(etype.struct.Id, "") != "RT_DIALOG":
        continue
    for e1 in etype.directory.entries:
        d = pe.get_data(e1.directory.entries[0].data.struct.OffsetToData,
                        e1.directory.entries[0].data.struct.Size)
        did = e1.struct.Id
        is_ex = (len(d) >= 4 and struct.unpack_from("<HH", d, 0)[0] == 1
                 and struct.unpack_from("<H", d, 2)[0] == 0xFFFF)
        try:
            title, font, ctrls, style, rect = parse_dialog(d, is_ex)
        except Exception as e:
            print(f"  dlg#{did} [{('EX' if is_ex else '01')}] FAIL {e}")
            continue
        print(f"\n  dlg#{did} [{'EX' if is_ex else 'TEMPLATE'}] title={title!r} rect={rect} font={font}")
        for cls, cid, txt, st, ec in ctrls:
            allctrl[cls] += 1
            mark = "  <<< TEXT INPUT" if cls == "Edit" else ""
            print(f"      {cls:10s} id={cid:<6d} style={st:#010x} ec={ec} txt={txt!r}{mark}")
            if cls == "Edit":
                edit_dialogs.append((did, cid, txt, st))
print("\n  控件类型合计:", dict(allctrl))
print("  EDIT 控件所在对话框:", [(d, i, t) for d, i, t, _ in edit_dialogs])
