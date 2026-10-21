# -*- coding: utf-8 -*-
"""PeG 分辨率补丁 v5（由 diff 反推重建）——生成于 2026-10-13

本文件由 work/peg/diff_res_canvas.py 自动生成，请勿手改；改口径请改生成器。

来源：母本 PeG030.exe（md5 c462e897b3aa1c384870c857ce9e01df）
      与 v4 实验产物 PeG030res.exe（md5 2107b73bbfd4213719b622a1a9d4c6ad）逐字节 diff
      = 差异 382 字节 / 259 个连续段 / 259 个站点
      v4 站点对应分辨率 1024x768，按站点重放与 v4 产物**逐字节相同**

纪律（继承原 v4）：
  * 绝不修改母本 PeG030.exe；只读当母本，产物另写副本；
  * 每个站点写入前做内容断言（当前整数必须等于记录里的旧值），任一不符即整体拒改；
  * 先写内存 -> 回读校验 -> 才落盘；
  * 落盘后复核中文补丁三处仍在（charset / codepage / LCID）；
  * 站点里若还有认不出的改动，脚本整体拒绝（绝不产出半成品 exe）。

站点语义（tag）：
  w / w-1 / w-4    绝对值：800 / 799 / 796  -> w / w-1 / w-4
  h / h-1          绝对值：600 / 599        -> h / h-1
  h-28 / h-30      绝对值：571|572 / 570    -> h-28 / h-30
  dx / dy          平移：旧值 + (w-800) / 旧值 + (h-600)
  （799/796/599/570/572 的绝对标签与 dx/dy 代数恒等；唯一不等价的是 571 -> h-28）

用法：
  python patch_resolution.py                              干跑：校验母本、逐点断言、打印计划
  python patch_resolution.py --repro                      复现 v4 产物并比对 md5（完整性自证）
  python patch_resolution.py --w 1280 --h 960 --out out/x.exe           干跑新分辨率
  python patch_resolution.py --w 1280 --h 960 --out out/x.exe --apply   落盘
  默认只写 work/peg/out/ 下的副本；要部署到安装目录请自己显式 --out。

母本若换版本（再次汉化改动等），md5 校验会失败并拒绝运行，需重跑 diff_res_canvas.py。
"""
import argparse
import hashlib
import os
import struct
import sys

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SRC = os.path.join(GAME, "PeG030.exe")
DST_V4 = os.path.join(GAME_ALT, "PeG030res.exe")
SRC_MD5 = "c462e897b3aa1c384870c857ce9e01df"
DST_V4_MD5 = "2107b73bbfd4213719b622a1a9d4c6ad"
HERE = os.path.dirname(os.path.abspath(__file__))

# 中文补丁必须在产物里保留的三处（文件偏移, 期望字节）
CN_CHECKS = [
    ("charset 0x4718E3 (.text)", 0x070CE3, bytes.fromhex("6a86")),
    ("__mbcodepage 0x4ABC8C (.data)", 0x0A948C, bytes.fromhex("a803")),
    ("LCID fo 0x7BE86", 0x07BE86, bytes.fromhex("b804080000")),
]

# 认不出的改动点（必须为空；非空则拒绝运行）
UNKNOWN = [

]

