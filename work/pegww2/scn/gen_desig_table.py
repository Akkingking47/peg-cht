# -*- coding: utf-8 -*-
"""番号展开 v2（用户裁定 2026-10-20）：
 ① 依据：.SCN 逐单位精确国籍（非战役视角）
 ② 数字/罗马 -> 「第N」；缩写 -> 既有 unit-abbr-map
 ③ 数字+字母后缀码 -> **同场景同后缀已译先例**补词（无同场景先例则用全局同后缀先例）
 ④ 意大利舰名碎片 -> 并入舰名批次（不再当内部代号保留）
 ⑤ 其余无据内部代号 -> 保留原文并登记
产出：对照表 + 字母后缀码清单 + 保留登记 + 舰名并入清单 + 挖掘映射
"""
import os, sys, io, re
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
DEP = r"D:\Program Files\PeG-WW2\SCENARIO"
BK = r"d:\DSH\军事游戏汉化\pegww2\testbed\backup\SCENARIO"
RES = r"d:\DSH\军事游戏汉化\pegww2\research"
DER = os.path.join(RES, "_derived")          # 生成器产出（可复算，勿手改；见 research/README.md）
os.makedirs(DER, exist_ok=True)
CJK = re.compile(r"[\u4e00-\u9fff]")
ROMAN = re.compile(r"^[IVXLCDM]+$")
SEP = re.compile(r"(\s+|/)")
SHIPPFX = {"RM","SMG","RN","CR","CA","Dt","Lgt","KMS","HMS","USS","ITS","FRS","RAN","SM","KM","R.Smg"}
SAT = {"罗马尼亚","匈牙利","芬兰","意大利","保加利亚"}   # 仆从国：未定字母码整行保留
CJK_R = re.compile(r"[\u4e00-\u9fff]")

def roman(t):
    v = {"I":1,"V":5,"X":10,"L":50,"C":100,"D":500,"M":1000}; n = 0
    for i, c in enumerate(t):
        if i+1 < len(t) and v[c] < v[t[i+1]]: n -= v[c]
        else: n += v[c]
    return n

def rd(p):
    return open(p, "rb").read().decode("gbk", errors="replace").split("\r\n")

# ---------- ① 年代（用户裁定：各时期规则必须分时代，缩写跨时代含义差别大） ----------
IDX = {f.lower(): f for f in os.listdir(DEP)}
YEAR = {}
def _own_year(stem):
    for suf in ("_i.txt", ".TXT", "_i.TXT", "_m.txt"):
        k = IDX.get((stem + suf).lower())
        if not k: continue
        txt = "\n".join(rd(os.path.join(DEP, k))[:8])
        m = re.search(r"(19[34]\d)(?=\s*年|[/\-])", txt) or re.search(r"19[34]\d", txt)
        if m: return int(m.group(1) if m.lastindex else m.group(0))
    return 0
# 场景 -> 战役（借既有 _scn-国别.tsv），战役 -> 年代（其场景自身年份的众数）
STEM_CAMP, CAMP_YEARS, STEM_YEAR = {}, defaultdict(list), {}
_np = os.path.join(RES, "_scn-国别.tsv")
if os.path.isfile(_np):
    for raw in io.open(_np, encoding="utf-8-sig"):
        s = raw.rstrip("\r\n")
        if not s or s.startswith("#") or s.startswith("场景stem"): continue
        f2 = s.split("\t")
        if len(f2) >= 2 and f2[0] and f2[1]: STEM_CAMP[f2[0].lower()] = f2[1]
for _st in (f[:-6].lower() for f in os.listdir(DEP) if f.lower().endswith("_u.txt")):
    _y = _own_year(_st); STEM_YEAR[_st] = _y
    if _y and _st in STEM_CAMP: CAMP_YEARS[STEM_CAMP[_st]].append(_y)
CAMP_ERA = {}
for _c, _ys in CAMP_YEARS.items():
    _y = Counter(_ys).most_common(1)[0][0]
    CAMP_ERA[_c] = "1939-41" if _y <= 1941 else "1942-43" if _y <= 1943 else "1944-46"
def era_of(stem):
    if stem in YEAR: return YEAR[stem]
    y = STEM_YEAR.get(stem, 0) or _own_year(stem)
    if y: e = "1939-41" if y <= 1941 else "1942-43" if y <= 1943 else "1944-46"
    else: e = CAMP_ERA.get(STEM_CAMP.get(stem, ""), "?")
    YEAR[stem] = e; return e

