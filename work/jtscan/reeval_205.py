import os, re, hashlib, struct, datetime

ROOT = r"D:\Program Files\John Tiller's Campaign Series"

def pe_timestamp(path):
    data = open(path,'rb').read()
    if data[:2] != b'MZ':
        return None
    pe_off = struct.unpack_from('<I', data, 0x3C)[0]
    if data[pe_off:pe_off+4] != b'PE\x00\x00':
        return None
    ts = struct.unpack_from('<I', data, pe_off+8)[0]
    return datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d')

def analyze(path):
    data = open(path,'rb').read()
    apis = sorted(set(m.group(1).decode('latin-1') for m in
        re.finditer(rb'(CreateFont[AW]|TextOut[AW]|DrawText[AW]|CreateFontIndirect[AW]|'
                    rb'ExtTextOut[AW]|GetTextExtent[AW])', data)))
    fonts = {}
    for n in [b'MS Sans Serif', b'Times New Roman', b'Arial', b'SimSun', b'SimHei',
              b'FangSong', b'System', b'Courier New']:
        c = data.count(n)
        if c: fonts[n.decode('latin-1')] = c
    return {
        'size': len(data),
        'md5': hashlib.md5(data).hexdigest(),
        'apis': apis,
        'fonts': fonts,
        'eastfont': data.count(b'EastFont'),
        'ts': pe_timestamp(path),
    }

engines = {}
print("===== 顶层目录 =====")
for name in sorted(os.listdir(ROOT)):
    p = os.path.join(ROOT, name)
    if os.path.isdir(p):
        print(" DIR ", name)
    else:
        print(" FILE", name, os.path.getsize(p))

print("\n===== 各游戏 exe 列表与大小 =====")
for g in ['East Front','West Front','Rising Sun']:
    gp = os.path.join(ROOT, g)
    if not os.path.isdir(gp):
        print("(missing)", g); continue
    print("-- %s --" % g)
    for fn in sorted(os.listdir(gp)):
        if fn.lower().endswith('.exe'):
            fp = os.path.join(gp, fn)
            print("   %-22s %9d  build=%s" % (fn, os.path.getsize(fp), pe_timestamp(fp)))

print("\n===== 主引擎二进制分析 =====")
# 识别每作的主引擎（按 1,085,440 旧尺寸或同名 ef/wf/rs）
candidates = {'East Front':'ef.exe','West Front':'wf.exe','Rising Sun':'rs.exe'}
for g, eng in candidates.items():
    fp = os.path.join(ROOT, g, eng)
    if os.path.exists(fp):
        a = analyze(fp)
        engines[g] = a
        print("\n[%s] %s" % (g, eng))
        print("  size=%d  md5=%s  build=%s" % (a['size'], a['md5'], a['ts']))
        print("  GDI text/font APIs:", a['apis'])
        print("  font name strings:", a['fonts'])
        print("  EastFont refs:", a['eastfont'])

print("\n===== 三作引擎是否一致 =====")
sizes = {g: e['size'] for g,e in engines.items()}
md5s  = {g: e['md5'] for g,e in engines.items()}
print("  sizes:", sizes)
print("  md5  :", md5s)
print("  全部字节相同?" , len(set(md5s.values()))==1 if md5s else "N/A")
