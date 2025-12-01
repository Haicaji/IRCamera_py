# -*- mode: python ; coding: utf-8 -*-
"""
IR Camera Viewer - PyInstaller 打包配置
"""

import sys
import os
import glob
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_dynamic_libs

# 收集 winrt 相关的所有模块
hiddenimports = []
binaries = []
datas = []

# 找到 winrt 包的位置
import importlib.util
spec = importlib.util.find_spec('winrt')
if spec and spec.submodule_search_locations:
    winrt_path = spec.submodule_search_locations[0]
    
    # 收集所有 .pyd 文件
    pyd_files = glob.glob(os.path.join(winrt_path, '*.pyd'))
    for pyd in pyd_files:
        binaries.append((pyd, 'winrt'))
    
    # 收集 msvcp140.dll
    dll_files = glob.glob(os.path.join(winrt_path, '*.dll'))
    for dll in dll_files:
        binaries.append((dll, 'winrt'))
    
    # 收集 .pyi 文件
    pyi_files = glob.glob(os.path.join(winrt_path, '*.pyi'))
    for pyi in pyi_files:
        datas.append((pyi, 'winrt'))
    
    # 收集子目录
    for subdir in ['runtime', 'system', 'windows']:
        subdir_path = os.path.join(winrt_path, subdir)
        if os.path.isdir(subdir_path):
            for root, dirs, files in os.walk(subdir_path):
                rel_path = os.path.relpath(root, winrt_path)
                dest = os.path.join('winrt', rel_path)
                for f in files:
                    src = os.path.join(root, f)
                    datas.append((src, dest))

# 添加 winrt 模块的导入名称
hiddenimports += [
    'winrt',
    'winrt.runtime',
    'winrt.system',
    'winrt.windows',
    'winrt.windows.devices',
    'winrt.windows.devices.enumeration',
    'winrt.windows.media',
    'winrt.windows.media.capture',
    'winrt.windows.media.capture.frames',
    'winrt.windows.graphics',
    'winrt.windows.graphics.imaging',
    'winrt.windows.foundation',
    'winrt.windows.foundation.collections',
    'winrt.windows.storage',
    'winrt.windows.storage.streams',
]

# 添加其他隐藏导入
hiddenimports += [
    'cv2',
    'numpy',
    'asyncio',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='IRCameraViewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设为 False 隐藏控制台窗口，设为 True 显示控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 如果有图标文件，可以在这里指定，如 icon='icon.ico'
)
