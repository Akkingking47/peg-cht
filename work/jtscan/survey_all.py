#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only cross-game survey: for each Campaign Series title, identify the
engine exe, scan for font / EastFont / language keywords, inspect EastFont.BMP,
classify data-file types (text vs binary), and summarize file counts."""
import os, re, struct

GAMES = {
    'East Front': r"D:\Program Files\John Tiller's Campaign Series\East Front",
    'West Front': r"D:\Program Files\John Tiller's Campaign Series\West Front",
    'Rising Sun (Pacific War)': r"D:\Program Files\John Tiller's Campaign Series\Rising Sun",
}
ENG = {'East Front':'ef.exe','West Front':'wf.exe','Rising Sun (Pacific War)':'rs.exe'}

def strings(data, pat):
    out=[]
    for m in re.finditer(pat, data):
        try:
            s=m.group().decode('utf-16-le' if pat.pattern.endswith(')\\x00){3,}') else 'latin-1')
        except: continue
        out.append(s)
    return out

def scan_exe(path):
    with open(path,'rb') as f: data=f.read()
    toks=[]
    a=strings(data, rb'[\x20-\x7e]{4,}')
    u=strings(data, rb'(?:[\x20-\x7e]\x00){3,}')
    for s in a+u:
        low=s.lower()
        if any(k in low for k in ('eastfont','small font','createfont','mssans','times new roman',
                                   'simsun','simhei','charset','.lng','language','langdlg','.lan')):
            toks.append(s)
    return dict(size=len(data), toks=list(dict.fromkeys(toks)))

def bmp(path):
    try:
        with open(path,'rb') as f: d=f.read(54)
        if d[:2]!=b'BM': return None
        w,h=struct.unpack('<ii', d[18:26]); bpp=struct.unpack('<H',d[28:30])[0]
        return (w,h,bpp)
    except Exception as e: return ('err',str(e))

def classify(path):
    with open(path,'rb') as f: data=f.read()
    if not data: return 'empty'
    printable=sum(1 for b in data if 32<=b<=126 or b in (9,10,13))
    nulls=data.count(0)
    if nulls/len(data)>0.05: return 'binary'
    return 'text' if printable/len(data)>0.85 else 'mixed'

def ext_counts(d):
    c={}
    for f in os.listdir(d):
        if os.path.isfile(os.path.join(d,f)):
            e=f.rsplit('.',1)[-1].lower() if '.' in f else '(noext)'
            c[e]=c.get(e,0)+1
    return c

for name, d in GAMES.items():
    print("\n########################################################################")
    print("GAME:", name, "->", d)
    eng=ENG[name]
    ep=os.path.join(d,eng)
    if os.path.exists(ep):
        r=scan_exe(ep)
        print("  engine: %s  size=%d" % (eng, r['size']))
        for t in r['toks'][:30]:
            print("    tok: %s" % t[:110])
    else:
        print("  engine %s NOT FOUND" % eng)
    ef=os.path.join(d,'EastFont.BMP')
    if os.path.exists(ef):
        print("  EastFont.BMP header:", bmp(ef))
    # classify key data extensions
    print("  data-file classification (first file of each ext):")
    for ext in ('oob','scn','org','scl','lcg','pdt','pdx','btl','tag','special','hlp','txt','ini','inf'):
        files=[f for f in os.listdir(d) if f.lower().endswith('.'+ext)]
        if files:
            cls=classify(os.path.join(d,files[0]))
            print("    .%-8s n=%-4d first=%s -> %s" % (ext, len(files), files[0][:24], cls))
    # top extensions
    c=ext_counts(d)
    top=sorted(c.items(), key=lambda x:-x[1])[:12]
    print("  top extensions:", ', '.join('%s=%d'%(k,v) for k,v in top))
