# -*- coding: utf-8 -*-
r"""程序优先匹配器 —— 新 efile 开工，先用 master 词库自动定译，只剩 miss 才交 LLM。

用法: python apply_master.py --efile PzLIGA [--with-words] [--root D:\OpenGeneral]
      （`--root` 服务 D:\OpenGeneral 等其它安装；默认 D:\OpenPG2）

流程（对应「程序做翻译、LLM 只校验」）：
  1. 导出目标 efile 的 .xscn 唯一串（按 cp1252 读，避开假汉字陷阱）
  2. master-glossary.tsv 精确匹配（跨 efile 全层）
  3. master-words.tsv 词级组合（--with-words 时；token 全命中才整串替换）
  4. 输出：
       prematch-map.tsv    程序已定 src→dst（无需 LLM）
       prematch-miss.tsv   需 LLM 的 src（按频次降序）

产出文件落在 work\<efile-lower>\ 下。用法: python apply_master.py --efile PzLIGA
"""
import collections
import importlib.util
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
# 默认游戏根目录；用 `--root D:\OpenGeneral` 或环境变量 XSCN_ROOT 覆盖（与 xscn.py 同规则）
ROOT = os.environ.get("XSCN_ROOT") or r"D:\OpenPG2"
HERE = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.join(HERE, "master-glossary.tsv")
WORDS = os.path.join(HERE, "master-words.tsv")
RESOLVE = os.path.join(HERE, "master-resolve.tsv")

spec = importlib.util.spec_from_file_location("xscn", os.path.join(HERE, "xscn.py"))
xscn = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(xscn)
except SystemExit:
    pass

TOK = re.compile(r"(?<![A-Za-z0-9\u00c0-\u024f])[A-Za-z\u00c0-\u024f][A-Za-z\u00c0-\u024f'\.\-]*")
NUM = re.compile(r"^[\d\.\-\/\s\[\],\(\)\'\"]+$")


def word_ok(s, toks):
    """词级拼接是否可用 —— ⚠️ 2026-10-09 修：旧版直接 `"".join(words[t])` 会**吞掉番号数字与分隔符**，
    把 `33 Army` 拼成「军」、`141 Mrt Rgt/8 Gds Army` 拼成「迫击炮团近卫军」（master 本身没这些条目，
    全是词级路径造出来的伪命中，Clu 一跑就暴露 24 条）。
    新判据（两条都要满足）：
      ① src **不含数字** —— 含番号的一律交 LLM（拼接无法补「第N」）；
      ② 拿掉全部命中 token 后**只剩分隔符/空白** —— 否则说明有未覆盖成分被丢掉。
    """
    if re.search(r"\d", s):
        return False
    rest = s
    for t in toks:
        rest = rest.replace(t, "", 1)
    return not rest.strip(" \t-/.,'()[]:")


def rd(path):
    d = {}
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2 and c[0] and c[1]:
                d.setdefault(c[0], c[1])
    return d


def detect_src_first(root):
    """判定该 root 的源文本是否「从未汉化」。

    规则：只要 root 下有**任意** efile 带 `TEXT-ZH\\`，就认为存在已汉化内容，保留 GBK 优先
    （PG2 行为逐字不变）；整个 root 都没有 `TEXT-ZH` ⇒ 源文本不可能含 GBK，跳过 GBK 探测。

    实测：`D:\\OpenPG2` 21 个 efile 中 18 个有 `TEXT-ZH` ⇒ False（不动）；
          `D:\\OpenGeneral` 5 个 efile 全无 ⇒ True。
    """
    try:
        names = os.listdir(root)
    except OSError:
        return False
    for fn in names:
        if fn.upper().startswith("EFILE_") and os.path.isdir(os.path.join(root, fn, "TEXT-ZH")):
            return False
    return True


def detect_enc(root, ef, sample=30):
    """按目标 efile 的 `.xscn` **串负载**探测原文侧单字节表。

    动机（`docs\\75` 发现）：`D:\\OpenGeneral` 的 `EFILE_GUS` / `EFILE_ALBERICH` 原文是
    **cp1250**（波兰语 `Pułk` / `Jastrząb` / `Jeńcy`），按 cp1252 读会变 `Pu³k` / `Jastrz¹b`。
    实测高位字节密度：GUS 5.30% · ALBERICH 5.86% · GUS_Zx / GUS_PeG / GUS_Wx 0.00%。

    两条关键设计（都是被实测逼出来的）：
    1. **只取串负载**（`parse` + `raw_at`），不读整文件 —— `.xscn` 的二进制段任意字节会
       淹没信号，整文件打分会对 GUS_Zx / GUS_Wx / PG2 的 AG（密度 0%）误判成 cp1250。
    2. **跳过会走 `ENC_OUT` 分支的串**（与 `xscn.decode` 同判据：GBK 解得出且含 CJK）。
       已汉化的 efile（如 PG2 的 AG，`.xscn` 里 94.6% 是 GBK 中文）因此样本为空、
       恒返回 cp1252 ⇒ `ENC_IN` 对它们是空操作，PG2 行为可证明不变。
    """
    d = os.path.join(root, ef, "SCENARIO")
    if not os.path.isdir(d):
        return xscn.ENC_IN
    blob = bytearray()
    n = 0
    for fn in sorted(os.listdir(d)):
        if not fn.lower().endswith(".xscn"):
            continue
        try:
            data, items, meta = xscn.parse(os.path.join(d, fn))
        except Exception:
            continue
        for _gi, _i, off, L in items:
            raw = xscn.raw_at(data, off, L)
            if not any(b >= 0x80 for b in raw):
                continue
            try:
                s = raw.decode(xscn.ENC_OUT)
                if any("\u4e00" <= c <= "\u9fff" for c in s):
                    continue  # 已走 ENC_OUT 分支，ENC_IN 无关
            except Exception:
                pass
            blob += raw
        n += 1
        if n >= sample:
            break
    return xscn.pick_enc_from_bytes(bytes(blob), text_file=False)


