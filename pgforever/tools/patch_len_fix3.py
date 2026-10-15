# -*- coding: utf-8 -*-
r"""
修复补丁 v3（关键理解修正）
==========================
0x401680 真实逻辑：
    mov  ecx, [esi+4]          ; 源宽串
    lea  eax, [esp+8]
    push 3                     ; CP_UTF8
    mov  [esp+8], eax
    push ecx
    lea  eax, [esp+0xc]
    call 0x402B50              ; W2U8(局部std::string&, 3, 宽串) → 返回 eax = 写入的 UTF-8 字节数
    mov  edx, [esi+4]          ; ★ 无用（覆盖了刚拿到的 eax？不，改的是 edx）
    mov  eax, [edx-0xC]        ; ★★ 错误：用「源宽串字符数」当 UTF-8 字节数
    mov  ecx, [esp+4]          ; 局部 UTF-8 串数据指针
    mov  edx, [esp+0x8c]       ; hElem
    push 0
    push eax                   ; htmlLength
    push ecx                   ; utf8bytes
    push edx                   ; hElem
    call HTMLayoutSetElementHtml

0x402B50 返回时 eax = WideCharToMultiByte 的返回值 = 实际写入的 UTF-8 字节数
（其结尾只改 ebx，未改 eax）。

修复：把 0x4016A0..0x4016A5（6 字节）整体 NOP，
      保留 0x402B50 的返回值 eax 作为 htmlLength。
      因为 0x4016A6 起会用 [esp+4] 作 utf8bytes —— 与 eax 恰好配对。
"""
import os
import shutil
import subprocess
import sys
import time

EXE = r'D:\PGForever1.021\PGForever.exe'
BAK = r'D:\DSH\军事游戏汉化\pgforever\backup\PGForever.before-len-fix3.exe'

SITES = [
    (0xAA0, bytes.fromhex('8B56048B42F4'), bytes.fromhex('909090909090'),
     '0x4016A0 两条无效/错误指令 NOP，改用 0x402B50 返回的 UTF-8 字节数'),
]


def kill():
    subprocess.run(['taskkill', '/F', '/IM', 'PGForever.exe'], capture_output=True)
    time.sleep(0.8)


def status(raw=None):
    raw = raw or open(EXE, 'rb').read()
    for off, old, new, desc in SITES:
        cur = raw[off:off + len(old)]
        st = '原始' if cur == old else ('已修复' if cur == new else '未知(%s)' % cur.hex())
        print('  file %#07x  %-10s %s' % (off, st, desc))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'status'
    if mode == 'status':
        print('当前状态：'); status(); return
    raw = open(EXE, 'rb').read()
    if mode == 'apply':
        if not os.path.exists(BAK):
            os.makedirs(os.path.dirname(BAK), exist_ok=True)
            kill(); shutil.copy2(EXE, BAK); print('备份 -> %s' % BAK)
        for off, old, new, desc in SITES:
            cur = raw[off:off + len(old)]
            if cur not in (old, new):
                print('!! file %#x 字节不符 %s' % (off, cur.hex())); return
        kill()
        buf = bytearray(raw)
        for off, old, new, desc in SITES:
            buf[off:off + len(new)] = new
            print('patch %#07x  %s -> %s' % (off, old.hex(), new.hex()))
        open(EXE, 'wb').write(bytes(buf))
        n = open(EXE, 'rb').read()
        print('大小 %d -> %d  %s' % (len(raw), len(n), 'OK' if len(n) == len(raw) else '!!! 变了'))
        status()
    elif mode == 'revert':
        if not os.path.exists(BAK):
            print('无备份'); return
        kill(); shutil.copy2(BAK, EXE); print('已回滚'); status()
    else:
        print(__doc__)


main()
