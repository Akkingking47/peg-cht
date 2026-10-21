# -*- coding: utf-8 -*-
"""batch-1 汉化：战役级文本 + 引擎生成的 __flow 报表。

原则：行数严格不变；每行原有的 `\\r` 原样保留（CRLF 不破坏）；表格列的
显示宽度用 `dwidth` 对齐（汉字按 2 列宽算），避免列错位。
"""
import os
import re

SRC = r"D:\DSH\军事游戏汉化\work\gus_zx\src"
DST = r"D:\DSH\军事游戏汉化\work\gus_zx\zh"

G06_HEAD = "G06 美国大战"
H02_HEAD = "H02 为了第三帝国"

H02_BLITZ = [
    H02_HEAD,
    "",
    "德军战役 1939—1945",
    "",
    "将军阁下，您将要发动的这场战争，将使千年帝国成为欧洲的霸主！",
]

BLITZLOSS = "我们曾对你寄予厚望。你让我们失望了。"

G27_STA = [
    "G27 斯大林格勒",
    "",
    "本战役呈现的是历次争夺斯大林格勒的作战，以及其后在城内、被红军逐步合围阶段的战斗。",
    "",
    "本战役中只有胜利六角格计入得分，除非另有说明。",
    "",
    "最后几个场景中已关闭 \"Auto Refit\" 选项",
    "",
    "注意：",
    "本战役尚未完成，仅供测试。",
]

# 场景文件 -> 标题（H02 用 .scn，G06 用 .xscn）
H02_TITLES = {
    "H02_Blitz00.scn": "莫克拉",
    "H02_Blitz01.scn": "博罗夫山",
    "H02_Blitz02.scn": "坎皮诺斯",
    "H02_Blitz03.scn": "利勒哈默尔",
    "H02_Blitz04.scn": "色当",
    "H02_Blitz05.scn": "冲向敦刻尔克",
    "H02_Blitz06.scn": "梅塔克萨斯防线",
    "H02_Blitz07.scn": "向托布鲁克追击",
    "H02_Blitz08.scn": "托布鲁克",
    "H02_Blitz09.scn": "水星行动",
    "H02_Blitz10.scn": "基什尼奥夫",
    "H02_Blitz11.scn": "诺夫哥罗德",
    "H02_Blitz12.scn": "沃洛科拉姆斯克",
    "H02_Blitz13.scn": "克林",
    "H02_Blitz14.scn": "难以置信行动",
    "H02_Blitz15.scn": "华沙 1945",
    "H02_Blitz16.scn": "莫斯科 1945",
    "H02_Blitz17.scn": "冬季风暴",
    "H02_Blitz18.scn": "堡垒行动",
    "H02_Blitz19.scn": "萨莱诺登陆",
    "H02_Blitz20.scn": "冲向大海",
    "H02_Blitz21.scn": "北风",
    "H02_Blitz22.scn": "康拉德行动",
    "H02_Blitz23.scn": "列宁格勒",
}

G06_TITLES = {
    "g06_01": "德国入侵美国", "g06_02": "橡树岭", "g06_03": "重返萨凡纳",
    "g06_04": "非洲登陆", "g06_05": "沙漠风暴", "g06_06": "非洲反击",
    "g06_07": "马耳他", "g06_08": "萨莱诺登陆", "g06_09": "希腊",
    "g06_10": "萨莱诺反击", "g06_11": "解放意大利", "g06_12": "诺曼底登陆日",
    "g06_13": "深入法国", "g06_14": "梅斯战役", "g06_15": "梅斯反击",
    "g06_16": "齐格菲防线", "g06_17": "山地要塞", "g06_18": "阿登",
    "g06_19": "追歼德国佬", "g06_20": "穿越阿尔卑斯", "g06_21": "荷兰",
    "g06_22": "党卫军出逃", "g06_23": "强攻柏林", "g06_24": "第三帝国覆灭",
    "g06_25": "俄国人来袭", "g06_26": "波兰", "g06_27": "华沙战役",
    "g06_28": "格但斯克", "g06_29": "东普鲁士", "g06_30": "列宁格勒",
    "g06_31": "列宁格勒解围", "g06_32": "冬季攻势", "g06_33": "向莫斯科",
    "g06_34": "合围莫斯科", "g06_35": "利沃夫行动", "g06_36": "阿克尔曼草原",
    "g06_37": "基辅攻势", "g06_38": "高加索", "g06_39": "摩尔达维亚",
    "g06_40": "亚历山大", "g06_41": "埃及决战", "g06_42": "朝鲜",
    "g06_43": "大田", "g06_44": "首尔", "g06_45": "萨哈林",
    "g06_46": "符拉迪沃斯托克",
}


