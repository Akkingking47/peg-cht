# -*- coding: utf-8 -*-
"""生成器「命中来源」溯源共享库 —— docs\\68 模块 D · 建议 **D-1**。

问题（docs\\49 教训；docs\\47 曾把它误判成「词库滞后于成品」）：生成器
「查表 → 写盘」不留痕，成品与真源一旦对不上就只能猜，**「成品对而真源错」的倒挂
极难发现**。本库给每个生成器一个**缺省关闭**的开关：打开后，每产出一个成品文件，
就在它旁边写一份 sidecar `<成品文件>.lineage.tsv`，**逐行**回答
「这行成品来自哪张表、表内第几行、哪个键」。

用法：
  1) 命令行（各生成器统一，参数顺序无关）：
       python <生成器>.py <原参数>                    # 缺省：一行溯源代码都不执行
       python <生成器>.py <原参数> --lineage           # sidecar 写在成品同级
       python <生成器>.py <原参数> --lineage=DIR       # sidecar 集中到 DIR，按成品相对路径镜像
  2) 代码（**最外层注入**，不动生成器原有的查表 / 写盘逻辑）：
       import sys; sys.path.insert(0, <work 目录>)
       from lineage import parse_argv, rel, want_help
       ...
       lin, rest = parse_argv(sys.argv)     # 未给 `--lineage` ⇒ lin is None
       ...
       if lin is not None:
           with lin.open(product_path, root=OUTDIR) as lg:
               lg.record(out_line, key, src_table, src_line, src_kind)   # out_line 从 1 计
           # 出 with 时自动补 `# agg` 聚合行

sidecar 格式（制表符分隔，UTF-8，LF 行尾）：
    # lineage v1<TAB>script=<脚本名><TAB>generated=<ISO8601><TAB>commit=<git rev-parse --short HEAD>
    out_line<TAB>key<TAB>src_table<TAB>src_line<TAB>src_kind
    ...
    # agg<TAB><表名><TAB><hit数>      ← 按命中数降序；只统计真正命中过表的行（src_table≠"-"）

`src_kind` 取值（全库统一词表，不得自造）：
    exact     整行 / 整串**精确**命中某张表
    prefix    以**前缀·子串**方式命中（行内嵌入替换等宽松匹配）
    override  命中**覆盖层**（per-file 行级覆盖 / 按场景定点覆盖），优先于全局表
    fallback  主表未命中，经**降级路径**命中次级表
    identity  命中「**保留原文**」语义（译法即原文 / 政策 KEEP）
    none      **无来源**（未命中任何表；空行 / 不可解码行 / 整文件跳过）

各生成器对这套词表的具体落法（读 sidecar 时的对照表）：
    work/peg/gen_scn_zh.py
        长段整行 / 映射表整行 ⇒ exact；行内嵌入替换 ⇒ prefix；按场景定点覆盖 ⇒ override；
        场景序号前缀（原行无文本来源时）⇒ override；未命中 / 空行 / 硬拷文件 ⇒ none
    work/pegww2/gen_scn.py
        ww2-scn-map.tsv 整串命中 ⇒ exact；per-file 行级覆盖 / 按场景定点覆盖 ⇒ override；
        命中但「保留原文」（来源列=保留 或 译文与原文同字节）⇒ identity；无表项 ⇒ none
    work/glossary/build_glossary.py
        多数票胜出的中文译名 ⇒ exact；政策 KEEP（原样保留）⇒ identity；无中文来源 ⇒ identity
    work/pegww2/build_glossary_unified.py
        本层唯一条目 ⇒ exact；同 en 多译法时按层优先级压过他层 ⇒ override；译法即原文 ⇒ identity

⚠️ 硬约束：`--lineage` 缺省关闭；关闭时生成器不得进入任何溯源分支，产物 sha256
   必须与加溯源前**逐字节相同**（各生成器的注入点与实测见回报 / docs\\69）。
⚠️ `src_table` 一律用**工作区相对 POSIX 路径**（跨机器可比）；`src_line` 为表内
   **1 起行号**（该来源没有行号概念时为 0，此时靠 `key` 定位）。
⚠️ 写盘用 UTF-8 + LF；`key` / `src_table` 里的 TAB / CR / LF 会被换成空格（防撕列）。
"""
import collections
import contextlib
import datetime
import os
import subprocess
import sys

LINEAGE_VERSION = "v1"
KINDS = ("exact", "prefix", "override", "fallback", "identity", "none")
SIDECAR_SUFFIX = ".lineage.tsv"
COLUMNS = ("out_line", "key", "src_table", "src_line", "src_kind")

# 工作区根：本文件位于 <ws>/work/lineage.py
WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rel(path, ws=None):
    """绝对路径 → 工作区相对 POSIX 路径（不在工作区内则原样正斜杠化）。"""
    ap = os.path.abspath(path)
    try:
        r = os.path.relpath(ap, os.path.abspath(ws or WS))
    except ValueError:                      # 跨盘符：os.path.relpath 会抛
        return ap.replace("\\", "/")
    return ap.replace("\\", "/") if r.startswith("..") else r.replace("\\", "/")


def want_help(argv):
    """argv 是否请求帮助（`-h` / `--help`）。生成器据此打印 __doc__ 后退出。"""
    return any(a in ("-h", "--help") for a in argv[1:])