def main():
    a = sys.argv[sys.argv.index("--efile") + 1] if "--efile" in sys.argv else None
    if not a:
        raise SystemExit("用法: python apply_master.py --efile PzLIGA [--with-words] "
                         "[--root D:\\OpenGeneral] [--enc-in cp1250|cp1252|utf-8|auto]")
    root = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else ROOT
    ef = xscn.norm_efile(a)
    # 必须用磁盘真实大小写：否则 `--efile GUS_Wx` 会拼成 EFILE_GUS_WX，
    # 在 Windows 上虽能打开，但备份/work 日志里会出现与实际不一致的名字
    ef = xscn.resolve_dir(root, ef) or ef
    # 原文侧单字节表（默认 auto = 按该 efile 的 .xscn 自动探测）
    sf = "--src-first" in sys.argv
    if "--gbk-first" in sys.argv:
        sf = False
    elif not sf:
        sf = detect_src_first(root)
    enc = sys.argv[sys.argv.index("--enc-in") + 1] if "--enc-in" in sys.argv else "auto"
    if enc == "auto":
        enc = detect_enc(root, ef)
    print("[enc-in] %s   [src-first] %s" % (xscn.set_enc_in(enc), xscn.set_src_first(sf)))
    with_words = "--with-words" in sys.argv
    outdir = os.path.join(os.path.dirname(os.path.dirname(HERE)), "work", ef.lower())
    os.makedirs(outdir, exist_ok=True)

    master = rd(MASTER)
    words = rd(WORDS) if with_words else {}
    # 冲突裁定表优先（resolve_master.py 产出，覆盖 master 里的多译法冲突）
    if os.path.exists(RESOLVE):
        resolve = rd(RESOLVE)
        master.update(resolve)

    D = os.path.join(root, ef, "SCENARIO")
    uniq = collections.Counter()
    for f in sorted(os.listdir(D)):
        if not f.endswith(".xscn"):
            continue
        data, its, meta = xscn.parse(os.path.join(D, f))
        for gi, i, off, L in (its or []):
            # 用 ENC_IN 而非写死 cp1252：`D:\OpenGeneral` 的 GUS/ALBERICH 原文是 cp1250
            # （`docs\76`）。当 ENC_IN == "cp1252"（PG2 全域）时与原写法逐字符等价。
            # 刻意**不走 xscn.decode()**：那条路会先试 GBK，而这里是「取源文本」不是「判是否已汉化」。
            s = xscn.raw_at(data, off, L).decode(xscn.ENC_IN, "replace").strip()
            if s:
                uniq[s] += 1

    mapped = {}
    miss = []
    wmiss = []
    for s in uniq:
        if s in master:
            mapped[s] = master[s]
        else:
            miss.append(s)
    if with_words:
        rest = miss
        miss = []
        for s in rest:
            toks = TOK.findall(s)
            if toks and all(t in words for t in toks) and word_ok(s, toks):
                mapped[s] = "".join(words[t] for t in toks)
                wmiss.append(s)
            else:
                miss.append(s)

    # 纯代号（编号）也算「程序已定＝保留原文」，不进 miss
    code = [s for s in miss if NUM.match(s) or not TOK.search(s)]
    miss = [s for s in miss if s not in code]
    miss.sort(key=lambda s: -uniq[s])

    with io.open(os.path.join(outdir, "prematch-map.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tdst\n")
        for s in sorted(mapped):
            f.write("%s\t%s\n" % (s, mapped[s]))
    with io.open(os.path.join(outdir, "prematch-miss.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tn\n")
        for s in miss:
            f.write("%s\t%d\n" % (s, uniq[s]))

    n = len(uniq)
    print("[%s]" % root)
    print("%s .xscn 唯一串 %d / 槽 %d" % (ef, n, sum(uniq.values())))
    print("master 精确命中  %5d (%.1f%%)" % (len(mapped) - len(wmiss), 100.0 * (len(mapped) - len(wmiss)) / n))
    if with_words:
        print("词级组合命中    %5d (%.1f%%)" % (len(wmiss), 100.0 * len(wmiss) / n))
    print("纯代号（保留）  %5d (%.1f%%)" % (len(code), 100.0 * len(code) / n))
    print("=> 程序覆盖 %.1f%%；需 LLM 的仅 %d 条 (%.1f%%)" %
          (100.0 * (len(mapped) + len(code)) / n, len(miss), 100.0 * len(miss) / n))
    print("已写 %s\\prematch-map.tsv / prematch-miss.tsv" % outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
