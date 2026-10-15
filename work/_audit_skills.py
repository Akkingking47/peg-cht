# -*- coding: utf-8 -*-
"""技能安全审计：对新建/改动的技能做 P0/P1/P2 风险扫描。"""
import os, re, sys

SK = r"C:\Users\Administrator\.workbuddy\skills"
TARGETS = [
    "ssi-modgen-peg-localization",
    "pgforever-htmlayout-localization",
    "win-game-html-ui-localization",
    "sd25-pe",
]

DANGER = {
    "P0 · 递归删除":      r"rm\s+-rf\s+/|rm\s+-rf\s+[A-Za-z]:|Remove-Item.*-Recurse.*-Force|shutil\.rmtree|del\s+/[sS]",
    "P0 · 远程执行":      r"curl\s+[^|]*\|\s*(ba)?sh|wget\s+[^|]*\|\s*(ba)?sh|iex\s*\(|Invoke-Expression",
    "P0 · 数据外泄":      r"curl\s+(-d|-F|-T|-X\s*POST)|requests\.post|Invoke-RestMethod|fetch\(.+method:\s*['\"]POST",
    "P0 · 代码注入":      r"\beval\s*\(|\bexec\s*\(|FromBase64String|base64\s+-d",
    "P1 · 凭据索取":      r"password|passwd|api[_-]?key|secret|credential|凭据|密码|token",
    "P1 · 系统写入":      r"reg\s+add|HKLM|Set-ItemProperty|chmod\s+777|/etc/",
    "P1 · 持久化":        r"schtasks|Register-ScheduledTask|crontab|autostart|run\\+注册表",
    "P1 · 包拉取执行":    r"npx\s+--?y(es)?\s+\S+@?latest|npm\s+i(nstall)?\s+-g|pip\s+install",
    "P2 · 外部链接":      r"https?://[^\s\)\]\"'>]+",
}

def scan(root):
    files = []
    for r, d, fs in os.walk(root):
        for f in fs:
            files.append(os.path.join(r, f))
    res = {"files": files}
    hits = {}
    for name, pat in DANGER.items():
        hh = []
        for f in files:
            try: t = open(f, encoding="utf-8").read()
            except Exception: continue
            for m in re.finditer(pat, t, re.I):
                ln = t[:m.start()].count("\n") + 1
                ctx = t[max(0, m.start()-45):m.end()+45].replace("\n", " ")
                hh.append((os.path.relpath(f, root), ln, ctx))
        if hh: hits[name] = hh
    res["hits"] = hits
    res["bad_ext"] = [f for f in files if not f.lower().endswith((".md", ".txt", ".json", ".yaml", ".yml"))]
    res["ctrl"] = []
    for f in files:
        b = open(f, "rb").read()
        nb = sum(1 for x in b if x < 9 or (13 < x < 32))
        if nb or b.count(b"\x00"):
            res["ctrl"].append((os.path.relpath(f, root), nb, b.count(b"\x00")))
    return res

for t in TARGETS:
    root = os.path.join(SK, t)
    if not os.path.isdir(root):
        print(f"### {t} —— 不存在，跳过\n"); continue
    r = scan(root)
    nf = len(r["files"])
    tot = sum(os.path.getsize(f) for f in r["files"])
    print("=" * 74)
    print(f"### {t}   （{nf} 文件 / {tot} B）")
    print("=" * 74)
    if r["bad_ext"]:
        print(f"  ⚠️ 非文档文件：{r['bad_ext']}")
    else:
        print("  ✓ 全部为文档（.md），无脚本/可执行文件")
    if r["ctrl"]:
        print(f"  ⚠️ 含控制/NUL 字节：{r['ctrl']}")
    else:
        print("  ✓ 无异常控制字节 / NUL")
    if not r["hits"]:
        print("  ✓ 危险模式：全部无命中")
    else:
        for name, hh in r["hits"].items():
            print(f"  {'⛔' if name.startswith('P0') else '⚠️'} {name}：{len(hh)} 处")
            for f, ln, ctx in hh[:3]:
                print(f"       {f}:{ln}  …{ctx}…")
    print()
