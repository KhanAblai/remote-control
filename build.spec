# -*- mode: python -*-
from PyInstaller.utils.hooks import collect_all
import os
import sys

# Определяем путь к Python и Tcl/Tk
python_dir = sys.base_prefix
tcl_dir = os.path.join(python_dir, 'tcl')
tkinter_dll = os.path.join(python_dir, 'DLLs', '_tkinter.pyd')

# Проверяем существование путей
if not os.path.exists(tcl_dir):
    raise FileNotFoundError(f"Tcl directory not found: {tcl_dir}")
if not os.path.exists(tkinter_dll):
    raise FileNotFoundError(f"Tkinter DLL not found: {tkinter_dll}")

# Собираем данные
datas, binaries, hiddenimports = collect_all('websockets')
datas += collect_all('pyautogui')[0]
datas += collect_all('pyperclip')[0]

# Добавляем Tcl/Tk
datas += [
    (os.path.join(tcl_dir, '**', '*'), 'tcl'),  # Рекурсивное копирование
    (tkinter_dll, '.'),
    (os.path.join(python_dir, 'DLLs', 'tcl86t.dll'), '.'),
    (os.path.join(python_dir, 'DLLs', 'tk86t.dll'), '.')
]

a = Analysis(
    ['client.py'],
    pathex=['.'],
     datas=[
        (r'C:\Python310\tcl\*', 'tcl'),
        (r'C:\Python310\DLLs\_tkinter.pyd', '.'),
        (r'C:\Python310\DLLs\tcl86t.dll', '.'),
        (r'C:\Python310\DLLs\tk86t.dll', '.')
    ],
    binaries=binaries,
    hiddenimports=hiddenimports + [
        'client_core',
        'websockets',
        'pyautogui',
        'asyncio.windows_events'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='RemoteClickController',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Для отладки
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)