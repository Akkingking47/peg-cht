#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only deep survey of a Campaign Series game folder (run with cwd = the
game dir, pass '.' as the arg). Extracts all ASCII + UTF-16LE strings from the
main engine exe, searches localization keywords, and inspects BMP headers of
graphics that may contain baked-in text or a bitmap font."""
import sys, os, struct, re

def ascii_strings(data, minlen=4):
    out = []
    for m in re.finditer(rb'[\x20-\x7e]{%d,}' % minlen, data):
        out.append((m.start(), m.group().decode('latin-1')))
    return out

def utf16_strings(data, minlen=3):
    out = []
    for m in re.finditer(rb'(?:[\x20-\x7e]\x00){%d,}' % minlen, data):
        try:
            out.append((m.start(), m.group().decode('utf-16-le')))
        except Exception:
            pass
    return out

def bmp_header(path):
    try:
        with open(path, 'rb') as f:
            d = f.read(54)
        if len(d) < 54 or d[0:2] != b'BM':
            return None
        w, h = struct.unpack('<ii', d[18:26])
        bpp = struct.unpack('<H', d[28:30])[0]
        comp = struct.unpack('<I', d[30:34])[0]
        return dict(w=w, h=h, bpp=bpp, comp=comp, size=os.path.getsize(path))
    except Exception as e:
        return dict(err=str(e))

def main():
    d = sys.argv[1] if len(sys.argv) > 1 else '.'
    OUT = r"D:\DSH\军事游戏汉化\work\jtscan"
    os.makedirs(OUT, exist_ok=True)
    print("DIR:", os.path.abspath(d))
    # find engine exe (largest .exe that isn't a tool)
    exes = [f for f in os.listdir(d) if f.lower().endswith('.exe')]
    # prefer the main game engine: ef.exe / wf.exe / rs.exe or *Front*.exe
    eng = None
    for cand in ('ef.exe','wf.exe','rs.exe','East Front.exe','west front.exe','rising sun.exe'):
        if cand in exes:
            eng = cand; break
    if not eng:
        eng = exes[0]
    print("ENGINE EXE:", eng)
    with open(os.path.join(d, eng), 'rb') as f:
        data = f.read()

    a = ascii_strings(data, 4)
    u = utf16_strings(data, 3)
    # save full lists
    with open(os.path.join(OUT, eng + '.ascii.txt'), 'w', encoding='utf-8') as fo:
        for off, s in a:
            fo.write('%08x\t%s\n' % (off, s))
    with open(os.path.join(OUT, eng + '.utf16.txt'), 'w', encoding='utf-8') as fo:
        for off, s in u:
            fo.write('%08x\t%s\n' % (off, s))
    print("ASCII strings: %d  | UTF-16LE strings: %d" % (len(a), len(u)))

    kws = ['EastFont','Small Font','Font','MS Sans','Times New Roman','Arial',
           'Language','LangDlg','charset','CharSet','DEFAULT_CHARSET','ANSI_CHARSET',
           'GB2312','936','1252','1250','Bitmap','LoadBitmap','CreateFont',
           'TextOut','DrawText','GetTextExtent','Menu','Dialog','Scenario',
           'Victory','Defeat','Turn','Help','Exit','Preferences','Options',
           'Campaign','Unit','Hex','Map','Picture','Pictures']
    print("\n=== keyword hits (ASCII) ===")
    for kw in kws:
        hits = [s for (off,s) in a if kw.lower() in s.lower()]
        if hits:
            uniq = list(dict.fromkeys(hits))[:6]
            print("  %-16s x%d: %s" % (kw, len(hits), uniq))
    print("\n=== keyword hits (UTF-16LE) ===")
    for kw in kws:
        hits = [s for (off,s) in u if kw.lower() in s.lower()]
        if hits:
            uniq = list(dict.fromkeys(hits))[:6]
            print("  %-16s x%d: %s" % (kw, len(hits), uniq))

    # BMP inspection
    print("\n=== BMP header inspection ===")
    for name in ('EastFont.BMP','Controls2.BMP','Menu Screen.BMP','Charport.BMP',
                 'Command Reports.BMP','Results.BMP','Tutorial.bmp','Victory0.BMP'):
        p = os.path.join(d, name)
        if os.path.exists(p):
            h = bmp_header(p)
            print("  %-22s %s" % (name, h))
        else:
            print("  %-22s (not present)" % name)

    # look for a Pictures subfolder
    pics = os.path.join(d, 'Pictures')
    if os.path.isdir(pics):
        n = len(os.listdir(pics))
        print("\nPictures/ subfolder exists: %d files" % n)
    else:
        print("\nPictures/ subfolder: NOT present at top of game dir")

if __name__ == '__main__':
    main()
