# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('bcr1-f138d-firebase-adminsdk-fbsvc-80d050eafd.json', '.'),
        ('client_secret_566200628496-j4aftfn1hfc7id1c7ju35csr38mnl97m.apps.googleusercontent.com.json', '.')
    ],
    hiddenimports=['user.transaksi', 'login_admin', 'admin.dashboard', 'admin.barang', 'admin.konfirmasi', 'admin.pembayaran', 'midtrans_webhook', 'midtrans_snap', 'midtrans_config'],
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
    name='Aplikasi_BC_SMKN13',
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