# ---------- ② 挖掘（按文件保留上下文 + 年代分桶） ----------
tok_g = defaultdict(Counter)
tok_e = defaultdict(Counter)                                  # (年代, token) -> 译法
sfx_file = defaultdict(lambda: defaultdict(Counter))
sfx_file_e = defaultdict(lambda: defaultdict(Counter))        # (年代, stem) -> 后缀 -> 词
sfx_g = defaultdict(Counter)
sfx_ge = defaultdict(lambda: defaultdict(Counter))             # 年代 -> 后缀 -> 词
whole = Counter()
for f in sorted(os.listdir(DEP)):
    if not f.lower().endswith("_u.txt"): continue
    bk = os.path.join(BK, f)
    if not os.path.isfile(bk): continue
    stem = f[:-6].lower(); E = era_of(stem)
    d = rd(os.path.join(DEP, f)); b = rd(bk)
    if len(d) < 2 or len(d) != len(b): continue
    for i in range(len(d)):
        x, y = b[i].strip(), d[i].strip()
        if not x or not y or x == y: continue
        if CJK.search(x) or not CJK.search(y): continue
        whole[(x, y)] += 1
        xt = [t for t in re.split(r"[/ ]+", x) if t]
        yt = [t for t in re.split(r"[/ ]+", y) if t]
        if len(xt) != len(yt): continue
        for a, c in zip(xt, yt):
            if CJK.search(a) or not CJK.search(c) or a == c: continue
            tok_g[a][c] += 1; tok_e[(E, a)][c] += 1
            m = re.fullmatch(r"\d+([A-Za-z]{1,3})", a)
            if m and (c.startswith("第") or c[:1].isascii()):
                w = re.sub(r"^第\s*\d+\s*", "", c).strip()
                if w and CJK.search(w):
                    sfx_file[stem][m.group(1)][w] += 1
                    sfx_file_e[(E, stem)][m.group(1)][w] += 1
for st in sfx_file:
    for s2, cc in sfx_file[st].items(): sfx_g[s2].update(cc)
for (E, st) in sfx_file_e:
    for s2, cc in sfx_file_e[(E, st)].items(): sfx_ge[E][s2].update(cc)

tmap = {a: (tok_g[a].most_common(1)[0][0], tok_g[a].most_common(1)[0][1]/sum(tok_g[a].values()), sum(tok_g[a].values())) for a in tok_g}
tmap_e = {}
for _k in tok_e:
    _c = tok_e[_k]; _t, _n = _c.most_common(1)[0]
    tmap_e[_k] = (_t, _n / sum(_c.values()), sum(_c.values()))
lmap = {}
for (x, y), n in whole.items(): lmap.setdefault(x, (y, n))
amap = {}
KEEP = set()          # 既有裁定：无展开依据的内部代号，保留原文
_amp = os.path.join(RES, "unit-abbr-map.tsv")
if os.path.isfile(_amp):
    _flag = False
    for raw in io.open(_amp, encoding="utf-8-sig"):
        s = raw.rstrip("\r\n")
        if "无展开依据" in s: _flag = True
        if not s: continue
        if s.startswith("#"):
            if _flag:
                KEEP |= set(re.findall(r"(?<![A-Za-z0-9])[A-Z][A-Za-z0-9]{1,20}(?![A-Za-z0-9])", s))
            continue
        if _flag: _flag = False
        f2 = s.split("\t")
        if len(f2) >= 3 and f2[0] and f2[2] and "{" not in f2[2]: amap[f2[0]] = f2[2]
KEEP -= {"AX", "MOD", "KEEP"}

# 位次→编制规模 阶梯（实测，单调）
LADD = defaultdict(dict)
_lp = os.path.join(RES, "_u-position-ladder.tsv")
if os.path.isfile(_lp):
    for raw in io.open(_lp, encoding="utf-8-sig"):
        s = raw.rstrip("\r\n")
        if not s or s.startswith("#"): continue
        f2 = s.split("\t")
        if len(f2) >= 3 and f2[1].isdigit():
            LADD[f2[0]][int(f2[1])] = f2[2].split("/")

