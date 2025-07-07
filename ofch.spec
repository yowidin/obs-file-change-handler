block_cipher = None


main_app_analysis = Analysis(
    ['src/obs_file_change_handler/__main__.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

main_pyz = PYZ(main_app_analysis.pure, main_app_analysis.zipped_data, cipher=block_cipher)

exe_main = EXE(
    main_pyz,
    main_app_analysis.scripts,
    main_app_analysis.binaries,
    main_app_analysis.zipfiles,
    main_app_analysis.datas,
    [],
    name='obs-file-change-handler',
    icon=None,
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

app = BUNDLE(
    exe_main,
    name='obs-file-change-handler.app',
    icon=None,
    bundle_identifier=None,
)