# -*- mode: python ; coding: utf-8 -*-
# 1フォルダ形式。Qt は同梱したものを差し替えできる配置のままにする。

a = Analysis(
    ["prismshot/ui/app.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=["PySide6"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PrismShotFrame",
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="PrismShotFrame",
)
