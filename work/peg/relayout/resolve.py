# -*- coding: utf-8 -*-
"""PeG030 重排版 —— 站点解析器（把设计空间的 800x600 值算成目标分辨率下的字节）

输入：`sites.tsv`（子代理 A 从 work\\peg\\peg_launcher.py 结构化而来）；表头
      va_hex  size  group  class  rule  params  old_hex  new_hex  label
输出：一批准补丁 (va, old_bytes, new_bytes, note)，交给 apply.py 沿用
      "挂起 + 写内存 + 回读校验" 的方式落地（母本 exe 一字节不改）。

rule 语法（params 用 `k=v` 逗号分隔）：
  fixed                        原值不动（校验用）
  const:<int>                 直接写常量
  scale_center                设计空间坐标 -> center 模式（axis=x|y，可选）
  anchor_right_scale          -> right/bottom 模式
  scale_origin                -> scale 模式
  stretch                     -> stretch 模式
  scale_len                   把原值当长度：scaled_len(v)
  surface_cap:<int>           max(原值, int)：画布/后台面宽度上限提升
  clamp_max                   上限改成目标轴像素（axis=x -> W，axis=y -> H）
  pair800_600                 4 字节记录 (x,y) 两个 word 分别变换（axis 默认 x,y）
  add_scaled:<int>            原值 + scaled_len(int)（右对齐条宽等）

编码：size=1/2/4 字节；signed=true/false（默认按 size 推断：2/4 字节按有符号，
      数值 >= 2^(bits-1) 时自动按无符号处理）。
代码站点：如果 new_hex 已是"人工写好的目标字节"，本模块只负责**校验**它是否
      与新模型一致（`legacy_mismatch`），并在可能时用 `rewrite_immediate` 就地
      把立即数换成新算出的值。
"""
from __future__ import annotations

import importlib.util
import os
import struct
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from layout_model import Layout, rp  # noqa: E402

DATA_LO = 0x400000 + 0x8A136  # .text 结束之后（.rdata 起）都算数据面
SITES_TSV = os.path.join(_HERE, "sites.tsv")

HEADER = ["va_hex", "size", "group", "class", "rule", "params", "old_hex", "new_hex", "label"]


class Site:
    __slots__ = HEADER

    def __init__(self, **kw):
        for k in HEADER:
            setattr(self, k, kw.get(k, ""))

    @property
    def va(self) -> int:
        return int(self.va_hex, 16)

    @property
    def size_i(self) -> int:
        return int(self.size or 0)

    @property
    def is_data(self) -> bool:
        return self.va >= DATA_LO

    def pat(self) -> dict:
        out = {}
        for kv in (self.params or "").split(","):
            kv = kv.strip()
            if not kv:
                continue
            k, _, v = kv.partition("=")
            out[k.strip()] = v.strip()
        return out

    def old_bytes(self) -> bytes:
        return bytes.fromhex(self.old_hex)

    def new_bytes(self) -> bytes:
        return bytes.fromhex(self.new_hex) if self.new_hex else b""

    def __repr__(self) -> str:
        return "<Site %s %s %s %s>" % (self.va_hex, self.size, self.rule, self.label)


class Resolved:
    __slots__ = ("site", "va", "old", "new", "note", "status")

    def __init__(self, site, old, new, note, status="ok"):
        self.site = site
        self.va = site.va
        self.old = old
        self.new = new
        self.note = note
        self.status = status

    def __repr__(self) -> str:
        return "<Resolved %06X %s %s %s>" % (self.va, self.status, self.new.hex(), self.note)


def load_sites(path: str = SITES_TSV) -> list:
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        head = None
        for raw in fh:
            line = raw.rstrip("\r\n")
            if not line.strip():
                continue
            cols = line.split("\t")
            if head is None:
                head = [c.strip() for c in cols]
                if head[0] != "va_hex":  # 不是表头就当成数据行，用默认表头
                    head = HEADER
                else:
                    continue
            rows.append(Site(**{head[i]: (cols[i] if i < len(cols) else "") for i in range(len(head))}))
    return rows


# ------------------------------------------------------------------ 编解码
def decode_int(b: bytes, signed: bool | None = None) -> int:
    n = len(b)
    if signed is None:
        v = int.from_bytes(b, "little")
        signed = v >= (1 << (8 * n - 1))  # 看着像负数就当有符号
    return int.from_bytes(b, "little", signed=bool(signed))


def encode_int(v: int, size: int) -> bytes:
    lo = -(1 << (8 * size - 1))
    hi = (1 << (8 * size)) - 1
    if not (lo <= v <= hi):
        raise ValueError("值 %d 超出 %d 字节范围" % (v, size))
    if v < 0:
        return v.to_bytes(size, "little", signed=True)
    if v >= (1 << (8 * size - 1)):
        return v.to_bytes(size, "little", signed=False)
    return v.to_bytes(size, "little", signed=True)


