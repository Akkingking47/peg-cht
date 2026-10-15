# -*- coding: utf-8 -*-
"""Emit zh/z2N*.jsonl chunk files (<=90 entries each) from index-aligned
ZH lists loaded from t2Nfull.py, verifying md5 comes from source verbatim."""
import json, os, sys

EQP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(EQP, 'zh')


def emit(src_name, prefix, zh, chunk=90):
    src = json.load(open(os.path.join(EQP, src_name), encoding='utf-8'))
    assert len(src) == len(zh), '%s len %d != %d' % (src_name, len(src), len(zh))
    paths = []
    for start in range(0, len(zh), chunk):
        part = zh[start:start + chunk]
        letters = 'abcdefghij'
        p = os.path.join(D, '%s%s.jsonl' % (prefix, letters[start // chunk]))
        with open(p, 'w', encoding='utf-8') as f:
            for e, z in zip(src[start:start + chunk], part):
                assert z != '', 'empty zh at %s' % e['md5']
                f.write(json.dumps({'md5': e['md5'], 'zh': z},
                                   ensure_ascii=False) + '\n')
        paths.append((os.path.basename(p), len(part)))
    return paths


if __name__ == '__main__':
    ns21 = {}
    exec(open(os.path.join(D, 't21full.py'), encoding='utf-8').read(), ns21)
    for n, c in emit('src21.json', 'z21', ns21['ZH']):
        print(n, c)