def dwidth(s):
    """显示宽度：CJK/全角按 2 列，其余按 1 列。"""
    n = 0
    for c in s:
        o = ord(c)
        n += 2 if (0x1100 <= o <= 0x115F or 0x2E80 <= o <= 0xA4CF
                   or 0xAC00 <= o <= 0xD7A3 or 0xF900 <= o <= 0xFAFF
                   or 0xFE30 <= o <= 0xFE6F or 0xFF00 <= o <= 0xFF60
                   or 0xFFE0 <= o <= 0xFFE6) else 1
    return n


ROW = re.compile(r"^(\s*\d+\s+\S+\.(?:xscn|scn))(\s+)(.+?)(\s{2,})(.*)$")


def rewrite_row(body, cr, table, key_re):
    m = ROW.match(body)
    if not m:
        return None
    pre, g1, title, g2, rest = m.groups()
    km = key_re.search(pre)
    if not km:
        return None
    key = km.group(1)
    if key not in table:
        raise SystemExit("__flow 未映射: %r (行 %r)" % (key, body))
    nt = table[key]
    pad = " " * max(0, dwidth(title) - dwidth(nt))
    return pre + g1 + nt + pad + g2 + rest + cr


def do_flow(name, table, key_re, head):
    t = open(os.path.join(SRC, name), encoding="utf-8", newline="").read()
    lines = t.split("\n")
    tnl = lines and lines[-1] == ""
    if tnl:
        lines = lines[:-1]
    out = []
    n = 0
    for ln in lines:
        cr = "\r" if ln.endswith("\r") else ""
        body = ln[:-1] if cr else ln
        if body.startswith("Campaign:"):
            out.append(re.sub(r"(Campaign:\s*\S+\s*\*\s*).*$", lambda m: m.group(1) + head, body) + cr)
            n += 1
            continue
        r = rewrite_row(body, cr, table, key_re)
        if r is not None:
            out.append(r)
            n += 1
        else:
            out.append(ln)
    assert len(out) == len(lines), (name, len(out), len(lines))
    os.makedirs(DST, exist_ok=True)
    with open(os.path.join(DST, name), "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(out) + ("\n" if tnl else ""))
    print("wrote %-18s %d 行（改写 %d 行，trailing_nl=%s）" % (name, len(out), n, tnl))


def do_lines(name, new_lines):
    t = open(os.path.join(SRC, name), encoding="utf-8", newline="").read()
    lines = t.split("\n")
    tnl = lines and lines[-1] == ""
    if tnl:
        lines = lines[:-1]
    crs = ["\r" if l.endswith("\r") else "" for l in lines]
    assert len(new_lines) == len(lines), \
        "%s 行数变化 %d -> %d" % (name, len(lines), len(new_lines))
    os.makedirs(DST, exist_ok=True)
    with open(os.path.join(DST, name), "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(x + crs[i] for i, x in enumerate(new_lines)) + ("\n" if tnl else ""))
    print("wrote %-18s %d 行（整篇替换，CR 逐行保留 %d/%d）"
          % (name, len(new_lines), sum(1 for c in crs if c), len(crs)))


if __name__ == "__main__":
    do_flow("G06__flow.txt", G06_TITLES, re.compile(r"(g06_\d+)\.xscn"), G06_HEAD)
    do_lines("G06.txt", [G06_HEAD])
    do_flow("H02__flow.txt", H02_TITLES, re.compile(r"(H02_Blitz\d+\.scn)"), H02_HEAD)
    do_lines("H02_Blitz.txt", H02_BLITZ)
    do_lines("H02_Blitzloss.txt", [BLITZLOSS])
    do_lines("G27_STA.txt", G27_STA)
