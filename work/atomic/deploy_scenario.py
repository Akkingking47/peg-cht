# -*- coding: utf-8 -*-
"""ATOMIC 场景散文部署（v2）：以原文行骨架为准，逐行决定输出编码。

规则（逐行）：
  - 原文该行是「装饰行」（去 \r 后仅由 0xAF 组成）→ 原样透传原文字节
  - 其余行 → 用译文（UTF-8）转 GBK
  - 换行符完全跟随原文（\r\n / 无）
"""
import os, re, collections

WORK = r"D:/DSH/军事游戏汉化/work/atomic"
SCN = os.path.join(WORK, "scn")
SRC = r"D:/OpenPG2/EFILE_ATOMIC/SCENARIO"
DST = r"D:/OpenPG2/EFILE_ATOMIC/TEXT-ZH/SCENARIO"

def split_files(raw):
    parts, idx = [], 0
    while True:
        j = raw.find(b'@@FILE\t', idx)
        if j < 0: break
        k = raw.find(b'\n', j)
        head = raw[j:k].rstrip(b'\r')
        nxt = raw.find(b'@@FILE\t', k)
        body = raw[k+1:] if nxt < 0 else raw[k+1:nxt]
        parts.append((head, body))
        if nxt < 0: break
        idx = nxt
    return parts

def decode_lines(bs, enc):
    """[bytes] -> [(text_str_or_None, has_cr, raw_bytes_or_None)]"""
    parts = bs.split(b'\n')
    if parts and parts[-1] == b'': parts = parts[:-1]
    out = []
    for p in parts:
        cr = p.endswith(b'\r')
        core = p[:-1] if cr else p
        if core and set(core) <= {0xAF}:
            out.append((None, cr, core))      # 装饰行：原样字节（裸 0xAF）
        elif core.decode('cp1252', errors='replace') and set(core.decode('cp1252', errors='replace')) <= {'Â', '¯'} and '¯' in core.decode('cp1252', errors='replace'):
            out.append((None, cr, core))      # 装饰行：cp1252 双字节 Â¯ 形态，同样原样透传
        else:
            out.append((core.decode(enc, errors='replace'), cr, None))
    return out

# 1. 读回译文 rep -> 文本行
zh = {}
for i in range(1, 13):
    raw = open(os.path.join(SCN, f"out-{i:02d}.txt"), 'rb').read()
    for head, body in split_files(raw):
        name = head.split(b'\t')[1].decode('utf-8')
        # 导出时每个文件内容后跟一个分隔 \n；原内容若自身以 \r\n 结尾则为 ...\r\n + \n
        if body.endswith(b'\n'):
            if body.endswith(b'\r\n'):
                body = body[:-1]          # 去掉分隔 \n，保留内容自身的 \r\n
            else:
                body = body[:-1]          # 去掉分隔 \n
        zh[name] = body
print("读回 rep:", len(zh))

# 2. reps 表
reps = {}
for ln in open(os.path.join(WORK, "atomic-scenario-reps.tsv"), encoding='utf-8').read().splitlines()[1:]:
    if not ln.strip(): continue
    c = ln.split('\t')
    reps[c[0]] = c[3].split(',')

def fold(s):
    """非 GBK 变音字符折写（仅输出侧；不改键）。"""
    # 先做双字符序列折写（UTF-8 双重编码残留）
    seq = {
        'Ã©':'e','Ã¨':'e','Ã¡':'a','Ã¤':'a','Ã¶':'o','Ã¼':'u','ÃŸ':'ss',
        'Ã¢':'a','Ã®':'i','Ã´':'o','Ã»':'u','Ã§':'c','Ã±':'n','Ã©':'e',
        'Â¯':'',   # 双编码装饰符残留（安全网）
        '\u00e2\u0080\u0089':' ', '\u00e2\u0080\u0099':"'", '\u00e2\u0080\u009c':'"', '\u00e2\u0080\u009d':'"',
    }
    for k, v in seq.items():
        s = s.replace(k, v)
    rep = {
        'ä':'a','á':'a','à':'a','â':'a','ã':'a','å':'a',
        'ö':'o','ó':'o','ò':'o','ô':'o','õ':'o','ø':'o',
        'ü':'u','ú':'u','ù':'u','û':'u',
        'ß':'ss',
        'é':'e','è':'e','ê':'e','ë':'e',
        'í':'i','ì':'i','î':'i','ï':'i',
        'ç':'c','ñ':'n','ý':'y',
        'Ä':'A','Ö':'O','Ü':'U','É':'E','Å':'A','Ø':'O','Ñ':'N',
        'Ã':'','Â':'','\u00c2':'','\u00c3':'','\u00a9':'(c)',
        'â€‰':' ','â€ž':'','â€œ':'"','â€':'"',
        '\u00a0':' ',
    }
    return ''.join(rep.get(ch, ch) for ch in s)

# 3. 部署
os.makedirs(DST, exist_ok=True)
problems = []
written = 0
for rep, names in reps.items():
    if rep not in zh:
        problems.append(f"{rep}: 无译文"); continue
    orig = open(os.path.join(SRC, rep), 'rb').read()
    olines = decode_lines(orig, 'cp1252')
    tlines = decode_lines(zh[rep], 'utf-8')
    if len(olines) != len(tlines):
        problems.append(f"{rep}: 行数 {len(olines)} != {len(tlines)}"); continue
    out = bytearray()
    ok = True
    for (otext, ocr, obytes), (ttext, tcr, tbytes) in zip(olines, tlines):
        if obytes is not None:
            piece = obytes       # 装饰行：原样
        else:
            try:
                piece = ttext.encode('gbk')
            except UnicodeEncodeError:
                try:
                    piece = fold(ttext).encode('gbk')
                except UnicodeEncodeError as e:
                    problems.append(f"{rep}: GBK丢字 {ttext[max(0,e.start-3):e.start+3]!r}")
                    ok = False; break
        out += piece + (b'\r' if ocr else b'')
        out += b'\n'
    if not ok: continue
    if not orig.endswith(b'\n') and out.endswith(b'\n'):
        out = out[:-1]
    for n in names:
        open(os.path.join(DST, n), 'wb').write(bytes(out))
        written += 1

print("写出文件:", written, "/", sum(len(v) for v in reps.values()))
print("### 问题:", len(problems))
for p in problems[:25]: print("   ", p)
