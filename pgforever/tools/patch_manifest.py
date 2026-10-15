# -*- coding: utf-8 -*-
r"""
把 PGForever.exe 的嵌入 manifest 换成精简版 + activeCodePage=UTF-8。
- 目标位置：文件偏移 0xAC27C，资源数据区大小 346 字节（Size 字段不变）
- 新 XML 246 字节，其余用空格填充 => 文件大小与资源结构零改动
- 删除 trustInfo 只会让程序回到默认的 asInvoker 行为（与原声明一致）

作用：使本进程 CP_ACP = 65001(UTF-8)，从而让引擎输出的窄字符文本
      被 HTMLayout（按 UTF-8 解析）正确显示中文。只影响该进程。
"""
import shutil
import struct

EXE = r'D:\PGForever1.021\PGForever.exe'
BAK = r'D:\DSH\军事游戏汉化\pgforever\backup\origin\PGForever.exe'

NEW_XML = (b'<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">'
           b'<application><windowsSettings><activeCodePage '
           b'xmlns="http://schemas.microsoft.com/SMI/2019/WindowsSettings">UTF-8'
           b'</activeCodePage></windowsSettings></application></assembly>')

data = bytearray(open(EXE, 'rb').read())
orig_size = len(data)

xml_off = data.find(b'<assembly')
assert xml_off == 0xAC27C, 'manifest 偏移与预期不符: 0x%X' % xml_off

# 读资源数据条目确认 Size（在数据条目里反查）
rsrc_file, rsrc_rva = 0xA3600, 0xA8000
xml_rva = rsrc_rva + (xml_off - rsrc_file)
entry = data.find(struct.pack('<I', xml_rva), rsrc_file, rsrc_file + 36312)
size, codepage, _ = struct.unpack_from('<III', data, entry + 4)
print('资源数据条目 @0x%X  Size=%d  CodePage=%d' % (entry, size, codepage))
assert size >= len(NEW_XML), '资源数据区放不下新 manifest'

block = NEW_XML + b' ' * (size - len(NEW_XML))
data[xml_off:xml_off + size] = block
assert len(data) == orig_size, '文件大小变化'
open(EXE, 'wb').write(bytes(data))
print('已写入：新 manifest %d 字节 + 空格填充 %d 字节 = %d 字节（Size 字段未改动）'
      % (len(NEW_XML), size - len(NEW_XML), size))

chk = open(EXE, 'rb').read()
s = chk.find(b'<assembly')
e = chk.find(b'</assembly>', s)
print()
print('=== 现在的 manifest ===')
print(chk[s:e + 11].decode('utf-8'))
print()
print('activeCodePage 已写入:', b'activeCodePage' in chk, ' 文件大小:', len(chk))
