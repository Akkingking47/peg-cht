# -*- coding: utf-8 -*-
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = 'place_V.py'
s = open(p, encoding='utf-8').read()

FIX = {
    "Valdecasa de Tajo": "塔霍河畔瓦尔德卡",   # 24B->21B? check
    "Varenikovskoye":    "瓦列尼科夫斯科",     # 24B->21B
    "Victorspradt":      "维克托斯普拉",       # 21B->18B
    "Vilkaviskis":       "维尔卡维什基",       # 21B->18B
    "Villaconejos":      "比利亚科内霍",       # 21B->18B
    "Villarquemado":     "比利亚尔克马",       # 21B->18B
    "Villaviciosa":      "比利亚维西奥",       # 21B->18B
    "Vittorio Veneto":   "维托里奥",           # 21B->12B
    "Vladimir-Volinskiy":"弗拉基米尔",         # 21B->15B
    "Vladimirovka":      "弗拉基米罗夫",       # 21B->18B
    "Vladislavovka":     "弗拉季斯拉沃",       # 24B->18B
    "Vladivostok":       "海参崴",             # 21B->9B
    "Volgostroy":        "伏尔加斯特罗",       # 21B->18B
    "Volokolamsk":       "沃洛科拉姆斯",       # 21B->18B
    "Voroshilovgrad":    "伏罗希洛夫",         # 21B->15B
}
for k, v in FIX.items():
    pat = re.compile(r'("%s"\s*:\s*)"[^"]*"' % re.escape(k))
    if not pat.search(s):
        print('MISS', k); continue
    s = pat.sub(lambda m: m.group(1) + '"%s"' % v, s, count=1)

# 追加尾随空格键
if '"Vinaroz "' not in s:
    s = s.replace('    "Vinaroz": "比纳罗斯",', '    "Vinaroz": "比纳罗斯",\n    "Vinaroz ": "比纳罗斯",')

open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('done')
for k, v in FIX.items():
    print(k, '->', v, len(v.encode('utf-8')), 'B')