def rewrite_immediate(code: bytes, old: int, new: int, size: int) -> bytes:
    """在指令字节里把 old 的立即数就地换成 new（要求唯一匹配、同宽）。"""
    pat = encode_int(old, size)
    hits = []
    start = 0
    while True:
        i = code.find(pat, start)
        if i < 0:
            break
        hits.append(i)
        start = i + 1
    if len(hits) != 1:
        raise ValueError("立即数 %s 在指令里出现 %d 次，无法安全替换：%s" % (pat.hex(), len(hits), code.hex()))
    i = hits[0]
    return code[:i] + encode_int(new, size) + code[i + size:]


# ------------------------------------------------------------------ 规则
def _axis_of(site, default_x="x", default_y="y"):
    p = site.pat()
    ax = p.get("axis")
    if ax:
        return ax
    return default_y if site.size_i == 2 and p.get("pair") == "second" else default_x


def resolve_site(site: Site, layout: Layout, verify_legacy: bool = True) -> Resolved:
    old_b = site.old_bytes()
    rule = (site.rule or "fixed").split(":")[0].strip()
    arg = (site.rule or "").split(":", 1)[1].strip() if ":" in (site.rule or "") else ""
    p = site.pat()
    axis = p.get("axis", "x")
    isz = int(p.get("imm_size", site.size_i) or len(old_b))
    if site.is_data:
        v = decode_int(old_b)
    else:
        v = int(p["v"], 0) if p.get("v") else None
    note = ""
    newv = None

    if rule == "fixed":
        newv = v if v is not None else 0
        note = "原值不动"
    elif rule == "const":
        newv = int(arg or p.get("value", "0"), 0)
        note = "写常量 %d" % newv
    elif v is None:
        return Resolved(site, old_b, old_b, "代码站点缺 params v=<设计空间原值>", status="skip")
    elif rule == "scale_len":
        newv = layout.scaled_len(v)
        note = "长度 %d -> %d (x%.2f)" % (v, newv, layout.s)
    elif rule == "scale_center":
        newv = layout.x(v) if axis == "x" else layout.y(v)
        note = "center %s: %d -> %d" % (axis, v, newv)
    elif rule == "anchor_right_scale":
        newv = layout.x(v, "right") if axis == "x" else layout.y(v, "bottom")
        note = "%s锚定: %d -> %d" % (axis, v, newv)
    elif rule == "scale_origin":
        newv = int(rp(v * layout.s))
        note = "origin 缩放: %d -> %d" % (v, newv)
    elif rule == "stretch":
        newv = layout.x(v, "stretch") if axis == "x" else layout.y(v, "stretch")
        note = "整轴拉伸 %s: %d -> %d" % (axis, v, newv)
    elif rule == "surface_cap":
        cap = int(arg or p.get("cap", "4096"), 0)
        newv = max(v, cap)
        note = "面宽/缓冲上限 max(%d,%d)" % (v, cap)
    elif rule == "clamp_max":
        newv = layout.W if axis == "x" else layout.H
        note = "上限 -> %s=%d" % (axis.upper(), newv)
    elif rule == "add_scaled":
        newv = v + layout.scaled_len(int(arg, 0))
        note = "原值 + scaled(%s)" % arg
    elif rule == "pair800_600":
        f = p.get("field", "x")
        newv = layout.x(v) if f == "x" else layout.y(v)
        note = "800/600 记录字段 %s: %d -> %d" % (f, v, newv)
    else:
        return Resolved(site, old_b, old_b, "未知 rule %r，跳过" % site.rule, status="skip")

    # ---- 代码站点：old_hex/new_hex 是"整条指令"，old_hex 里含设计空间立即数
    if not site.is_data:
        legacy = site.new_bytes()
        off = None
        try:
            off = old_b.find(encode_int(v, isz))
            if off < 0:
                off = None
        except ValueError:
            off = None
        if p.get("imm") == "1" and off is not None:
            try:
                new_b = rewrite_immediate(old_b, v, newv, isz)
                note += "；就地替换立即数"
                return Resolved(site, old_b, new_b, note, status="ok")
            except ValueError as exc:
                note += "；%s" % exc
        new_b = legacy or old_b
        status = "manual"
        note += "；代码站点保留人工字节（模型预测 %d）" % newv
        if verify_legacy and legacy and off is not None and len(legacy) >= off + isz:
            lv = decode_int(legacy[off:off + isz])
            if lv != newv:
                status = "legacy_mismatch"
                note += "；人工值 %d != 模型 %d" % (lv, newv)
        return Resolved(site, old_b, new_b, note, status=status)

    if newv is None:
        return Resolved(site, old_b, old_b, "规则未产出新值", status="skip")

    try:
        new_b = encode_int(newv, site.size_i or len(old_b))
    except ValueError as exc:
        return Resolved(site, old_b, old_b, str(exc), status="error")

    status = "ok"
    if rule == "fixed" and site.new_bytes() and site.new_bytes() != old_b:
        # 标注为 fixed 但人工改了字节 -> 说明分类有问题
        status = "clash_fixed"
        note += "；但站点表里有手工新字节 %s" % site.new_hex

    return Resolved(site, old_b, new_b, note, status=status)


