# -*- coding: utf-8 -*-
"""下载史实德国旗（1935-45 红底白盘黑卐）高清 PNG —— 经 images.weserv.nl 代理。

通道实测（probe_weserv2 结论）：
  ✗ upload.wikimedia.org 的 /thumb/ 路径 → 回源 400
  ✓ 原始 SVG 文件 + weserv 栅格化（w=800, output=png）→ 200
  ✓ thumb.php / Special:FilePath → 200（备用）

像素自检（PIL）：史实旗特征 = 红占比>0.5 且 含白盘>0.05 且 含黑卐>0.02
  现行三色旗（金带>0.2）与 1933-35 黑白红（红仅~1/3）都会被拒绝。
"""
import hashlib
import os
import struct
import sys
import urllib.request
import urllib.error
from urllib.parse import quote

from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "reich_flag_800.png")
W = 800
# 候选 (仓库, 文件名)：commons 或 en（en.wikipedia 本地文件）；原始文件路径规则同 MD5 分桶
CANDS = [
    ("commons", "Flag_of_Germany.svg"),                       # 通道基准（现行旗，应被自检拒绝）
    ("commons", "Flag_of_Germany_(1935\u20131945).svg"),
    ("commons", "Flag_of_Germany_(1935-1945).svg"),
    ("commons", "Flag_of_the_German_Reich_(1935\u20131945).svg"),
    ("en", "Flag_of_Nazi_Germany_(1935\u20131945).svg"),
    ("en", "Flag_of_Nazi_Germany_(1935-1945).svg"),
    ("en", "Flag_of_Nazi_Germany.svg"),
    ("en", "Flag_of_Germany_1933-1945.svg"),
    ("commons", "Flag_of_German_Reich.svg"),
]


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def weserv_orig(repo, name):
    """原始 SVG 交 weserv 栅格化为 800px PNG。"""
    h = hashlib.md5(name.encode("utf-8")).hexdigest()
    path = "upload.wikimedia.org/wikipedia/%s/%s/%s/%s" % (
        repo, h[0], h[:2], quote(name, safe="()_"))
    return "https://images.weserv.nl/?url=" + quote("ssl:" + path, safe="") + "&w=%d&output=png" % W


def weserv_filepath(name):
    path = "commons.wikimedia.org/wiki/Special:FilePath/" + quote(name, safe="()_") + "?width=%d" % W
    return "https://images.weserv.nl/?url=" + quote("ssl:" + path, safe="")


def color_stats(path):
    img = Image.open(path).convert("RGB")
    img.thumbnail((80, 80))
    n = 0
    red = white = black = gold = 0
    for r, g, b in img.getdata():
        n += 1
        if r > 140 and g < 90 and b < 90:
            red += 1
        elif min(r, g, b) > 200:
            white += 1
        elif max(r, g, b) < 60:
            black += 1
        elif r > 200 and g > 140 and b < 110:
            gold += 1
    return dict(w=img.size[0], h=img.size[1], red=red / n, white=white / n,
                black=black / n, gold=gold / n)


def looks_historic(s):
    """史实旗（红底白盘黑卐）：红为主、有白盘、有黑卐、无大面积金。"""
    return s["red"] > 0.5 and s["white"] > 0.05 and s["black"] > 0.02 and s["gold"] < 0.05


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    for repo, name in CANDS:
        tag = "%s %s" % (repo, name)
        for chan, url in (("orig", weserv_orig(repo, name)), ("fpath", weserv_filepath(name))):
            print("尝试:", tag, "[%s]" % chan)
            try:
                data = fetch(url)
            except Exception as e:
                print("  网络:", repr(e)[:120])
                continue
            if len(data) < 2000 or not data.startswith(b"\x89PNG"):
                print("  非PNG/过小:", len(data), data[:16])
                continue
            with open(tmp, "wb") as f:
                f.write(data)
            try:
                s = color_stats(tmp)
            except Exception as e:
                print("  解码失败:", repr(e)[:120])
                continue
            print("  %dx%d  红%.2f 白%.2f 黑%.2f 金%.2f" %
                  (s["w"], s["h"], s["red"], s["white"], s["black"], s["gold"]))
            if not looks_historic(s):
                print("  ≠史实旗特征，跳过")
                continue
            os.replace(tmp, OUT)
            print("OK ->", OUT, len(data), "bytes   (源: %s | %s)" % (name, chan))
            return 0
    print("全部候选失败")
    return 1


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
