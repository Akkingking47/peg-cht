#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only: find which file references 'EastFont' (byte search), and classify
.map / .dat files as text vs binary. Helps pin down the bitmap-font risk."""
import os, re

def classify(path):
    with open(path,'rb') as f: data=f.read()
    if not data: return 'empty'
    nulls=data.count(0)
    if nulls/len(data)>0.05: return 'binary'
    pr=sum(1 for b in data if 32<=b<=126 or b in (9,10,13))
    return 'text' if pr/len(data)>0.85 else 'mixed'

base=r"D:\Program Files\John Tiller's Campaign Series\East Front"
print("=== files referencing 'EastFont' (bytes, case-insensitive) ===")
hits=0
for root,_,files in os.walk(base):
    for fn in files:
        p=os.path.join(root,fn)
        try:
            with open(p,'rb') as f: data=f.read()
        except: continue
        if b'EastFont' in data or b'eastfont' in data.lower():
            print("  %s  (%d bytes)" % (p, len(data)))
            hits+=1
if hits==0:
    print("  (none found)")

print("\n=== .map / .dat classification (first file each) ===")
for ext in ('map','dat'):
    fs=[f for f in os.listdir(base) if f.lower().endswith('.'+ext)]
    if fs:
        print("  .%-4s n=%-4d first=%s -> %s" % (ext, len(fs), fs[0][:26], classify(os.path.join(base,fs[0]))))

print("\n=== which files reference 'MS Sans Serif' / 'Times New Roman' ===")
for root,_,files in os.walk(base):
    for fn in files:
        if fn.lower().endswith(('.exe','.dll')):
            p=os.path.join(root,fn)
            try: data=open(p,'rb').read()
            except: continue
            if b'MS Sans Serif' in data or b'Times New Roman' in data:
                print("  %s" % p)
