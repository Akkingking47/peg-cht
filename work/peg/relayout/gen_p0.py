# -*- coding: utf-8 -*-
"""P0 普查：把 peg_launcher.py 现有补丁站点结构化，导出 sites.tsv / tables.tsv。

只读：import peg_launcher 只为复用它的常量与 build_plan（不写母本、不启动游戏）。
输出目录：work\\peg\\relayout\\
用法：C:\\Python314\\python.exe work\\peg\\relayout\\gen_p0.py
"""
import os
import sys
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
PEGDIR = os.path.dirname(HERE)                      # work\peg
ROOT = os.path.dirname(os.path.dirname(PEGDIR))     # 工作区根
sys.path.insert(0, PEGDIR)
import peg_launcher as PL                           # noqa: E402

W, H = 1920, 1080
SITES = os.path.join(HERE, "sites.tsv")
TABLES = os.path.join(HERE, "tables.tsv")

# ---------------------------------------------------------------- 站点分组索引
def _idx(seq, has_tag=True):
    out = {}
    for row in seq:
        va = row[0]
        tag = row[2] if has_tag else None
        note = row[3] if has_tag else row[-1]
        out[va] = (tag, note)
    return out


VA2 = {}
for va, old, tag, note in PL.CODE_EDITS:
    VA2[va] = ("CODE_EDITS", tag, note)
for va, old, tag, note in PL.CANVAS_SITES:
    VA2[va] = ("A", tag, note)
for va, ob, nb, note in PL.TOOLTIP_SITES:
    VA2[va] = ("E", None, note)
for va, ob, nb, note in PL.CLIP_ARITH:
    VA2[va] = ("F", None, note)
for va, old, tag, note in PL.SECONDARY:
    VA2[va] = ("G", tag, note)
for va, old, tag, note in PL.EXTRA:
    VA2[va] = ("H", tag, note)
for va, note in PL.MAP_SITES:
    VA2[va] = ("M", None, note)
for cname, g, note_idx in (("REPAINT", "B", 3), ("MAPREPAINT", "R", 3),
                           ("PRESENT", "S", 3), ("RANGE_EVERY", "T", 3),
                           ("OVERLAY", "P", 3)):
    c = getattr(PL, cname, None)
    if c:
        VA2[c[0]] = (g, None, c[note_idx])
p = PL.PANEL
VA2[p[0]] = ("D-panel", p[2], p[3])

# TSV 驱动的三组：K(尺寸站点表) / D(UI 记录位移) / I(布局表右对齐)
TSVROWS = {}
for r in PL.load_tsv("res_diff_v4.tsv"):
    TSVROWS[int(r["va"], 16)] = ("K", r)
for r in PL.load_tsv("ui_layout_v9.tsv"):
    TSVROWS[int(r["va"], 16)] = ("D", r)
for r in PL.load_tsv("panel_table_v1.tsv"):
    TSVROWS[int(r["va_x1"], 16)] = ("I", r)
    TSVROWS[int(r["va_x2"], 16)] = ("I", r)


# 设计空间常量 -> 规则（tag 驱动的机械映射，见 P0 报告）
TAG_RULE = {
    "w": ("stretch_w", "new=W"),
    "w-1": ("clamp_max:W", "new=W-1"),
    "w-4": ("stretch_w:offset=-4", "new=W-4"),
    "h": ("stretch_h", "new=H"),
    "h-1": ("clamp_max:H", "new=H-1"),
    "h-28": ("stretch_h:offset=-28", "new=H-28"),
    "h-30": ("stretch_h:offset=-30", "new=H-30"),
    "dx": ("translate_legacy:x+1120", "new=x+(W-800)"),
    "dy": ("translate_legacy:y+480", "new=y+(H-600)"),
}


