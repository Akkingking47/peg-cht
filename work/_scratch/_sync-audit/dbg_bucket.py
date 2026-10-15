import importlib.util, sys
spec = importlib.util.spec_from_file_location("a4", r"D:\DSH\军事游戏汉化\work\_sync-audit\audit_brief_map4.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print("主库条目数:", len(m.CATS))
for k in ("ss","pt","longest path:","number of scenarios:","lodz","tunis","leningrad","suchan","amur river","katowice","son"):
    print(f"  {k!r:26} norm={m.norm_en(k)!r:26} bucket={m.bucket(k)}  cats={sorted(m.CATS.get(k, []))}")
