# -*- coding: utf-8 -*-
"""统一回归入口：把 7 项**既有**校验资产编排成一条命令，输出机器可比的对照结果。

用法：
    python work\\regression.py --help               # 列出全部模式与选项
    python work\\regression.py --list               # 只列回归包含的检查项、真实命令与门键
    python work\\regression.py --save-baseline      # 跑全部检查并冻结基线
    python work\\regression.py                      # 跑全部检查并与基线比对
    python work\\regression.py --only layer_gate    # 只跑指定项（可重复，或逗号分隔）
    python work\\regression.py --json               # 机器可读结果（stdout 纯 ASCII 转义 JSON）
    python work\\regression.py rebuild              # 显式重建链（会写盘，默认不跑）
    python work\\regression.py rebuild --yes        # 真的跑（ingest_layers → converge_plan）

判据纪律（本文件的核心约束，改这个文件时不许破）：
 1. **绝不重写判据**。每一项的结论都直接来自既有脚本自己的 stdout / stderr / 退出码；
    本文件只做两件事：正则**提取**它已经报出来的数字，以及**前后数值比对**。
    一行判据逻辑（阈值、白名单、编码判定、槽结构比较…）都不许复制进这里。
 2. 既有脚本的 stdout 一律按 **UTF-8** 解码，且统一以 `PYTHONIOENCODING=utf-8`
    起子进程。理由是实测出来的：`work\\_sync-audit\\residual_scan.py` 在 cp936
    stdout 下会因 `print(repr(含 U+FFFD 的行))` 抛 `UnicodeEncodeError: 'gbk' codec
    can't encode character '\\ufffd'`，退出码 1（见报告 §不符点）。
 3. 会**改权威输入**的重建链（`ingest_layers.py → converge_plan.py`）不进默认回归，
    只挂在 `rebuild` 模式后面。
 4. 既有脚本各自会刷自己的证据文件（副作用见 SIDE_EFFECTS）——这是它们固有的行为，
    本文件不代劳、不掩盖，只逐次在报告头部点名。

退出码：`0` 无新增偏离；`1` 出现新增偏离；`2` 用法/基线缺失等自身错误。
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

PY = sys.executable or r"C:\Python314\python.exe"
ROOT = r"D:\DSH\军事游戏汉化"
OUT = os.path.join(ROOT, "work", "out")
BASELINE = os.path.join(OUT, "regression-baseline.json")
SCHEMA = "regression-baseline/v1"
DEV_TIMEOUT = 900

# 「全绿」的定义（任务书 §硬约束 6），此串原样写进基线，供以后对照口径是否被改过。
GREEN_DEF = ("全绿 = 层表门新增偏离 0 + 层表门缺失 0 + 部署 sha 全部一致 + 权威核对问题数不劣化")

# 既有脚本固有的写盘副作用登记（只登记，不干预）。`tracked=True` 表示写的是**入库存档**，
# 跑一次回归就会让 `git status` 出现该文件的改动 —— 这是既有脚本的行为，不是本文件造成的。
SIDE_EFFECTS = {
    "layer_gate": [("glossary/evidence/layer-gate.txt", True,
                    "每次运行都重写，且首行是**时间戳** ⇒ 必然产生 1 行 diff（非幂等）"),
                   ("glossary/GLOSSARY.lock", True,
                    "仅 --baseline 时写；本文件从不加 --baseline")],
    "authority": [("glossary/glossary-authority-review.tsv", True,
                   "每次运行都重写；内容是判定的纯函数 ⇒ 库未变时字节一致（实测无 diff）")],
    "naming": [],
    "residual": [],
    "progress": [],
    "deploy": [("pegww2/research/evidence/verify-deploy.txt", True,
                "每次运行都重写；内容由部署态决定 ⇒ 部署未变时字节一致")],
    "launcher": [("work/peg/out/launcher-log.txt", False,
                  "每次运行都重写（Tee 日志）；路径被 .gitignore 覆盖")],
}


# ------------------------------------------------------------------ 检查项登记
class Check:
    """一项既有校验资产：真实命令 + 它的 stdout 解析器 + 门键规则。"""

    def __init__(self, name, title, argv, parser, gates, note="", gate_prefixes=None):
        self.name = name
        self.title = title
        self.argv = argv
        self.parser = parser
        self.gates = gates          # {metric_key: "up" | "down"}，up 表示变大即劣化
        self.gate_prefixes = gate_prefixes or {}   # {键前缀: 规则}，覆盖动态展开出来的键
        self.note = note


def p_layer_gate(t):
    """词库门：提表行数/缺失、偏离总数、相对基线新增偏离、通过标记。"""
    m = {}
    r = re.search(r"词库候选原文 (\d+) 条", t)
    if r:
        m["candidates"] = int(r.group(1))
    r = re.search(r"override 登记 (\d+) 条", t)
    if r:
        m["overrides"] = int(r.group(1))
    miss = 0
    ntbl = 0
    for mm in re.finditer(
            r"^\s+(\S+)\s+行\s+(\d+)\s+本项目层\s+(\d+)\s+跨层\s+(\d+)\s+缺失\s+(\d+)\s*$", t, re.M):
        ntbl += 1
        n = int(mm.group(5))
        miss += n
        m["表[%s].缺失" % mm.group(1)] = n
    m["tables"] = ntbl
    m["missing_total"] = miss
    r = re.search(r"偏离（同原文多译）共 (\d+) 条", t)
    if r:
        m["divergence_total"] = int(r.group(1))
    r = re.search(r"相对基线\*\*新增\*\*的偏离 (\d+) 条", t)
    if r:
        m["new_divergence"] = int(r.group(1))
    m["verdict_pass"] = 1 if "判定：✅ 通过" in t else 0
    return m


def p_authority(t):
    """权威核对：库条目/基准/问题总数 + 各 kind 计数。"""
    m = {}
    r = re.search(r"库条目 (\d+) \| 基准 (\d+) \| 问题 (\d+)", t)
    if r:
        m["rows"] = int(r.group(1))
        m["baseline_rows"] = int(r.group(2))
        m["problems_total"] = int(r.group(3))
    for mm in re.finditer(r"^\s{2}([A-Z][^\[\]\s]{0,23})\s+(\d+)\s*$", t, re.M):
        m["kind[%s]" % mm.group(1)] = int(mm.group(2))
    return m


def p_naming(t):
    """命名校验：核对文件数/槽结构异常数/尺寸变化分布。"""
    m = {}
    r = re.search(r"核对 \.xscn (\d+) 个 · 槽结构异常 (\d+) 个", t)
    if r:
        m["files"] = int(r.group(1))
        m["bad_slots"] = int(r.group(2))
    r = re.search(r"尺寸有变化的文件 (\d+) 个", t)
    if r:
        m["sizediff_files"] = int(r.group(1))
    r = re.search(r"尺寸总变化 ([+-]\d+) B", t)
    if r:
        m["size_delta"] = int(r.group(1))
    m["missing_origin"] = len(re.findall(r"^! 原始侧缺失", t, re.M))
    m["verdict_pass"] = 1 if "结论：槽结构全部一致" in t else 0
    return m


def p_residual(t):
    """残留扫描：按「目录 × 关键词」提取真残留行数。"""
    m = {}
    label = None
    ndir = 0
    total = 0
    for line in t.splitlines():
        mm = re.match(r"^#{10} (.+?)\s+\((.*)\)\s*$", line)
        if mm:
            label = mm.group(1).strip()
            ndir += 1
            continue
        mm = re.match(r"^\s+── ([^：]+)：真残留 (\d+) 行\s*$", line)
        if mm and label:
            n = int(mm.group(2))
            total += n
            m["hits[%s][%s]" % (label, mm.group(1).strip())] = n
    m["dirs"] = ndir
    m["residual_total"] = total
    return m


def p_progress(t):
    """全库进度：L1/L7 台账 + L8 位图 + 各 efile 合计。只记可稳定比对的量。"""
    m = {}
    r = re.search(r"L1 UI 主串\*\*：(\d+) 非空行；[^\n]*?\*\*(\d+) 待译行 / (\d+) 含汉字\*\*", t)
    if r:
        m["l1_lines"] = int(r.group(1))
        m["l1_pending"] = int(r.group(2))
        m["l1_han"] = int(r.group(3))
    r = re.search(r"L7 exe\*\*：md5 `([0-9a-f]+)`；`RT_DIALOG` \*\*(\d+)/(\d+)\*\* 含中文", t)
    if r:
        m["l7_md5"] = r.group(1)
        m["l7_dialog_zh"] = int(r.group(2))
        m["l7_dialog_total"] = int(r.group(3))
    for mm in re.finditer(r"^- (.+?)：(\d+) 份 / (\d+) 种内容\s*$", t, re.M):
        m["l8[%s].份" % mm.group(1)] = int(mm.group(2))
        m["l8[%s].种" % mm.group(1)] = int(mm.group(3))
    r = re.search(r"\*\*合计\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \| \*\*([\d.]+)%\*\* \| "
                  r"\*\*(\d+)\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \| \*\*([\d.]+)%\*\* \| "
                  r"\*\*(\d+)\*\* \| \*\*(\d+)\*\*", t)
    if r:
        m["total_xscn"] = int(r.group(1))
        m["total_xscn_han"] = int(r.group(2))
        m["total_xscn_pct"] = r.group(3)
        m["total_suspect_miss"] = int(r.group(4))
        m["total_txt"] = int(r.group(5))
        m["total_txt_zh"] = int(r.group(6))
        m["total_txt_pct"] = r.group(7)
        m["total_ply"] = int(r.group(8))
        m["total_ply_zh"] = int(r.group(9))
    r = re.search(r"完成（[^）]*）：(\d+) 个 efile", t)
    if r:
        m["done_efiles"] = int(r.group(1))
    return m


def p_deploy(t):
    """部署 sha：逐条三方对齐结果 + 抽查行。"""
    m = {}
    n = ok = 0
    for line in t.splitlines():
        mm = re.match(r"^\s{2}(.+?)\s+(✅|❌)\s+当前=(\S+) 成品=(\S+) 原版=(\S+) 备份文件=(\S+)", line)
        if not mm:
            continue
        n += 1
        if mm.group(2) == "✅":
            ok += 1
        else:
            m["sha_fail[%s]" % mm.group(1).strip()] = 1
    m["items_total"] = n
    m["items_ok"] = ok
    m["not_ok"] = n - ok
    spot = 0
    for line in t.splitlines():
        if re.match(r"^\s+行\d+", line) and "❌" in line:
            spot += 1
    m["spot_fail"] = spot
    m["rowcount_fail"] = len(re.findall(r"^  \S+: 行数 \d+（原版 \d+） ❌", t, re.M))
    m["verdict_pass"] = 1 if "总判定: ✅" in t else 0
    return m


def p_launcher(t):
    """启动器自检：母本 md5、各组站点数、写入并回读条数、终止标记。"""
    m = {}
    r = re.search(r"md5\s+：([0-9a-f]{32})", t)
    if r:
        m["mother_md5"] = r.group(1)
    r = re.search(r"补丁站点：(\d+) 条", t)
    if r:
        m["patch_sites"] = int(r.group(1))
    r = re.search(r"站点表尺寸：(\d+) 条（其中 dx/dy 位置行 (\d+) 条", t)
    if r:
        m["site_table"] = int(r.group(1))
        m["dx_rows"] = int(r.group(2))
    r = re.search(r"UI 记录位移：(\d+) 条 \+ 面板位置 (\d+) 条", t)
    if r:
        m["ui_shift"] = int(r.group(1))
        m["panel_pos"] = int(r.group(2))
    r = re.search(r"布局表右对齐记录：(\d+) 条 × (\d+) word = (\d+) 处", t)
    if r:
        m["align_recs"] = int(r.group(1))
        m["align_writes"] = int(r.group(3))
    r = re.search(r"M 地图面/绘制界：(\d+) 处 (\d+) -> (\d+)", t)
    if r:
        m["map_sites"] = int(r.group(1))
    r = re.search(r"内存补丁完成：(\d+) 条已写入并回读一致", t)
    if r:
        m["patched"] = int(r.group(1))
    m["verify_fail"] = t.count("❌")
    m["selftest_terminated"] = 1 if "selftest：已终止进程" in t else 0
    return m


CHECKS = [
    Check("layer_gate", "层表门", [r"work\glossary\layer_gate.py"], p_layer_gate,
          {"missing_total": "up", "new_divergence": "up", "verdict_pass": "down"},
          "判据在 layer_gate.py；本文件只读它的表行与「相对基线新增」计数",
          {"表[": "up"}),
    Check("authority", "权威核对", [r"work\glossary\audit_authority.py"], p_authority,
          {"problems_total": "up"},
          "各 kind 计数逐键按「变大即劣化」比对；不做任何阈值判断",
          {"kind[": "up"}),
    Check("naming", "命名校验", [r"work\_sync-audit\verify_naming.py"], p_naming,
          {"bad_slots": "up", "missing_origin": "up", "verdict_pass": "down"},
          "槽结构判据全在 verify_naming.py；尺寸变化只记录不判"),
    Check("residual", "残留扫描", [r"work\_sync-audit\residual_scan.py"], p_residual,
          {"residual_total": "up"},
          "逐「目录×关键词」行数按「变多即劣化」比对",
          {"hits[": "up"}),
    Check("progress", "全库进度", [r"work\audit\progress.py"], p_progress,
          {},
          "度量项，无门键：只报告变化，不影响退出码"),
    Check("deploy", "部署 sha", [r"work\pegww2\verify_deploy.py"], p_deploy,
          {"not_ok": "up", "spot_fail": "up", "rowcount_fail": "up", "verdict_pass": "down"},
          "三方 sha 对齐判据全在 verify_deploy.py",
          {"sha_fail[": "up"}),
    Check("launcher", "启动器自检", [r"work\peg\peg_launcher.py", "--w", "1920", "--h", "1080",
                                    "--selftest"], p_launcher,
          {"verify_fail": "up", "patch_sites": "down"},
          "补丁站点数变少 = 打不全；判据在 peg_launcher.py（挂起启动→打补丁→回读→杀死）"),
]

# 重建链：会写权威输入，绝不进默认回归。
REBUILD_CHAIN = [
    (r"work\glossary\ingest_layers.py", "重建层表（写 glossary/layers/*.tsv）"),
    (r"work\glossary\converge_plan.py", "收敛计划（写 glossary/GLOSSARY.lock 等）"),
]
# 每项 gate key 在基线里缺席时的态度：fail-closed（缺席本身算偏离）。
GATE_FAIL_CLOSED = True


# ------------------------------------------------------------------ 运行与取证
def tool_fingerprint(rel):
    """脚本指纹：绝对路径 + sha256 + mtime，用于证明「同一版工具」下前后可比。"""
    ab = os.path.join(ROOT, rel)
    fp = {"path": ab}
    try:
        with open(ab, "rb") as fh:
            fp["sha256"] = hashlib.sha256(fh.read()).hexdigest()
        fp["mtime"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(ab)))
    except OSError as e:
        fp["error"] = str(e)
    return fp


def run_check(c):
    """跑一项既有脚本，原样收 stdout/stderr/退出码，再交给它自己的解析器。"""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    argv = [PY] + [a for a in c.argv]
    t0 = time.time()
    err = None
    rc = None
    so = b""
    se = b""
    try:
        p = subprocess.run(argv, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=DEV_TIMEOUT)
        rc, so, se = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        err = "timeout after %ds" % DEV_TIMEOUT
        so = e.stdout or b""
        se = e.stderr or b""
    except OSError as e:
        err = "%s: %s" % (type(e).__name__, e)
    el = int((time.time() - t0) * 1000)
    so_t = so.decode("utf-8", "replace")
    se_t = se.decode("utf-8", "replace")
    m = {}
    perr = None
    try:
        m = c.parser(so_t)
    except Exception as e:               # 解析器自身出错：记下，不当成检查项的结论
        perr = "%s: %s" % (type(e).__name__, e)
    lines = so_t.splitlines()
    return {
        "title": c.title,
        "cmd": c.argv,
        "exit_code": rc,
        "elapsed_ms": el,
        "metrics": m,
        "stdout_sha256": hashlib.sha256(so).hexdigest(),
        "stdout_lines": len(lines),
        "stdout_tail": lines[-6:],
        "stderr_tail": se_t.splitlines()[-6:],
        "run_error": err,
        "parse_error": perr,
    }


def green_state(res):
    """把任务书定义的「全绿」口径落到基线的三个具体量上（只读数值，不重算判据）。"""
    lg = res.get("layer_gate", {}).get("metrics", {})
    dp = res.get("deploy", {}).get("metrics", {})
    au = res.get("authority", {}).get("metrics", {})
    nd = lg.get("new_divergence")
    miss = lg.get("missing_total")
    nok = dp.get("not_ok")
    prob = au.get("problems_total")
    unmeasured = [n for n, x in (("layer_gate", nd), ("deploy", nok), ("authority", prob))
                  if x is None]
    if unmeasured:
        v = "部分判定（未跑/未给出 %s；已知 新增偏离 %s / 缺失 %s / 部署不一致 %s）" % (
            ",".join(unmeasured), nd, miss, nok)
    elif nd == 0 and miss == 0 and nok == 0:
        v = "全绿（问题数 %s，仅作基线锚点）" % prob
    else:
        v = "非全绿（层表门新增偏离 %s / 缺失 %s / 部署不一致 %s）" % (nd, miss, nok)
    return {"层表门新增偏离": nd, "层表门缺失": miss, "部署sha不一致": nok,
            "权威核对问题数": prob, "verdict": v}


def snapshot(only):
    tools = {}
    for c in only:
        tools[c.name] = tool_fingerprint(c.argv[0])
        tools[c.name]["argv"] = c.argv
    res = {}
    for c in only:
        res[c.name] = run_check(c)
        res[c.name]["side_effects"] = [{"path": p, "tracked": tr, "note": n}
                                       for p, tr, n in SIDE_EFFECTS.get(c.name, [])]
    return tools, res


# ------------------------------------------------------------------ 比对
def compare(base, cur):
    """前后比对：新增 / 消失 / 变化 三种事件，并标注是否命中门键。"""
    ev = []
    for name, c in cur.items():
        b = base.get("checks", {}).get(name)
        gates = {k: v for k, v in c.get("_gates", {}).items()}
        prefs = c.get("_gate_prefixes", {})

        def rule_of(k):
            if k in gates:
                return gates[k]
            for p, r in prefs.items():
                if k.startswith(p):
                    return r
            return None

        if b is None:
            ev.append({"check": name, "kind": "new_check", "key": "-", "base": None,
                       "cur": None, "gate": True,
                       "why": "基线里没有这一项，无法比对（fail-closed）"})
            continue
        if c["exit_code"] != 0:
            ev.append({"check": name, "kind": "exit", "key": "exit_code",
                       "base": b.get("exit_code"), "cur": c["exit_code"], "gate": True,
                       "why": "既有脚本自身判非零"})
        elif b.get("exit_code") not in (0, None) and c["exit_code"] == 0:
            ev.append({"check": name, "kind": "changed", "key": "exit_code",
                       "base": b.get("exit_code"), "cur": 0, "gate": False,
                       "why": "既有脚本由非零转为 0"})
        bm = b.get("metrics", {})
        cm = c["metrics"]
        for k in sorted(set(bm) | set(cm)):
            rule = rule_of(k)
            if k not in bm:
                gate = bool(rule) and _worse(rule, None, cm[k])
                ev.append({"check": name, "kind": "new", "key": k, "base": None,
                           "cur": cm[k], "gate": gate,
                           "why": "基线无此键" + ("，且按门规则已劣化" if gate else "")})
            elif k not in cm:
                gate = bool(rule) and GATE_FAIL_CLOSED
                ev.append({"check": name, "kind": "gone", "key": k, "base": bm[k],
                           "cur": None, "gate": gate,
                           "why": "键消失（门键 fail-closed）" if gate else "键消失"})
            elif bm[k] != cm[k]:
                gate = bool(rule) and _worse(rule, bm[k], cm[k])
                ev.append({"check": name, "kind": "changed", "key": k, "base": bm[k],
                           "cur": cm[k], "gate": gate,
                           "why": "门键 %s 劣化" % rule if gate else "非门键变化，仅报告"})
    return ev


def _worse(rule, b, c):
    """门规则：up=变大即劣化，down=变小即劣化。非数值一律按「不等即劣化」处理。"""
    if rule == "up":
        try:
            return b is None or float(c) > float(b)
        except (TypeError, ValueError):
            return True
    if rule == "down":
        try:
            return b is None or float(c) < float(b)
        except (TypeError, ValueError):
            return True
    return True


# ------------------------------------------------------------------ 输出
def out(s=""):
    """按 stdout 真实编码安全打印：既有脚本的输出里有 ✅❌ 这类 cp936 装不下的字符。"""
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        s.encode(enc)
    except (UnicodeEncodeError, LookupError):
        s = s.encode(enc, "replace").decode(enc, "replace")
    print(s)


def fmt(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        return ("%g" % v)
    return str(v)


def report_md(snap, base, ev, green, took):
    L = []
    L.append("# 汉化工程回归报告")
    L.append("")
    L.append("生成时间：%s ｜ 解释器：%s ｜ 耗时 %.1fs" % (snap["generated_at"], snap["python"], took))
    L.append("")
    L.append("> 本报告不产生判据：所有结论均由既有校验脚本自己给出，本入口只做提取与前后比对。")
    L.append("")
    L.append("## 1. 检查项实测")
    L.append("")
    L.append("| 项 | 真实命令 | 退出码 | 耗时 | 关键量 |")
    L.append("|---|---|---:|---:|---|")
    for name, r in snap["checks"].items():
        keys = sorted(r["metrics"].items())
        brief = " · ".join("%s=%s" % (k, fmt(v)) for k, v in keys[:6])
        if len(keys) > 6:
            brief += " …(共 %d 键)" % len(keys)
        L.append("| %s | `python %s` | %s | %.2fs | %s |"
                 % (name, " ".join(r["cmd"]), fmt(r["exit_code"]), r["elapsed_ms"] / 1000.0, brief))
    L.append("")
    L.append("## 2. 全绿口径（任务书定义）")
    L.append("")
    L.append("口径：%s" % GREEN_DEF)
    L.append("")
    for k, v in green.items():
        L.append("- %s = %s" % (k, fmt(v)))
    L.append("")
    L.append("## 3. 写盘副作用登记（既有脚本固有行为）")
    L.append("")
    any_se = False
    for name, r in snap["checks"].items():
        for se in r["side_effects"]:
            any_se = True
            L.append("- `%s` %s：%s" % (name, se["path"], se["note"]))
    if not any_se:
        L.append("- （无）")
    L.append("")
    L.append("## 4. 与基线比对")
    L.append("")
    if base is None:
        L.append("（本次是基线冻结运行，无对照；`%s`）" % BASELINE)
    else:
        L.append("基线：%s（生成于 %s）" % (BASELINE, base.get("generated_at")))
        L.append("")
        for kind, head in (("new", "新增（基线没有 / 现在出现）"),
                           ("gone", "消失（基线有 / 现在没了）"),
                           ("changed", "变化（两边都有，值不同）")):
            rows = [e for e in ev if e["kind"] == kind]
            L.append("### %s —— %d 条" % (head, len(rows)))
            L.append("")
            if not rows:
                L.append("- （无）")
            else:
                L.append("| 项 | 键 | 基线 | 现在 | 门 | 说明 |")
                L.append("|---|---|---|---|---|---|")
                for e in rows:
                    L.append("| %s | %s | %s | %s | %s | %s |"
                             % (e["check"], e["key"], fmt(e["base"]), fmt(e["cur"]),
                                "偏离" if e["gate"] else "报告", e["why"]))
            L.append("")
    L.append("## 5. 判定")
    L.append("")
    dev = [e for e in ev if e["gate"]]
    L.append("- 新增偏离：**%d 条**" % len(dev))
    L.append("- 退出码：**%d**（非零当且仅当有新增偏离）" % snap["exit_code"])
    L.append("")
    return "\n".join(L)


def list_checks():
    out("本次回归包含的检查项（按依赖序 / 运行序）：")
    for i, c in enumerate(CHECKS, 1):
        gs = "、".join("%s↑" % k if v == "up" else "%s↓" % k for k, v in c.gates.items())
        ps = "、".join("%s*↑" % k if v == "up" else "%s*↓" % k for k, v in c.gate_prefixes.items())
        allg = "、".join(x for x in (gs, ps) if x) or "（无门键）"
        out("  %d. %-10s %-8s python %s" % (i, c.name, c.title, " ".join(c.argv)))
        out("     门键：%s" % allg)
        out("     %s" % c.note)
    out("")
    out("不在默认回归（会写权威输入，需显式 rebuild）：")
    for rel, why in REBUILD_CHAIN:
        out("  * python %s   —— %s" % (rel, why))


# ------------------------------------------------------------------ 入口
def main():
    ap = argparse.ArgumentParser(
        prog="regression.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="汉化工程统一回归入口：编排既有校验脚本，输出机器可比的前后对照。",
        epilog=("模式：\n"
                "  check          默认。跑全部检查并与基线比对（也可 --only 单跑）\n"
                "  rebuild        显式重建链 ingest_layers.py -> converge_plan.py（会写盘）\n"
                "\n"
                "退出码：0 无新增偏离 ｜ 1 出现新增偏离 ｜ 2 用法或基线问题\n"))
    ap.add_argument("mode", nargs="?", default="check", choices=["check", "rebuild"],
                    help="子命令（默认 check）")
    ap.add_argument("--save-baseline", action="store_true",
                    help="跑全部检查并把结果冻结为 %s" % BASELINE)
    ap.add_argument("--only", action="append", default=[], metavar="NAME",
                    help="只跑指定项（可重复或逗号分隔）；用 --list 查名字")
    ap.add_argument("--list", action="store_true", help="列出检查项、真实命令与门键后退出")
    ap.add_argument("--json", action="store_true",
                    help="机器可读结果打到 stdout（ensure_ascii，纯 ASCII）")
    ap.add_argument("--baseline", default=BASELINE, metavar="PATH", help="基线文件路径")
    ap.add_argument("--yes", action="store_true", help="rebuild 模式下真正执行（默认只打印）")
    a = ap.parse_args()

    if a.list:
        list_checks()
        return 0

    if a.mode == "rebuild":
        out("重建链（会写盘，故不进默认回归）：")
        for rel, why in REBUILD_CHAIN:
            out("  python %s   —— %s" % (rel, why))
        if not a.yes:
            out("")
            out("（dry-run；确认后加 --yes 执行）")
            return 0
        for rel, why in REBUILD_CHAIN:
            out("")
            out(">>> python %s  # %s" % (rel, why))
            t0 = time.time()
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"
            rc = subprocess.run([PY, rel], cwd=ROOT, env=env).returncode
            out("<<< 退出码 %d，耗时 %.1fs" % (rc, time.time() - t0))
            if rc != 0:
                return 1
        return 0

    names = []
    for x in a.only:
        names += [s.strip() for s in x.split(",") if s.strip()]
    known = {c.name: c for c in CHECKS}
    if names:
        bad = [n for n in names if n not in known]
        if bad:
            out("未知检查项：%s（可用：%s）" % (", ".join(bad), ", ".join(known)))
            return 2
        only = [known[n] for n in names]
    else:
        only = list(CHECKS)

    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    tools, res = snapshot(only)
    base = None
    if os.path.isfile(a.baseline):
        try:
            with open(a.baseline, encoding="utf-8") as fh:
                base = json.load(fh)
        except (OSError, ValueError) as e:
            out("基线读取失败：%s（%s）" % (a.baseline, e))
            return 2

    snap = {
        "schema": SCHEMA,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "generated_at_unix": int(time.time()),
        "python": sys.version.split()[0],
        "python_full": sys.version.replace("\n", " "),
        "platform": sys.platform,
        "cwd": ROOT,
        "green_definition": GREEN_DEF,
        "tools": tools,
        "checks": res,
    }
    for c in only:
        res[c.name]["_gates"] = dict(c.gates)
        res[c.name]["_gate_prefixes"] = dict(c.gate_prefixes)
    ev = compare(base, res) if base else []
    for r in res.values():
        r.pop("_gates", None)
        r.pop("_gate_prefixes", None)
    dev = [e for e in ev if e["gate"]]
    snap["exit_code"] = 1 if dev else 0
    snap["green"] = green_state(res)
    if a.save_baseline:
        snap["exit_code"] = 0          # 冻结基线没有「新增偏离」概念
        keep = {"schema": "regression-report/v1", "baseline_written": a.baseline,
                "generated_at": snap["generated_at"], "exit_code": 0,
                "green": snap["green"],
                "checks": {k: {"exit_code": v["exit_code"], "elapsed_ms": v["elapsed_ms"],
                               "metrics": v["metrics"]} for k, v in res.items()}}
        with open(a.baseline, "w", encoding="utf-8") as fh:
            json.dump(snap, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        art = json.dumps(keep, ensure_ascii=False, indent=1)
    else:
        art = json.dumps(snap, ensure_ascii=False, indent=1)

    took = time.time() - t0
    day = time.strftime("%Y-%m-%d")
    md = report_md(snap, base, ev, snap["green"], took)
    for path, body in ((os.path.join(OUT, "regression-%s.md" % day), md),
                       (os.path.join(OUT, "regression-%s.json" % day), art)):
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(body if body.endswith("\n") else body + "\n")
        except OSError as e:
            out("产物写入失败 %s：%s" % (path, e))

    if a.json:
        print(json.dumps({"schema": "regression-report/v1",
                          "generated_at": snap["generated_at"],
                          "baseline": a.baseline if base else None,
                          "exit_code": snap["exit_code"],
                          "green": snap["green"],
                          "checks": {k: {"exit_code": v["exit_code"],
                                         "elapsed_ms": v["elapsed_ms"],
                                         "metrics": v["metrics"],
                                         "run_error": v["run_error"],
                                         "parse_error": v["parse_error"]}
                                     for k, v in res.items()},
                          "events": ev,
                          "deviations": dev}, ensure_ascii=True, indent=1))
        return snap["exit_code"]

    out("=" * 78)
    out("汉化工程统一回归入口  " + snap["generated_at"])
    out("=" * 78)
    out("")
    for name, r in res.items():
        out("  %-10s %-8s 退出码 %-3s %6.2fs  键 %2d  %s"
            % (name, r["title"], fmt(r["exit_code"]), r["elapsed_ms"] / 1000.0,
               len(r["metrics"]), r["cmd"][0]))
        if r["run_error"]:
            out("            ⚠ 运行错误：%s" % r["run_error"])
        if r["parse_error"]:
            out("            ⚠ 解析错误：%s" % r["parse_error"])
        if r["exit_code"] not in (0, None) and r["stderr_tail"]:
            out("            stderr 尾：%s" % r["stderr_tail"][-1][:160])
    out("")
    out("全绿口径：%s" % GREEN_DEF)
    for k, v in snap["green"].items():
        out("  %s = %s" % (k, fmt(v)))
    out("")
    seen = False
    for name, r in res.items():
        for se in r["side_effects"]:
            if not seen:
                out("写盘副作用（既有脚本固有行为）：")
                seen = True
            out("  · %s → %s" % (name, se["path"]))
    if seen:
        out("")
    if base is None:
        out("（未找到基线 %s ⇒ 只报告，不判新增）" % a.baseline)
    else:
        tag = "旧基线（本次已被新基线覆盖，此行仅供对照）" if a.save_baseline else "基线"
        out("%s：%s（生成于 %s）" % (tag, a.baseline, base.get("generated_at")))
        for kind, head in (("new", "新增"), ("gone", "消失"), ("changed", "变化")):
            rows = [e for e in ev if e["kind"] == kind]
            out("  %s %d 条%s" % (head, len(rows), "：" if rows else ""))
            for e in rows[:20]:
                out("      [%s] %s %s: %s → %s  （%s）"
                    % ("偏离" if e["gate"] else "报告", e["check"], e["key"],
                       fmt(e["base"]), fmt(e["cur"]), e["why"]))
            if len(rows) > 20:
                out("      …另 %d 条（见 work\\out\\regression-%s.md）" % (len(rows) - 20,
                                                                        time.strftime("%Y-%m-%d")))
    out("")
    out("判定：新增偏离 %d 条 ⇒ 退出码 %d" % (len(dev), snap["exit_code"]))
    out("产物：work\\out\\regression-%s.md / .json" % day)
    return snap["exit_code"]


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