def classify(va, size, group, label, old_hex):
    """返回 (class, rule, params)。语义不清的标 need_re。
    params 里 always 记录设计空间原值与所属表/字段。"""
    tag, note = (VA2.get(va, (None, None, None))[1], VA2.get(va, (None, None, None))[2])
    ts = TSVROWS.get(va)
    # ---- 数据面：三张 TSV 表 ----
    if ts and ts[0] == "K":
        r = ts[1]
        sec, t = r.get("section", "?"), r.get("tag", "?")
        rule, how = TAG_RULE.get(t, ("need_re", ""))
        if rule == "need_re":
            return ("need_re", "need_re", "table=%s;tag=%s;design_old=%s" % (sec, t, r.get("old")))
        # .text 里的立即数属于代码面；.data 里的是布局记录字段
        return ("L2" if sec == ".text" else "L3", rule,
                "src=res_diff_v4.tsv;section=%s;tag=%s;design_old=%s;%s;%s" %
                (sec, t, r.get("old"), how, r.get("note", "")[:48]))
    if ts and ts[0] == "D":
        r = ts[1]
        return ("L3", "relayout_record",
                "src=ui_layout_v9.tsv;tag=%s;idx=%s;field=%s;design_old=%s;legacy_delta=%s;new_value=%s" %
                (r.get("tag"), r.get("idx"), r.get("field"), r.get("new_value"),
                 r.get("delta"), r.get("new_value")))
    if ts and ts[0] == "I":
        r = ts[1]
        field = "x1" if va == int(r["va_x1"], 16) else "x2"
        return ("L3", "anchor_right_scale",
                "table=0x4A96E8;stride=15;idx=%s;field=%s(%s);design_old=%s;dx=%s" %
                (r.get("idx"), field, r.get("role", "?"), r.get("x1"), r.get("dx")))
    # ---- 代码面 ----
    if group == "CODE_EDITS":
        if va in (0x41C4D7, 0x41C4DE):
            return ("L4", "anchor_bottom_scale" if tag == "h-28" else "anchor_right_scale",
                    "code=panel_rect;tag=%s;design_old=%s" % (tag, old_hex))
        if va in (0x44C5CD, 0x44C5D2):
            return ("L2", "descriptor_size",
                    "code=screen_border;tag=%s;design_old=%s" % (tag, old_hex))
        return ("L2", "viewport_rect",
                "code=viewport_clip;tag=%s;design_old=%s" % (tag, old_hex))
    if group == "A":
        return ("L2", "descriptor_size", "code=canvas_desc;tag=%s;design_old=%s" % (tag, old_hex))
    if group == "F":
        return ("L2", "clamp_neg:W" if "x：" in note else "clamp_neg:H",
                "code=blit_clip_arith;design_old=%s" % old_hex)
    if group == "G":
        if "文本排版矩形" in note or "文本" in note:
            return ("L8", "text_rect", "code=text_layout_rect;tag=%s;design_old=%s" % (tag, old_hex))
        if "居中" in note:
            return ("L5", "scale_center", "code=msgbox_center;design_old=%s(400)" % old_hex)
        if "贴边滚动" in note or "滚动方向" in note:
            return ("L7", "clamp_max:W" if tag in ("w-1",) else "clamp_max:H",
                    "code=edge_scroll_test;tag=%s;design_old=%s" % (tag, old_hex))
        return ("L4", "viewport_rect", "code=strategic_map_viewport;tag=%s;design_old=%s" % (tag, old_hex))
    if group == "H":
        if "重绘区" in note:
            return ("L7", "stretch_h" if tag == "h-1" else "stretch_w",
                    "code=fullscreen_damage_reg;tag=%s;design_old=%s" % (tag, old_hex))
        return ("L7", "clamp_max:W" if tag == "w" else "clamp_max:H",
                "code=cell25_cull;tag=%s;design_old=%s" % (tag, old_hex))
    if group == "M":
        if "dwWidth" in note or "dwHeight" in note:
            return ("L1", "descriptor_size", "code=map_surface_desc;design_old=1920;cap=4096")
        if "imul" in note:
            return ("L1", "surface_cap", "code=map_pixel_stride;design_old=1920;cap=4096")
        return ("L1", "surface_cap", "code=map_surface_bound;design_old=1920;cap=4096")
    if group == "B":
        return ("L7", "diag_force_repaint", "optin=on_by_default;diagnostic")
    if group == "R":
        return ("L7", "diag_force_repaint", "optin=off_by_default;diagnostic;实测无效")
    if group == "S":
        return ("L7", "diag_force_present", "optin=off_by_default;diagnostic;实测无效")
    if group == "T":
        return ("L7", "diag_range_recompute", "optin=off_by_default;diagnostic;实测无效")
    if group == "E":
        return ("L9", "disable_blit", "optin=off_by_default;hover_hintbox_blit")
    if group == "D-panel":
        return ("L4", "anchor_right_scale", "code=right_panel_x;design_old=799")
    if group == "N":
        return ("L7", "clamp_max:W", "code=scroll_clamp_x;design_old=mapW-vpW-1")
    return ("need_re", "need_re", "unknown_group")


