# -*- coding: utf-8 -*-
"""对比「cat 治理前后」的权威核对问题集（只读，不写 OUT、不改任何文件）。

用途：`audit_authority.py` 的分类逻辑有三处读 `cat`
（:176 `cat not in ('UNIT','PLACE')` · :207 `lay='txt' if cat in ('PLACE','TEXT')` · :218 `cat not in ('LEADER','PLACE')`），
本轮把 904 行 `PLACE` 改成 `UNIT`/`EQUIP` ⇒ 必须确认问题集变化是「cat 列标签变了」还是「真的多/少了问题」。
"""
import os
import importlib.util
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
AG = os.path.join(WS, "work", "glossary", "audit_authority.py")
OLD = os.path.join(WS, "backup", "before-cat-fix", "glossary", "standard-glossary.tsv")

spec = importlib.util.spec_from_file_location("audit_authority", AG)
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
NEW = M.GLOSS


def run(path):
    M.GLOSS = path
    rows = M.load_glossary()
    base = M.load_baseline()
    return rows, M.audit(rows, base)


def key(i):
    return (i["kind"], i["cat"], i["en"], i["zh"])


old_rows, old_issues = run(OLD)
new_rows, new_issues = run(NEW)

print("旧库条目 %d · 旧问题 %d" % (len(old_rows), len(old_issues)))
print("新库条目 %d · 新问题 %d" % (len(new_rows), len(new_issues)))
for tag, issues in (("旧", old_issues), ("新", new_issues)):
    c = collections.Counter(i["kind"] for i in issues)
    print("  %s：%s" % (tag, " · ".join("%s %d" % (k, c[k]) for k in sorted(c))))
    print("  %s：cat 分布 %s" % (tag, dict(collections.Counter(i["cat"] for i in issues))))

so, sn = {key(i) for i in old_issues}, {key(i) for i in new_issues}
print("\n完全相同的 (kind,cat,en,zh) 行数 %d" % len(so & sn))
print("新库独有 %d 行（前 25）：" % len(sn - so))
for k in sorted(sn - so)[:25]:
    print("   + %s" % (k,))
print("旧库独有 %d 行（前 25）：" % len(so - sn))
for k in sorted(so - sn)[:25]:
    print("   - %s" % (k,))

# 只比 (kind,en,zh)，忽略 cat：看问题「本体」有没有增减
ko = {(i["kind"], i["en"], i["zh"]) for i in old_issues}
kn = {(i["kind"], i["en"], i["zh"]) for i in new_issues}
print("\n忽略 cat 后：新库独有 %d · 旧库独有 %d" % (len(kn - ko), len(ko - kn)))
for k in sorted(kn - ko)[:20]:
    print("   + %s" % (k,))
for k in sorted(ko - kn)[:20]:
    print("   - %s" % (k,))
