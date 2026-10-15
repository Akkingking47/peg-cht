# -*- coding: utf-8 -*-
r"""提取 PGForever.exe 中的 UTF-16LE 宽字符串清单, 供汉化用。
只扫描 .rdata / .text / .data 三个节(数据区), 输出候选清单。
每条记录: 文件偏移 / 字节长度 / 字符数 / 文本 / 预判类型
"""
import json
import os
import re
import struct

EXE = r'D:\PGForever1.021\PGForever.exe'
OUTDIR = r'D:\DSH\军事游戏汉化\pgforever\work\exe'

# 判定规则
RE_FILENAME = re.compile(r'\.[a-zA-Z0-9]{2,5}$')
RE_KEYLIKE = re.compile(r'^[A-Z][A-Za-z0-9]*([A-Z][A-Za-z0-9]*)+$')   # 驼峰内部键
RE_PATH = re.compile(r'[/\\]')
RE_FORMAT = re.compile(r'%[0-9]*[sdufxX]|%%|\{0\}|\{1\}')
RE_HTMLTAG = re.compile(r'</?[a-zA-Z]')


def load_sections(b):
    e = struct.unpack_from('<I', b, 0x3c)[0]
    nsec = struct.unpack_from('<H', b, e + 6)[0]
    sizeopt = struct.unpack_from('<H', b, e + 20)[0]
    optoff = e + 24
    so = optoff + sizeopt
    secs = []
    for i in range(nsec):
        o = so + i * 40
        nm = b[o:o + 8].rstrip(b'\x00').decode()
        vs, va, srd, prd = struct.unpack_from('<IIII', b, o + 8)
        secs.append((nm, va, vs, prd, srd))
    return secs


def main():
    b = open(EXE, 'rb').read()
    secs = load_sections(b)
    os.makedirs(OUTDIR, exist_ok=True)

    targets = [s for s in secs if s[0] in ('.rdata', '.text', '.data')]
    found = {}
    for nm, va, vs, prd, srd in targets:
        limit = min(srd, vs) if srd else vs
        data = b[prd:prd + limit]
        # UTF-16LE 字符串: 每个字符 后两字节, 以 \0\0 结尾
        i = 0
        while i < len(data) - 1:
            # 找一个可打印 ASCII 作为串首
            if 0x20 <= data[i] <= 0x7E and data[i + 1] == 0:
                j = i
                chars = []
                while j < len(data) - 1:
                    lo, hi = data[j], data[j + 1]
                    if lo == 0 and hi == 0:
                        break
                    if hi != 0:
                        break  # 非 ASCII -> 不是纯宽串(? 保留)
                    if lo < 0x20 or lo > 0x7E:
                        break
                    chars.append(chr(lo))
                    j += 2
                if len(chars) >= 3:
                    s = ''.join(chars)
                    # 要求后面确实跟着 0000
                    if j + 1 < len(data) and data[j] == 0 and data[j + 1] == 0:
                        key = (prd + i, s)
                        found[prd + i] = {
                            'offset': prd + i,
                            'bytes': len(chars) * 2,
                            'chars': len(chars),
                            'text': s,
                            'section': nm,
                        }
                        i = j + 2
                        continue
            i += 1

    items = sorted(found.values(), key=lambda x: x['offset'])
    print('共提取 %d 个宽字符串' % len(items))

    # 分类
    for it in items:
        s = it['text']
        if RE_PATH.search(s) or RE_FILENAME.search(s) or s.endswith('.dll'):
            it['kind'] = 'path'
        elif RE_KEYLIKE.match(s) and len(s) < 40:
            it['kind'] = 'key'
        elif len(s) < 3:
            it['kind'] = 'short'
        else:
            it['kind'] = 'text'
        it['has_format'] = bool(RE_FORMAT.search(s))
        it['has_tag'] = bool(RE_HTMLTAG.search(s))
        # 是否像自然语言: 有空格且含常见冠词/介词
        it['likely_ui'] = (
            it['kind'] == 'text'
            and (' ' in s or it['has_tag'])
            and bool(re.search(r'[a-z]', s))
        )

    json.dump(items, open(os.path.join(OUTDIR, 'strings-raw.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    counts = {}
    for it in items:
        counts[it['kind']] = counts.get(it['kind'], 0) + 1
    print('分类统计:', counts)
    ui = [x for x in items if x['likely_ui']]
    print('疑似 UI 文案: %d 条' % len(ui))

    # 输出可读清单
    lines = []
    for i, it in enumerate(ui, 1):
        lines.append('%4d | off=0x%X | len=%3d | %s%s' % (
            i, it['offset'], it['chars'], it['text'],
            '  [含格式符]' if it['has_format'] else ('  [含标签]' if it['has_tag'] else '')))
    open(os.path.join(OUTDIR, 'strings-ui.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
    print('已输出 ' + os.path.join(OUTDIR, 'strings-ui.txt'))


if __name__ == '__main__':
    main()