def export_sites():
    entries, notes = PL.build_plan(
        W, H, ui=True, repaint=True, canvas=True, tooltip=False, extra=True,
        panel=True, dxdy=False, mapmargin=True, scrollfix=True,
        maprepaint=False, present=False)
    rows = []
    cls_count = {}
    need_re = []
    for e in entries:
        va = e["va"]
        label = e["label"]
        group = "N"
        if va in VA2:
            group = VA2[va][0]
        elif va in TSVROWS:
            group = TSVROWS[va][0]
        cls, rule, params = classify(va, e["size"], group, label, e["old"].hex())
        if cls == "need_re":
            need_re.append((va, label))
        cls_count[cls] = cls_count.get(cls, 0) + 1
        rows.append((va, e["size"], group, cls, rule, params,
                     e["old"].hex(), e["new"].hex(), label))
    rows.sort(key=lambda r: r[0])
    with open(SITES, "w", encoding="utf-8", newline="\n") as f:
        f.write("va_hex\tsize\tgroup\tclass\trule\tparams\told_hex\tnew_hex\tlabel\n")
        for r in rows:
            f.write("%#010x\t%d\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % r)
    return rows, cls_count, need_re, notes


TABLES_ROWS = [
    ("layout_records_0x4A96E8", "0x4A96E8", 15, 272,
     "x1@+0x00,y1@+0x02,x2@+0x04,y2@+0x06(推测)，右对齐字段用 Xr()",
     "L3", "docs\\80 §0/§3；18 处 `imul reg,reg,0xF` + `add reg,0x4A96E8` 读点，消费函数 0x413932/0x41407A/0x430960/0x445FFF；launcher I 组(panel_table_v1.tsv)与 K 组均落在该表"),
    ("layout_records_right_aligned_37", "0x4A96E8", 15, 37,
     "x1@+0x00,x2@+0x04（role=RIGHT 的子集）",
     "L3", "work\\peg\\out\\panel_table_v1.tsv 37 条 role=RIGHT、dx=+1120；launcher I 组每条写 2 个 word"),
    ("main_layout_0x490470", "0x490470", 0x24, None,
     "x@+0x02,y@+0x04,right@+0x06",
     "L3", "docs\\72 表订正（x@+0x02/y@+0x04/right@+0x06，非 +0x04/+0x08）；与 20 处 800,600 word 对同族"),
    ("screen_size_pairs_800x600", "0x48E202", 4, 20,
     "w@+0x00=800,h@+0x02=600（word 对 20 03 58 02）",
     "L2", "docs\\80 §0 列出的 20 个 VA：0x48E202 0x48E4FA 0x48F556 0x48F7DA 0x490FA2 0x491CE2 0x492982 0x493B76 0x49481A 0x4973CA 0x498166 0x4A0046 0x4A137E 0x4A17BE 0x4A1A82 0x4A3B0A 0x4A60B2 0x4A9316 0x4A9616 0x4AB0D2；另有 dword 对 0x491118"),
    ("controls_0x4CCE2C", "0x4CCE2C", 0x24, None,
     "flags@+0x00,x@+0x02,y@+0x04,id@+0x0A,draw_cb@+0x10",
     "L6", "docs\\72 控件数组；docs\\74 实测 `0x4CCE2C + 0x14 == 0x4CCE40`（越界遍历会踩图层 B）"),
    ("range_table_0x622D4A", "0x622D4A", 7, None,
     "cell word@+0x00（行距 0x13B，格距 7B，地图 extent 37×27）",
     "L7", "写入者 0x42D1A5（0x42D392 imul j,0x13B / 0x42D3A0 imul i,7 / 0x42D3AA mov word[..,0x622d4a]）；读者 0x42D0F2 与 word[0x686FD4] 比较"),
    ("mask_layer_A_0x4CCE40", "0x4CCE40", 1, 0x70800,
     "1bpp 位图（1920×1920/8），每格 1 bit",
     "L9", "docs\\72/§3 L9；0x43D67F 写/清；0x4CCE40 有 17 处引用（0x43D67F/0x43F64E/0x43F9E8/0x43FC09）"),
    ("mask_layer_B_0x53D640", "0x53D640", 1, 0x70800,
     "1bpp 位图（同 A，另一张遮挡层）",
     "L9", "同上；docs\\74 记录 0x4CCE2C 越界即踩到 0x4CCE40"),
    ("unit_table_0x65AA00", "0x65AA00", 0x58, 400,
     "+0x04 flags(word),+0x08 缓存屏X,+0x0A 缓存屏Y,+0x52/+0x54 hex(hx,hy)",
     "L7", "docs\\72：0x441952 push 0x8980 = 400×0x58 memset；0x410E90 cmp ecx,0x190；0x455CA8 命中测试唯一读缓存者"),
    ("hex_param_table_0x4A0200", "0x4A0200", 0x18, None,
     "+0x02 格高−1,+0x06 行高−1,+0x0B 列宽−1",
     "L3", "docs\\72：选择器 word[0x4AF45C] 44 处引用全为读、无写者（恒取第 0 项）"),
    ("icon_grid_coords_0x4A2DF8", "0x4A2DF8", 4, None,
     "每项 word x@+0,y@+2；个数在 0x4A2DD8；索引在 0x4C90A0",
     "L9", "0x4517F7 固定坐标图标阵（i*0x25+0x5E, i*0x0D+0x35）；docs\\72 注 0x4A2DD8 不是个数"),
    ("dirty_flag_0x498D74", "0x498D74", 2, 1, "word，0/1/2 三态", "L7",
     "62 处引用；6 处写 1（0x425CAB 0x4282DA 0x42CA0B 0x43499F 0x44BF33 0x456AC2）、1 处写 2（0x42E4B4）、30 处清 0"),
    ("present_flag_0x498D78", "0x498D78", 1, 1, "byte，1=地图面需要上屏", "L7",
     "写入 0x42D0F8（逐格画范围前）与 0x42D2B2/0x42D3B2；读点 0x42D4FE"),
    ("scroll_state", "0x4AF2F8", 2, 2, "word[0x4AF2F8]=scrollX, word[0x4AF2FC]=scrollY", "L4",
     "缓存副本按视口槽 word[0x4AF32C]：word[0x498D34+slot*2]/word[0x498D38+slot*2]（0x42D509/0x42D52A）"),
    ("viewport_words", "0x498D3C", 2, 3, "0x498D3C=top(22),0x498D40=right(1919),0x498D44=bottom(1052)", "L4",
     "0x41FF8A 上屏源矩形与 0x41F0D6 视口设置器共用；docs\\72"),
    ("src_table_res_diff_v4", "-", 0, 259,
     "index,section,va,file_off,width,old,new,tag,note；.text 52 / .data 207",
     "L1-L4", "work\\peg\\out\\res_diff_v4.tsv（K 组站点来源；tag 分布 w20 h21 w-1 26 h-1 10 h-28 15 w-4 1 h-30 1 dx163 dy2）"),
    ("src_table_ui_layout_v9", "-", 0, 31,
     "idx,field,va,delta,new_value,tag；field x14/right15/y1/bottom1，tag toolbar-button26/action-box2/bottom-bar3",
     "L3", "work\\peg\\out\\ui_layout_v9.tsv（D 组来源，legacy delta +1120/+560/+480）"),
    ("src_table_panel_table_manifest", "0x4A96E8", 15, 272,
     "idx,VA,x1,y1,x2,y2,w,h,+8,+a,+c,role,dx；role KEEP133 / RIGHT(+1120)42 / MID(+560)93 / PANEL(+560)3",
     "L3", "work\\peg\\out\\panel_table_manifest.tsv（0x4A96E8 全表清单，I 组只覆盖其中 RIGHT 的 37 条字段）"),
]


def export_tables():
    with open(TABLES, "w", encoding="utf-8", newline="\n") as f:
        f.write("name\tbase_va\trecord_size\tcount\tfields\tclass\tevidence\n")
        for r in TABLES_ROWS:
            f.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" %
                    (r[0], r[1], r[2], "" if r[3] is None else r[3], r[4], r[5], r[6]))


def main():
    rows, cls_count, need_re, notes = export_sites()
    export_tables()
    print("sites.tsv 行数 = %d" % len(rows))
    print("按类统计：")
    for k in sorted(cls_count):
        print("  %-8s %d" % (k, cls_count[k]))
    print("语义待查(need_re) = %d" % len(need_re))
    for va, label in need_re:
        print("  %#010x  %s" % (va, label))
    print("--- 校验：build_plan(1920,1080) 与 launcher 默认参数 ---")
    entries, notes2 = PL.build_plan(
        W, H, ui=True, repaint=True, canvas=True, tooltip=False, extra=True,
        panel=True, dxdy=False, mapmargin=True, scrollfix=True,
        maprepaint=False, present=False)
    print("build_plan entries = %d   （launcher 打印的默认值应为 275）" % len(entries))
    print("sites.tsv 行数 = %d" % len(rows))
    print("输出：%s" % SITES)
    print("输出：%s" % TABLES)
    return 0


if __name__ == "__main__":
    sys.exit(main())