def show_help(doc):
    """`--help` 打印模块 docstring，容忍 Windows 控制台编码。

    ⚠️ 本机 stdout 是 GBK，而本工作区文档里有 `⇒` / `⭐` / `↔` 等 **GBK 编不出**的字符，
       直接 `print(__doc__)` 会 `UnicodeEncodeError`（`gen_scn.py` 等三个脚本的
       docstring 里本来就有 `⇒`）⇒ 这里先试编，编不出就按该编码替换成 `?`。
    ⚠️ `_Tee` 这类包装流没有 `encoding` 属性 ⇒ 保守按 GBK 试（宁可少几个符号，不可崩）。
    """
    enc = getattr(sys.stdout, "encoding", None) or "gbk"
    try:
        doc.encode(enc)
    except (UnicodeEncodeError, LookupError):
        doc = doc.encode(enc, "replace").decode(enc, "replace")
    sys.stdout.write(doc if doc.endswith("\n") else doc + "\n")
    sys.stdout.flush()


def _git_head(ws):
    """`git rev-parse --short HEAD`；取不到（无 git / 非仓库）时返回 `unknown`。"""
    try:
        r = subprocess.run(["git", "-C", ws, "rev-parse", "--short", "HEAD"],
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=15)
        if r.returncode == 0:
            return r.stdout.decode("ascii", "replace").strip()
    except Exception:
        pass
    return "unknown"


def _cell(x):
    """TSV 单元格消毒：TAB / CR / LF 会把裸 TSV 撕开（读取方一律 split('\\t')）。"""
    return str(x).replace("\t", " ").replace("\r", " ").replace("\n", " ")


_IDX = {}


def table_key_line(path, key, keycol=0):
    """在 TSV 里按第 `keycol` 列**精确相等**查 `key` 的 1 起行号；查不到返回 0。

    注释行（`#` 起头）与空行不参与索引；同一张表只扫一次（结果缓存）。
    用途：生成器内部只留下「来源文件名」而没记行号时，用它补出表内行号。
    """
    idx = _IDX.get(path)
    if idx is None:
        idx = {}
        try:
            with open(path, encoding="utf-8-sig", errors="replace") as f:
                for ln, raw in enumerate(f, 1):
                    s = raw.rstrip("\r\n")
                    if not s.strip() or s.lstrip().startswith("#"):
                        continue
                    c = s.split("\t")
                    if len(c) > keycol and c[keycol] not in idx:
                        idx[c[keycol]] = ln
        except OSError:
            pass
        _IDX[path] = idx
    return idx.get(key, 0)


class _Sink:
    """单个 sidecar 的写入器（由 Lineage.open() 交出；不要自己 new）。"""

    def __init__(self, fh, stat):
        self._fh = fh
        self._stat = stat        # Counter: src_table → 命中行数

    def record(self, out_line, key, src_table, src_line, src_kind):
        """记一行成品的命中来源。`out_line` 是**成品文件内的 1 起行号**。"""
        if src_kind not in KINDS:
            raise ValueError("未知 src_kind %r（取值：%s）" % (src_kind, "/".join(KINDS)))
        t = _cell(src_table) or "-"
        self._fh.write("%d\t%s\t%s\t%d\t%s\n"
                       % (int(out_line), _cell(key), t, int(src_line or 0), src_kind))
        if t != "-":
            self._stat[t] += 1

    def close(self):
        if self._fh is None:
            return
        for t, n in sorted(self._stat.items(), key=lambda kv: (-kv[1], kv[0])):
            self._fh.write("# agg\t%s\t%d\n" % (t, n))
        self._fh.close()
        self._fh = None


class Lineage:
    """一次运行的溯源会话：一个成品文件 = 一份 sidecar。"""

    def __init__(self, base=None, script=None, ws=None):
        self.base = base or None                 # None ⇒ 写在成品同级
        self.script = script or os.path.basename(sys.argv[0] or "?")
        self.ws = ws or WS
        self.commit = _git_head(self.ws)
        self.generated = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        self.files = 0

    def sidecar(self, product, root=None):
        """算出 sidecar 路径（不建文件）。给了 `root` 就按成品相对 root 的路径镜像。"""
        if not self.base:
            return os.path.abspath(product) + SIDECAR_SUFFIX
        if root:
            p = os.path.relpath(os.path.abspath(product), os.path.abspath(root))
            if p.startswith(".."):
                p = os.path.basename(product)
        else:
            p = os.path.basename(product)
        return os.path.join(self.base, p + SIDECAR_SUFFIX)

    @contextlib.contextmanager
    def open(self, product, root=None):
        """开一份 sidecar，交出 `_Sink`；出 with 时自动补 `# agg` 并关闭。"""
        path = self.sidecar(product, root)
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        fh = open(path, "w", encoding="utf-8", newline="\n")
        fh.write("# lineage %s\tscript=%s\tgenerated=%s\tcommit=%s\n"
                 % (LINEAGE_VERSION, _cell(self.script), self.generated, self.commit))
        fh.write("\t".join(COLUMNS) + "\n")
        sink = _Sink(fh, collections.Counter())
        self.files += 1
        try:
            yield sink
        finally:
            sink.close()


def parse_argv(argv, ws=None, script=None):
    """摘出 `--lineage[=DIR]`，返回 `(Lineage 或 None, 其余参数)`。

    未出现该开关 ⇒ 返回 `(None, argv)`：调用方必须走**完全不知道溯源存在**的旧路径。
    """
    base, on = None, False
    rest = [argv[0]] if argv else []
    for a in (argv[1:] if argv else []):
        if a == "--lineage":
            on = True
        elif a.startswith("--lineage="):
            on = True
            base = a.split("=", 1)[1] or None
        else:
            rest.append(a)
    if not on:
        return None, list(argv)
    return Lineage(base=base, script=script, ws=ws), rest
