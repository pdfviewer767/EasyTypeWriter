# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

project_root = Path(SPECPATH)
runtime_data_files = [
    "lessons_ar.json",
    "lessons_en.json",
    "practice_ar.json",
    "practice_en.json",
    "tests_ar.json",
    "tests_en.json",
    "messages.json",
    "finger_positions.json",
]
datas = [
    (str(project_root / "assets"), "assets"),
    (str(project_root / "styles"), "styles"),
]
datas.extend(
    (str(project_root / "data" / filename), "data")
    for filename in runtime_data_files
)
datas.extend(
    (str(project_root / "data" / "translations" / f"{lang}.json"), "data/translations")
    for lang in ["ar", "en"]
)

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
    name="EasyTypeWriter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