# (文件偏移, VA, 旧值, 标签, 宽度)，备注 = 原指令
SITES = [
    (0x01DFF2, 0x41EBF2,   800, "w"    , 2),  # .text  cmp ecx, 0x320
    (0x01DFFB, 0x41EBFB,   800, "w"    , 2),  # .text  cmp dword ptr [ebp + 8], 0x320
    (0x01E075, 0x41EC75,   600, "h"    , 2),  # .text  cmp edx, 0x258
    (0x01E07E, 0x41EC7E,   600, "h"    , 2),  # .text  cmp dword ptr [ebp + 0xc], 0x258
    (0x01E0A7, 0x41ECA7,   600, "h"    , 2),  # .text  pop eax
    (0x02261A, 0x42321A,   800, "w"    , 2),  # .text  cmp eax, 0x320
    (0x022624, 0x423224,   799, "w-1"  , 2),  # .text  mov word ptr [ebp + 0x10], 0x31f
    (0x02262C, 0x42322C,   600, "h"    , 2),  # .text  cmp ecx, 0x258
    (0x022636, 0x423236,   599, "h-1"  , 2),  # .text  mov dword ptr [ebp + 0x14], 0x8b660257
    (0x0227E3, 0x4233E3,   800, "w"    , 2),  # .text  cmp edx, 0x320
    (0x0227ED, 0x4233ED,   799, "w-1"  , 2),  # .text  mov word ptr [ebp + 0x10], 0x31f
    (0x0227F4, 0x4233F4,   600, "h"    , 2),  # .text  pop eax
    (0x0227FE, 0x4233FE,   599, "h-1"  , 2),  # .text  mov dword ptr [ebp + 0x14], 0xbf0f0257
    (0x0240D7, 0x424CD7,   800, "w"    , 2),  # .text  cmp eax, 0x320
    (0x0240E3, 0x424CE3,   600, "h"    , 2),  # .text  cmp ecx, 0x258
    (0x024F90, 0x425B90,   800, "w"    , 2),  # .text  mov dword ptr [ebp - 8], 0x320
    (0x024F97, 0x425B97,   600, "h"    , 2),  # .text  mov dword ptr [ebp - 4], 0x258
    (0x024FE2, 0x425BE2,   800, "w"    , 2),  # .text  mov dword ptr [ebp - 8], 0x320
    (0x024FE9, 0x425BE9,   600, "h"    , 2),  # .text  mov dword ptr [ebp - 4], 0x258
    (0x03A626, 0x43B226,   800, "w"    , 2),  # .text  cmp dword ptr [0x61e928], 0x320
    (0x03A632, 0x43B232,   799, "w-1"  , 2),  # .text  mov dword ptr [0x61e928], 0x31f
    (0x03A63C, 0x43B23C,   600, "h"    , 2),  # .text  cmp dword ptr [0x61e92c], 0x258
    (0x03A648, 0x43B248,   599, "h-1"  , 2),  # .text  mov dword ptr [0x61e92c], 0x257
    (0x03B0B5, 0x43BCB5,   600, "h"    , 2),  # .text  mov dword ptr [ebp - 4], 0x258
    (0x03B189, 0x43BD89,   800, "w"    , 2),  # .text  cmp dword ptr [0x61e928], 0x320
    (0x03B195, 0x43BD95,   799, "w-1"  , 2),  # .text  mov dword ptr [0x61e928], 0x31f
    (0x03B19F, 0x43BD9F,   600, "h"    , 2),  # .text  cmp dword ptr [0x61e92c], 0x258
    (0x03B1AB, 0x43BDAB,   599, "h-1"  , 2),  # .text  mov dword ptr [0x61e92c], 0x257
    (0x040B96, 0x441796,   600, "h"    , 2),  # .text  
    (0x040B9B, 0x44179B,   800, "w"    , 2),  # .text  push 0x320
    (0x040E79, 0x441A79,   600, "h"    , 2),  # .text  push 0x258
    (0x040E7E, 0x441A7E,   800, "w"    , 2),  # .text  push 0x320
    (0x0413AF, 0x441FAF,   800, "w"    , 2),  # .text  mov dword ptr [ebp - 0x70], 0x320
    (0x0413B6, 0x441FB6,   600, "h"    , 2),  # .text  mov dword ptr [ebp - 0x74], 0x258
    (0x04B933, 0x44C533,   800, "w"    , 2),  # .text  push 0x320
    (0x04B95F, 0x44C55F,   600, "h"    , 2),  # .text  push 0x258
    (0x04B964, 0x44C564,   800, "w"    , 2),  # .text  push 0x320
    (0x04B969, 0x44C569,   572, "h-28" , 2),  # .text  push 0x23c
    (0x04B999, 0x44C599,   796, "w-4"  , 2),  # .text  push 0x31c
    (0x04B9B2, 0x44C5B2,   570, "h-30" , 2),  # .text  inc dword ptr [ebx + 0x3a6814c4]
    (0x04BB2A, 0x44C72A,   800, "w"    , 2),  # .text  cmp dword ptr [0x663388], 0x320
    (0x04BB46, 0x44C746,   800, "w"    , 2),  # .text  mov dword ptr [0x663388], 0x320
    (0x04BB71, 0x44C771,   600, "h"    , 2),  # .text  cmp dword ptr [0x66338c], 0x258
    (0x04BB8E, 0x44C78E,   600, "h"    , 2),  # .text  mov dword ptr [0x66338c], 0x258
    (0x04BC63, 0x44C863,   800, "w"    , 2),  # .text  
    (0x04BC80, 0x44C880,   800, "w"    , 2),  # .text  mov dword ptr [0x6769a8], 0x320
    (0x04BCAA, 0x44C8AA,   600, "h"    , 2),  # .text  cmp dword ptr [0x6769ac], 0x258
    (0x04BCC7, 0x44C8C7,   600, "h"    , 2),  # .text  mov dword ptr [0x6769ac], 0x258
    (0x04C061, 0x44CC61,   800, "w"    , 2),  # .text  
    (0x04C07E, 0x44CC7E,   800, "w"    , 2),  # .text  mov dword ptr [0x6769a8], 0x320
    (0x04C0A8, 0x44CCA8,   600, "h"    , 2),  # .text  cmp dword ptr [0x6769ac], 0x258
    (0x04C0C5, 0x44CCC5,   600, "h"    , 2),  # .text  mov dword ptr [0x6769ac], 0x258
    (0x08C3AE, 0x48EBAE,   799, "w-1"  , 2),  # .data  
    (0x08C3B0, 0x48EBB0,   599, "h-1"  , 2),  # .data  
    (0x08DC76, 0x490476,   799, "w-1"  , 2),  # .data  
    (0x08DC78, 0x490478,   571, "h-28" , 2),  # .data  
    (0x08DC96, 0x490496,   762, "dx"   , 2),  # .data  
    (0x08DC9A, 0x49049A,   787, "dx"   , 2),  # .data  
    (0x08DCBA, 0x4904BA,   762, "dx"   , 2),  # .data  
    (0x08DCBE, 0x4904BE,   787, "dx"   , 2),  # .data  
    (0x08DCDE, 0x4904DE,   762, "dx"   , 2),  # .data  
    (0x08DCE2, 0x4904E2,   787, "dx"   , 2),  # .data  
    (0x08DD02, 0x490502,   762, "dx"   , 2),  # .data  
    (0x08DD06, 0x490506,   787, "dx"   , 2),  # .data  
    (0x08DD26, 0x490526,   762, "dx"   , 2),  # .data  
    (0x08DD2A, 0x49052A,   787, "dx"   , 2),  # .data  
    (0x08DD4A, 0x49054A,   762, "dx"   , 2),  # .data  
    (0x08DD4E, 0x49054E,   787, "dx"   , 2),  # .data  
    (0x08DD6E, 0x49056E,   762, "dx"   , 2),  # .data  
    (0x08DD72, 0x490572,   787, "dx"   , 2),  # .data  
    (0x08E216, 0x490A16,   799, "w-1"  , 2),  # .data  
    (0x08E218, 0x490A18,   571, "h-28" , 2),  # .data  
    (0x09134E, 0x493B4E,   756, "dx"   , 2),  # .data  
    (0x091352, 0x493B52,   781, "dx"   , 2),  # .data  
    (0x0915FE, 0x493DFE,   799, "w-1"  , 2),  # .data  
    (0x091600, 0x493E00,   571, "h-28" , 2),  # .data  
    (0x091876, 0x494076,   799, "w-1"  , 2),  # .data  
    (0x091878, 0x494078,   571, "h-28" , 2),  # .data  
    (0x091A22, 0x494222,   762, "dx"   , 2),  # .data  
    (0x091A26, 0x494226,   787, "dx"   , 2),  # .data  
    (0x091A46, 0x494246,   762, "dx"   , 2),  # .data  
    (0x091A4A, 0x49424A,   787, "dx"   , 2),  # .data  
    (0x091A6A, 0x49426A,   762, "dx"   , 2),  # .data  
    (0x091A6E, 0x49426E,   787, "dx"   , 2),  # .data  
    (0x091A8E, 0x49428E,   762, "dx"   , 2),  # .data  
    (0x091A92, 0x494292,   787, "dx"   , 2),  # .data  
    (0x091AB2, 0x4942B2,   762, "dx"   , 2),  # .data  
    (0x091AB6, 0x4942B6,   787, "dx"   , 2),  # .data  
    (0x091AD6, 0x4942D6,   762, "dx"   , 2),  # .data  
    (0x091ADA, 0x4942DA,   787, "dx"   , 2),  # .data  
    (0x091AFA, 0x4942FA,   762, "dx"   , 2),  # .data  
    (0x091AFE, 0x4942FE,   787, "dx"   , 2),  # .data  
    (0x091B1E, 0x49431E,   762, "dx"   , 2),  # .data  
    (0x091B22, 0x494322,   787, "dx"   , 2),  # .data  
    (0x091B42, 0x494342,   762, "dx"   , 2),  # .data  
    (0x091B46, 0x494346,   787, "dx"   , 2),  # .data  
    (0x091B66, 0x494366,   762, "dx"   , 2),  # .data  
    (0x091B6A, 0x49436A,   787, "dx"   , 2),  # .data  
    (0x091B8A, 0x49438A,   762, "dx"   , 2),  # .data  
    (0x091B8E, 0x49438E,   787, "dx"   , 2),  # .data  
    (0x091BAE, 0x4943AE,   762, "dx"   , 2),  # .data  
    (0x091BB2, 0x4943B2,   787, "dx"   , 2),  # .data  
    (0x091BD2, 0x4943D2,   762, "dx"   , 2),  # .data  
    (0x091BD6, 0x4943D6,   787, "dx"   , 2),  # .data  
    (0x091BF6, 0x4943F6,   762, "dx"   , 2),  # .data  
    (0x091BFA, 0x4943FA,   787, "dx"   , 2),  # .data  
    (0x091C1E, 0x49441E,   799, "w-1"  , 2),  # .data  
    (0x091C20, 0x494420,   571, "h-28" , 2),  # .data  
    (0x0921CA, 0x4949CA,   762, "dx"   , 2),  # .data  
    (0x0921CE, 0x4949CE,   778, "dx"   , 2),  # .data  
    (0x0921EE, 0x4949EE,   762, "dx"   , 2),  # .data  
    (0x0921F2, 0x4949F2,   778, "dx"   , 2),  # .data  
    (0x092212, 0x494A12,   762, "dx"   , 2),  # .data  
    (0x092216, 0x494A16,   787, "dx"   , 2),  # .data  
    (0x092236, 0x494A36,   754, "dx"   , 2),  # .data  
    (0x09223A, 0x494A3A,   788, "dx"   , 2),  # .data  
    (0x09225A, 0x494A5A,   762, "dx"   , 2),  # .data  
    (0x09225E, 0x494A5E,   787, "dx"   , 2),  # .data  
    (0x09227E, 0x494A7E,   762, "dx"   , 2),  # .data  
    (0x092282, 0x494A82,   787, "dx"   , 2),  # .data  
    (0x0922A2, 0x494AA2,   762, "dx"   , 2),  # .data  
    (0x0922A6, 0x494AA6,   787, "dx"   , 2),  # .data  
    (0x0922C6, 0x494AC6,   762, "dx"   , 2),  # .data  
    (0x0922CA, 0x494ACA,   787, "dx"   , 2),  # .data  
    (0x0922EA, 0x494AEA,   762, "dx"   , 2),  # .data  
    (0x0922EE, 0x494AEE,   787, "dx"   , 2),  # .data  
    (0x09230E, 0x494B0E,   762, "dx"   , 2),  # .data  
    (0x092312, 0x494B12,   787, "dx"   , 2),  # .data  
    (0x092332, 0x494B32,   762, "dx"   , 2),  # .data  
    (0x092336, 0x494B36,   787, "dx"   , 2),  # .data  
    (0x092356, 0x494B56,   762, "dx"   , 2),  # .data  
    (0x09235A, 0x494B5A,   787, "dx"   , 2),  # .data  
    (0x09237A, 0x494B7A,   762, "dx"   , 2),  # .data  
    (0x09237E, 0x494B7E,   787, "dx"   , 2),  # .data  
    (0x0923A2, 0x494BA2,   799, "w-1"  , 2),  # .data  
    (0x0923A4, 0x494BA4,   571, "h-28" , 2),  # .data  
    (0x096540, 0x498D40,   799, "w-1"  , 2),  # .data  
    (0x096544, 0x498D44,   571, "h-28" , 2),  # .data  
    (0x09D7B6, 0x49FFB6,   799, "w-1"  , 2),  # .data  
    (0x09D7B8, 0x49FFB8,   599, "h-1"  , 2),  # .data  
    (0x09F3A6, 0x4A1BA6,   799, "w-1"  , 2),  # .data  
    (0x09F3A8, 0x4A1BA8,   571, "h-28" , 2),  # .data  
    (0x09F86A, 0x4A206A,   762, "dx"   , 2),  # .data  
    (0x09F86E, 0x4A206E,   787, "dx"   , 2),  # .data  
    (0x09F88E, 0x4A208E,   762, "dx"   , 2),  # .data  
    (0x09F892, 0x4A2092,   787, "dx"   , 2),  # .data  
    (0x09F8B2, 0x4A20B2,   762, "dx"   , 2),  # .data  
    (0x09F8B6, 0x4A20B6,   787, "dx"   , 2),  # .data  
    (0x09F8D6, 0x4A20D6,   762, "dx"   , 2),  # .data  
    (0x09F8DA, 0x4A20DA,   787, "dx"   , 2),  # .data  
    (0x09F8FA, 0x4A20FA,   762, "dx"   , 2),  # .data  
    (0x09F8FE, 0x4A20FE,   787, "dx"   , 2),  # .data  
    (0x09F91E, 0x4A211E,   762, "dx"   , 2),  # .data  
    (0x09F922, 0x4A2122,   787, "dx"   , 2),  # .data  
    (0x09F942, 0x4A2142,   762, "dx"   , 2),  # .data  
    (0x09F946, 0x4A2146,   787, "dx"   , 2),  # .data  
    (0x09F96A, 0x4A216A,   799, "w-1"  , 2),  # .data  
    (0x09F96C, 0x4A216C,   571, "h-28" , 2),  # .data  
    (0x09F9B2, 0x4A21B2,   762, "dx"   , 2),  # .data  
    (0x09F9B6, 0x4A21B6,   787, "dx"   , 2),  # .data  
    (0x09F9D6, 0x4A21D6,   760, "dx"   , 2),  # .data  
    (0x09F9DA, 0x4A21DA,   768, "dx"   , 2),  # .data  
    (0x09F9FA, 0x4A21FA,   760, "dx"   , 2),  # .data  
    (0x09F9FE, 0x4A21FE,   799, "w-1"  , 2),  # .data  
    (0x09FA1E, 0x4A221E,   762, "dx"   , 2),  # .data  
    (0x09FA22, 0x4A2222,   787, "dx"   , 2),  # .data  
    (0x09FA42, 0x4A2242,   760, "dx"   , 2),  # .data  
    (0x09FA46, 0x4A2246,   768, "dx"   , 2),  # .data  
    (0x09FA66, 0x4A2266,   760, "dx"   , 2),  # .data  
    (0x09FA6A, 0x4A226A,   799, "w-1"  , 2),  # .data  
    (0x09FA8A, 0x4A228A,   762, "dx"   , 2),  # .data  
    (0x09FA8E, 0x4A228E,   787, "dx"   , 2),  # .data  
    (0x09FAB2, 0x4A22B2,   799, "w-1"  , 2),  # .data  
    (0x09FAB4, 0x4A22B4,   571, "h-28" , 2),  # .data  
    (0x09FAFA, 0x4A22FA,   762, "dx"   , 2),  # .data  
    (0x09FAFE, 0x4A22FE,   787, "dx"   , 2),  # .data  
    (0x09FB1E, 0x4A231E,   762, "dx"   , 2),  # .data  
    (0x09FB22, 0x4A2322,   787, "dx"   , 2),  # .data  
    (0x09FB42, 0x4A2342,   762, "dx"   , 2),  # .data  
    (0x09FB46, 0x4A2346,   787, "dx"   , 2),  # .data  
    (0x09FB66, 0x4A2366,   762, "dx"   , 2),  # .data  
    (0x09FB6A, 0x4A236A,   787, "dx"   , 2),  # .data  
    (0x09FB8A, 0x4A238A,   762, "dx"   , 2),  # .data  
    (0x09FB8E, 0x4A238E,   787, "dx"   , 2),  # .data  
    (0x09FBAE, 0x4A23AE,   762, "dx"   , 2),  # .data  
    (0x09FBB2, 0x4A23B2,   787, "dx"   , 2),  # .data  
    (0x09FBD2, 0x4A23D2,   762, "dx"   , 2),  # .data  
    (0x09FBD6, 0x4A23D6,   787, "dx"   , 2),  # .data  
    (0x09FBF6, 0x4A23F6,   762, "dx"   , 2),  # .data  
    (0x09FBFA, 0x4A23FA,   787, "dx"   , 2),  # .data  
    (0x09FC1A, 0x4A241A,   762, "dx"   , 2),  # .data  
    (0x09FC1E, 0x4A241E,   787, "dx"   , 2),  # .data  
    (0x09FC3E, 0x4A243E,   762, "dx"   , 2),  # .data  
    (0x09FC42, 0x4A2442,   787, "dx"   , 2),  # .data  
    (0x09FC62, 0x4A2462,   762, "dx"   , 2),  # .data  
    (0x09FC66, 0x4A2466,   787, "dx"   , 2),  # .data  
    (0x09FC86, 0x4A2486,   762, "dx"   , 2),  # .data  
    (0x09FC8A, 0x4A248A,   787, "dx"   , 2),  # .data  
    (0x09FCAA, 0x4A24AA,   762, "dx"   , 2),  # .data  
    (0x09FCAE, 0x4A24AE,   787, "dx"   , 2),  # .data  
    (0x09FCF4, 0x4A24F4,   576, "dy"   , 2),  # .data  
    (0x09FCF6, 0x4A24F6,   790, "dx"   , 2),  # .data  
    (0x09FCF8, 0x4A24F8,   594, "dy"   , 2),  # .data  
    (0x09FD1A, 0x4A251A,   799, "w-1"  , 2),  # .data  
    (0x09FD1C, 0x4A251C,   571, "h-28" , 2),  # .data  
    (0x09FD62, 0x4A2562,   762, "dx"   , 2),  # .data  
    (0x09FD66, 0x4A2566,   787, "dx"   , 2),  # .data  
    (0x09FD86, 0x4A2586,   762, "dx"   , 2),  # .data  
    (0x09FD8A, 0x4A258A,   787, "dx"   , 2),  # .data  
    (0x09FDAE, 0x4A25AE,   799, "w-1"  , 2),  # .data  
    (0x09FDB0, 0x4A25B0,   599, "h-1"  , 2),  # .data  
    (0x0A00FE, 0x4A28FE,   799, "w-1"  , 2),  # .data  
    (0x0A0100, 0x4A2900,   599, "h-1"  , 2),  # .data  
    (0x0A25EE, 0x4A4DEE,   799, "w-1"  , 2),  # .data  
    (0x0A25F0, 0x4A4DF0,   571, "h-28" , 2),  # .data  
    (0x0A3866, 0x4A6066,   756, "dx"   , 2),  # .data  
    (0x0A386A, 0x4A606A,   772, "dx"   , 2),  # .data  
    (0x0A388A, 0x4A608A,   756, "dx"   , 2),  # .data  
    (0x0A388E, 0x4A608E,   772, "dx"   , 2),  # .data  
    (0x0A5E4A, 0x4A864A,   762, "dx"   , 2),  # .data  
    (0x0A5E4E, 0x4A864E,   787, "dx"   , 2),  # .data  
    (0x0A5E6E, 0x4A866E,   762, "dx"   , 2),  # .data  
    (0x0A5E72, 0x4A8672,   787, "dx"   , 2),  # .data  
    (0x0A5E92, 0x4A8692,   762, "dx"   , 2),  # .data  
    (0x0A5E96, 0x4A8696,   787, "dx"   , 2),  # .data  
    (0x0A5EB6, 0x4A86B6,   762, "dx"   , 2),  # .data  
    (0x0A5EBA, 0x4A86BA,   787, "dx"   , 2),  # .data  
    (0x0A5EDA, 0x4A86DA,   762, "dx"   , 2),  # .data  
    (0x0A5EDE, 0x4A86DE,   787, "dx"   , 2),  # .data  
    (0x0A5EFE, 0x4A86FE,   762, "dx"   , 2),  # .data  
    (0x0A5F02, 0x4A8702,   787, "dx"   , 2),  # .data  
    (0x0A5F22, 0x4A8722,   762, "dx"   , 2),  # .data  
    (0x0A5F26, 0x4A8726,   787, "dx"   , 2),  # .data  
    (0x0A5F46, 0x4A8746,   762, "dx"   , 2),  # .data  
    (0x0A5F4A, 0x4A874A,   787, "dx"   , 2),  # .data  
    (0x0A5F6A, 0x4A876A,   762, "dx"   , 2),  # .data  
    (0x0A5F6E, 0x4A876E,   787, "dx"   , 2),  # .data  
    (0x0A5F8E, 0x4A878E,   762, "dx"   , 2),  # .data  
    (0x0A5F92, 0x4A8792,   787, "dx"   , 2),  # .data  
    (0x0A5FB2, 0x4A87B2,   762, "dx"   , 2),  # .data  
    (0x0A5FB6, 0x4A87B6,   787, "dx"   , 2),  # .data  
    (0x0A5FD6, 0x4A87D6,   762, "dx"   , 2),  # .data  
    (0x0A5FDA, 0x4A87DA,   787, "dx"   , 2),  # .data  
    (0x0A5FFA, 0x4A87FA,   762, "dx"   , 2),  # .data  
    (0x0A5FFE, 0x4A87FE,   787, "dx"   , 2),  # .data  
    (0x0A601E, 0x4A881E,   762, "dx"   , 2),  # .data  
    (0x0A6022, 0x4A8822,   787, "dx"   , 2),  # .data  
    (0x0A6042, 0x4A8842,   762, "dx"   , 2),  # .data  
    (0x0A6046, 0x4A8846,   787, "dx"   , 2),  # .data  
    (0x0A606A, 0x4A886A,   799, "w-1"  , 2),  # .data  
    (0x0A606C, 0x4A886C,   571, "h-28" , 2),  # .data  
    (0x0A6C66, 0x4A9466,   799, "w-1"  , 2),  # .data  
    (0x0A6C68, 0x4A9468,   571, "h-28" , 2),  # .data  
    (0x0A6E5A, 0x4A965A,   750, "dx"   , 2),  # .data  
    (0x0A6E5E, 0x4A965E,   776, "dx"   , 2),  # .data  
    (0x0A8FAE, 0x4AB7AE,   799, "w-1"  , 2),  # .data  
    (0x0A8FB0, 0x4AB7B0,   599, "h-1"  , 2),  # .data  
    (0x0A901A, 0x4AB81A,   799, "w-1"  , 2),  # .data  
    (0x0A901C, 0x4AB81C,   599, "h-1"  , 2),  # .data  
]


