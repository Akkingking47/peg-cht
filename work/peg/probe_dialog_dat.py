# -*- coding: utf-8 -*-
"""枚举 PeG030.exe 对话框模板的控件类型 + 解析 CWGEN.dat 目录"""
import pefile, struct, os, collections

GAME = r"D:\Program Files\PeG"

# ---------------- 1. 对话框控件 ----------------
CtrlNames = {0x80:"BUTTON",0x81:"EDIT",0x82:"STATIC",0x83:"LISTBOX",0x84:"SCROLLBAR",
             0x85:"COMBOBOX"}
pe = pefile.PE(os.path.join(GAME, "PeG030.exe"))

def iter_dialogs():
    for etype in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        tn = pefile.RESOURCE_TYPE.get(etype.struct.Id, str(etype.struct.Id))
        if tn != "RT_DIALOG":
            continue
        for e1 in etype.directory.entries:
            did = e1.struct.Id
            d = pe.get_data(e1.directory.entries[0].data.struct.OffsetToData,
                            e1.directory.entries[0].data.struct.Size)
            yield did, d

def parse_dialog(d):
    """返回 (title, font, [ (class, id, text) ])"""
    dlgVer, sig = struct.unpack_from("<HH", d, 0)
    assert dlgVer == 1 and sig == 0xFFFF, (dlgVer, sig)
    helpID, exStyle, style, cItems = struct.unpack_from("<IIII", d, 4)
    x, y, cx, cy = struct.unpack_from("<hhhh", d, 20)
    off = 28
    # menu
    menu = struct.unpack_from("<H", d, off)[0]; off += 2
    if menu == 0:
        pass
    elif menu == 0xFFFF:
        off += 2
    else:
        off += 2  # ordinal
    # windowClass
    cls = struct.unpack_from("<H", d, off)[0]; off += 2
    if cls == 0xFFFF:
        off += 2
    # title (unicode if first char is 0xFFFF flag... actually: if d[off]==0xFF and d[off+1]==0xFF -> ordinal)
    title = ""
    tlen = struct.unpack_from("<H", d, off)[0]; off += 2
    if tlen:
        if tlen == 0xFFFF:
            title = f"<ord {struct.unpack_from('<H', d, off)[0]}>"; off += 2
        else:
            title = d[off:off+tlen*2].decode("utf-16-le", "replace"); off += tlen*2
    # creation data / font
    font = None
    # point size / weight / italic / charset / face (only present if style & DS_SETFONT)
    DS_SETFONT = 0x40
    if style & DS_SETFONT:
        ptsize, = struct.unpack_from("<h", d, off); off += 2
        weight = struct.unpack_from("<H", d, off)[0]; off += 2
        italic, charset = struct.unpack_from("<BB", d, off); off += 2
        fname = d[off:off+64].decode("utf-16-le", "replace").split("\x00")[0]; off += 64
        font = (ptsize, weight, charset, fname)
    ctrls = []
    for i in range(cItems):
        # align to DWORD
        off = (off + 3) & ~3
        c_help, c_ex, c_style, c_x, c_y, c_cx, c_cy, c_id = struct.unpack_from("<IIihhhhI", d, off)
        off += 4 + 4 + 4 + 2 + 2 + 2 + 2 + 4
        c_class, c_title = "", ""
        # class: 0xFFFF -> ordinal (atom), else unicode string
        v = struct.unpack_from("<H", d, off)[0]; off += 2
        if v == 0xFFFF:
            c_class = f"ord#{struct.unpack_from('<H', d, off)[0]}"; off += 2
        else:
            # v is length
            c_class = d[off:off+v*2].decode("utf-16-le", "replace"); off += v*2
        v = struct.unpack_from("<H", d, off)[0]; off += 2
        if v == 0xFFFF:
            c_title = f"<id {struct.unpack_from('<H', d, off)[0]}>"; off += 2
        else:
            c_title = d[off:off+v*2].decode("utf-16-le", "replace"); off += v*2
        # extra count
        ec, = struct.unpack_from("<H", d, off); off += 2
        ctrls.append((c_class, c_id, c_title, c_style, ec, off - 2))
    return title, font, ctrls

print("### 对话框控件枚举")
allctrl = collections.Counter()
for did, d in iter_dialogs():
    try:
        title, font, ctrls = parse_dialog(d)
    except Exception as e:
        print(f"  dlg#{did}: parse fail {e}")
        continue
    print(f"\n  dlg#{did}  style_font={font}  title={title!r}  items={len(ctrls)}")
    for c in ctrls:
        cls, cid, txt, st, ec, eoff = c
        allctrl[cls] += 1
        print(f"      [{cls:14s}] id={cid:<6d} ec={ec:<3d} txt={txt!r}")
print("\n  控件类型合计:", dict(allctrl))

# ---------------- 2. CWGEN.dat 目录 ----------------
print("\n### CWGEN.dat 目录解析")
p = os.path.join(GAME, "CWGEN.dat")
with open(p, "rb") as f:
    head = f.read(8)
    count, dirofs = struct.unpack("<II", head)
    print(f"  count={count}  dir_end={dirofs}  (8+{count}*17={8+count*17})")
    f.seek(4)
    names = []
    for i in range(count):
        rec = f.read(17)
        nm = rec[:13].split(b"\x00")[0].decode("latin-1")
        ofs = struct.unpack("<I", rec[13:17])[0]
        names.append((nm, ofs))
print(f"  解析 {len(names)} 条; 前5:", names[:5])
# 关注 UI 图
interesting = [n for n, _ in names if n.lower() in
               ("buttn30.s16", "st030.s16", "mainbar.s16", "dialog.s16", "mouse.s16",
                "strngm.s16", "hex.s16", "gamefunc.s16", "oldescen.s16", "loadsave.s16",
                "hiscor.s16", "medals.s16", "backgrd.s16", "purchase.s16", "audio.s16",
                "airset.s16", "airslct.s16", "inspunit.s16", "deploy.s16", "vicflags.s16",
                "leaders.s16", "edplshdn.s16", "scendesc.s16", "fire.s16", "explode.s16",
                "bttn30.s16")] 
print("  关注的 UI 图存在:", interesting)
print("  含 'strng' 的:", [n for n, _ in names if "strng" in n.lower()])
print("  含 'font' 的:", [n for n, _ in names if "font" in n.lower()])
print("  含 'text' 的:", [n for n, _ in names if "text" in n.lower()])
print("  含 'menu' 的:", [n for n, _ in names if "menu" in n.lower()][:20])
