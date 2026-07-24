# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

# 确保打包前 templates 和 output 目录存在，避免 CI 环境报错
os.makedirs('templates', exist_ok=True)
os.makedirs('output', exist_ok=True)

# 打包静态文件
added_files = [
    ('templates', 'templates'),
    ('output', 'output'),
]

# 隐式依赖
hidden_imports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.http.h11_impl',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'pydantic',
    'jinja2',
    'sqlite3',
    'requests',
    'bs4',
    'openai',
    'src.server',
    'src.engine',
    'src.models',
    'src.db',
    'src.renderer',
    'src.deepseek_client',
    'src.adapters.counselor_adapter'
]

a = Analysis(
    ['src/app_launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='JobHunter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