def resolve_all(sites, layout: Layout) -> list:
    return [resolve_site(s, layout) for s in sites]


# ------------------------------------------------------------------ 数据表展开
TABLES_TSV = os.path.join(_HERE, "tables.tsv")


class TableRow:
    __slots__ = ("name", "base_va", "record_size", "count", "fields", "cls", "evidence")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k, ""))

    def field_list(self):
        """'x1@+0x00,y1@+0x02' -> [('x1', 0), ('y1', 2)]（只取能解析的 name@+0xNN）"""
        out = []
        for part in (self.fields or "").replace("（", "(").split(","):
            part = part.strip()
            if "@" not in part:
                continue
            name, _, rest = part.partition("@")
            rest = rest.split("(")[0].strip().lstrip("+")
            name = name.strip().strip("?")
            try:
                off = int(rest, 16) if rest.lower().startswith("0x") else int(rest, 0)
            except ValueError:
                continue
            out.append((name, off))
        return out

    def __repr__(self):
        return "<TableRow %s base=%s rec=%s count=%s>" % (
            self.name, self.base_va, self.record_size, self.count)


def load_tables(path: str = TABLES_TSV) -> list:
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        head = None
        for raw in fh:
            line = raw.rstrip("\r\n")
            if not line.strip():
                continue
            cols = line.split("\t")
            if head is None:
                head = [c.strip() for c in cols]
                if head[0] == "name":
                    continue
                head = ["name", "base_va", "record_size", "count", "fields", "class", "evidence"]
            rows.append(TableRow(**{head[i]: (cols[i] if i < len(cols) else "") for i in range(len(head))}))
    return rows


def expand_layout_table(base_va: int, rec_size: int, count: int, fields, layout: Layout,
                        mode=None, image_path=None, label_prefix="layout"):
    """把"控件矩形表"里的矩形字段展开成待写条目。

    fields: [(name, off)]，name 以 x/y 开头决定轴；mode 缺省一律 center。
    old 字节从母本镜像读取（.data 已初始化，文件里的就是原值）。
    只处理落在设计空间（含少量负内缩）内的值；越界的记录跳过并计数。
    """
    import image as _img
    entries = []
    skipped = []
    for idx in range(count):
        va = base_va + idx * rec_size
        vals = []
        ok = True
        for name, off in fields:
            v = decode_int(_img.read_va(va + off, 2, image_path) if image_path
                           else _img.read_va(va + off, 2))
            lo, hi = (-64, 864) if name[0] == "x" else (-64, 664)
            if not (lo <= v <= hi):
                ok = False
                skipped.append((idx, name, v))
            vals.append(v)
        if not ok:
            continue          # 整条记录都不可信：不碰
        for (name, off), v in zip(fields, vals):
            m = mode or "center"
            newv = layout.x(v, m) if name[0] == "x" else layout.y(v, m)
            if newv == v:
                continue
            entries.append({
                "va": va + off, "size": 2,
                "old": encode_int(v, 2), "new": encode_int(newv, 2),
                "label": "%s[%d].%s %d->%d" % (label_prefix, idx, name, v, newv),
            })
    return entries, skipped


def relayout_plan(w: int, h: int, strategy: str = "S2", tables_path: str = TABLES_TSV,
                  image_path: str = None, ctrl_table_name="layout_records_0x4A96E8"):
    """P1 主计划：把控件矩形表（0x4A96E8，272×15B）按新模型重排。返回 (entries, notes)。"""
    layout = Layout(w, h, strategy)
    notes = ["重排版 %dx%d（%s）：%s" % (w, h, strategy, layout.describe())]
    rows = load_tables(tables_path)
    target = None
    for r in rows:
        if r.name == ctrl_table_name:
            target = r
            break
    if target is None:
        raise SystemExit("找不到表 %r 于 %s" % (ctrl_table_name, tables_path))
    fields = target.field_list()
    if not fields:
        fields = [("x1", 0x00), ("y1", 0x02), ("x2", 0x04), ("y2", 0x06)]
    count = int(target.count or 0)
    rec = int(target.record_size or 15)
    base = int(target.base_va, 16)
    entries, skipped = expand_layout_table(base, rec, count, fields, layout,
                                          image_path=image_path, label_prefix="ctrl")
    notes.append("  控件矩形表 %s：%d 条 × %d 字段 = %d 条站点（规格 %s）" % (
        target.base_va, count, len(fields), len(entries),
        ",".join("%s@+%#x" % (n, o) for n, o in fields)))
    if skipped:
        notes.append("  越界跳过 %d 个字段（不在设计空间内，多半不是矩形），例如 %s" % (
            len(skipped), ", ".join("[%d].%s=%d" % s for s in skipped[:5])))
    return entries, notes


