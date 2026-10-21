#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only: scan several Campaign Series exes for font / EastFont / bitmap
references (ASCII + UTF-16LE). Helps decide whether EastFont.BMP is actually
consumed and which font the map/editor uses."""
import os, re, sys

def scan(path):
    with open(path,'rb') as f: data=f.read()
    res={}
    for enc,pat in (('ascii', rb'[\x20-\x7e]{4,}'), ('utf16', rb'(?:[\x20-\x7e]\x00){3,}')):
        hits=[]
        for m in re.finditer(pat, data):
            try: s=m.group().decode('utf-16-le' if enc=='utf16' else 'latin-1')
            except: continue
            low=s.lower()
            if 'eastfont' in low or 'small font' in low or '.bmp' in low or \
               'createfont' in low or 'mssans' in low or 'times new roman' in low or \
               'simsun' in low or 'simhei' in low or 'charset' in low or 'font' in low:
                hits.append(s)
        res[enc]=hits
    return res

def main():
    base=r"D:\Program Files\John Tiller's Campaign Series\East Front"
    for exe in ('efmap.exe','efedit.exe','eforg.exe','East Front.exe','ef.exe'):
        p=os.path.join(base,exe)
        if not os.path.exists(p): continue
        print("\n===== %s =====" % exe)
        r=scan(p)
        seen=set()
        for enc in ('ascii','utf16'):
            for s in r[enc]:
                if s in seen: continue
                seen.add(s)
                print("  [%s] %s" % (enc, s[:120]))

if __name__=='__main__':
    main()