with io.open(os.path.join(DER, "_u-token-map-mined.tsv"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("# 原版_u ↔ 已译_u 实测 token 映射（按文件上下文保留）\n原文token\t最高频译法\t次数\t占比\t全部候选\n")
    for a in sorted(tok_g, key=lambda k: -sum(tok_g[k].values())):
        c = tok_g[a]; t, n = c.most_common(1)[0]
        fh.write("%s\t%s\t%d\t%.2f\t%s\n" % (a, t, n, n/sum(c.values()), " | ".join("%s(%d)" % kv for kv in c.most_common(6))))
with io.open(os.path.join(DER, "_u-line-map-mined.tsv"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("# 原版_u ↔ 已译_u 实测 整行 映射\n原文行\t译法\t次数\n")
    for (x, y), n in whole.most_common(6000): fh.write("%s\t%s\t%d\n" % (x, y, n))

# ---------- ② 生成 ----------
def prop_tok(t, stem, era):
    s = t.strip()
    if not s: return s, "", ""
    if re.fullmatch(r"-+", s): return s, "", ""
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if re.fullmatch(r"\d+", inner) or (ROMAN.match(inner) and len(inner) <= 6): return s, "", ""
        v, c, n2 = prop_tok(inner, stem, era)
        if v == inner: return s, "", ""
        return "[" + v + "]", c, n2
    if re.fullmatch(r"\d+", s): return "第" + s, "", ""
    if era and era != "?":                          # ⓪ 同年代实测映射优先（用户裁定：分时代）
        te = tmap_e.get((era, s))
        if te and te[1] >= 0.8 and te[2] >= 2: return te[0], "", ""
    if s in tmap:                                   # ① 全局实测映射
        v, share, cnt = tmap[s]
        if share >= 0.8 and cnt >= 2: return v, "", ""
        if s in amap: return amap[s], "", ""
        if not re.fullmatch(r"\d+[A-Za-z]{1,3}", s): return s, "code", ""
    elif s in amap: return amap[s], "", ""
    if s in KEEP: return s, "opq", ""               # 既有裁定：无据内部代号保留
    if ROMAN.match(s) and 2 <= len(s) <= 5: return "第" + str(roman(s)), "", ""   # 罗马（≥2字符）
    m = re.fullmatch(r"(\d+)([A-Za-z]{1,3})", s)
    if m:
        num, sfx = m.group(1), m.group(2)
        cands = []
        if era and era != "?":
            cands += [sfx_file_e.get((era, stem), {}).get(sfx), sfx_ge.get(era, {}).get(sfx)]
        cands += [sfx_file.get(stem, {}).get(sfx), sfx_g.get(sfx)]
        for src in cands:
            if src:
                w = src.most_common(1)[0][0]
                return "第" + num + w, "", "后缀先例:" + w
        return s, "code", ""
    if re.fullmatch(r"[A-Za-z]{1,5}", s) or re.fullmatch(r"[A-Za-z]{1,2}[0-9]{2,4}", s):
        return s, "opq", ""
    return s, "code", ""

def is_ship(line):
    return any(t.strip() in SHIPPFX for t in SEP.split(line))

def is_frag(tk, nat, line):
    """舰名判据：U-数字潜艇 / 舰船行 / 全小写 / 意籍词形 / 长词形名（≥6字母含小写）"""
    if re.fullmatch(r"[Uu]-\d+", tk): return True
    if is_ship(line): return True
    if tk.islower(): return True
    if tk.isalpha() and any(c.islower() for c in tk):
        if nat == "意大利": return True
        if len(tk) >= 6: return True
    return False

def uncertain_coded(segs):
    """仆从国判据：链中是否含**未定字母码**（单字母 R/F/C、HA、H、SS 等）。
    仅放行：纯数字、`数字+R`（R=团）、已译中文。其余一律视为未定 ⇒ 整行保留。"""
    for seg in segs:
        for tk in seg.split():
            if not tk or re.fullmatch(r"[-\[\]0-9]+", tk): continue
            if re.fullmatch(r"\d+[Rr]", tk): continue
            if re.fullmatch(r"\d+(ID|id)", tk): continue     # ID=Infantry Division（既有译法「第N步兵师」）
            if CJK.search(tk): continue
            return True
    return False


def propose2(line, stem, nat, era):
    """链路感知：仆从国先判未定字母码 → 罗马尼亚按史实 OOB 定级 → 整行实测 → 位次阶梯 → token 规则。"""
    st = line.strip()
    segs = line.split("/")
    n = len(segs)
    if nat in SAT:
        # —— 未定字母码 ⇒ 整行保留（优先于「整行实测」，避免旧译把 C/F/R 硬解成军/团）——
        if uncertain_coded(segs):
            return st, "含未定字母码，整行保留", Counter({"keep": 1}), "", []
        # —— 史实 OOB 校正（用户裁定 2026-10-21，按地图规模）——
        #   罗马尼亚 2 段裸数字 = 团/师（25/15 = 第15步兵师第25团）
        #   XR/35R = 团/预备师（50R/35R = 第35预备步兵师第50团；R=Reserve 非 Regiment）
        if nat == "罗马尼亚" and n == 2:
            a, b = segs[0].strip(), segs[1].strip()
            if re.fullmatch(r"\d+R", a) and b == "35R":
                return ("第%s团/第35预备师" % a[:-1], "史实OOB:35预备步兵师",
                        Counter(), "", ["0=团", "1=预备师"])
            if re.fullmatch(r"\d+R", a) and re.fullmatch(r"\d+", b):
                return ("第%s团/第%s师" % (a[:-1], b), "史实OOB:团/师",
                        Counter(), "", ["0=团", "1=师"])
    if st in lmap:
        return lmap[st][0], "整行实测(%d)" % lmap[st][1], Counter(), "", []
    lad = LADD.get(nat, {}).get(n, [])
    if nat == "罗马尼亚" and n == 2:
        a, b = segs[0].strip(), segs[1].strip()
        if re.fullmatch(r"\d+", a) and re.fullmatch(r"\d+", b):
            lad = ["团", "师"]
    if n == 1 and lad and re.fullmatch(r"\d+", st):          # 单段裸数字：按国别补 团/营 泛化前缀
        return "第" + st + lad[0], "位次实测:0=%s" % lad[0], Counter(), "", ["0=%s" % lad[0]]
    outs = []; cats = Counter(); tags = []; lad_used = []
    for i, seg in enumerate(segs):
        toks = seg.split()
        if not toks:
            outs.append(seg); continue
        head = toks[0]
        if re.fullmatch(r"\d+", head) and i < len(lad) and lad[i]:
            rendered = ["第" + head + lad[i]]; lad_used.append("%d=%s" % (i, lad[i]))
        else:
            v, c, t2 = prop_tok(head, stem, era); rendered = [v]
            if c: cats[c] += 1
            if t2: tags.append(t2)
        for tk in toks[1:]:
            v, c, t2 = prop_tok(tk, stem, era)
            rendered.append(v)
            if c: cats[c] += 1
            if t2: tags.append(t2)
        outs.append(" ".join(rendered))
    why = ("位次实测:" + ",".join(lad_used)) if lad_used else ("待判token" if cats else "规则/实测")
    return "/".join(outs), why, cats, ";".join(tags), lad_used

src = os.path.join(DER, "_番号未展开统计-按SCN国籍v2-20261020.tsv")
data = [r for r in [l.rstrip("\n").split("\t") for l in open(src, encoding="utf-8") if l.strip()][1:] if len(r) >= 6]
out = os.path.join(DER, "_番号展开-对照表-20261020.tsv")
stat2 = Counter(); done = Counter(); stat = Counter()
code_rows = defaultdict(lambda: {"n": 0, "nat": Counter(), "scn": set(), "res": set()})
opq_rows = defaultdict(lambda: {"n": 0, "nat": Counter(), "scn": set(), "ship": 0, "res": set()})
for r in data:
    nat, scn, txt = r[0], r[3], r[4]
    ship = is_ship(txt)
    for tk in [t.strip() for t in SEP.split(txt) if t.strip() and not SEP.fullmatch(t)]:
        if tk in tmap or tk in amap: continue
        v, c, _tag = prop_tok(tk, scn.lower(), era_of(scn.lower()))
        if re.fullmatch(r"\d+[A-Za-z]{1,3}", tk):
            e = code_rows[tk]; e["n"] += 1; e["nat"][nat] += 1; e["scn"].add(scn)
            if c == "": e["res"].add(v)
            if is_frag(tk, nat, txt):
                e2 = opq_rows[tk]; e2["n"] += 1; e2["nat"][nat] += 1; e2["scn"].add(scn); e2["ship"] += 1
        elif c == "opq" and (re.fullmatch(r"[A-Za-z]{1,5}", tk) or re.fullmatch(r"[A-Za-z]{1,2}[0-9]{2,4}", tk)):
            e = opq_rows[tk]; e["n"] += 1; e["nat"][nat] += 1; e["scn"].add(scn)
            if is_frag(tk, nat, txt): e["ship"] += 1
with io.open(out, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("# 番号展开对照表 v3（国别=.SCN逐单位精确国籍；年代=各时期规则分时代）\n国别\t年代\t战役族\t战区\t场景\t原文行\t建议译法\t依据\t处置\t置信度\n")
    for r in data:
        nat, fam, th, scn, txt = r[0], r[1], r[2], r[3], r[4]
        era = era_of(scn.lower())
        p, why, cats, tags, lad = propose2(txt, scn.lower(), nat, era)
        opqs = [t.strip() for t in SEP.split(txt) if t.strip() and not SEP.fullmatch(t) and prop_tok(t, scn.lower(), era)[1] in ("opq", "code")]
        if cats.get("keep"):
            p = txt.strip(); disp, cf = "保留", "—"
        elif opqs and all(is_frag(t, nat, txt) for t in opqs):
            disp, cf = "舰名待译", "—"
        elif cats.get("opq"):
            disp, cf = "保留", "—"
        elif cats.get("code"):
            disp, cf = ("待判" if p == txt.strip() else "部分待判"), "低"
        elif why.startswith("整行实测"):
            disp, cf = "译", "高"
        elif lad:
            disp, cf = "译", "中"
        else:
            disp, cf = "译", ("高" if not tags else "中")
        compressed = why if (why.startswith("整行实测") or why.startswith("位次实测") or why.startswith("待判")) else why
        stat[nat] += 1; stat2[disp] += 1; done[(nat, disp)] += 1
        fh.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (nat, era, fam, th, scn, txt, p, compressed, disp, cf))
print("== 处置分布 ==")
for k, v in stat2.most_common(): print("  %s\t%d" % (k, v))
print("== 各国 ==")
for nat in sorted(set(k[0] for k in done), key=lambda n: -stat[n]):
    print("  %-8s 合计%5d  译%5d  部分待判%5d  待判%5d  保留%5d  舰名待译%5d" % (nat, stat[nat],
          done[(nat,"译")], done[(nat,"部分待判")], done[(nat,"待判")], done[(nat,"保留")], done[(nat,"舰名待译")]))

# ---- 字母后缀码清单（含已按先例定词） ----
def suffix(t):
    m = re.findall(r"\d+([A-Za-z]+)", t); return m[0] if m else ""
lst = os.path.join(DER, "_番号-字母后缀码-待判清单-20261020.tsv")
with io.open(lst, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("# 数字+字母后缀码清单（同场景同后缀先例定词；用户裁定 2026-10-20）\n后缀\t原文\t行数\t国别分布\t出现场景数\t同后缀已译实例\t定词结果\t状态\n")
    for tk in sorted(code_rows, key=lambda k: (-code_rows[k]["n"], k)):
        e = code_rows[tk]; sfx = suffix(tk)
        ex = [(a, tmap[a][0]) for a in tmap if re.fullmatch(r"\d+" + sfx + r"(/\d+)?", a) and tmap[a][1] >= .8 and tmap[a][2] >= 2][:3]
        res = "/".join(sorted(e["res"])) if e["res"] else ""
        fh.write("%s\t%s\t%d\t%s\t%d\t%s\t%s\t%s\n" % (sfx, tk, e["n"],
                 "/".join("%s%d" % kv for kv in e["nat"].most_common(3)), len(e["scn"]),
                 ", ".join("%s→%s" % kv for kv in ex), res, "已定词" if res else "仍待判"))
print("字母后缀码 去重 %d（已定词 %d / 仍待判 %d）-> %s" % (len(code_rows),
      sum(1 for k in code_rows if code_rows[k]["res"]), sum(1 for k in code_rows if not code_rows[k]["res"]), lst))

# ---- 保留登记（剔除舰名碎片） ----
reg = os.path.join(DER, "_番号-有意保留代号清单-20261020.tsv")
shipl = os.path.join(DER, "_番号-舰名碎片-并入清单-20261020.tsv")
with io.open(reg, "w", encoding="utf-8", newline="\n") as fh, io.open(shipl, "w", encoding="utf-8", newline="\n") as g:
    fh.write("# 无据内部代号 有意保留登记（绝不臆造；沿用既有裁定）\n代号\t行数\t国别分布\t出现场景数\n")
    g.write("# 意大利/盟军舰名碎片（用户裁定：并入舰名批次处理，不再当内部代号保留）\n碎片\t行数\t国别分布\t舰名行占比\t出现场景数\n")
    nok = nship = 0
    for tk in sorted(opq_rows, key=lambda k: (-opq_rows[k]["n"], k)):
        e = opq_rows[tk]; ratio = e["ship"] / max(1, e["n"])
        natd = "/".join("%s%d" % kv for kv in e["nat"].most_common(3))
        if ratio >= 0.5:
            g.write("%s\t%d\t%s\t%.0f%%\t%d\n" % (tk, e["n"], natd, 100 * ratio, len(e["scn"]))); nship += 1
        else:
            fh.write("%s\t%d\t%s\t%d\n" % (tk, e["n"], natd, len(e["scn"]))); nok += 1
print("内部代号 保留登记 %d 个；舰名碎片 并入 %d 个" % (nok, nship))
print("[out]", os.path.basename(out))
