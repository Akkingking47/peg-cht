# -*- coding: utf-8 -*-
r"""
PGForever.exe 补丁总控
=====================
集中管理所有 exe 字节补丁，可重复执行、可校验、可回滚。
文件恒为 753664 字节，全部为等长原地替换。

补丁清单
--------
P1  manifest 追加 <activeCodePage>UTF-8</activeCodePage>
    目的：把进程 ACP 改成 65001，使 WideCharToMultiByte(CP_ACP) 输出 UTF-8，
          HTMLayout 按 UTF-8 解析时中文不再乱码。
    位置：内嵌 RT_MANIFEST，文件偏移 0xAC27C 起（见 patch_manifest.py）

P2  ⚠️ 已废弃/回退 —— 0x6CA3E 的 sar eax,1 -> shl eax,1
    该点位于 fwrite 内部的 W2M 转换，与屏幕显示无关。
    （保留说明，勿再施加）

P3  L7 exe 硬编码文案汉化（77 处，见 patch_exe_strings.py）

P4  ★ 中文长文本截断修复（本脚本）
    位置：0x4016A0，文件偏移 0xAA0，6 字节
    原：8B 56 04      mov edx, [esi+4]
        8B 42 F4      mov eax, [edx-0xC]
    新：90 × 6        NOP
    原理：
      0x401680 函数先把宽字符 HTML 经 0x402B50(W2U8, CP_UTF8) 转成
      局部 std::string 的 UTF-8 字节流，然后调用
      HTMLayoutSetElementHtml(hElem, utf8bytes, htmlLength, where)。
      原代码把 htmlLength 取成「源宽串的字符数」，
      而数据是「UTF-8 字节数」（中文 3 字节/字符）
      → HTMLayout 只解析前 N 字节，HTML 不闭合，
        列表后面的条目被截断/整条消失，并泄漏默认模板的 "body>"。
      0x402B50 返回时 eax 恰为「实际写入的 UTF-8 字节数」
      （其结尾只改 ebx），故把中间两条无用/错误指令 NOP 掉，
      直接用 eax 即得正确长度。

用法
----
    python patch_exe_all.py status     # 查看各补丁状态
    python patch_exe_all.py apply-p4   # 施加 P4
    python patch_exe_all.py revert-p4  # 回滚 P4
"""
import hashlib
import os
import shutil
import subprocess
import sys
import time

EXE = r'D:\PGForever1.021\PGForever.exe'
BAKDIR = r'D:\DSH\军事游戏汉化\pgforever\backup'
BAK_P4 = os.path.join(BAKDIR, 'PGForever.before-len-fix-P1P2P3.exe')

P4_OFF = 0xAA0
P4_OLD = bytes.fromhex('8B56048B42F4')
P4_NEW = bytes.fromhex('909090909090')


def kill():
    subprocess.run(['taskkill', '/F', '/IM', 'PGForever.exe'], capture_output=True)
    time.sleep(0.8)


def md5(b):
    return hashlib.md5(b).hexdigest()


def p4_state(raw):
    cur = raw[P4_OFF:P4_OFF + 6]
    if cur == P4_OLD:
        return '原始(未修)'
    if cur == P4_NEW:
        return '已修复'
    return '未知 %s' % cur.hex()


def status():
    raw = open(EXE, 'rb').read()
    print('PGForever.exe  %d 字节  md5=%s' % (len(raw), md5(raw)))
    print('  P4 中文长文本截断修复 @0x%X : %s' % (P4_OFF, p4_state(raw)))
    for tag in ('PGForever.before-w2m-patch.exe',
                'PGForever.before-L7.exe',
                'PGForever.before-len-fix-P1P2P3.exe'):
        p = os.path.join(BAKDIR, tag)
        if os.path.exists(p):
            d = open(p, 'rb').read()
            print('  备份 %-40s %d  md5=%s' % (tag, len(d), md5(d)[:16]))
    return raw


def apply_p4():
    raw = status()
    if raw[P4_OFF:P4_OFF + 6] == P4_NEW:
        print('P4 已是修复状态，无需操作。'); return
    if raw[P4_OFF:P4_OFF + 6] != P4_OLD:
        print('!! 0x%X 字节不符，中止。' % P4_OFF); return
    if not os.path.exists(BAK_P4):
        os.makedirs(BAKDIR, exist_ok=True)
        kill(); shutil.copy2(EXE, BAK_P4); print('备份 ->', BAK_P4)
    kill()
    buf = bytearray(raw)
    buf[P4_OFF:P4_OFF + 6] = P4_NEW
    open(EXE, 'wb').write(bytes(buf))
    n = open(EXE, 'rb').read()
    print('P4 已施加。大小 %d -> %d %s' % (len(raw), len(n),
                                        'OK' if len(n) == len(raw) else '!!! 变了'))
    status()


def revert_p4():
    if not os.path.exists(BAK_P4):
        print('无 P4 备份', BAK_P4); return
    kill(); shutil.copy2(BAK_P4, EXE)
    print('P4 已回滚 <-', BAK_P4)
    status()


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'status'
    if mode == 'status':
        status()
    elif mode == 'apply-p4':
        apply_p4()
    elif mode == 'revert-p4':
        revert_p4()
    else:
        print(__doc__)


main()
