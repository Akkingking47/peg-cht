# -*- coding: utf-8 -*-
import io, json, re, sys
m = json.load(io.open('_xscn-crossmap.json', encoding='utf-8'))
for tok in sys.argv[1:]:
    hits = [k for k in m if re.search(r'(?<![A-Za-z])%s(?![A-Za-z])' % re.escape(tok), k)]
    print('### %s  (%d 命中)' % (tok, len(hits)))
    for k in hits[:12]:
        print('   %-40s -> %s' % (k[:40], m[k]))
    print()
