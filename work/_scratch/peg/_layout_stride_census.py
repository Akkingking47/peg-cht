# -*- coding: utf-8 -*-
"""_layout_stride_census.py — 布局表消费点普查（步长证据路）。

背景：题面给出布局记录表 `0x4A96E8`，**记录长度 15 字节**。
      → 消费该表的代码必然含 `imul reg, reg, 0xF` 或 `lea reg, [reg + reg*8]` 类
        乘 15 / 位移 15 的寻址。这是比"立即数 800/600"更硬的 L3 指纹：
        800/600 会被位图头、行跨距、字形尺寸污染，而 **stride 0xF 不会**。

本脚本产出（全部只读，只写 tsv/txt）：
  1. work/peg/relayout/imul0f_sites.tsv        全部 0xF 步长乘法的站点
  2. work/peg/relayout/func_value_matrix.tsv   每个函数的命中值集合（布尔列）
  3. work/peg/relayout/value_pair_matrix.tsv   出现过的值对 + 次数（找 800×600 双常量函数）
  4. 控制台/报告用的汇总
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _census_common as C


def all_mem_disp(ins):
    """一条指令里所有 [reg+disp] 的位移（含 8 位、32 位）。"""
    out = []
    for op in ins.operands:
        if op.type == 3:  # CS_OP_MEM
            d = op.mem.disp
            if d:
                out.append(d)
    return out


def find_stride_sites(insns, stride=0xF):
    """找 imul r,r,stride 与 lea r,[r + r*k]（k 使总倍率 = stride 的等价式）。"""
    hits = []
    for i, ins in enumerate(insns):
        if ins.mnemonic == "imul" and len(ins.operands) == 3:
            v = ins.operands[-1]
            if v.type == 2 and (v.imm & 0xFFFFFFFF) == stride:
                hits.append((ins, "imul"))
                continue
        # lea r, [r + r*8] 再加 r*... 的组合；只收单条就能表达 ×15 的
        if ins.mnemonic == "lea":
            s = ins.op_str.replace(" ", "")
            if re.search(r"\[[a-z0-9]+\+[a-z0-9]+\*[0-9a-fx]+\]", s):
                pass  # 交错的 lea 链需要数据流，本脚本不做
    return hits


def main():
    data = C.load_text()
    insns, nbad = C.disasm_text(data)
    starts = C.func_starts(data, insns)
    print("insns=%d resync=%d func_starts=%d" % (len(insns), nbad, len(starts)))

    relayout = os.path.join(C.ROOT, "work", "peg", "relayout")
    outdir = os.path.join(C.ROOT, "work", "peg", "out")
    os.makedirs(relayout, exist_ok=True)
    os.makedirs(outdir, exist_ok=True)

    # ---------------- 1. stride 0xF 站点 ----------------
    stride_hits = find_stride_sites(insns, 0xF)
    rows = []
    for ins, kind in stride_hits:
        fn = C.func_start_of(ins.address, starts)
        rows.append((ins.address, C.va2fo(ins.address), fn,
                     data[ins.address - C.IMAGE_BASE: ins.address - C.IMAGE_BASE + ins.size].hex(" "),
                     "%s %s" % (ins.mnemonic, ins.op_str)))
    p1 = os.path.join(relayout, "imul0f_sites.tsv")
    with open(p1, "w", encoding="utf-8", newline="\n") as f:
        f.write("va\tfile_off\tfunc_start\tinstr_hex\tinstr_text\n")
        for va, fo, fn, hx, tx in rows:
            f.write("0x%06X\t0x%06X\t0x%06X\t%s\t%s\n" % (va, fo, fn, hx, tx))
    stride_funcs = sorted(set(r[2] for r in rows))
    print("imul*0xF sites=%d funcs=%d -> %s" % (len(rows), len(stride_funcs), p1))

    # ---------------- 2. 立即数命中 → 每函数值集合 ----------------
    # 这里独立做一遍立即数扫描（与 _immediate_census.py 同规则，保证自洽）
    import _immediate_census as IC  # 复用同一套 classify
    hits = []
    for i, ins in enumerate(insns):
        for raw in IC.imm_values(ins):
            if raw in IC.TARGET_SET:
                notes, excl = IC.check_exclude(ins, raw)
                if excl:
                    continue
                guess, notes2 = IC.classify(ins, raw, i, insns)
                hits.append({"va": ins.address, "fn": C.func_start_of(ins.address, starts),
                             "val": raw, "guess": guess, "ins": ins,
                             "hex": data[ins.address - C.IMAGE_BASE:
                                         ins.address - C.IMAGE_BASE + ins.size].hex(" ")})
    print("live immediate hits=%d" % len(hits))

    fn_vals = {}
    for h in hits:
        fn_vals.setdefault(h["fn"], set()).add(h["val"])
    fn_cnt = {}
    for h in hits:
        fn_cnt[h["fn"]] = fn_cnt.get(h["fn"], 0) + 1

    p2 = os.path.join(relayout, "func_value_matrix.tsv")
    tgt_sorted = sorted(C.TARGETS)
    with open(p2, "w", encoding="utf-8", newline="\n") as f:
        f.write("func_start\thits\t" + "\t".join(str(v) for v in tgt_sorted) + "\tstride0F\tnote\n")
        for fn in sorted(fn_vals, key=lambda k: (-fn_cnt[k], k)):
            vs = fn_vals[fn]
            mark = []
            if 800 in vs and 600 in vs:
                mark.append("W+H")
            if 799 in vs and 599 in vs:
                mark.append("W-1+H-1")
            if 800 in vs and 799 in vs:
                mark.append("W+W-1->clamp")
            if 600 in vs and 599 in vs:
                mark.append("H+H-1->clamp")
            if 400 in vs and 800 in vs:
                mark.append("half-W-pair")
            if fn in stride_funcs:
                mark.append("stride0F")
            f.write("%s\t%d\t%s\t%d\t%s\n" % (
                "0x%06X" % fn, fn_cnt[fn],
                "\t".join(str(v) for v in tgt_sorted),
                1 if fn in stride_funcs else 0,
                ";".join(mark)))

    # ---------------- 3. 值对矩阵 ----------------
    from collections import Counter
    pair = Counter()
    for fn, vs in fn_vals.items():
        vl = sorted(vs)
        for a in range(len(vl)):
            for b in range(a, len(vl)):
                pair[(vl[a], vl[b])] += 1
    p3 = os.path.join(relayout, "value_pair_matrix.tsv")
    with open(p3, "w", encoding="utf-8", newline="\n") as f:
        f.write("value_a\tvalue_b\tfuncs\n")
        for (a, b), n in pair.most_common():
            f.write("%d\t%d\t%d\n" % (a, b, n))

    # ---------------- 4. 汇总 ----------------
    both = [fn for fn, vs in fn_vals.items() if 800 in vs and 600 in vs]
    w_and_w1 = [fn for fn, vs in fn_vals.items() if 800 in vs and 799 in vs]
    h_and_h1 = [fn for fn, vs in fn_vals.items() if 600 in vs and 599 in vs]
    core = [fn for fn, vs in fn_vals.items()
            if 800 in vs and 600 in vs and 799 in vs and 599 in vs]
    print("funcs with 800&600          = %d" % len(both))
    print("funcs with 800&799          = %d" % len(w_and_w1))
    print("funcs with 600&599          = %d" % len(h_and_h1))
    print("funcs with 800&600&799&599  = %d %s" % (len(core), ["0x%06X" % c for c in sorted(core)]))
    print("stride0F funcs=%d" % len(stride_funcs))
    both_stride = sorted(set(stride_funcs) & set(both))
    print("stride0F AND 800&600 funcs = %d %s" % (len(both_stride), ["0x%06X" % x for x in both_stride]))
    print("stride0F funcs list: %s" % ", ".join("0x%06X" % x for x in stride_funcs))
    print("TSV: %s" % p1)
    print("TSV: %s" % p2)
    print("TSV: %s" % p3)

    # 报告
    lines = []
    a = lines.append
    a("LAYOUT-STRIDE CENSUS  (stride = 0x0F = 15, 布局记录表 0x4A96E8)")
    a("insns=%d  resync=%d  func_starts=%d" % (len(insns), nbad, len(starts)))
    a("")
    a("[A] imul reg,reg,0x0F 站点 = %d 个，分布在 %d 个函数" % (len(rows), len(stride_funcs)))
    a("    这是 15 字节布局记录被消费的**直接指纹**。清单：")
    from collections import defaultdict
    byf = defaultdict(list)
    for va, fo, fn, hx, tx in rows:
        byf[fn].append(va)
    for fn in sorted(byf):
        a("    0x%06X  n=%d  %s" % (fn, len(byf[fn]),
                                    " ".join("0x%06X" % v for v in byf[fn])))
    a("")
    a("[B] 立即数命中里同时出现 800 与 600 的函数 = %d 个" % len(both))
    for fn in sorted(both):
        a("    0x%06X  hits=%d  vals=%s%s" % (
            fn, fn_cnt[fn], sorted(fn_vals[fn]),
            "   <== 同时含 stride0F" if fn in stride_funcs else ""))
    a("")
    a("[C] 800 与 799 同函数（宽度钳位 min(v,799) 模式）= %d 个" % len(w_and_w1))
    a("    " + " ".join("0x%06X" % x for x in sorted(w_and_w1)))
    a("[C2] 600 与 599 同函数（高度钳位）= %d 个" % len(h_and_h1))
    a("    " + " ".join("0x%06X" % x for x in sorted(h_and_h1)))
    a("[C3] 四常量齐全 800+600+799+599（屏幕矩形钳位）= %d 个" % len(core))
    a("    " + " ".join("0x%06X" % x for x in sorted(core)))
    a("")
    a("[D] stride0F ∩ (800&600) = %d 个（L3 布局消费点最强候选）" % len(both_stride))
    a("    " + " ".join("0x%06X" % x for x in both_stride))

    txt = "\n".join(lines) + "\n"
    p4 = os.path.join(outdir, "layout-stride-report.txt")
    with open(p4, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)
    print("REPORT: %s" % p4)


if __name__ == "__main__":
    main()
