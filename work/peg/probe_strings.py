# -*- coding: utf-8 -*-
"""PeG 汉化可行性 - 字符串 / 字体 / 资源 侦查"""
import pefile, os, re, sys, struct, collections

GAME = r"D:\Program Files\PeG"
pe = pefile.PE(os.path.join(GAME, "PeG030.exe"))

# ---------- 1. 资源目录 ----------
print("### 资源目录 (PeG030.exe)")
counts = collections.Counter()
dialogs = []
if hasattr(pe, "DIRECTORY_ENTRY_RESOURCE"):
    for etype in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        tn = pefile.RESOURCE_TYPE.get(etype.struct.Id, str(etype.struct.Id)) if etype.struct.Id else (etype.name.string.decode() if etype.name else "?")
        n = 0
        sub = []
        for e1 in getattr(etype, "directory", pefile.ResourceDirEntryData(None, None, None)).entries if False else etype.directory.entries:
            n += 1
            idv = e1.struct.Id if e1.struct.Id else (e1.name.string.decode() if e1.name else "?")
            sub.append(idv)
            if tn == "RT_DIALOG":
                d = pe.get_data(e1.directory.entries[0].data.struct.OffsetToData,
                                e1.directory.entries[0].data.struct.Size)
                dialogs.append((idv, d))
        counts[tn] = n
        print(f"  {tn:16s} : {n}   {sub[:20]}")
print()

# ---------- 2. 对话框字体 ----------
print("### 对话框模板中的字体声明")
for did, d in dialogs:
    try:
        # DIALOGEX: dlgVer(2) sig(2) helpID(4) exStyle(4) style(4) cDlgItems(2) x,y,cx,cy(8)
        dlgVer, sig = struct.unpack_from("<HH", d, 0)
        off = 8 + 4 + 4 + 2 + 8
        if dlgVer == 1 and sig == 0xFFFF:
            off += 2  # menu
            off += 2  # class
            tlen, = struct.unpack_from("<H", d, off); off += 2
            title = d[off:off+tlen]; off += tlen * (2 if (title[:1] == b"\x00" and tlen > 2) else 1)
            # extra fill
            if tlen and title[:1] not in (b"\x00",):
                pass
            # point size(2) + weight(2) + italic(1)+charset(1) + face name (utf16 null-term)
            ptsize, weight = struct.unpack_from("<HH", d, off); off += 4
            italic, charset = struct.unpack_from("<BB", d, off); off += 2
            fname = d[off:off+64].decode("utf-16-le", "replace").split("\x00")[0]
            print(f"  dialog#{did}: ver={dlgVer} pt={ptsize} w={weight} charset={charset} face='{fname}'")
    except Exception as e:
        pass

# ---------- 3. 字符串表 ----------
print("\n### STRINGTABLE 资源")
if hasattr(pe, "DIRECTORY_ENTRY_RESOURCE"):
    for etype in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        tn = pefile.RESOURCE_TYPE.get(etype.struct.Id, str(etype.struct.Id))
        if tn == "RT_STRING":
            for e1 in etype.directory.entries:
                for e2 in e1.directory.entries:
                    data = pe.get_data(e2.data.struct.OffsetToData, e2.data.struct.Size)
                    base = (e1.struct.Id - 1) * 16
                    off = 0
                    for i in range(16):
                        ln, = struct.unpack_from("<H", data, off); off += 2
                        s = data[off:off+ln*2].decode("utf-16-le", "replace"); off += ln*2
                        if s.strip():
                            print(f"  [{base+i}] {s!r}")

# ---------- 4. ASCII 字符串扫描（重点：字体名 / 语言 / 编码） ----------
print("\n### 关键 ASCII 字符串扫描")
data = pe.__data__
pat = re.compile(rb"[\x20-\x7e]{5,}")
seen = collections.Counter()
KEY = ["arial", "courier", "times", "serif", "sans", "system", "fixedsys", "terminal",
       "ms sans", "helv", "tahoma", "verdana", "gothic", "mingliu", "simsun", "batang",
       "gulim", "msgothic", "font", ".ttf", ".fnt", ".fon", "charset", "codepage",
       "lang", "english", "german", "french", "spanish", "russian", "unicode",
       "ansi", "oem", "latin", "gb2312", "shift", "jis", "big5"]
hits = collections.defaultdict(set)
for m in pat.finditer(data):
    s = m.group()
    if len(s) > 120:
        continue
    low = s.lower()
    for k in KEY:
        if k.encode() in low:
            hits[k].add(s.decode("latin-1"))
            break
for k in KEY:
    if hits[k]:
        vals = sorted(hits[k])[:25]
        print(f"  [{k}] ({len(hits[k])}) {vals}")
