import os, re, hashlib

ROOT = r"D:\Program Files\John Tiller's Campaign Series"

def read(path):
    return open(path,'rb').read()

def analyze(path):
    data = read(path)
    apis = sorted(set(m.group(1).decode('latin-1') for m in
        re.finditer(rb'(CreateFont[AW]|TextOut[AW]|DrawText[AW]|CreateFontIndirect[AW]|'
                    rb'ExtTextOut[AW]|GetTextExtent[AW])', data)))
    fonts = {}
    for n in [b'MS Sans Serif', b'Times New Roman', b'Arial', b'SimSun', b'SimHei',
              b'FangSong', b'System', b'Courier New']:
        c = data.count(n)
        if c: fonts[n.decode('latin-1')] = c
    return {'size':len(data),'apis':apis,'fonts':fonts,'eastfont':data.count(b'EastFont')}

print("="*70)
print("1) risun.exe (Rising Sun 引擎, 2025 改名) 字体机制复核")
print("="*70)
ra = analyze(os.path.join(ROOT,'Rising Sun','risun.exe'))
print("  size=%d  apis=%s" % (ra['size'], ra['apis']))
print("  fonts=%s  EastFont=%d" % (ra['fonts'], ra['eastfont']))

print("\n"+"="*70)
print("2) ef.exe 清单(manifest)扫描 —— 关键: activeCodePage / dpiAware / language")
print("="*70)
ef = read(os.path.join(ROOT,'East Front','ef.exe'))
for key in [b'<assembly', b'activeCodePage', b'UTF-8', b'utf-8', b'dpiAware',
            b'<language>', b'processorArchitecture', b'Microsoft.Windows.Common-Controls']:
    idx = ef.find(key)
    if idx >= 0:
        seg = ef[idx:idx+160]
        # 截断到下一个 '>' 之后
        end = seg.find(b'>')
        snippet = seg[:end+1] if end>=0 else seg
        print("  FOUND %-26s @0x%x : %s" % (key.decode('latin-1','replace'), idx,
              snippet.decode('utf-8','replace')))
    else:
        print("  (absent) %s" % key.decode('latin-1','replace'))

print("\n"+"="*70)
print("3) ef.exe 导入运行库 —— 判断工具链(Borland vs MSVC vs MFC)")
print("="*70)
dlls = sorted(set(m.group(1).decode('latin-1') for m in
        re.finditer(rb'([A-Za-z0-9_\\-]+\.(?:dll|DLL))', ef)))
interesting = [d for d in dlls if any(k in d.upper() for k in
    ['MSVCRT','MSVCP','VCRUNTIME','API-MS-WIN','BORLND','OWL','BC45','VCL','KERNEL32',
     'USER32','GDI32','COMCTL32','MFC','ATL'])]
for d in interesting:
    print("   ", d)
print("   ...total dll-like tokens:", len(dlls))

print("\n"+"="*70)
print("4) East Front 数据文件非ASCII(仍含 cp1252 变音?) 复核")
print("="*70)
base = os.path.join(ROOT,'East Front')
exts = ('oob','scn','org','scl','lcg','pdt','pdx','btl','tag','txt','map','dat')
total=0; withna=0; samples=[]
for fn in os.listdir(base):
    if fn.lower().endswith(exts):
        total+=1
        d=read(os.path.join(base,fn))
        if any(b>=0x80 for b in d):
            withna+=1
            if len(samples)<10:
                for j,b in enumerate(d):
                    if b>=0x80:
                        samples.append((fn, d[max(0,j-12):j+12].decode('latin-1','replace')))
                        break
print("  文本数据文件数:%d  含非ASCII:%d" % (total, withna))
for fn,seg in samples:
    print("   %-20s …%s…" % (fn, seg))
