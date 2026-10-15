#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 场景层：**称呼与视角国别实测普查**（为「国别军语口径」提供实证）。

1) 称呼/敬语模式在场景文本里的**实际出现频次 + 例句**（Herr / Comrade / Sir / General / Marshal / mon …）
2) 说话人前缀（`Strock: …` 形式）
3) **文件前缀 → 视角国别** 推定（用国名关键词 + 称呼证据），供后续视角分桶
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2"
RES = os.path.join(WS, "pegww2", "research")
OUTBUCKET = os.path.join(RES, "_scn-视角分桶.tsv")
_sink = io.StringIO()

EXCLUDE = re.compile(r"(?i)(^info\.txt$|read ?me|report)")

# 称呼/敬语模式（大小写不敏感）
PATTERNS = [
    ("Herr", r"\bHerr\b"),
    ("Comrade", r"\bComrade\b"),
    ("Sir", r"\bSir\b"),
    ("Commander(称呼)", r"(?<!\.)\bCommander\b"),
    ("General", r"\bGeneral\b"),
    ("Marshal/Feld-Marschall", r"\b(?:Marshal|Feld-?Marschall|Feld-?Marshal)\b"),
    ("mein/meine", r"\b(?:mein|meine)\b"),
    ("mon/ma (法语)", r"\b(?:mon|ma)\b\s+[A-ZÉ]"),
    ("Signor/Signore (意)", r"\bSignor(?:e)?\b"),
    ("Monsieur (法)", r"\bMonsieur\b"),
    ("soldiers/Comrades 呼语", r"\b(?:Soldiers|Comrades|Kameraden|Camarades)\b"),
    ("Hail/Heil 式", r"\b(?:Heil|Sieg)\b"),
    ("comrade 小写", r"\bcomrade\b"),
    ("sir 小写", r"\bsir\b"),
    ("你方 our/we", r"\b(?:our|we)\b"),
]
NATION = {
    "德/奥": r"(?i)\b(?:German|Germany|Wehrmacht|Kriegsmarine|Luftwaffe|Waffen SS|SS|Panzer|Reich|Berlin|OKW|Hitler)\b",
    "苏": r"(?i)\b(?:Soviet|Soviets|Russia|Russian|Red Army|Stalin|Moscow|Kiev|Stalingrad|Zhukov|Konev)\b",
    "美": r"(?i)\b(?:American|Americans|USA|US |U\.S\.|Eisenhower|Patton|Bradley|Third Army|GIs)\b",
    "英": r"(?i)\b(?:British|Britain|British Army|Montgomery|8th Army|Eighth Army|Commonwealth|Royal)\b",
    "意": r"(?i)\b(?:Italian|Italians|Italy|Regia|Mussolini|Rome)\b",
    "法": r"(?i)\b(?:French|France|Free French|FFL|Vichy|de Gaulle|Paris)\b",
    "波": r"(?i)\b(?:Polish|Poland|Warsaw|LWP|Anders|Home Army)\b",
    "芬": r"(?i)\b(?:Finnish|Finland|Finns|Mannerheim)\b",
    "匈": r"(?i)\b(?:Hungarian|Hungary|Honved)\b",
    "罗": r"(?i)\b(?:Romanian|Rumanian|Romania|Antonescu)\b",
    "保": r"(?i)\b(?:Bulgarian|Bulgaria)\b",
    "希": r"(?i)\b(?:Greek|Greece)\b",
    "南": r"(?i)\b(?:Yugoslav|Partisan|Tito|Serb|Croat)\b",
    "挪": r"(?i)\b(?:Norwegian|Norway|Quisling)\b",
    "加": r"(?i)\b(?:Canadian|Canada)\b",
    "捷": r"(?i)\b(?:Czech|Slovak|Prague)\b",
    "西": r"(?i)\b(?:Spanish|Spain|Republican|Nationalist|Franco|Barcelona|Madrid)\b",
    "比荷": r"(?i)\b(?:Belgian|Belgium|Dutch|Netherland|Holland)\b",
    "美/西 混合": r"(?i)\b(?:Brazilian|Brazil)\b",
}


class _Tee:
    def __init__(self, *s):
        self.s = s

    def write(self, x):
        for t in self.s:
            t.write(x)
        return len(x)

    def flush(self):
        for t in self.s:
            t.flush()


sys.stdout = _Tee(sys.stdout, _sink)


def main():
    d = os.path.join(GAME, "SCENARIO")
    files = [f for f in sorted(os.listdir(d))
             if os.path.isfile(os.path.join(d, f)) and re.search(r"(?i)\.(txt|tx|t|log)$", f)
             and not EXCLUDE.search(f)]
    counts = Counter()
    examples = defaultdict(list)
    speakers = Counter()
    prefix_nation = defaultdict(Counter)
    prefix_files = Counter()

    for f in files:
        with open(os.path.join(d, f), "rb") as fh:
            txt = fh.read().decode("latin-1")
        low = txt
        for name, pat in PATTERNS:
            for m in re.finditer(pat, low):
                counts[name] += 1
                if len(examples[name]) < 3:
                    a = max(0, m.start() - 40)
                    examples[name].append((f, low[a:m.end() + 60].replace("\n", " ").replace("\r", " ")))
        for m in re.finditer(r"(?m)^([A-Z][A-Za-z]{2,14}):\s", low):
            speakers[m.group(1)] += 1
        pre = re.match(r"[A-Za-z0-9_]{2,10}", f)
        pre = (pre.group(0) if pre else f).lower()
        prefix_files[pre] += 1
        for nat, pat in NATION.items():
            n = len(re.findall(pat, low))
            if n:
                prefix_nation[pre][nat] += n

    print("=" * 92)
    print("A. 称呼/敬语 实际出现频次")
    print("=" * 92)
    for name, _ in PATTERNS:
        print(f"  {name:26s} {counts[name]:>6d}")
        for f, s in examples[name]:
            print(f"        [{f}] …{s.strip()}…")

    print()
    print("=" * 92)
    print("B. 说话人前缀（`Name: …`）top 25")
    print("=" * 92)
    for k, v in speakers.most_common(25):
        print(f"  {k:22s} {v:>5d}")

    print()
    print("=" * 92)
    print("C. 文件前缀 → 视角国别 推定（关键词加权）")
    print("=" * 92)
    rows = []
    for pre, natc in prefix_nation.items():
        top = natc.most_common(3)
        rows.append((prefix_files[pre], pre, top))
    for n, pre, top in sorted(rows, reverse=True)[:40]:
        print(f"  {pre:12s} 文件 {n:>4d}  视角推定: {top}")

    with open(OUTBUCKET, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# 视角分桶（推定，非终判）：前缀 / 文件数 / 国别关键词计数\n")
        fh.write("前缀\t文件数\t国别关键词计数\n")
        for n, pre, top in sorted(rows, reverse=True):
            fh.write(f"{pre}\t{n}\t{'; '.join(f'{k}={v}' for k, v in top)}\n")
    print(f"\n[out] {os.path.relpath(OUTBUCKET, WS)}")


if __name__ == "__main__":
    main()
    os.makedirs(os.path.join(RES, "evidence"), exist_ok=True)
    with open(os.path.join(RES, "evidence", "scn-address-scan.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