# ------------------------------------------------------------------ 自检
def _selftest() -> int:
    L = Layout(1920, 1080, "S2")

    def S(va, size, rule, old, params="", label="t", new=""):
        return Site(va_hex="%06X" % va, size=str(size), group="T", **{"class": "Lx"},
                    rule=rule, params=params, old_hex=old.hex(), new_hex=new, label=label)

    # 数据面：布局记录字段重排
    r = resolve_site(S(0x4947F0, 2, "scale_center", (336).to_bytes(2, "little", signed=True)), L)
    assert r.new == (845).to_bytes(2, "little", signed=True), r
    assert r.status == "ok", r

    r = resolve_site(S(0x4947F0, 2, "scale_center", (701).to_bytes(2, "little", signed=True), "axis=x"), L)
    assert r.new == (1502).to_bytes(2, "little", signed=True), r

    r = resolve_site(S(0x4947F0, 2, "anchor_right_scale", (701).to_bytes(2, "little", signed=True)), L)
    assert r.new == (1742).to_bytes(2, "little", signed=True), r

    r = resolve_site(S(0x4947F0, 4, "surface_cap:4096", (1920).to_bytes(4, "little")), L)
    assert r.new == (4096).to_bytes(4, "little"), r

    r = resolve_site(S(0x4947F0, 2, "clamp_max", (799).to_bytes(2, "little")), L)
    assert r.new == (1920).to_bytes(2, "little", signed=False), r.new.hex()

    r = resolve_site(S(0x4947F0, 4, "stretch", (600).to_bytes(4, "little"), "axis=y"), L)
    assert r.new == (1080).to_bytes(4, "little"), r

    # 代码站点：old_hex/new_hex 是整条指令，old_hex 内含设计空间立即数
    ins_old = bytes.fromhex("0fb706" + "3d" + (800).to_bytes(2, "little").hex() + "0000")   # cmp eax,0x320
    r = resolve_site(S(0x412345, 2, "scale_center", ins_old, "imm=1,v=800"), L)
    want = "0fb706" + "3d" + (1680).to_bytes(2, "little").hex() + "0000"
    assert r.status == "ok" and r.new.hex() == want, (r.status, r.new.hex(), want)

    # 人工字节与新模型不一致 -> legacy_mismatch（旧方案把它写成 1920）
    ins_new = bytes.fromhex("0fb706" + "3d" + (1920).to_bytes(2, "little").hex() + "0000")
    r = resolve_site(S(0x412345, 2, "scale_center", ins_old, "v=800", new=ins_new.hex()), L)
    assert r.status == "legacy_mismatch", (r.status, r.note)
    print("resolve.py SELFTEST OK")
    return 0


def main(argv) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="重排版解析器：算站点 / 出报告")
    ap.add_argument("--w", type=int, default=1920)
    ap.add_argument("--h", type=int, default=1080)
    ap.add_argument("--strategy", default="S2", choices=["S1", "S2"])
    ap.add_argument("--report", action="store_true", help="打印控件矩形表的逐条 old->new 摘要")
    ap.add_argument("--sample", type=int, default=0, help="每屏/每段抽样条数（0=全部统计）")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv[1:])
    if a.selftest:
        return _selftest()
    entries, notes = relayout_plan(a.w, a.h, a.strategy)
    for n in notes:
        print(n)
    print("待写站点：%d 条" % len(entries))
    if a.report:
        step = max(1, len(entries) // max(1, a.sample)) if a.sample else 1
        shown = entries if not a.sample else entries[::step][:a.sample]
        for e in shown:
            print("  %#010x  %d  %-28s %s -> %s" % (
                e["va"], e["size"], e["label"], e["old"].hex(), e["new"].hex()))
    # 聚合：按记录号统计
    import collections
    groups = collections.defaultdict(int)
    for e in entries:
        key = e["label"].split("]")[0].split("[")[-1] if "[" in e["label"] else "?"
        groups[key] += 1
    n_move = sum(1 for e in entries if e["old"] != e["new"])
    print("其中值发生变化的：%d 条；涉及记录：%d 条" % (n_move, len(groups)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
