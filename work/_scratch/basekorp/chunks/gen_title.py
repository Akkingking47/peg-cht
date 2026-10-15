# -*- coding: utf-8 -*-
import io, os

SRC = r"D:/DSH/军事游戏汉化/work/basekorp/chunks/in-title.tsv"
DST = r"D:/DSH/军事游戏汉化/work/basekorp/chunks/zh-title.tsv"

TRANS = {
    "10Air war": "10 空战",
    "11Der Adlertag": "11 鹰日",
    "12 Seelowe - invasion  on England 1940": "12 海狮 - 1940年入侵英格兰",
    "13Battle of Britain - Final battle?": "13 不列颠之战 - 最终决战？",
    "14Balkan": "14 巴尔干",
    "15Barbarossa": "15 巴巴罗萨",
    "16Dubno": "16 杜布诺",
    "17Mogilev": "17 莫吉廖夫",
    "18Kijev": "18 基辅",
    "19 October41": "19 1941年10月",
    "1Poland - september 1939": "1 波兰 - 1939年9月",
    "20 Volkhov river": "20 沃尔霍夫河",
    "21Moscow": "21 莫斯科",
    "22 Kharkov42": "22 哈尔科夫1942",
    "23 Summer42": "23 1942年夏",
    "24 Malta": "24 马耳他",
    "25 Rostov43": "25 罗斯托夫1943",
    "26 Tunis 43": "26 突尼斯1943",
    "27 Sicily43": "27 西西里1943",
    "28 Kijev43": "28 基辅1943",
    "29 Rescue 1944": "29 救援 1944",
    "2Attack on Poland": "2 进攻波兰",
    "30 Riga 1944": "30 里加 1944",
    "31 Hungary45": "31 匈牙利1945",
    "32 Germany": "32 德国",
    "3Bzura-polish attack": "3 布祖拉 - 波军进攻",
    "4Fort Modlin": "4 莫德林要塞",
    "5Invest Warsaw": "5 围攻华沙",
    "6Crusade on west": "6 西征",
    "7Attack near Sedan": "7 色当附近进攻",
    "8 Attack Peronne": "8 佩罗讷进攻",
    "9From Somma to Paris": "9 从索姆到巴黎",
    "7th French Army rush North": "第7法国集团军北上",
    "120 Piortkow": "120 皮奥特库夫",
    "130 Vistula": "130 维斯瓦河",
    "140 France 1940": "140 法国1940",
    "150 France Nord": "150 法国北部",
    "155 Maginote line": "155 马奇诺防线",
    "160 Defensive": "160 防御",
    "170 Road Paris": "170 巴黎公路",
    "180 England": "180 英国",
    "190 Balkan": "190 巴尔干",
    "200 Crete": "200 克里特",
    "205 Litovsk": "205 利托夫斯克",
    "220 Minsk": "220 明斯克",
    "230 Bobruisk": "230 博布鲁伊斯克",
    "240 Bryansk": "240 布良斯克",
    "250 Mozhaisk": "250 莫扎伊斯克",
    "260 Demjansk": "260 杰米扬斯克",
    "270 Kharkov 42": "270 哈尔科夫1942",
    "280 Don river": "280 顿河",
    "290 Autum 1942": "290 1942年秋",
    "300 Kharkov 43": "300 哈尔科夫1943",
    "310 Kursk": "310 库尔斯克",
    "312 Road to North": "312 通往北方之路",
    "314 Moskow 43": "314 莫斯科1943",
    "316 Winter44": "316 冬季1944",
    "315 Bagration": "315 巴格拉季昂",
    "320 Falaise": "320 法莱斯",
    "330 Kustrin": "330 屈斯特林",
    "340 Seelow": "340 塞洛",
    "2 Army Encirclement": "第2集团军合围",
    "00 Unternehmen Taifun": "00 台风行动",
    "01 Relief of Kholm": "01 霍尔姆解围",
    "02 Rzhev Salient": "02 勒热夫突出部",
    "03 Unternehmen Zitadelle": "03 堡垒行动",
    "04 Second Battle of Smolensk": "04 第二次斯摩棱斯克之战",
    "05 Strachwitz's Offensive": "05 施特拉赫维茨攻势",
    "06 Unternehmen Doppelkopf": "06 双头行动",
    "07 Final Collapse In Pomerania": "07 波美拉尼亚的最终崩溃",
}

with io.open(SRC, "r", encoding="utf-8-sig", newline="") as f:
    rows = [ln.rstrip("\r\n").split("\t") for ln in f if ln.strip()]

rows = rows[1:] if rows and rows[0][0] == "file" else rows

out, miss = [], []
for r in rows:
    src = r[1] if len(r) > 1 else r[0]
    if src not in TRANS:
        miss.append(src)
        continue
    out.append((src, TRANS[src]))

if miss or len(out) != 70:
    raise SystemExit("MISMATCH missing=%s count=%d" % (miss, len(out)))

with io.open(DST, "w", encoding="utf-8", newline="\r\n") as f:
    for src, dst in out:
        f.write(src + "\t" + dst + "\r\n")

# self check
with io.open(DST, "r", encoding="utf-8", newline="") as f:
    chk = [ln.rstrip("\r\n") for ln in f if ln.strip()]
with io.open(SRC, "r", encoding="utf-8-sig", newline="") as f:
    srcs = [ln.rstrip("\r\n").split("\t")[1] for ln in f if ln.strip()][1:]

assert len(chk) == 70, len(chk)
assert all(ln.count("\t") == 1 for ln in chk)
assert [ln.split("\t")[0] for ln in chk] == srcs
with open(DST, "rb") as f:
    head = f.read(3)
assert head != b"\xef\xbb\xbf"
assert b"\r\n" in open(DST, "rb").read()
print("OK rows=%d tabs=1 bom=no crlf=yes" % len(chk))
