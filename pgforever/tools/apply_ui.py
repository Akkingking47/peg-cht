# -*- coding: utf-8 -*-
r"""
UI 层回填（全量）：backup\origin\<game>\UI 的原文 -> 应用翻译 -> 写出 UTF-8 with BOM 到游戏目录。
覆盖 Default\UI 与全部 game 级 UI 覆盖目录。

规则：
 1. per_file 覆盖优先于 global，各按 en 长度降序（避免短串吃掉长串）
 2. 纯字母串加词边界保护
 3. ★ 屏蔽区保护：<...> 标签内部、id=/class=/name= 属性值、<style> 块内一律不替换
    （否则 id="Experience" 会被译成 id="经验"，破坏 exe 的运行时注入与表格结构）
 4. ★ 译文不得引入原文没有的半角空格（会导致单元格宽度变化、列错位）
 5. 逐行替换，保持行结构；校验行数与 %% 转义数量
 6. 中文排版清理：去除汉字间多余空格、闭合标签后多余空格
"""
import json
import os
import re

B = r'D:\DSH\军事游戏汉化\pgforever\backup\origin'
GAME = r'D:\PGForever1.021'
TR = r'D:\DSH\军事游戏汉化\pgforever\work\ui\translations.json'

tr = json.load(open(TR, encoding='utf-8'))
GLOBAL = tr['global']
PER = tr['per_file']


def build_rules(fn):
    rules = [(k, v) for k, v in PER.get(fn, {}).items() if not k.startswith('_')]
    rules += [(k, v) for k, v in GLOBAL.items()
              if not k.startswith('_') and k not in PER.get(fn, {})]
    rules.sort(key=lambda x: -len(x[0]))
    return rules


TAG = re.compile(r'<[^>]*>')


def shield(line):
    """把 <...> 标签（含属性值，如 id="Experience"）挖出来做占位符，返回 (掩码行, 还原表)。
    只保护标签本体，标签之间的可见文本仍可替换。"""
    store = []

    def _stash(m):
        store.append(m.group(0))
        return '\x01%d\x02' % (len(store) - 1)

    return TAG.sub(_stash, line), store


def unshield(masked, store):
    def _pop(m):
        return store[int(m.group(1))]
    return re.sub(r'\x01(\d+)\x02', _pop, masked)


def replace_all(line, en, zh):
    """纯字母/纯词 -> 加词边界; 含标记的短语在掩码文本上不会出现，故不适用。"""
    if re.fullmatch(r'[A-Za-z][A-Za-z0-9]*', en):
        pat = r'(?<![A-Za-z])' + re.escape(en) + r'(?![A-Za-z])'
    else:
        pat = re.escape(en)
    return re.sub(pat, lambda m: zh, line)


def cleanup(text):
    # 汉字之间的多余半角空格
    text = re.sub(r'(?<=[\u4e00-\u9fff]) +(?=[\u4e00-\u9fff])', '', text)
    # 闭合标签后、汉字前的多余空格
    text = re.sub(r'(</[a-zA-Z][a-zA-Z0-9]*>)[ \t]+(?=[\u4e00-\u9fff])', r'\1', text)
    # ★ 汉字与 &nbsp; / 冒号之间的多余半角空格（译文误加空格时修回）
    text = re.sub(r'(?<=[\u4e00-\u9fff])[ \t]+(?=(:|&nbsp;|<))', '', text)
    # ★ 汉字后紧跟冒号再跟多余空格
    text = re.sub(r'(?<=[\u4e00-\u9fff]:)[ \t]+(?=&nbsp;|<|$)', '', text)
    return text


# 收集所有 UI 目录：Default 与各 game
dirs = []
if os.path.isdir(os.path.join(B, 'Default', 'UI')):
    dirs.append(('Default', os.path.join(B, 'Default', 'UI'), os.path.join(GAME, 'Default', 'UI')))
for g in sorted(os.listdir(B)):
    gp = os.path.join(B, g, 'UI')
    if os.path.isdir(gp) and g != 'Default':
        dirs.append((g, gp, os.path.join(GAME, g, 'UI')))

total_files = 0
total_hits = 0
for game, srcdir, dstdir in dirs:
    os.makedirs(dstdir, exist_ok=True)
    files = sorted(f for f in os.listdir(srcdir) if f.lower().endswith(('.htm', '.html')))
    ghits = 0
    for fn in files:
        raw = open(os.path.join(srcdir, fn), 'rb').read()
        text = raw.decode('utf-8').lstrip('\ufeff')
        nlines = text.count('\n')
        nesc = text.count('%%')

        rules = build_rules(fn)
        out_lines = []
        for line in text.split('\n'):
            if '<' in line:
                new, store = shield(line)
            else:
                new, store = line, []
            for en, zh in rules:
                if en in new:
                    b = new
                    new = replace_all(new, en, zh)
                    if new != b:
                        ghits += 1
            if store:
                new = unshield(new, store)
            out_lines.append(new)
        out = cleanup('\n'.join(out_lines))

        assert out.count('\n') == nlines, '%s/%s 行数变化' % (game, fn)
        assert out.count('%%') == nesc, '%s/%s %% 数量变化' % (game, fn)

        open(os.path.join(dstdir, fn), 'wb').write(b'\xef\xbb\xbf' + out.encode('utf-8'))
        total_files += 1
    total_hits += ghits
    print('%-22s %2d 个 htm，命中 %d 处' % (game, len(files), ghits))

print()
print('合计：%d 个 htm，替换命中 %d 处' % (total_files, total_hits))
