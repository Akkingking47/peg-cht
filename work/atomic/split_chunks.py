# -*- coding: utf-8 -*-
"""EFILE_ATOMIC `.xscn` 待译串分片器 —— 按 POLICY.md 风格，400 行/片。

输入：work/atomic/_xscn-todo.txt（未命中跨 efile 复用的唯一串，已排序）
输出：work/atomic/chunks/chunk-NN.tsv  （单列纯文本，UTF-8 无 BOM，CRLF）
用法：python split_chunks.py [--size 400]
"""
import io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TODO = os.path.join(HERE, '_xscn-todo.txt')
OUT = os.path.join(HERE, 'chunks')


def main():
    size = 400
    if '--size' in sys.argv:
        size = int(sys.argv[sys.argv.index('--size') + 1])
    rows = [l.rstrip('\n') for l in io.open(TODO, encoding='utf-8') if l.strip()]
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.startswith('chunk-') and f.endswith('.tsv'):
            os.remove(os.path.join(OUT, f))
    n = 0
    for i in range(0, len(rows), size):
        n += 1
        part = rows[i:i + size]
        p = os.path.join(OUT, 'chunk-%02d.tsv' % n)
        io.open(p, 'w', encoding='utf-8', newline='').write('\r\n'.join(part) + '\r\n')
    print('分片 %d 片 / %d 行 -> %s' % (n, len(rows), OUT))


if __name__ == '__main__':
    main()
