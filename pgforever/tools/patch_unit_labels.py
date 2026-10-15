# -*- coding: utf-8 -*-
r"""
P7：单元信息栏 Fuel/Ammo 标签汉化 + 地形格名称汉化

问题（用户第三轮截图）
    ① 单元栏显示 `Fuel:0  Ammo:7`  —— 标签是 exe 硬编码
    ② 地形格信息显示 `Clear (5,11)` —— 地形名来自 Scenario\MAPNAMES.STR

一、exe 硬编码（NUL 终止宽串，等长替换）
    `Fuel:%d` @0x8A95C  ->  `燃料:%d`
    `Ammo:%d` @0x8A96C  ->  `弹药:%d`

二、MAPNAMES.STR（定长记录表）
    结构： 2 字节小端计数 N  +  N 条 × 20 字节记录（记录内为单字节字符串，NUL 补满）
    记录 0..13 为地形名：Clear/Coast/Ocean/Port/River/Mountain/Airfield/Swamp/
                        City/Rough/Forest/Desert/Fortification/Bocage
    记录 14..  为地名（城市/地图名），本次不动（数量大、且多为专名，按口径保留原文）。

    单字节编码 → 中文写 **UTF-8**（不是 GBK！）
    ★ 原因：本工程已给 exe 内嵌 manifest 加 `<activeCodePage>UTF-8</activeCodePage>`，
      该进程 CP_ACP = 65001。引擎把这些单字节按 CP_ACP 解码成宽字符时，
      按 UTF-8 解析 —— 若写入 GBK 字节会变成无效序列 → 显示成一个个空方框。
      （实测踩过：写 GBK 后地形名显示为 `□□□□□□□`）
    20 字节槽位可放最多 6 个汉字（3 字节/字），写后用 NUL 填满整个槽位，
    **记录数与文件大小都不变**。
"""
import os
import shutil
import struct
import sys

EXE = r'D:\PGForever1.021\PGForever.exe'
BAK_EXE = r'D:\DSH\军事游戏汉化\pgforever\backup\PGForever.before-P7-units.exe'

# 逐场景目录里的 MAPNAMES.STR（各 game 有自己的一份）
# 实际用 os.scandir 扫描，避免手写目录名漏项
GAME_ROOT = r'D:\PGForever1.021'

# 地形名（记录索引 0..13）-> 中文
TERRAIN = {
    0:  '开阔地',       # Clear
    1:  '海岸',         # Coast
    2:  '海洋',         # Ocean
    3:  '港口',         # Port
    4:  '河流',         # River
    5:  '山地',         # Mountain
    6:  '机场',         # Airfield
    7:  '沼泽',         # Swamp
    8:  '城市',         # City
    9:  '起伏地',       # Rough
    10: '森林',         # Forest
    11: '沙漠',         # Desert
    12: '要塞',         # Fortification
    13: '树篱地',       # Bocage
}

REC = 20


def patch_exe():
    data = bytearray(open(EXE, 'rb').read())
    size0 = len(data)
    if not os.path.exists(BAK_EXE):
        shutil.copy2(EXE, BAK_EXE)
        print('已备份 exe ->', BAK_EXE)

    for en, off in (('Fuel:%d', 0x8A95C), ('Ammo:%d', 0x8A96C)):
        zh = {'Fuel:%d': '燃料:%d', 'Ammo:%d': '弹药:%d'}[en]
        cur = data[off:off + len(en) * 2].decode('utf-16-le').rstrip('\x00')
        if cur == zh:
            print('  %-8s 已是目标值，跳过' % en)
            continue
        assert cur == en, '偏移核对失败 @%X：%r' % (off, cur)
        raw = zh + '\x00' * (len(en) - len(zh))
        data[off:off + len(en) * 2] = raw.encode('utf-16-le')
        print('  %-8s -> %-8s @0x%X (占 %d 字符)' % (en, zh, off, len(en)))

    assert len(data) == size0, 'exe 大小变化！'
    open(EXE, 'wb').write(bytes(data))
    print('exe 已写入，大小 %d 字节（未变）\n' % len(data))


def patch_mapnames(path):
    raw = bytearray(open(path, 'rb').read())
    size0 = len(raw)
    cnt = struct.unpack_from('<H', raw, 0)[0]
    # 部分文件在记录数组之后还有 \r\n / 0x1A / 填充字节，只要求「不小于」数组长度
    if 2 + cnt * REC > size0:
        return '结构不符(计数%d 需%d 实际%d)' % (cnt, 2 + cnt * REC, size0)

    # 只改地形名（记录 0..13），地名记录保持原文
    changed = 0
    for idx, zh in TERRAIN.items():
        off = 2 + idx * REC
        enc = zh.encode('utf-8')       # ★ 必须 UTF-8（该进程 CP_ACP=UTF-8）
        if len(enc) >= REC:
            return '地形 %d 译文过长 (%d >= %d)' % (idx, len(enc), REC)
        raw[off:off + REC] = enc + b'\x00' * (REC - len(enc))
        changed += 1
    assert len(raw) == size0, '文件大小变化！'
    open(path, 'wb').write(bytes(raw))
    return '改 %d 条地形名（原 %d 字节，现 %d 字节）' % (changed, size0, len(raw))


def main():
    patch_exe()
    ok = 0
    for g in sorted(os.listdir(GAME_ROOT)):
        scen = os.path.join(GAME_ROOT, g, 'Scenario')
        if not os.path.isdir(scen):
            continue
        for fn in os.listdir(scen):
            if fn.lower() == 'mapnames.str':
                r = patch_mapnames(os.path.join(scen, fn))
                print('  %-34s %s' % (g, r))
                ok += 1
    print('\n共处理 %d 个 MAPNAMES.STR' % ok)
    return 0


sys.exit(main())
