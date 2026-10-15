# -*- coding: utf-8 -*-
import io, json, re, random
m = json.load(io.open('_xscn-crossmap.json', encoding='utf-8'))
ks = list(m.keys())
random.seed(3)
print('=== 含 "/" 的番号串样例 40 ===')
sub = [k for k in ks if '/' in k and re.search(r'\d', k)]
for k in random.sample(sub, 40):
    print('%-42s -> %s' % (k[:42], m[k]))
print()
print('=== 含罗马数字的 25 ===')
sub2 = [k for k in ks if re.search(r'\b(?:I{1,3}V?|VI{0,3}|IX|XI{0,2})\b', k)]
for k in random.sample(sub2, 25):
    print('%-42s -> %s' % (k[:42], m[k]))
print()
print('=== 地名类 20 ===')
sub3 = [k for k in ks if re.match(r'^[A-Z][a-z]+$', k)]
for k in random.sample(sub3, 20):
    print('%-42s -> %s' % (k[:42], m[k]))