def md5f(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def new_value(tag, old, w, h):
    if tag == "w":
        return w
    if tag == "w-1":
        return w - 1
    if tag == "w-4":
        return w - 4
    if tag == "h":
        return h
    if tag == "h-1":
        return h - 1
    if tag == "h-28":
        return h - 28
    if tag == "h-30":
        return h - 30
    if tag == "dx":
        return old + (w - 800)
    if tag == "dy":
        return old + (h - 600)
    raise SystemExit("未知标签 %r" % tag)


def build(w, h, quiet=False):
    """在内存里造出产物字节；返回 (bytes, 计划列表)"""
    if w < 800 or h < 600:
        raise SystemExit("拒绝：只有 w>=800 且 h>=600 才成立（右移/下拉假设），收到 %dx%d" % (w, h))
    if UNKNOWN:
        raise SystemExit("拒绝：还有 %d 个认不出的改动点，需先补齐语义" % len(UNKNOWN))
    raw = open(SRC, "rb").read()
    got = md5f(SRC)
    if got != SRC_MD5:
        raise SystemExit("拒绝：母本 md5 %s != 记录 %s" % (got, SRC_MD5))
    buf = bytearray(raw)
    plan = []
    for fo, va, old, tag, width in SITES:
        cur = int.from_bytes(buf[fo:fo + width], "little")
        nv = new_value(tag, old, w, h)
        if cur != old:
            raise SystemExit("内容断言失败 @fo 0x%06X VA 0x%06X [%s]：当前 %d，记录旧值 %d" % (fo, va, tag, cur, old))
        if not (0 <= nv < (1 << (8 * width))):
            raise SystemExit("新值越界 @fo 0x%06X [%s u%d] -> %d" % (fo, tag, width, nv))
        buf[fo:fo + width] = nv.to_bytes(width, "little")
        plan.append((fo, va, old, nv, tag, width))
    for lbl, fo, exp in CN_CHECKS:
        gotb = bytes(buf[fo:fo + len(exp)])
        if gotb != exp:
            raise SystemExit("中文补丁被破坏：%s 期望 %s 实得 %s" % (lbl, exp.hex(), gotb.hex()))
    if not quiet:
        for fo, va, old, nv, tag, width in plan:
            print("  0x%06X VA 0x%06X  %-5d -> %-5d [%s u%d]" % (fo, va, old, nv, tag, width))
    return bytes(buf), plan


def write_out(buf, path):
    tmp = path + ".tmp"
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(tmp, "wb") as f:
        f.write(buf)
    if open(tmp, "rb").read() != buf:
        raise SystemExit("回读校验失败，未落盘：%s" % tmp)
    os.replace(tmp, path)
    print("已落盘 %s  (%d B, md5 %s)" % (path, len(buf), md5f(path)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--w", type=int, default=1024)
    ap.add_argument("--h", type=int, default=768)
    ap.add_argument("--out", default=None)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--repro", action="store_true", help="复现 v4 产物并比对 md5")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    print("母本 %s  md5 %s" % (SRC, md5f(SRC)))
    print("目标 %dx%d，站点 %d 个" % (a.w, a.h, len(SITES)))
    buf, plan = build(a.w, a.h, quiet=a.quiet)
    print("内存构建完成：%d 个站点已改，中文补丁三处仍在" % len(plan))

    if a.repro:
        out = a.out or os.path.join(HERE, "out", "PeG030res.repro.exe")
        write_out(buf, out)
        got = md5f(out)
        rec = md5f(DST_V4) if os.path.exists(DST_V4) else DST_V4_MD5
        ok = got == DST_V4_MD5
        print("复现结果 md5 %s；v4 产物 md5 %s；%s" % (got, rec, "逐字节一致 ✅" if ok else "⚠不一致"))
        return 0 if ok else 2

    out = a.out or os.path.join(HERE, "out", "PeG030res.%dx%d.exe" % (a.w, a.h))
    if a.apply:
        write_out(buf, out)
    else:
        print("干跑：未写盘。要落盘加 --apply，产物将写到 %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
